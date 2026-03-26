# 分类体系迁移服务器部署脚本（简化版）
# 部署到服务器 43.143.139.197
# 使用方法: .\scripts\deploy-to-server-43-simple.ps1

$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "分类体系迁移服务器部署脚本" -ForegroundColor Cyan
Write-Host "目标服务器: 43.143.139.197" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$ServerIP = "43.143.139.197"
$ServerUser = "root"
$ServerPath = "/opt/enterprise-ai-platform"
$PROJECT_ROOT = if ($PSScriptRoot) { Split-Path $PSScriptRoot -Parent } else { $PWD }

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# 步骤1: 检查SSH连接
Write-Host "[1/6] 检查SSH连接..." -ForegroundColor Yellow
try {
    $testResult = ssh -o ConnectTimeout=5 "${ServerUser}@${ServerIP}" "echo 'SSH连接成功'" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Info "SSH连接正常"
    } else {
        Write-Error "SSH连接失败"
        exit 1
    }
} catch {
    Write-Error "SSH连接失败: $($_.Exception.Message)"
    exit 1
}

# 步骤2: 上传代码文件
Write-Host ""
Write-Host "[2/6] 上传代码文件到服务器..." -ForegroundColor Yellow

$filesToUpload = @(
    "database\src\migrations\versions\028_add_classification_dimensions.py"
    "metadata-service\src\models\data_asset.py"
    "metadata-service\src\models\ai_model.py"
    "metadata-service\src\models\workflow_metadata.py"
    "metadata-service\src\models\business_entity.py"
    "metadata-service\src\services\metadata_catalog.py"
    "metadata-service\src\api\data_assets.py"
    "metadata-service\src\api\ai_models.py"
    "metadata-service\src\api\workflows.py"
    "metadata-service\src\api\business_entities.py"
    "metadata-service\src\api\classification_migration.py"
    "metadata-service\src\utils\classification_migration.py"
    "metadata-service\src\main.py"
    "web-ui\src\lib\metadata-classification.ts"
    "web-ui\src\lib\classification-standards.ts"
    "web-ui\src\components\metadata\ClassificationDimensionEditor.tsx"
    "web-ui\src\components\metadata\index.ts"
    "web-ui\src\app\admin\metadata\page.tsx"
)

$uploaded = 0
$failed = 0

foreach ($relativePath in $filesToUpload) {
    $localPath = Join-Path $PROJECT_ROOT $relativePath
    $remotePath = "$ServerPath/$relativePath".Replace('\', '/')
    
    if (Test-Path $localPath) {
        Write-Host "  上传: $(Split-Path $localPath -Leaf)..." -ForegroundColor Gray
        
        # 确保远程目录存在
        $remoteDir = Split-Path $remotePath -Parent
        ssh "${ServerUser}@${ServerIP}" "mkdir -p `"$remoteDir`"" 2>&1 | Out-Null
        
        # 上传文件
        scp $localPath "${ServerUser}@${ServerIP}:$remotePath" 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            $uploaded++
        } else {
            Write-Warn "文件上传失败: $relativePath"
            $failed++
        }
    } else {
        Write-Warn "文件不存在: $localPath"
        $failed++
    }
}

Write-Info "文件上传完成: $uploaded 成功, $failed 失败"

if ($failed -gt 0) {
    $continue = Read-Host "部分文件上传失败，是否继续？(yes/no)"
    if ($continue -ne "yes") {
        exit 1
    }
}

# 步骤3: 备份数据库
Write-Host ""
Write-Host "[3/6] 备份数据库..." -ForegroundColor Yellow
$backupCmd = "mkdir -p /backup/database; docker exec enterprise-ai-postgres pg_dump -U ai_user -d ai_platform -F c -f /tmp/backup_before_028_$(date +%Y%m%d_%H%M%S).dump; docker cp enterprise-ai-postgres:/tmp/backup_before_028_*.dump /backup/database/ 2>&1"
ssh "${ServerUser}@${ServerIP}" $backupCmd 2>&1 | Out-Null
Write-Info "数据库备份完成（如果失败请手动检查）"

# 步骤4: 执行数据库迁移
Write-Host ""
Write-Host "[4/6] 执行数据库迁移..." -ForegroundColor Yellow

# 构建迁移命令
Write-Info "执行Alembic迁移..."
$migrationCmd = "cd $ServerPath; docker-compose run --rm -e DB_HOST=postgres -e DB_PORT=5432 -e DB_USER=ai_user -e DB_PASSWORD=ai_password -e DB_NAME=ai_platform metadata-service sh -c 'cd /database/src/migrations; alembic upgrade head'"
$migrationOutput = ssh "${ServerUser}@${ServerIP}" $migrationCmd 2>&1
Write-Host $migrationOutput -ForegroundColor Gray

if ($LASTEXITCODE -eq 0) {
    Write-Info "数据库迁移完成"
    
    # 验证迁移结果
    Write-Info "验证迁移结果..."
    $checkCmd = "docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -t -c 'SELECT COUNT(*) FROM information_schema.columns WHERE table_name = ''data_assets'' AND column_name = ''classification_dimensions'';'"
    $checkResult = ssh "${ServerUser}@${ServerIP}" $checkCmd
    
    if ($checkResult -and [int]$checkResult.Trim() -gt 0) {
        Write-Info "✓ 字段验证通过：classification_dimensions 字段已创建"
    } else {
        Write-Error "字段验证失败：classification_dimensions 字段不存在"
        exit 1
    }
} else {
    Write-Error "数据库迁移失败"
    exit 1
}

# 步骤5: 重启服务
Write-Host ""
Write-Host "[5/6] 重启服务..." -ForegroundColor Yellow
ssh "${ServerUser}@${ServerIP}" "cd $ServerPath; docker-compose restart metadata-service; docker-compose restart web-ui" 2>&1 | Out-Null
Write-Info "服务已重启，等待启动..."

Start-Sleep -Seconds 10

# 检查服务状态
$maxRetries = 30
$retryCount = 0
$API_URL = "http://$ServerIP:8005"

while ($retryCount -lt $maxRetries) {
    try {
        $response = Invoke-WebRequest -Uri "$API_URL/api/health" -Method GET -TimeoutSec 5 -UseBasicParsing 2>&1
        if ($response.StatusCode -eq 200) {
            Write-Info "metadata-service已就绪"
            break
        }
    } catch {
        # 继续重试
    }
    $retryCount++
    Write-Host "等待metadata-service启动... ($retryCount/$maxRetries)" -ForegroundColor Gray
    Start-Sleep -Seconds 2
}

if ($retryCount -eq $maxRetries) {
    Write-Error "metadata-service启动超时"
    exit 1
}

# 步骤6: 测试迁移工具
Write-Host ""
Write-Host "[6/6] 测试迁移工具..." -ForegroundColor Yellow

# 预览迁移结果
Write-Info "预览迁移结果..."
try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/classification/migration/preview?limit=10" -Method GET -TimeoutSec 30
    if ($response.status -eq "success") {
        Write-Info "预览成功"
    }
} catch {
    Write-Warn "预览失败: $($_.Exception.Message)"
}

# 试运行迁移
Write-Info "执行试运行迁移..."
try {
    $body = @{
        dry_run = $true
        batch_size = 10
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$API_URL/api/classification/migrate" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 60
    
    if ($response.status -eq "success") {
        Write-Info "试运行成功"
        Write-Host "统计信息:" -ForegroundColor Gray
        Write-Host ($response.stats | ConvertTo-Json -Depth 3) -ForegroundColor Gray
    }
} catch {
    Write-Warn "试运行失败: $($_.Exception.Message)"
}

# 完成
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Info "部署完成！"
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Info "下一步："
Write-Info "1. 访问前端页面验证: http://$ServerIP:3000/admin/metadata"
Write-Info "2. 检查分类维度是否正确显示"
Write-Info "3. 测试维度查询功能"
Write-Host ""
Write-Info "执行实际数据迁移（在服务器上运行）："
Write-Host "  ssh ${ServerUser}@${ServerIP} 'curl -X POST http://localhost:8005/api/classification/migrate -H Content-Type:application/json -d `"{\"dry_run\":false,\"batch_size\":100}`"'" -ForegroundColor Gray
Write-Host ""

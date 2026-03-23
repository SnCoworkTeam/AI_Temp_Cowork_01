# 分类体系迁移服务器部署脚本 (PowerShell版本)
# 部署到服务器 43.143.139.197
# 使用方法: .\scripts\deploy-classification-migration-to-server.ps1

param(
    [string]$ServerIP = "43.143.139.197",
    [string]$ServerUser = "root",
    [string]$ServerPath = "/opt/enterprise-ai-platform",
    [switch]$SkipBackup = $false,
    [switch]$SkipMigration = $false,
    [switch]$SkipDataMigration = $false,
    [switch]$SkipAPITests = $false
)

$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "分类体系迁移服务器部署脚本" -ForegroundColor Cyan
Write-Host "目标服务器: $ServerIP" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 配置变量
$PROJECT_ROOT = if ($PSScriptRoot) { Split-Path $PSScriptRoot -Parent } else { $PWD }
$DB_NAME = "ai_platform"
$DB_USER = "ai_user"
$DB_PASSWORD = "ai_password"
$API_URL = "http://$ServerIP:8005"
$BACKUP_DIR = "/backup/database"

# 函数：打印信息
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

# 函数：执行远程SSH命令
function Invoke-RemoteCommand {
    param(
        [string]$Command,
        [switch]$IgnoreError = $false
    )
    
    try {
        # 使用bash -c执行命令，避免引号嵌套问题
        $sshCommand = "ssh ${ServerUser}@${ServerIP} bash -c `"$Command`""
        $result = Invoke-Expression $sshCommand 2>&1
        $exitCode = $LASTEXITCODE
        if ($exitCode -ne 0 -and -not $IgnoreError) {
            Write-Error "远程命令执行失败 (退出码: $exitCode): $Command"
            if ($result) {
                Write-Host $result -ForegroundColor Red
            }
            return $false
        }
        return $result
    }
    catch {
        Write-Error "SSH连接失败: $($_.Exception.Message)"
        return $false
    }
}

# 函数：上传文件到服务器
function Upload-File {
    param(
        [string]$LocalPath,
        [string]$RemotePath
    )
    
    if (-not (Test-Path $LocalPath)) {
        Write-Error "本地文件不存在: $LocalPath"
        return $false
    }
    
    try {
        # 确保远程目录存在
        $remoteDir = Split-Path $RemotePath -Parent
        Invoke-RemoteCommand "mkdir -p `"$remoteDir`"" -IgnoreError | Out-Null
        
        Write-Host "  上传: $(Split-Path $LocalPath -Leaf)..." -ForegroundColor Gray
        scp -q $LocalPath "${ServerUser}@${ServerIP}:$RemotePath" 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            return $true
        } else {
            Write-Warn "文件上传失败: $LocalPath"
            return $false
        }
    }
    catch {
        Write-Warn "文件上传失败: $($_.Exception.Message)"
        return $false
    }
}

# 步骤1: 检查SSH连接
Write-Host "[1/9] 检查SSH连接..." -ForegroundColor Yellow
try {
    $testResult = ssh -o ConnectTimeout=5 "${ServerUser}@${ServerIP}" "echo 'SSH连接成功'" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Info "SSH连接正常"
    } else {
        Write-Error "SSH连接失败，请检查："
        Write-Host "  1. 服务器IP是否正确: $ServerIP" -ForegroundColor Yellow
        Write-Host "  2. SSH密钥是否配置" -ForegroundColor Yellow
        Write-Host "  3. 服务器是否可访问" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Error "SSH连接失败: $($_.Exception.Message)"
    exit 1
}

# 步骤2: 检查服务器环境
Write-Host ""
Write-Host "[2/9] 检查服务器环境..." -ForegroundColor Yellow

# 检查Docker
$dockerCheck = Invoke-RemoteCommand "docker ps" -IgnoreError
if ($dockerCheck -match "CONTAINER") {
    Write-Info "Docker运行正常"
} else {
    Write-Error "Docker未运行或无法访问"
    exit 1
}

# 检查PostgreSQL容器
$pgCheck = Invoke-RemoteCommand "docker ps --filter 'name=postgres' --format '{{.Names}}'" -IgnoreError
if ($pgCheck -match "postgres") {
    Write-Info "PostgreSQL容器运行中"
} else {
    Write-Warn "PostgreSQL容器未运行，将尝试启动"
    Invoke-RemoteCommand "cd $ServerPath && docker-compose up -d postgres" -IgnoreError
    Start-Sleep -Seconds 5
}

# 步骤3: 上传代码文件
Write-Host ""
Write-Host "[3/9] 上传代码文件到服务器..." -ForegroundColor Yellow

# 方法1: 使用rsync批量上传（推荐，如果服务器支持）
Write-Info "使用rsync批量上传文件..."

# 创建临时目录结构
$tempDir = Join-Path $env:TEMP "classification-migration-upload"
if (Test-Path $tempDir) {
    Remove-Item -Path $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# 复制需要上传的文件到临时目录
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
    if (Test-Path $localPath) {
        # 保持目录结构
        $destPath = Join-Path $tempDir $relativePath
        $destDir = Split-Path $destPath -Parent
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        Copy-Item -Path $localPath -Destination $destPath -Force
        $uploaded++
    } else {
        Write-Warn "文件不存在: $localPath"
        $failed++
    }
}

Write-Info "准备上传 $uploaded 个文件..."

# 使用rsync上传（如果可用）
$rsyncAvailable = Get-Command rsync -ErrorAction SilentlyContinue
if ($rsyncAvailable) {
    Write-Info "使用rsync上传文件..."
    $rsyncCmd = "rsync -avz --progress `"$tempDir/`" ${ServerUser}@${ServerIP}:${ServerPath}/"
    Invoke-Expression $rsyncCmd
    
    if ($LASTEXITCODE -eq 0) {
        Write-Info "文件上传成功（使用rsync）"
    } else {
        Write-Warn "rsync上传失败，尝试使用scp逐个上传"
        # 回退到scp方式
        foreach ($relativePath in $filesToUpload) {
            $localPath = Join-Path $PROJECT_ROOT $relativePath
            $remotePath = "$ServerPath/$relativePath".Replace('\', '/')
            if (Upload-File -LocalPath $localPath -RemotePath $remotePath) {
                # 已在上传函数中计数
            }
        }
    }
} else {
    # 使用scp逐个上传
    Write-Info "使用scp逐个上传文件..."
    foreach ($relativePath in $filesToUpload) {
        $localPath = Join-Path $PROJECT_ROOT $relativePath
        $remotePath = "$ServerPath/$relativePath".Replace('\', '/')
        if (Upload-File -LocalPath $localPath -RemotePath $remotePath) {
            # 已在上传函数中计数
        } else {
            $failed++
        }
    }
}

# 清理临时目录
if (Test-Path $tempDir) {
    Remove-Item -Path $tempDir -Recurse -Force
}

Write-Info "文件上传完成: $uploaded 成功, $failed 失败"

if ($failed -gt 0) {
    $continue = Read-Host "部分文件上传失败，是否继续？(yes/no)"
    if ($continue -ne "yes") {
        exit 1
    }
}

# 步骤4: 备份数据库
if (-not $SkipBackup) {
    Write-Host ""
    Write-Host "[4/9] 备份数据库..." -ForegroundColor Yellow
    
    # 在服务器上创建备份目录
    Invoke-RemoteCommand "mkdir -p $BACKUP_DIR" -IgnoreError
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = "$BACKUP_DIR/backup_before_028_$timestamp.dump"
    
    Write-Info "执行数据库备份..."
    $backupCmd1 = "docker exec enterprise-ai-postgres pg_dump -U $DB_USER -d $DB_NAME -F c -f /tmp/backup_before_028_$timestamp.dump"
    $backupCmd2 = "docker cp enterprise-ai-postgres:/tmp/backup_before_028_$timestamp.dump $backupFile"
    $backupResult1 = Invoke-RemoteCommand $backupCmd1 -IgnoreError
    $backupResult2 = Invoke-RemoteCommand $backupCmd2 -IgnoreError
    
    if ($backupResult2 -ne $false) {
        Write-Info "数据库备份成功: $backupFile"
    } else {
        Write-Warn "数据库备份失败，但继续执行"
    }
} else {
    Write-Host "[4/9] 跳过数据库备份" -ForegroundColor Gray
}

# 步骤5: 执行数据库迁移
if (-not $SkipMigration) {
    Write-Host ""
    Write-Host "[5/9] 执行数据库迁移..." -ForegroundColor Yellow
    
    Write-Info "检查当前数据库版本..."
    $versionCmd = "docker exec enterprise-ai-postgres psql -U $DB_USER -d $DB_NAME -t -c 'SELECT version_num FROM alembic_version;'"
    $fullVersionCmd = "cd $ServerPath && $versionCmd"
    $currentVersion = Invoke-RemoteCommand $fullVersionCmd
    if ($currentVersion) {
        Write-Info "当前版本: $($currentVersion.Trim())"
    }
    
    Write-Info "执行Alembic迁移..."
    # 构建迁移命令，使用单引号包裹sh命令
    $migrationCmd = "cd $ServerPath; docker-compose run --rm -e DB_HOST=postgres -e DB_PORT=5432 -e DB_USER=$DB_USER -e DB_PASSWORD=$DB_PASSWORD -e DB_NAME=$DB_NAME metadata-service sh -c 'cd /database/src/migrations; alembic upgrade head'"
    $migrationResult = Invoke-RemoteCommand $migrationCmd
    
    # 显示迁移输出
    if ($migrationResult) {
        Write-Host $migrationResult -ForegroundColor Gray
    }
    
    # 检查迁移是否成功（通过检查输出或退出码）
    $migrationSuccess = $true
    if ($migrationResult -match "error|Error|ERROR|failed|Failed|FAILED") {
        $migrationSuccess = $false
    }
    
    if ($migrationSuccess) {
        Write-Info "数据库迁移完成"
        
        # 验证迁移结果
        Write-Info "验证迁移结果..."
        $checkCmd = "docker exec enterprise-ai-postgres psql -U $DB_USER -d $DB_NAME -t -c 'SELECT COUNT(*) FROM information_schema.columns WHERE table_name = ''data_assets'' AND column_name = ''classification_dimensions'';'"
        $fullCheckCmd = "cd $ServerPath && $checkCmd"
        $checkResult = Invoke-RemoteCommand $fullCheckCmd
        
        if ($checkResult -and [int]$checkResult.Trim() -gt 0) {
            Write-Info "✓ 字段验证通过：classification_dimensions 字段已创建"
        } else {
            Write-Error "字段验证失败：classification_dimensions 字段不存在"
            Write-Host "检查结果: $checkResult" -ForegroundColor Yellow
            exit 1
        }
    } else {
        Write-Error "数据库迁移失败"
        Write-Info "查看详细日志: ssh ${ServerUser}@${ServerIP} 'cd $ServerPath && docker-compose logs metadata-service'"
        exit 1
    }
} else {
    Write-Host "[5/9] 跳过数据库迁移" -ForegroundColor Gray
}

# 步骤6: 重启metadata-service和web-ui
Write-Host ""
Write-Host "[6/9] 重启服务..." -ForegroundColor Yellow
Write-Info "重启metadata-service..."
$restartResult = Invoke-RemoteCommand "cd $ServerPath && docker-compose restart metadata-service"

Write-Info "重启web-ui（如果需要）..."
Invoke-RemoteCommand "cd $ServerPath && docker-compose restart web-ui" -IgnoreError | Out-Null

# 等待服务启动
Write-Info "等待服务启动..."
$maxRetries = 30
$retryCount = 0
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
    Write-Info "查看日志: ssh ${ServerUser}@${ServerIP} bash -c 'cd $ServerPath; docker-compose logs metadata-service'"
    exit 1
}

# 步骤7: 预览迁移结果
Write-Host ""
Write-Host "[7/9] 预览迁移结果..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/classification/migration/preview?limit=10" -Method GET -TimeoutSec 30
    if ($response.status -eq "success") {
        Write-Info "预览成功"
        Write-Host "预览统计:" -ForegroundColor Gray
        Write-Host "  数据资产: $($response.preview.data_assets.Count) 条" -ForegroundColor Gray
        Write-Host "  AI模型: $($response.preview.ai_models.Count) 条" -ForegroundColor Gray
        Write-Host "  工作流: $($response.preview.workflows.Count) 条" -ForegroundColor Gray
        Write-Host "  业务实体: $($response.preview.business_entities.Count) 条" -ForegroundColor Gray
    } else {
        Write-Warn "预览失败，但继续执行"
    }
} catch {
    Write-Warn "预览失败: $($_.Exception.Message)，但继续执行"
}

# 步骤8: 试运行迁移
Write-Host ""
Write-Host "[8/9] 执行试运行迁移..." -ForegroundColor Yellow
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
    } else {
        Write-Warn "试运行失败，但继续执行"
    }
} catch {
    Write-Warn "试运行失败: $($_.Exception.Message)"
}

# 步骤9: 执行实际数据迁移（可选）
if (-not $SkipDataMigration) {
    Write-Host ""
    Write-Host "[9/9] 执行实际数据迁移（可选）..." -ForegroundColor Yellow
    $runActual = Read-Host "是否执行实际数据迁移？(yes/no)"
    
    if ($runActual -eq "yes") {
        try {
            $body = @{
                dry_run = $false
                batch_size = 100
            } | ConvertTo-Json
            
            Write-Info "执行实际数据迁移..."
            $response = Invoke-RestMethod -Uri "$API_URL/api/classification/migrate" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 300
            
            if ($response.status -eq "success") {
                Write-Info "数据迁移成功"
                Write-Host "统计信息:" -ForegroundColor Gray
                Write-Host ($response.stats | ConvertTo-Json -Depth 3) -ForegroundColor Gray
            } else {
                Write-Error "数据迁移失败"
            }
        } catch {
            Write-Error "数据迁移失败: $($_.Exception.Message)"
        }
    } else {
        Write-Info "跳过实际数据迁移，稍后可以手动执行"
    }
} else {
    Write-Host "[9/9] 跳过实际数据迁移" -ForegroundColor Gray
}

# 步骤10: 测试API接口
if (-not $SkipAPITests) {
    Write-Host ""
    Write-Host "[10/10] 测试API接口..." -ForegroundColor Yellow
    
    $tests = @(
        @{ name = "健康检查"; url = "$API_URL/api/health" }
        @{ name = "业务领域查询"; url = "$API_URL/api/data-assets?business_domain=finance&limit=1" }
        @{ name = "技术来源查询"; url = "$API_URL/api/data-assets?technical_source=sap&limit=1" }
        @{ name = "生命周期查询"; url = "$API_URL/api/data-assets?lifecycle_stage=production&limit=1" }
        @{ name = "标签查询"; url = "$API_URL/api/data-assets?standardized_tag=biz:critical&limit=1" }
    )
    
    $passed = 0
    $failed = 0
    
    foreach ($test in $tests) {
        try {
            $response = Invoke-WebRequest -Uri $test.url -Method GET -UseBasicParsing -TimeoutSec 10
            if ($response.StatusCode -eq 200) {
                Write-Info "$($test.name) - 通过"
                $passed++
            } else {
                Write-Warn "$($test.name) - 失败 (状态码: $($response.StatusCode))"
                $failed++
            }
        }
        catch {
            Write-Warn "$($test.name) - 失败: $($_.Exception.Message)"
            $failed++
        }
    }
    
    Write-Host ""
    Write-Info "API测试完成: $passed 通过, $failed 失败"
} else {
    Write-Host "[10/10] 跳过API测试" -ForegroundColor Gray
}

# 完成
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Info "服务器部署完成！"
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Info "下一步："
Write-Info "1. 访问前端页面验证: http://$ServerIP:3000/admin/metadata"
Write-Info "2. 检查分类维度是否正确显示"
Write-Info "3. 测试维度查询功能"
Write-Host ""
Write-Info "如果尚未执行实际数据迁移，可以在服务器上运行："
Write-Host "  curl -X POST `"$API_URL/api/classification/migrate`" -H `"Content-Type: application/json`" -d '{\"dry_run\": false, \"batch_size\": 100}'" -ForegroundColor Gray
Write-Host ""
Write-Info "或者通过SSH执行："
Write-Host "  ssh ${ServerUser}@${ServerIP} 'curl -X POST http://localhost:8005/api/classification/migrate -H Content-Type:application/json -d `"{\"dry_run\":false,\"batch_size\":100}`"'" -ForegroundColor Gray
Write-Host ""









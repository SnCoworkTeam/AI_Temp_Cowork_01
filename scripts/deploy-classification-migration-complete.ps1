# 分类体系迁移完整部署脚本 (PowerShell版本)
# 使用方法: .\scripts\deploy-classification-migration-complete.ps1

param(
    [switch]$SkipBackup = $false,
    [switch]$SkipMigration = $false,
    [switch]$SkipDataMigration = $false,
    [switch]$SkipAPITests = $false
)

$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "分类体系迁移完整部署脚本" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 配置变量
$PROJECT_ROOT = if ($PSScriptRoot) { Split-Path $PSScriptRoot -Parent } else { $PWD }
$DB_NAME = "ai_platform"
$DB_USER = "ai_user"
$DB_PASSWORD = "ai_password"
$DB_HOST = "localhost"
$DB_PORT = "5432"
$API_URL = "http://localhost:8005"
$BACKUP_DIR = Join-Path $PROJECT_ROOT "backup\database"

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

# 步骤1: 检查Docker环境
Write-Host "[1/8] 检查Docker环境..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Info "Docker正在运行"
} catch {
    Write-Error "Docker未运行，请先启动Docker Desktop"
    exit 1
}

# 步骤2: 启动基础服务
Write-Host ""
Write-Host "[2/8] 启动基础服务（PostgreSQL）..." -ForegroundColor Yellow
docker-compose up -d postgres

# 等待PostgreSQL就绪
$maxRetries = 30
$retryCount = 0
while ($retryCount -lt $maxRetries) {
    try {
        $pgHealth = docker exec enterprise-ai-postgres pg_isready -U $DB_USER -d $DB_NAME 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Info "PostgreSQL已就绪"
            break
        }
    } catch {
        # 继续重试
    }
    $retryCount++
    Write-Host "等待PostgreSQL启动... ($retryCount/$maxRetries)" -ForegroundColor Gray
    Start-Sleep -Seconds 2
}

if ($retryCount -eq $maxRetries) {
    Write-Error "PostgreSQL启动超时"
    exit 1
}

# 步骤3: 备份数据库
if (-not $SkipBackup) {
    Write-Host ""
    Write-Host "[3/8] 备份数据库..." -ForegroundColor Yellow
    
    # 创建备份目录
    if (-not (Test-Path $BACKUP_DIR)) {
        New-Item -ItemType Directory -Path $BACKUP_DIR -Force | Out-Null
    }
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = Join-Path $BACKUP_DIR "backup_before_028_$timestamp.dump"
    
    Write-Info "执行数据库备份..."
    docker exec enterprise-ai-postgres pg_dump -U $DB_USER -d $DB_NAME -F c -f "/tmp/backup_before_028_$timestamp.dump"
    
    if ($LASTEXITCODE -eq 0) {
        # 从容器复制到主机
        docker cp "enterprise-ai-postgres:/tmp/backup_before_028_$timestamp.dump" $backupFile
        Write-Info "数据库备份成功: $backupFile"
    } else {
        Write-Warn "数据库备份失败，但继续执行"
    }
} else {
    Write-Host "[3/8] 跳过数据库备份" -ForegroundColor Gray
}

# 步骤4: 执行数据库迁移
if (-not $SkipMigration) {
    Write-Host ""
    Write-Host "[4/8] 执行数据库迁移..." -ForegroundColor Yellow
    
    # 检查迁移文件
    $migrationFile = Join-Path $PROJECT_ROOT "database\src\migrations\versions\028_add_classification_dimensions.py"
    if (-not (Test-Path $migrationFile)) {
        Write-Error "迁移文件不存在: $migrationFile"
        exit 1
    }
    
    Write-Info "检查当前数据库版本..."
    docker exec enterprise-ai-postgres psql -U $DB_USER -d $DB_NAME -c "SELECT version_num FROM alembic_version;" 2>&1 | Out-Null
    
    Write-Info "执行Alembic迁移..."
    # 使用metadata-service容器执行迁移（因为它有完整的Python环境）
    docker-compose run --rm `
        -e DB_HOST=postgres `
        -e DB_PORT=5432 `
        -e DB_USER=$DB_USER `
        -e DB_PASSWORD=$DB_PASSWORD `
        -e DB_NAME=$DB_NAME `
        metadata-service sh -c "cd /database/src/migrations && alembic upgrade head"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Info "数据库迁移完成"
    } else {
        Write-Error "数据库迁移失败"
        Write-Info "查看详细日志: docker-compose logs metadata-service"
        exit 1
    }
    
    # 验证迁移结果
    Write-Info "验证迁移结果..."
    $checkResult = docker exec enterprise-ai-postgres psql -U $DB_USER -d $DB_NAME -t -c `
        "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'data_assets' AND column_name = 'classification_dimensions';"
    
    if ($checkResult -and [int]$checkResult.Trim() -gt 0) {
        Write-Info "✓ 字段验证通过：classification_dimensions 字段已创建"
    } else {
        Write-Error "字段验证失败：classification_dimensions 字段不存在"
        exit 1
    }
} else {
    Write-Host "[4/8] 跳过数据库迁移" -ForegroundColor Gray
}

# 步骤5: 启动metadata-service
Write-Host ""
Write-Host "[5/8] 启动metadata-service..." -ForegroundColor Yellow
docker-compose up -d --build metadata-service

# 等待服务启动
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
    Write-Info "查看日志: docker-compose logs metadata-service"
    exit 1
}

# 步骤6: 预览迁移结果
Write-Host ""
Write-Host "[6/8] 预览迁移结果..." -ForegroundColor Yellow
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

# 步骤7: 试运行迁移
Write-Host ""
Write-Host "[7/8] 执行试运行迁移..." -ForegroundColor Yellow
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

# 步骤8: 执行实际数据迁移（可选）
if (-not $SkipDataMigration) {
    Write-Host ""
    Write-Host "[8/8] 执行实际数据迁移（可选）..." -ForegroundColor Yellow
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
    Write-Host "[8/8] 跳过实际数据迁移" -ForegroundColor Gray
}

# 步骤9: 测试API接口
if (-not $SkipAPITests) {
    Write-Host ""
    Write-Host "[9/9] 测试API接口..." -ForegroundColor Yellow
    
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
    Write-Host "[9/9] 跳过API测试" -ForegroundColor Gray
}

# 完成
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Info "部署完成！"
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Info "下一步："
Write-Info "1. 访问前端页面验证: http://localhost:3000/admin/metadata"
Write-Info "2. 检查分类维度是否正确显示"
Write-Info "3. 测试维度查询功能"
Write-Host ""
Write-Info "如果尚未执行实际数据迁移，可以运行："
Write-Host "  curl -X POST `"$API_URL/api/classification/migrate`" -H `"Content-Type: application/json`" -d '{\"dry_run\": false, \"batch_size\": 100}'" -ForegroundColor Gray
Write-Host ""









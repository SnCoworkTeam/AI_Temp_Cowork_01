# 分类体系迁移本地部署脚本 (PowerShell版本)
# 使用方法: .\scripts\deploy-classification-migration-local.ps1

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "分类体系迁移本地部署脚本" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 配置变量（根据实际环境调整）
$PROJECT_ROOT = $PSScriptRoot + "\.."
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

# 函数：检查Docker容器
function Test-DockerContainer {
    param([string]$ContainerName)
    
    $container = docker ps --filter "name=$ContainerName" --format "{{.Names}}"
    if ($container) {
        Write-Info "Docker容器 '$ContainerName' 运行中"
        return $true
    } else {
        Write-Warn "Docker容器 '$ContainerName' 未运行"
        return $false
    }
}

# 函数：检查服务
function Test-Service {
    Write-Info "检查 Metadata Service 状态..."
    
    try {
        $response = Invoke-WebRequest -Uri "$API_URL/api/health" -Method GET -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Info "Metadata Service 运行正常"
            return $true
        }
    }
    catch {
        Write-Warn "Metadata Service 未运行或无法访问: $($_.Exception.Message)"
        return $false
    }
}

# 函数：备份数据库
function Backup-Database {
    Write-Info "开始备份数据库..."
    
    # 创建备份目录
    if (-not (Test-Path $BACKUP_DIR)) {
        New-Item -ItemType Directory -Path $BACKUP_DIR -Force | Out-Null
    }
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = Join-Path $BACKUP_DIR "backup_before_028_$timestamp.dump"
    
    # 检查PostgreSQL容器
    $postgresContainer = docker ps --filter "name=postgres" --format "{{.Names}}" | Select-Object -First 1
    
    if ($postgresContainer) {
        Write-Info "使用Docker容器备份: $postgresContainer"
        # 在容器内执行备份
        docker exec $postgresContainer pg_dump -U $DB_USER -d $DB_NAME -F c -f "/tmp/backup_before_028_$timestamp.dump"
        
        if ($LASTEXITCODE -eq 0) {
            # 从容器复制到主机
            docker cp "${postgresContainer}:/tmp/backup_before_028_$timestamp.dump" $backupFile
            Write-Info "数据库备份成功: $backupFile"
            return $true
        } else {
            Write-Error "数据库备份失败"
            return $false
        }
    } else {
        # 尝试直接连接（如果PostgreSQL在主机上）
        Write-Info "尝试直接连接PostgreSQL..."
        $env:PGPASSWORD = $DB_PASSWORD
        $backupCmd = "pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -F c -f `"$backupFile`""
        
        try {
            Invoke-Expression $backupCmd
            if ($LASTEXITCODE -eq 0) {
                Write-Info "数据库备份成功: $backupFile"
                return $true
            } else {
                Write-Error "数据库备份失败"
                return $false
            }
        }
        catch {
            Write-Error "数据库备份失败: $($_.Exception.Message)"
            Write-Warn "请手动备份数据库或确保PostgreSQL可访问"
            return $false
        }
    }
}

# 函数：执行数据库迁移
function Start-DatabaseMigration {
    Write-Info "开始执行数据库迁移..."
    
    $migrationDir = Join-Path $PROJECT_ROOT "database\src\migrations"
    
    if (-not (Test-Path $migrationDir)) {
        Write-Error "迁移目录不存在: $migrationDir"
        return $false
    }
    
    # 检查迁移文件
    $migrationFile = Join-Path $migrationDir "versions\028_add_classification_dimensions.py"
    if (-not (Test-Path $migrationFile)) {
        Write-Error "迁移文件不存在: $migrationFile"
        return $false
    }
    
    Write-Info "迁移文件存在: $migrationFile"
    
    # 检查当前版本
    Push-Location (Join-Path $PROJECT_ROOT "database\src\migrations")
    try {
        Write-Info "检查当前数据库版本..."
        
        # 设置环境变量
        $env:DB_HOST = $DB_HOST
        $env:DB_PORT = $DB_PORT
        $env:DB_USER = $DB_USER
        $env:DB_PASSWORD = $DB_PASSWORD
        $env:DB_NAME = $DB_NAME
        
        # 检查alembic是否可用
        $alembicCheck = Get-Command alembic -ErrorAction SilentlyContinue
        if (-not $alembicCheck) {
            Write-Warn "alembic命令未找到，尝试使用Python模块..."
            # 尝试使用Python运行
            $pythonCmd = "python -m alembic current"
            $currentVersion = Invoke-Expression $pythonCmd 2>&1
            Write-Info "当前版本: $currentVersion"
        } else {
            $currentVersion = alembic current 2>&1
            Write-Info "当前版本: $currentVersion"
        }
        
        # 执行迁移
        Write-Info "执行迁移到最新版本..."
        if ($alembicCheck) {
            alembic upgrade head
        } else {
            python -m alembic upgrade head
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Info "数据库迁移成功"
            return $true
        } else {
            Write-Error "数据库迁移失败"
            return $false
        }
    }
    catch {
        Write-Error "迁移执行出错: $($_.Exception.Message)"
        return $false
    }
    finally {
        Pop-Location
    }
}

# 函数：验证迁移结果
function Test-MigrationResult {
    Write-Info "验证迁移结果..."
    
    $postgresContainer = docker ps --filter "name=postgres" --format "{{.Names}}" | Select-Object -First 1
    
    if ($postgresContainer) {
        # 在容器内执行验证
        $checkCmd = "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'data_assets' AND column_name = 'classification_dimensions';"
        $result = docker exec $postgresContainer psql -U $DB_USER -d $DB_NAME -t -c $checkCmd
        
        if ($result -and [int]$result.Trim() -gt 0) {
            Write-Info "字段验证通过：classification_dimensions 字段已创建"
            return $true
        } else {
            Write-Error "字段验证失败：classification_dimensions 字段不存在"
            return $false
        }
    } else {
        Write-Warn "无法验证迁移结果（PostgreSQL容器未运行）"
        return $true  # 假设成功，让用户手动验证
    }
}

# 函数：重启服务
function Restart-Services {
    Write-Info "重启服务..."
    
    # 检查docker-compose.yml
    $dockerComposeFile = Join-Path $PROJECT_ROOT "docker-compose.yml"
    if (Test-Path $dockerComposeFile) {
        Write-Info "使用docker-compose重启metadata-service..."
        Push-Location $PROJECT_ROOT
        try {
            docker-compose restart metadata-service
            if ($LASTEXITCODE -eq 0) {
                Write-Info "metadata-service已重启"
                
                # 等待服务启动
                Write-Info "等待服务启动..."
                $maxRetries = 30
                $retryCount = 0
                while ($retryCount -lt $maxRetries) {
                    Start-Sleep -Seconds 2
                    if (Test-Service) {
                        Write-Info "服务已就绪"
                        return $true
                    }
                    $retryCount++
                    Write-Host "等待中... ($retryCount/$maxRetries)" -ForegroundColor Gray
                }
                
                Write-Warn "服务启动超时，请手动检查"
                return $false
            } else {
                Write-Error "服务重启失败"
                return $false
            }
        }
        finally {
            Pop-Location
        }
    } else {
        Write-Warn "docker-compose.yml不存在，跳过服务重启"
        Write-Info "请手动重启metadata-service"
        return $true
    }
}

# 函数：预览迁移
function Test-PreviewMigration {
    Write-Info "预览迁移结果（试运行）..."
    
    if (-not (Test-Service)) {
        Write-Warn "服务未运行，跳过预览"
        return $false
    }
    
    try {
        $response = Invoke-RestMethod -Uri "$API_URL/api/classification/migration/preview?limit=10" -Method GET
        if ($response.status -eq "success") {
            Write-Info "预览成功"
            Write-Host ($response | ConvertTo-Json -Depth 5) -ForegroundColor Gray
            return $true
        } else {
            Write-Error "预览失败"
            return $false
        }
    }
    catch {
        Write-Error "预览失败: $($_.Exception.Message)"
        return $false
    }
}

# 函数：执行试运行迁移
function Test-DryRunMigration {
    Write-Info "执行试运行迁移..."
    
    if (-not (Test-Service)) {
        Write-Warn "服务未运行，跳过试运行"
        return $false
    }
    
    $body = @{
        dry_run = $true
        batch_size = 10
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$API_URL/api/classification/migrate" -Method POST -Body $body -ContentType "application/json"
        if ($response.status -eq "success") {
            Write-Info "试运行成功"
            Write-Info "统计信息:"
            Write-Host ($response.stats | ConvertTo-Json -Depth 5) -ForegroundColor Gray
            return $true
        } else {
            Write-Error "试运行失败"
            return $false
        }
    }
    catch {
        Write-Error "试运行失败: $($_.Exception.Message)"
        return $false
    }
}

# 函数：执行实际迁移
function Start-ActualMigration {
    Write-Warn "即将执行实际数据迁移，这将更新数据库！"
    $confirm = Read-Host "确认继续？(yes/no)"
    
    if ($confirm -ne "yes") {
        Write-Info "已取消迁移"
        return $false
    }
    
    Write-Info "执行实际数据迁移..."
    
    if (-not (Test-Service)) {
        Write-Error "服务未运行，无法执行迁移"
        return $false
    }
    
    $body = @{
        dry_run = $false
        batch_size = 100
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$API_URL/api/classification/migrate" -Method POST -Body $body -ContentType "application/json"
        if ($response.status -eq "success") {
            Write-Info "数据迁移成功"
            Write-Info "统计信息:"
            Write-Host ($response.stats | ConvertTo-Json -Depth 5) -ForegroundColor Gray
            return $true
        } else {
            Write-Error "数据迁移失败"
            return $false
        }
    }
    catch {
        Write-Error "数据迁移失败: $($_.Exception.Message)"
        return $false
    }
}

# 函数：测试API
function Test-ClassificationAPI {
    Write-Info "测试分类维度查询API..."
    
    if (-not (Test-Service)) {
        Write-Warn "服务未运行，跳过API测试"
        return $false
    }
    
    $tests = @(
        @{ name = "业务领域查询"; url = "$API_URL/api/data-assets?business_domain=finance&limit=1" }
        @{ name = "技术来源查询"; url = "$API_URL/api/data-assets?technical_source=sap&limit=1" }
        @{ name = "生命周期查询"; url = "$API_URL/api/data-assets?lifecycle_stage=production&limit=1" }
        @{ name = "标签查询"; url = "$API_URL/api/data-assets?standardized_tag=biz:critical&limit=1" }
    )
    
    $allPassed = $true
    foreach ($test in $tests) {
        try {
            $response = Invoke-WebRequest -Uri $test.url -Method GET -UseBasicParsing -TimeoutSec 10
            if ($response.StatusCode -eq 200) {
                Write-Info "$($test.name) - 通过"
            }
            else {
                Write-Warn "$($test.name) - 失败 (状态码: $($response.StatusCode))"
                $allPassed = $false
            }
        }
        catch {
            Write-Warn "$($test.name) - 失败: $($_.Exception.Message)"
            $allPassed = $false
        }
    }
    
    return $allPassed
}

# 主函数
function Main {
    Write-Info "开始部署流程..."
    Write-Host ""
    
    # 步骤1: 检查环境
    Write-Host "[1/7] 检查环境..." -ForegroundColor Yellow
    $postgresRunning = Test-DockerContainer "postgres"
    $metadataRunning = Test-DockerContainer "metadata"
    
    if (-not $postgresRunning) {
        Write-Warn "PostgreSQL容器未运行，请先启动数据库"
        Write-Info "启动命令: docker-compose up -d postgres"
        $continue = Read-Host "是否继续？(yes/no)"
        if ($continue -ne "yes") {
            exit 1
        }
    }
    
    # 步骤2: 备份数据库
    Write-Host ""
    Write-Host "[2/7] 备份数据库..." -ForegroundColor Yellow
    $backupSuccess = Backup-Database
    if (-not $backupSuccess) {
        $continue = Read-Host "备份失败，是否继续？(yes/no)"
        if ($continue -ne "yes") {
            exit 1
        }
    }
    
    # 步骤3: 执行数据库迁移
    Write-Host ""
    Write-Host "[3/7] 执行数据库迁移..." -ForegroundColor Yellow
    if (-not (Start-DatabaseMigration)) {
        Write-Error "数据库迁移失败，终止部署"
        exit 1
    }
    
    # 步骤4: 验证迁移结果
    Write-Host ""
    Write-Host "[4/7] 验证迁移结果..." -ForegroundColor Yellow
    if (-not (Test-MigrationResult)) {
        Write-Error "迁移验证失败"
        exit 1
    }
    
    # 步骤5: 重启服务
    Write-Host ""
    Write-Host "[5/7] 重启服务..." -ForegroundColor Yellow
    Restart-Services | Out-Null
    
    # 步骤6: 预览和试运行迁移
    Write-Host ""
    Write-Host "[6/7] 预览和试运行迁移..." -ForegroundColor Yellow
    Test-PreviewMigration | Out-Null
    
    if (Test-DryRunMigration) {
        Write-Info "试运行成功"
    } else {
        Write-Warn "试运行失败，请检查日志"
        $continue = Read-Host "是否继续执行实际迁移？(yes/no)"
        if ($continue -ne "yes") {
            Write-Info "已取消实际迁移"
            exit 0
        }
    }
    
    # 步骤7: 执行实际迁移（可选）
    Write-Host ""
    Write-Host "[7/7] 执行实际数据迁移（可选）..." -ForegroundColor Yellow
    $runActual = Read-Host "是否执行实际数据迁移？(yes/no)"
    if ($runActual -eq "yes") {
        if (-not (Start-ActualMigration)) {
            Write-Error "实际迁移失败"
            exit 1
        }
    } else {
        Write-Info "跳过实际数据迁移，稍后可以手动执行"
    }
    
    # 步骤8: 测试API
    Write-Host ""
    Write-Host "[8/8] 测试API接口..." -ForegroundColor Yellow
    Test-ClassificationAPI | Out-Null
    
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
}

# 执行主函数
Main









# 修复迁移028的问题并重新部署
# 使用方法: .\scripts\fix-migration-028.ps1

$ErrorActionPreference = "Continue"

$ServerIP = "43.143.139.197"
$ServerUser = "root"
$ServerPath = "/opt/enterprise-ai-platform"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "修复迁移028并重新部署" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤1: 检查服务器当前迁移版本
Write-Host "[1/5] 检查服务器当前迁移版本..." -ForegroundColor Yellow
$currentVersion = ssh "${ServerUser}@${ServerIP}" "docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -t -c 'SELECT version_num FROM alembic_version;'"
Write-Host "当前版本: $($currentVersion.Trim())" -ForegroundColor Gray

# 步骤2: 检查字段是否已存在
Write-Host ""
Write-Host "[2/5] 检查字段是否已存在..." -ForegroundColor Yellow
$fieldCheck = ssh "${ServerUser}@${ServerIP}" "docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -t -c \"SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'data_assets' AND column_name = 'classification_dimensions';\""
if ([int]$fieldCheck.Trim() -gt 0) {
    Write-Host "[警告] 字段已存在，可能需要手动修复迁移版本" -ForegroundColor Yellow
} else {
    Write-Host "[OK] 字段不存在，可以执行迁移" -ForegroundColor Green
}

# 步骤3: 修复迁移文件（如果需要）
Write-Host ""
Write-Host "[3/5] 检查迁移文件..." -ForegroundColor Yellow
$migrationFile = "database\src\migrations\versions\028_add_classification_dimensions.py"
if (Test-Path $migrationFile) {
    Write-Host "[OK] 迁移文件存在" -ForegroundColor Green
    
    # 检查文件是否有语法错误
    $content = Get-Content $migrationFile -Raw
    if ($content -match "sa\.Column\s*$") {
        Write-Host "[错误] 发现不完整的sa.Column语句，需要修复" -ForegroundColor Red
    } else {
        Write-Host "[OK] 迁移文件语法检查通过" -ForegroundColor Green
    }
} else {
    Write-Host "[错误] 迁移文件不存在" -ForegroundColor Red
    exit 1
}

# 步骤4: 上传修复后的文件
Write-Host ""
Write-Host "[4/5] 上传修复后的迁移文件..." -ForegroundColor Yellow
scp $migrationFile "${ServerUser}@${ServerIP}:$ServerPath/database/src/migrations/versions/028_add_classification_dimensions.py"
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] 文件上传成功" -ForegroundColor Green
} else {
    Write-Host "[错误] 文件上传失败" -ForegroundColor Red
    exit 1
}

# 步骤5: 提供手动执行命令
Write-Host ""
Write-Host "[5/5] 提供执行命令..." -ForegroundColor Yellow
Write-Host ""
Write-Host "请在服务器上执行以下命令：" -ForegroundColor Cyan
Write-Host ""
Write-Host "ssh ${ServerUser}@${ServerIP}" -ForegroundColor Gray
Write-Host "cd $ServerPath" -ForegroundColor Gray
Write-Host "docker-compose run --rm -e DB_HOST=postgres -e DB_PORT=5432 -e DB_USER=ai_user -e DB_PASSWORD=ai_password -e DB_NAME=ai_platform metadata-service sh -c 'cd /database/src/migrations && alembic upgrade head'" -ForegroundColor Gray
Write-Host ""
Write-Host "如果迁移失败，可以尝试手动执行SQL（见 docs/deployment/migration-troubleshooting.md）" -ForegroundColor Yellow
Write-Host ""









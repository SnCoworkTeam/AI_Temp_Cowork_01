# 上传数据库迁移文件和数据同步文件到服务器
$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"
$SERVER_PATH = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  上传数据库迁移文件和数据同步文件" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 检查密钥文件
if (-not (Test-Path $SSH_KEY)) {
    $SSH_KEY = "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem"
    if (-not (Test-Path $SSH_KEY)) {
        Write-Host "错误: 找不到密钥文件" -ForegroundColor Red
        exit 1
    }
}

# 测试SSH连接
Write-Host "[1/5] 测试SSH连接..." -ForegroundColor Cyan
$test = ssh -i $SSH_KEY -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server "echo OK" 2>&1
if ($LASTEXITCODE -ne 0) {
    $test = ssh -i $SSH_KEY -o ConnectTimeout=10 -o StrictHostKeyChecking=no $SERVER "echo OK" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "SSH连接失败!" -ForegroundColor Red
        Write-Host $test
        exit 1
    }
}
Write-Host "✓ SSH连接成功" -ForegroundColor Green
Write-Host ""

# 上传数据库模型文件
Write-Host "[2/5] 上传数据库模型文件..." -ForegroundColor Cyan
if (Test-Path "database/src/models/project_models.py") {
    $remoteDir = "$SERVER_PATH/database/src/models"
    ssh -i $SSH_KEY -F remote.ssh enterprise-ai-server "mkdir -p $remoteDir" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p $remoteDir" 2>&1 | Out-Null
    }
    scp -i $SSH_KEY -F remote.ssh -o StrictHostKeyChecking=no database/src/models/project_models.py enterprise-ai-server:$remoteDir/ 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        scp -i $SSH_KEY -o StrictHostKeyChecking=no database/src/models/project_models.py $SERVER`:$remoteDir/ 2>&1 | Out-Null
    }
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ project_models.py 上传成功" -ForegroundColor Green
    } else {
        Write-Host "  ✗ project_models.py 上传失败" -ForegroundColor Red
    }
}

# 上传数据库迁移文件
Write-Host ""
Write-Host "[3/5] 上传数据库迁移文件..." -ForegroundColor Cyan
if (Test-Path "database/src/migrations") {
    Write-Host "  上传 migrations 目录..." -ForegroundColor Yellow
    $remoteDir = "$SERVER_PATH/database/src/migrations"
    
    # 上传整个migrations目录
    scp -i $SSH_KEY -F remote.ssh -r -o StrictHostKeyChecking=no database/src/migrations enterprise-ai-server:$SERVER_PATH/database/src/ 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        scp -i $SSH_KEY -r -o StrictHostKeyChecking=no database/src/migrations $SERVER`:$SERVER_PATH/database/src/ 2>&1 | Out-Null
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ migrations 目录上传成功" -ForegroundColor Green
    } else {
        Write-Host "  ✗ migrations 目录上传失败" -ForegroundColor Red
    }
    
    # 特别上传项目管理迁移文件
    if (Test-Path "database/src/migrations/versions/0024_add_project_management_tables.py") {
        Write-Host "  上传项目管理迁移文件..." -ForegroundColor Yellow
        $remoteVersionsDir = "$SERVER_PATH/database/src/migrations/versions"
        ssh -i $SSH_KEY -F remote.ssh enterprise-ai-server "mkdir -p $remoteVersionsDir" 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p $remoteVersionsDir" 2>&1 | Out-Null
        }
        scp -i $SSH_KEY -F remote.ssh -o StrictHostKeyChecking=no database/src/migrations/versions/0024_add_project_management_tables.py enterprise-ai-server:$remoteVersionsDir/ 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            scp -i $SSH_KEY -o StrictHostKeyChecking=no database/src/migrations/versions/0024_add_project_management_tables.py $SERVER`:$remoteVersionsDir/ 2>&1 | Out-Null
        }
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ 0024_add_project_management_tables.py 上传成功" -ForegroundColor Green
        }
    }
}

# 上传SQL脚本（如果有）
Write-Host ""
Write-Host "[4/5] 上传SQL脚本..." -ForegroundColor Cyan
if (Test-Path "create_pm_tables.sql") {
    scp -i $SSH_KEY -F remote.ssh -o StrictHostKeyChecking=no create_pm_tables.sql enterprise-ai-server:$SERVER_PATH/ 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        scp -i $SSH_KEY -o StrictHostKeyChecking=no create_pm_tables.sql $SERVER`:$SERVER_PATH/ 2>&1 | Out-Null
    }
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ create_pm_tables.sql 上传成功" -ForegroundColor Green
    }
}

# 查找并上传数据同步脚本
Write-Host ""
Write-Host "[5/5] 查找并上传数据同步脚本..." -ForegroundColor Cyan
$syncScripts = @(
    "scripts/sync_data.py",
    "scripts/data_sync.py",
    "sync_data.py",
    "data_sync.py"
)

$found = $false
foreach ($script in $syncScripts) {
    if (Test-Path $script) {
        Write-Host "  发现数据同步脚本: $script" -ForegroundColor Yellow
        scp -i $SSH_KEY -F remote.ssh -o StrictHostKeyChecking=no $script enterprise-ai-server:$SERVER_PATH/ 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            scp -i $SSH_KEY -o StrictHostKeyChecking=no $script $SERVER`:$SERVER_PATH/ 2>&1 | Out-Null
        }
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ $script 上传成功" -ForegroundColor Green
            $found = $true
        }
    }
}

if (-not $found) {
    Write-Host "  ⚠ 未找到数据同步脚本" -ForegroundColor Yellow
}

# 验证上传的文件
Write-Host ""
Write-Host "验证上传的文件..." -ForegroundColor Cyan
$verifyCmd = "cd $SERVER_PATH; ls -la database/src/models/project_models.py database/src/migrations/versions/0024_add_project_management_tables.py 2>&1"
$verify = ssh -i $SSH_KEY -F remote.ssh enterprise-ai-server $verifyCmd 2>&1
if ($LASTEXITCODE -ne 0) {
    $verify = ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $verifyCmd 2>&1
}
Write-Host $verify

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步操作:" -ForegroundColor Cyan
Write-Host "  1. 在服务器上运行数据库迁移:" -ForegroundColor Yellow
Write-Host "     ssh -i $SSH_KEY -F remote.ssh enterprise-ai-server 'cd $SERVER_PATH; docker compose exec postgres psql -U ai_user -d ai_platform -f /docker-entrypoint-initdb.d/create_pm_tables.sql'" -ForegroundColor White
Write-Host ""
Write-Host "  2. 或者使用Alembic运行迁移:" -ForegroundColor Yellow
Write-Host "     ssh -i $SSH_KEY -F remote.ssh enterprise-ai-server 'cd $SERVER_PATH; docker compose exec project-management alembic upgrade head'" -ForegroundColor White
Write-Host ""
Write-Host "  3. 重启项目管理服务:" -ForegroundColor Yellow
$restartCmd = "ssh -i $SSH_KEY -F remote.ssh enterprise-ai-server 'cd $SERVER_PATH; docker compose restart project-management'"
Write-Host "     $restartCmd" -ForegroundColor White
Write-Host ""


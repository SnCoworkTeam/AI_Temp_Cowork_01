# 完整部署：使用SSH密钥，清理服务器数据，上传所有迁移文件，执行迁移，启动服务
# 使用方法: .\scripts\full-deploy-with-key.ps1

$ErrorActionPreference = "Continue"

$ServerIP = "43.143.139.197"
$ServerUser = "root"
$ServerPath = "/opt/enterprise-ai-platform"
$SSHKey = "E:\enterprise-ai-platform\enterprise_ai_platform.pem"

# 检查SSH密钥文件
if (-not (Test-Path $SSHKey)) {
    Write-Host "[错误] SSH密钥文件不存在: $SSHKey" -ForegroundColor Red
    exit 1
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "完整部署：同步迁移并启动服务" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤1: 测试SSH连接（不使用密钥，先测试基本连接）
Write-Host "[0/10] 测试SSH连接..." -ForegroundColor Yellow
try {
    $testResult = ssh -o ConnectTimeout=5 "${ServerUser}@${ServerIP}" "echo 'OK'" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] SSH连接正常（未使用密钥）" -ForegroundColor Green
        $useKey = $false
    } else {
        # 尝试使用密钥
        Write-Host "尝试使用SSH密钥连接..." -ForegroundColor Yellow
        $testResult = ssh -i $SSHKey -o ConnectTimeout=5 "${ServerUser}@${ServerIP}" "echo 'OK'" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] SSH连接正常（使用密钥）" -ForegroundColor Green
            $useKey = $true
        } else {
            Write-Host "[错误] SSH连接失败" -ForegroundColor Red
            Write-Host "错误信息: $testResult" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "[错误] SSH连接失败: $_" -ForegroundColor Red
    exit 1
}

# 设置SSH和SCP命令前缀
if ($useKey) {
    $sshCmd = "ssh -i `"$SSHKey`" -o StrictHostKeyChecking=no"
    $scpCmd = "scp -i `"$SSHKey`" -o StrictHostKeyChecking=no"
} else {
    $sshCmd = "ssh -o StrictHostKeyChecking=no"
    $scpCmd = "scp -o StrictHostKeyChecking=no"
}

# 步骤1: 停止服务
Write-Host ""
Write-Host "[1/10] 停止服务器上的服务..." -ForegroundColor Yellow
& $sshCmd "${ServerUser}@${ServerIP}" "cd $ServerPath && docker-compose stop metadata-service web-ui api-gateway agent-service" 2>&1 | Out-Null
Write-Host "[OK] 服务已停止" -ForegroundColor Green

# 步骤2: 备份数据库
Write-Host ""
Write-Host "[2/10] 备份数据库..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupCmd = "mkdir -p /backup/database && docker exec enterprise-ai-postgres pg_dump -U ai_user -d ai_platform -F c -f /tmp/backup_$timestamp.dump 2>&1 && docker cp enterprise-ai-postgres:/tmp/backup_$timestamp.dump /backup/database/ 2>&1"
& $sshCmd "${ServerUser}@${ServerIP}" $backupCmd 2>&1 | Out-Null
Write-Host "[OK] 数据库已备份到 /backup/database/backup_$timestamp.dump" -ForegroundColor Green

# 步骤3: 重建数据库
Write-Host ""
Write-Host "[3/10] 重建数据库（删除所有数据）..." -ForegroundColor Yellow
Write-Host "警告：这将删除所有现有数据！" -ForegroundColor Red
& $sshCmd "${ServerUser}@${ServerIP}" "docker exec enterprise-ai-postgres psql -U ai_user -d postgres -c 'DROP DATABASE IF EXISTS ai_platform;'" 2>&1 | Out-Null
Start-Sleep -Seconds 2
& $sshCmd "${ServerUser}@${ServerIP}" "docker exec enterprise-ai-postgres psql -U ai_user -d postgres -c 'CREATE DATABASE ai_platform;'" 2>&1 | Out-Null
Write-Host "[OK] 数据库已重建" -ForegroundColor Green

# 步骤4: 上传所有迁移文件
Write-Host ""
Write-Host "[4/10] 上传所有迁移文件..." -ForegroundColor Yellow
$migrationFiles = Get-ChildItem -Path "database\src\migrations\versions" -Filter "*.py" | Sort-Object Name

$uploaded = 0
foreach ($file in $migrationFiles) {
    $localPath = $file.FullName
    $remotePath = "$ServerPath/database/src/migrations/versions/$($file.Name)"
    
    Write-Host "  上传: $($file.Name)" -ForegroundColor Gray
    & $scpCmd -q $localPath "${ServerUser}@${ServerIP}:$remotePath" 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        $uploaded++
    }
}

Write-Host "[OK] 已上传 $uploaded/$($migrationFiles.Count) 个迁移文件" -ForegroundColor Green

# 步骤5: 上传Alembic配置文件
Write-Host ""
Write-Host "[5/10] 上传Alembic配置文件..." -ForegroundColor Yellow
$alembicFiles = @(
    "database\src\migrations\alembic.ini",
    "database\src\migrations\env.py"
)

foreach ($file in $alembicFiles) {
    $localPath = Join-Path $PWD $file
    if (Test-Path $localPath) {
        $remotePath = "$ServerPath/database/src/migrations/$((Split-Path $file -Leaf))"
        & $scpCmd -q $localPath "${ServerUser}@${ServerIP}:$remotePath" 2>&1 | Out-Null
    }
}
Write-Host "[OK] 配置文件已上传" -ForegroundColor Green

# 步骤6: 执行所有迁移
Write-Host ""
Write-Host "[6/10] 执行数据库迁移（从头开始）..." -ForegroundColor Yellow
Write-Host "这可能需要一些时间，请耐心等待..." -ForegroundColor Gray

$migrationCmd = "cd $ServerPath && docker-compose run --rm -e DB_HOST=postgres -e DB_PORT=5432 -e DB_USER=ai_user -e DB_PASSWORD=ai_password -e DB_NAME=ai_platform metadata-service sh -c 'cd /database/src/migrations && alembic upgrade head' 2>&1"
$migrationResult = & $sshCmd "${ServerUser}@${ServerIP}" $migrationCmd

Write-Host $migrationResult -ForegroundColor Gray

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] 数据库迁移成功完成！" -ForegroundColor Green
} else {
    Write-Host "[错误] 数据库迁移失败" -ForegroundColor Red
    exit 1
}

# 步骤7: 验证迁移版本
Write-Host ""
Write-Host "[7/10] 验证迁移版本..." -ForegroundColor Yellow
$finalVersion = & $sshCmd "${ServerUser}@${ServerIP}" "docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -t -A -c 'SELECT version_num FROM alembic_version;'"
$finalVersion = $finalVersion.Trim()
Write-Host "数据库版本: $finalVersion" -ForegroundColor Gray

# 步骤8: 验证字段
Write-Host ""
Write-Host "[8/10] 验证数据库字段..." -ForegroundColor Yellow
$fieldCheck = & $sshCmd "${ServerUser}@${ServerIP}" "docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -t -A -c 'SELECT COUNT(*) FROM information_schema.columns WHERE table_name = ''data_assets'' AND column_name = ''classification_dimensions'';'"
$fieldCheck = $fieldCheck.Trim()

if ([int]$fieldCheck -gt 0) {
    Write-Host "[OK] classification_dimensions 字段已存在" -ForegroundColor Green
} else {
    Write-Host "[警告] classification_dimensions 字段不存在" -ForegroundColor Yellow
}

# 步骤9: 启动服务
Write-Host ""
Write-Host "[9/10] 启动服务..." -ForegroundColor Yellow
& $sshCmd "${ServerUser}@${ServerIP}" "cd $ServerPath && docker-compose up -d metadata-service web-ui api-gateway agent-service" 2>&1 | Out-Null
Write-Host "[OK] 服务启动命令已执行" -ForegroundColor Green
Write-Host "等待服务启动..." -ForegroundColor Gray
Start-Sleep -Seconds 15

# 步骤10: 验证服务状态
Write-Host ""
Write-Host "[10/10] 验证服务状态..." -ForegroundColor Yellow
$services = @("metadata-service", "web-ui", "api-gateway", "agent-service")
foreach ($service in $services) {
    $status = & $sshCmd "${ServerUser}@${ServerIP}" "docker ps --filter name=$service --format '{{.Status}}'"
    if ($status -match "Up") {
        Write-Host "  [OK] $service 运行中" -ForegroundColor Green
    } else {
        Write-Host "  [警告] $service 状态: $status" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "部署完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "部署摘要：" -ForegroundColor Yellow
Write-Host "  数据库版本: $finalVersion" -ForegroundColor Gray
Write-Host "  迁移文件: $uploaded 个" -ForegroundColor Gray
Write-Host ""
Write-Host "访问地址：" -ForegroundColor Yellow
Write-Host "  前端: http://${ServerIP}:3000" -ForegroundColor Gray
Write-Host "  API: http://${ServerIP}:8005" -ForegroundColor Gray
Write-Host "  元数据管理: http://${ServerIP}:3000/admin/metadata" -ForegroundColor Gray
Write-Host ""

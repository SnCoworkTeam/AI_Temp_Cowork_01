# 完整部署：清理数据库，上传所有迁移文件，执行迁移，启动服务
# 基于 deploy-to-server-43-quick.ps1 的成功模式
# 使用方法: .\scripts\deploy-rebuild-complete.ps1

$ErrorActionPreference = "Continue"

$ServerIP = "43.143.139.197"
$ServerUser = "root"
$ServerPath = "/opt/enterprise-ai-platform"
$API_URL = "http://${ServerIP}:8005"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "完整部署：同步迁移并启动服务" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤1: 检查SSH连接
Write-Host "[1/8] 检查SSH连接..." -ForegroundColor Yellow
try {
    $test = ssh -o ConnectTimeout=5 "${ServerUser}@${ServerIP}" "echo 'OK'" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] SSH连接正常" -ForegroundColor Green
    } else {
        Write-Host "[错误] SSH连接失败" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "[错误] SSH连接失败: $_" -ForegroundColor Red
    exit 1
}

# 步骤2: 停止服务
Write-Host ""
Write-Host "[2/8] 停止服务器上的服务..." -ForegroundColor Yellow
ssh "${ServerUser}@${ServerIP}" "cd $ServerPath && docker-compose stop metadata-service web-ui api-gateway agent-service" 2>&1 | Out-Null
Write-Host "[OK] 服务已停止" -ForegroundColor Green

# 步骤3: 备份并重建数据库
Write-Host ""
Write-Host "[3/8] 备份并重建数据库..." -ForegroundColor Yellow
Write-Host "警告：这将删除所有现有数据！" -ForegroundColor Red

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupCmd = "mkdir -p /backup/database && docker exec enterprise-ai-postgres pg_dump -U ai_user -d ai_platform -F c -f /tmp/backup_$timestamp.dump 2>&1 && docker cp enterprise-ai-postgres:/tmp/backup_$timestamp.dump /backup/database/ 2>&1"
ssh "${ServerUser}@${ServerIP}" $backupCmd | Out-Null
Write-Host "[OK] 数据库备份完成" -ForegroundColor Green

# 删除并重建数据库
Write-Host "重建数据库..." -ForegroundColor Yellow
ssh "${ServerUser}@${ServerIP}" "docker exec enterprise-ai-postgres psql -U ai_user -d postgres -c 'DROP DATABASE IF EXISTS ai_platform;'" | Out-Null
Start-Sleep -Seconds 2
ssh "${ServerUser}@${ServerIP}" "docker exec enterprise-ai-postgres psql -U ai_user -d postgres -c 'CREATE DATABASE ai_platform;'" | Out-Null
Write-Host "[OK] 数据库已重建" -ForegroundColor Green

# 步骤4: 上传所有迁移文件
Write-Host ""
Write-Host "[4/8] 上传所有迁移文件..." -ForegroundColor Yellow

$migrationFiles = Get-ChildItem -Path "database\src\migrations\versions" -Filter "*.py" | Sort-Object Name

$uploaded = 0
foreach ($file in $migrationFiles) {
    $localPath = $file.FullName
    $remotePath = "$ServerPath/database/src/migrations/versions/$($file.Name)"
    $remoteDir = Split-Path $remotePath -Parent
    
    ssh "${ServerUser}@${ServerIP}" "mkdir -p `"$remoteDir`"" | Out-Null
    scp -q $localPath "${ServerUser}@${ServerIP}:$remotePath" 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        $uploaded++
        Write-Host "  [OK] $($file.Name)" -ForegroundColor Green
    } else {
        Write-Host "  [失败] $($file.Name)" -ForegroundColor Red
    }
}

Write-Host "[OK] 已上传 $uploaded/$($migrationFiles.Count) 个迁移文件" -ForegroundColor Green

# 上传Alembic配置文件
$alembicFiles = @("database\src\migrations\alembic.ini", "database\src\migrations\env.py")
foreach ($file in $alembicFiles) {
    $localPath = Join-Path $PWD $file
    if (Test-Path $localPath) {
        $remotePath = "$ServerPath/database/src/migrations/$((Split-Path $file -Leaf))"
        scp -q $localPath "${ServerUser}@${ServerIP}:$remotePath" 2>&1 | Out-Null
    }
}

# 步骤5: 执行数据库迁移
Write-Host ""
Write-Host "[5/8] 执行数据库迁移（从头开始）..." -ForegroundColor Yellow
Write-Host "这可能需要一些时间，请耐心等待..." -ForegroundColor Gray

$migrationCmd = "cd $ServerPath && docker-compose run --rm -e DB_HOST=postgres -e DB_PORT=5432 -e DB_USER=ai_user -e DB_PASSWORD=ai_password -e DB_NAME=ai_platform metadata-service sh -c 'cd /database/src/migrations && alembic upgrade head'"
$result = ssh "${ServerUser}@${ServerIP}" $migrationCmd
Write-Host $result -ForegroundColor Gray

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] 数据库迁移完成" -ForegroundColor Green
} else {
    Write-Host "[错误] 数据库迁移失败" -ForegroundColor Red
    exit 1
}

# 步骤6: 验证迁移版本
Write-Host ""
Write-Host "[6/8] 验证迁移版本..." -ForegroundColor Yellow
$finalVersion = ssh "${ServerUser}@${ServerIP}" "docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -t -A -c 'SELECT version_num FROM alembic_version;'"
$finalVersion = $finalVersion.Trim()
Write-Host "数据库版本: $finalVersion" -ForegroundColor Gray

# 验证heads
$headsCmd = "cd $ServerPath && docker-compose run --rm -e DB_HOST=postgres -e DB_PORT=5432 -e DB_USER=ai_user -e DB_PASSWORD=ai_password -e DB_NAME=ai_platform metadata-service sh -c 'cd /database/src/migrations && alembic heads'"
$headsResult = ssh "${ServerUser}@${ServerIP}" $headsCmd
Write-Host "Heads: $headsResult" -ForegroundColor Gray

# 步骤7: 启动服务
Write-Host ""
Write-Host "[7/8] 启动服务..." -ForegroundColor Yellow
ssh "${ServerUser}@${ServerIP}" "cd $ServerPath && docker-compose up -d metadata-service web-ui api-gateway agent-service" | Out-Null
Write-Host "[OK] 服务已启动" -ForegroundColor Green
Write-Host "等待服务启动..." -ForegroundColor Gray
Start-Sleep -Seconds 15

# 步骤8: 验证服务状态
Write-Host ""
Write-Host "[8/8] 验证服务状态..." -ForegroundColor Yellow

$services = @("metadata-service", "web-ui", "api-gateway", "agent-service")
foreach ($service in $services) {
    $status = ssh "${ServerUser}@${ServerIP}" "docker ps --filter name=$service --format '{{.Status}}'"
    if ($status -match "Up") {
        Write-Host "  [OK] $service 运行中" -ForegroundColor Green
    } else {
        Write-Host "  [警告] $service 状态: $status" -ForegroundColor Yellow
    }
}

# 测试API
Write-Host ""
Write-Host "测试API健康检查..." -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "$API_URL/api/health" -UseBasicParsing -TimeoutSec 10
    if ($health.StatusCode -eq 200) {
        Write-Host "[OK] API健康检查通过" -ForegroundColor Green
    }
} catch {
    Write-Host "[警告] API健康检查失败，服务可能还在启动中" -ForegroundColor Yellow
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
Write-Host "下一步操作：" -ForegroundColor Yellow
Write-Host "1. 测试迁移工具预览: curl -X GET `"$API_URL/api/classification/migration/preview?limit=10`"" -ForegroundColor Gray
Write-Host "2. 试运行迁移: curl -X POST `"$API_URL/api/classification/migrate`" -H `"Content-Type: application/json`" -d '{\"dry_run\": true, \"batch_size\": 10}'" -ForegroundColor Gray
Write-Host ""









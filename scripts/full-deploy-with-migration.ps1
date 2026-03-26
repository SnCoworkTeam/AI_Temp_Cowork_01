# 完整部署：清理服务器数据，上传所有迁移文件，执行迁移，启动服务
# 使用方法: .\scripts\full-deploy-with-migration.ps1

$ErrorActionPreference = "Continue"

$ServerIP = "43.143.139.197"
$ServerUser = "root"
$ServerPath = "/opt/enterprise-ai-platform"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "完整部署：同步迁移并启动服务" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤1: 停止服务
Write-Host "[1/10] 停止服务器上的服务..." -ForegroundColor Yellow
ssh "${ServerUser}@${ServerIP}" "cd $ServerPath && docker-compose stop metadata-service web-ui api-gateway agent-service" 2>&1 | Out-Null
Write-Host "[OK] 服务已停止" -ForegroundColor Green

# 步骤2: 备份数据库（以防万一）
Write-Host ""
Write-Host "[2/10] 备份数据库..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupCmd = "mkdir -p /backup/database && docker exec enterprise-ai-postgres pg_dump -U ai_user -d ai_platform -F c -f /tmp/backup_$timestamp.dump 2>&1 && docker cp enterprise-ai-postgres:/tmp/backup_$timestamp.dump /backup/database/ 2>&1"
$backupResult = ssh "${ServerUser}@${ServerIP}" $backupCmd
Write-Host "[OK] 数据库已备份到 /backup/database/backup_$timestamp.dump" -ForegroundColor Green

# 步骤3: 删除数据库数据（重建数据库）
Write-Host ""
Write-Host "[3/10] 清理数据库数据..." -ForegroundColor Yellow
Write-Host "警告：这将删除所有现有数据！" -ForegroundColor Red

# 删除并重建数据库
$dropDbCmd = 'docker exec enterprise-ai-postgres psql -U ai_user -d postgres -c "DROP DATABASE IF EXISTS ai_platform;"'
$createDbCmd = 'docker exec enterprise-ai-postgres psql -U ai_user -d postgres -c "CREATE DATABASE ai_platform;"'

ssh "${ServerUser}@${ServerIP}" $dropDbCmd 2>&1 | Out-Null
Start-Sleep -Seconds 2
ssh "${ServerUser}@${ServerIP}" $createDbCmd 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] 数据库已重建" -ForegroundColor Green
} else {
    Write-Host "[警告] 数据库重建可能有问题，继续..." -ForegroundColor Yellow
}

# 步骤4: 上传所有迁移文件
Write-Host ""
Write-Host "[4/10] 上传所有迁移文件..." -ForegroundColor Yellow

$migrationFiles = Get-ChildItem -Path "database\src\migrations\versions" -Filter "*.py" | Where-Object { $_.Name -match '^\d{3}_|^[a-f0-9]+_' } | Sort-Object Name

$uploaded = 0
foreach ($file in $migrationFiles) {
    $localPath = $file.FullName
    $relativePath = $file.FullName.Replace((Get-Location).Path + "\", "").Replace("\", "/")
    $remotePath = "$ServerPath/$relativePath"
    $remoteDir = Split-Path $remotePath -Parent
    
    # 确保远程目录存在
    ssh "${ServerUser}@${ServerIP}" "mkdir -p `"$remoteDir`"" | Out-Null
    
    Write-Host "  上传: $($file.Name)" -ForegroundColor Gray
    scp -q $localPath "${ServerUser}@${ServerIP}:$remotePath" 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        $uploaded++
        Write-Host "  [OK] $($file.Name)" -ForegroundColor Green
    } else {
        Write-Host "  [错误] $($file.Name) 上传失败" -ForegroundColor Red
    }
}

Write-Host "[OK] 已上传 $uploaded/$($migrationFiles.Count) 个迁移文件" -ForegroundColor Green

# 步骤5: 上传alembic配置文件
Write-Host ""
Write-Host "[5/10] 上传Alembic配置文件..." -ForegroundColor Yellow

$alembicFiles = @(
    "database\src\migrations\alembic.ini",
    "database\src\migrations\env.py",
    "database\src\migrations\script.py.mako"
)

foreach ($file in $alembicFiles) {
    $localPath = Join-Path $PWD $file
    if (Test-Path $localPath) {
        $remotePath = "$ServerPath/$($file.Replace('\', '/'))"
        $remoteDir = Split-Path $remotePath -Parent
        
        ssh "${ServerUser}@${ServerIP}" "mkdir -p `"$remoteDir`"" | Out-Null
        scp -q $localPath "${ServerUser}@${ServerIP}:$remotePath" 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] $file" -ForegroundColor Green
        }
    }
}

# 步骤6: 执行所有迁移
Write-Host ""
Write-Host "[6/10] 执行数据库迁移（从头开始）..." -ForegroundColor Yellow
Write-Host "这可能需要一些时间，请耐心等待..." -ForegroundColor Gray

$migrationCmd = "cd $ServerPath && docker-compose run --rm -e DB_HOST=postgres -e DB_PORT=5432 -e DB_USER=ai_user -e DB_PASSWORD=ai_password -e DB_NAME=ai_platform metadata-service sh -c 'cd /database/src/migrations && alembic upgrade head' 2>&1"
$migrationResult = ssh "${ServerUser}@${ServerIP}" $migrationCmd

Write-Host $migrationResult -ForegroundColor Gray

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] 数据库迁移成功完成！" -ForegroundColor Green
} else {
    Write-Host "[错误] 数据库迁移失败" -ForegroundColor Red
    Write-Host "错误信息:" -ForegroundColor Yellow
    Write-Host $migrationResult -ForegroundColor Red
    exit 1
}

# 步骤7: 验证迁移版本
Write-Host ""
Write-Host "[7/10] 验证迁移版本..." -ForegroundColor Yellow
$finalVersion = ssh "${ServerUser}@${ServerIP}" "docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -t -A -c 'SELECT version_num FROM alembic_version;'" 2>&1
$finalVersion = $finalVersion.Trim()
Write-Host "数据库版本: $finalVersion" -ForegroundColor Gray

# 检查heads
$headsCmd = "cd $ServerPath && docker-compose run --rm -e DB_HOST=postgres -e DB_PORT=5432 -e DB_USER=ai_user -e DB_PASSWORD=ai_password -e DB_NAME=ai_platform metadata-service sh -c 'cd /database/src/migrations && alembic heads' 2>&1"
$headsResult = ssh "${ServerUser}@${ServerIP}" $headsCmd
$headLines = $headsResult -split "`n" | Where-Object { $_.Trim() -match '^[a-f0-9]+$|^[0-9]+$|^[a-f0-9]+_[a-z_]+$' }
$headCount = ($headLines | Measure-Object).Count

Write-Host "Heads数量: $headCount" -ForegroundColor Gray
if ($headCount -eq 1) {
    Write-Host "[OK] 版本一致，只有一个head" -ForegroundColor Green
} else {
    Write-Host "[警告] 有 $headCount 个heads: $headsResult" -ForegroundColor Yellow
}

# 步骤8: 验证字段
Write-Host ""
Write-Host "[8/10] 验证数据库字段..." -ForegroundColor Yellow
$fieldCheckCmd = 'docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -t -A -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = ''data_assets'' AND column_name = ''classification_dimensions'';" 2>&1'
$fieldCheck = ssh "${ServerUser}@${ServerIP}" $fieldCheckCmd
$fieldCheck = $fieldCheck.Trim()

if ([int]$fieldCheck -gt 0) {
    Write-Host "[OK] classification_dimensions 字段已存在" -ForegroundColor Green
} else {
    Write-Host "[警告] classification_dimensions 字段不存在" -ForegroundColor Yellow
}

# 步骤9: 启动服务
Write-Host ""
Write-Host "[9/10] 启动服务..." -ForegroundColor Yellow
ssh "${ServerUser}@${ServerIP}" "cd $ServerPath && docker-compose up -d metadata-service web-ui api-gateway agent-service" 2>&1 | Out-Null
Write-Host "[OK] 服务启动命令已执行" -ForegroundColor Green
Write-Host "等待服务启动..." -ForegroundColor Gray
Start-Sleep -Seconds 15

# 步骤10: 验证服务状态
Write-Host ""
Write-Host "[10/10] 验证服务状态..." -ForegroundColor Yellow

$services = @("metadata-service", "web-ui", "api-gateway", "agent-service")
foreach ($service in $services) {
    $status = ssh "${ServerUser}@${ServerIP}" "docker ps --filter name=$service --format '{{.Status}}'" 2>&1
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
    $health = Invoke-WebRequest -Uri "http://${ServerIP}:8005/api/health" -UseBasicParsing -TimeoutSec 10 -ErrorAction SilentlyContinue
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
Write-Host "  Heads数量: $headCount" -ForegroundColor Gray
Write-Host "  迁移文件: $uploaded 个" -ForegroundColor Gray
Write-Host ""
Write-Host "访问地址：" -ForegroundColor Yellow
Write-Host "  前端: http://${ServerIP}:3000" -ForegroundColor Gray
Write-Host "  API: http://${ServerIP}:8005" -ForegroundColor Gray
Write-Host "  元数据管理: http://${ServerIP}:3000/admin/metadata" -ForegroundColor Gray
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "1. 测试迁移API: curl -X GET http://${ServerIP}:8005/api/classification/migration/preview?limit=10" -ForegroundColor Gray
Write-Host "2. 检查服务日志: ssh ${ServerUser}@${ServerIP} 'cd $ServerPath && docker-compose logs --tail=50 metadata-service'" -ForegroundColor Gray
Write-Host ""









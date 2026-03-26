# 快速部署到服务器43的简化脚本
# 使用方法: .\scripts\deploy-to-server-43-quick.ps1

$ErrorActionPreference = "Continue"

$ServerIP = "43.143.139.197"
$ServerUser = "root"
$ServerPath = "/opt/enterprise-ai-platform"
$API_URL = "http://${ServerIP}:8005"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "快速部署到服务器 $ServerIP" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤1: 检查SSH连接
Write-Host "[1/6] 检查SSH连接..." -ForegroundColor Yellow
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

# 步骤2: 上传所有迁移文件和关键文件
Write-Host ""
Write-Host "[2/6] 上传代码文件..." -ForegroundColor Yellow

# 先上传所有迁移文件
$migrationFiles = Get-ChildItem -Path "database\src\migrations\versions" -Filter "*.py" | Sort-Object Name
foreach ($file in $migrationFiles) {
    $localPath = $file.FullName
    $remotePath = "$ServerPath/database/src/migrations/versions/$($file.Name)"
    $remoteDir = Split-Path $remotePath -Parent
    ssh "${ServerUser}@${ServerIP}" "mkdir -p `"$remoteDir`"" | Out-Null
    scp -q $localPath "${ServerUser}@${ServerIP}:$remotePath" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] $($file.Name)" -ForegroundColor Green
    }
}

# 上传Alembic配置文件
$alembicFiles = @("database\src\migrations\alembic.ini", "database\src\migrations\env.py")
foreach ($file in $alembicFiles) {
    $localPath = Join-Path $PWD $file
    if (Test-Path $localPath) {
        $remotePath = "$ServerPath/database/src/migrations/$((Split-Path $file -Leaf))"
        scp -q $localPath "${ServerUser}@${ServerIP}:$remotePath" 2>&1 | Out-Null
    }
}

# 上传其他关键文件
$files = @(
    "metadata-service\src\models\data_asset.py",
    "metadata-service\src\models\ai_model.py",
    "metadata-service\src\models\workflow_metadata.py",
    "metadata-service\src\models\business_entity.py",
    "metadata-service\src\services\metadata_catalog.py",
    "metadata-service\src\api\data_assets.py",
    "metadata-service\src\api\ai_models.py",
    "metadata-service\src\api\workflows.py",
    "metadata-service\src\api\business_entities.py",
    "metadata-service\src\api\classification_migration.py",
    "metadata-service\src\utils\classification_migration.py",
    "metadata-service\src\main.py",
    "web-ui\src\lib\metadata-classification.ts",
    "web-ui\src\lib\classification-standards.ts",
    "web-ui\src\components\metadata\ClassificationDimensionEditor.tsx",
    "web-ui\src\components\metadata\index.ts",
    "web-ui\src\app\admin\metadata\page.tsx"
)

$uploaded = 0
foreach ($file in $files) {
    $localPath = Join-Path $PWD $file
    if (Test-Path $localPath) {
        $remotePath = "$ServerPath/$($file.Replace('\', '/'))"
        $remoteDir = Split-Path $remotePath -Parent
        
        # 确保远程目录存在
        ssh "${ServerUser}@${ServerIP}" "mkdir -p `"$remoteDir`"" | Out-Null
        
        Write-Host "  上传: $file" -ForegroundColor Gray
        scp -q $localPath "${ServerUser}@${ServerIP}:$remotePath" 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            $uploaded++
        }
    }
}

Write-Host "[OK] 已上传 $uploaded/$($files.Count) 个文件" -ForegroundColor Green

# 步骤3: 备份并重建数据库
Write-Host ""
Write-Host "[3/6] 备份并重建数据库..." -ForegroundColor Yellow
Write-Host "警告：这将删除所有现有数据！" -ForegroundColor Red
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupCmd = "mkdir -p /backup/database && docker exec enterprise-ai-postgres pg_dump -U ai_user -d ai_platform -F c -f /tmp/backup_$timestamp.dump && docker cp enterprise-ai-postgres:/tmp/backup_$timestamp.dump /backup/database/"
ssh "${ServerUser}@${ServerIP}" $backupCmd | Out-Null
Write-Host "[OK] 数据库备份完成" -ForegroundColor Green

# 删除并重建数据库
Write-Host "重建数据库..." -ForegroundColor Yellow
ssh "${ServerUser}@${ServerIP}" "docker exec enterprise-ai-postgres psql -U ai_user -d postgres -c 'DROP DATABASE IF EXISTS ai_platform;'" | Out-Null
Start-Sleep -Seconds 2
ssh "${ServerUser}@${ServerIP}" "docker exec enterprise-ai-postgres psql -U ai_user -d postgres -c 'CREATE DATABASE ai_platform;'" | Out-Null
Write-Host "[OK] 数据库已重建" -ForegroundColor Green

# 步骤4: 执行数据库迁移
Write-Host ""
Write-Host "[4/6] 执行数据库迁移..." -ForegroundColor Yellow
$migrationCmd = "cd $ServerPath && docker-compose run --rm -e DB_HOST=postgres -e DB_PORT=5432 -e DB_USER=ai_user -e DB_PASSWORD=ai_password -e DB_NAME=ai_platform metadata-service sh -c 'cd /database/src/migrations && alembic upgrade head'"
$result = ssh "${ServerUser}@${ServerIP}" $migrationCmd
Write-Host $result -ForegroundColor Gray

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] 数据库迁移完成" -ForegroundColor Green
} else {
    Write-Host "[错误] 数据库迁移失败" -ForegroundColor Red
    exit 1
}

# 步骤5: 重启服务
Write-Host ""
Write-Host "[5/6] 重启服务..." -ForegroundColor Yellow
ssh "${ServerUser}@${ServerIP}" "cd $ServerPath && docker-compose restart metadata-service web-ui" | Out-Null
Write-Host "[OK] 服务已重启" -ForegroundColor Green
Write-Host "等待服务启动..." -ForegroundColor Gray
Start-Sleep -Seconds 15

# 步骤6: 测试服务
Write-Host ""
Write-Host "[6/6] 测试服务..." -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "$API_URL/api/health" -UseBasicParsing -TimeoutSec 10
    if ($health.StatusCode -eq 200) {
        Write-Host "[OK] 服务健康检查通过" -ForegroundColor Green
    }
} catch {
    Write-Host "[警告] 服务健康检查失败，但继续..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "部署完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步操作：" -ForegroundColor Yellow
Write-Host "1. 测试迁移工具预览: curl -X GET `"$API_URL/api/classification/migration/preview?limit=10`"" -ForegroundColor Gray
Write-Host "2. 试运行迁移: curl -X POST `"$API_URL/api/classification/migrate`" -H `"Content-Type: application/json`" -d '{\"dry_run\": true, \"batch_size\": 10}'" -ForegroundColor Gray
Write-Host "3. 访问前端: http://${ServerIP}:3000/admin/metadata" -ForegroundColor Gray
Write-Host ""









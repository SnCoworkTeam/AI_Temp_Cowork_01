# 上传项目管理服务并导入Excel数据
$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"
$SERVER_PATH = "/opt/enterprise-ai-platform"
$EXCEL_FILE = "2025项目周月进度报告 (1).xlsx"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  上传项目管理服务并导入Excel数据" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 检查密钥文件
if (-not (Test-Path $SSH_KEY)) {
    $SSH_KEY = "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem"
    if (-not (Test-Path $SSH_KEY)) {
        Write-Host "错误: 密钥文件未找到" -ForegroundColor Red
        exit 1
    }
}

# 测试SSH连接
Write-Host "测试SSH连接..." -ForegroundColor Cyan
$test = ssh -i $SSH_KEY -o ConnectTimeout=5 -o StrictHostKeyChecking=no $SERVER "echo OK" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "SSH连接失败!" -ForegroundColor Red
    exit 1
}
Write-Host "SSH连接成功" -ForegroundColor Green
Write-Host ""

# 1. 上传数据库迁移脚本
Write-Host "1. 上传数据库迁移脚本..." -ForegroundColor Green
if (Test-Path "database/src/migrations/versions/024_add_project_management_tables.py") {
    $remoteDir = "$SERVER_PATH/database/src/migrations/versions"
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p $remoteDir" | Out-Null
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "database/src/migrations/versions/024_add_project_management_tables.py" "${SERVER}:${remoteDir}/" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  迁移脚本上传成功" -ForegroundColor Green
    }
}

# 2. 上传项目管理服务
Write-Host ""
Write-Host "2. 上传项目管理服务..." -ForegroundColor Green
if (Test-Path "project-management") {
    scp -i $SSH_KEY -r -o StrictHostKeyChecking=no "project-management" "${SERVER}:${SERVER_PATH}/" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  项目管理服务上传成功" -ForegroundColor Green
    }
}

# 3. 上传数据库模型
Write-Host ""
Write-Host "3. 上传数据库模型..." -ForegroundColor Green
if (Test-Path "database/src/models/project_models.py") {
    $remoteDir = "$SERVER_PATH/database/src/models"
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p $remoteDir" | Out-Null
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "database/src/models/project_models.py" "${SERVER}:${remoteDir}/" 2>&1 | Out-Null
    Write-Host "  数据库模型上传成功" -ForegroundColor Green
}

# 4. 上传docker-compose.yml
Write-Host ""
Write-Host "4. 上传docker-compose.yml..." -ForegroundColor Green
if (Test-Path "docker-compose.yml") {
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "docker-compose.yml" "${SERVER}:${SERVER_PATH}/" 2>&1 | Out-Null
    Write-Host "  docker-compose.yml上传成功" -ForegroundColor Green
}

# 5. 上传Excel文件
Write-Host ""
Write-Host "5. 上传Excel文件..." -ForegroundColor Green
if (Test-Path $EXCEL_FILE) {
    scp -i $SSH_KEY -o StrictHostKeyChecking=no $EXCEL_FILE "${SERVER}:${SERVER_PATH}/" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Excel文件上传成功" -ForegroundColor Green
    }
} else {
    Write-Host "  Excel文件不存在，跳过" -ForegroundColor Yellow
}

# 6. 上传导入脚本
Write-Host ""
Write-Host "6. 上传导入脚本..." -ForegroundColor Green
if (Test-Path "scripts/import_excel_to_server.py") {
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "scripts/import_excel_to_server.py" "${SERVER}:${SERVER_PATH}/" 2>&1 | Out-Null
    Write-Host "  导入脚本上传成功" -ForegroundColor Green
}

# 7. 执行数据库迁移
Write-Host ""
Write-Host "7. 执行数据库迁移..." -ForegroundColor Green
$migrateCmd = "cd $SERVER_PATH/database && alembic upgrade head"
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $migrateCmd 2>&1

# 8. 重启服务
Write-Host ""
Write-Host "8. 重启项目管理服务..." -ForegroundColor Green
$stopCmd = "cd $SERVER_PATH && docker compose stop project-management 2>&1 || true"
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $stopCmd | Out-Null

$startCmd = "cd $SERVER_PATH && docker compose up -d --build project-management"
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $startCmd 2>&1

Write-Host ""
Write-Host "等待服务启动..." -ForegroundColor Cyan
Start-Sleep -Seconds 20

# 9. 检查服务状态
Write-Host ""
Write-Host "9. 检查服务状态..." -ForegroundColor Green
$statusCmd = "cd $SERVER_PATH && docker compose ps project-management"
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $statusCmd

# 10. 导入Excel
Write-Host ""
Write-Host "10. 导入Excel数据..." -ForegroundColor Green
$importCmd = "cd $SERVER_PATH && python3 import_excel_to_server.py"
$importResult = ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $importCmd 2>&1
Write-Host $importResult

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "访问地址:" -ForegroundColor Cyan
Write-Host "  健康检查: http://43.143.139.197:8016/api/health" -ForegroundColor Yellow
Write-Host "  API文档: http://43.143.139.197:8016/docs" -ForegroundColor Yellow
Write-Host "  项目管理页面: http://43.143.139.197:3000/admin/projects" -ForegroundColor Yellow
Write-Host ""

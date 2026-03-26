# 快速上传项目管理服务 - 分步执行
$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"
$SERVER_PATH = "/opt/enterprise-ai-platform"

Write-Host "快速上传项目管理服务..." -ForegroundColor Green

# 检查密钥
if (-not (Test-Path $SSH_KEY)) {
    $SSH_KEY = "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem"
}

# 1. 上传迁移脚本（最重要）
Write-Host "`n1. 上传数据库迁移脚本..." -ForegroundColor Cyan
scp -i $SSH_KEY -o StrictHostKeyChecking=no "database/src/migrations/versions/024_add_project_management_tables.py" "${SERVER}:${SERVER_PATH}/database/src/migrations/versions/" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  OK" -ForegroundColor Green
}

# 2. 上传Excel文件
Write-Host "`n2. 上传Excel文件..." -ForegroundColor Cyan
if (Test-Path "2025项目周月进度报告 (1).xlsx") {
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "2025项目周月进度报告 (1).xlsx" "${SERVER}:${SERVER_PATH}/" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK" -ForegroundColor Green
    }
}

# 3. 执行迁移
Write-Host "`n3. 执行数据库迁移..." -ForegroundColor Cyan
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "cd $SERVER_PATH/database && alembic upgrade head" 2>&1

# 4. 重启服务
Write-Host "`n4. 重启服务..." -ForegroundColor Cyan
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "cd $SERVER_PATH && docker compose up -d --build project-management" 2>&1

Write-Host "`n完成！等待20秒后检查服务..." -ForegroundColor Green
Start-Sleep -Seconds 20

# 5. 检查服务
Write-Host "`n5. 检查服务状态..." -ForegroundColor Cyan
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "cd $SERVER_PATH && docker compose ps project-management" 2>&1

Write-Host "`n访问: http://43.143.139.197:8016/api/health" -ForegroundColor Yellow


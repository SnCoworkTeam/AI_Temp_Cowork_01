# 上传项目管理API路由到服务器

$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"
$SERVER_PATH = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  上传项目管理API路由到服务器" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# 1. 上传任务管理路由
Write-Host ""
Write-Host "1. 上传任务管理路由..." -ForegroundColor Yellow
scp -i $SSH_KEY -o StrictHostKeyChecking=no "project-management/src/routes/tasks.py" "${SERVER}:${SERVER_PATH}/project-management/src/routes/tasks.py"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 任务管理路由已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 2. 上传里程碑管理路由
Write-Host ""
Write-Host "2. 上传里程碑管理路由..." -ForegroundColor Yellow
scp -i $SSH_KEY -o StrictHostKeyChecking=no "project-management/src/routes/milestones.py" "${SERVER}:${SERVER_PATH}/project-management/src/routes/milestones.py"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 里程碑管理路由已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 3. 上传周报管理路由
Write-Host ""
Write-Host "3. 上传周报管理路由..." -ForegroundColor Yellow
scp -i $SSH_KEY -o StrictHostKeyChecking=no "project-management/src/routes/weekly_reports.py" "${SERVER}:${SERVER_PATH}/project-management/src/routes/weekly_reports.py"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 周报管理路由已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 4. 上传月报管理路由
Write-Host ""
Write-Host "4. 上传月报管理路由..." -ForegroundColor Yellow
scp -i $SSH_KEY -o StrictHostKeyChecking=no "project-management/src/routes/monthly_reports.py" "${SERVER}:${SERVER_PATH}/project-management/src/routes/monthly_reports.py"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 月报管理路由已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 5. 上传风险管理路由
Write-Host ""
Write-Host "5. 上传风险管理路由..." -ForegroundColor Yellow
scp -i $SSH_KEY -o StrictHostKeyChecking=no "project-management/src/routes/risks.py" "${SERVER}:${SERVER_PATH}/project-management/src/routes/risks.py"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 风险管理路由已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 6. 上传项目阶段路由
Write-Host ""
Write-Host "6. 上传项目阶段路由..." -ForegroundColor Yellow
scp -i $SSH_KEY -o StrictHostKeyChecking=no "project-management/src/routes/phases.py" "${SERVER}:${SERVER_PATH}/project-management/src/routes/phases.py"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 项目阶段路由已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 7. 上传更新后的main.py
Write-Host ""
Write-Host "7. 上传更新后的main.py..." -ForegroundColor Yellow
scp -i $SSH_KEY -o StrictHostKeyChecking=no "project-management/src/main.py" "${SERVER}:${SERVER_PATH}/project-management/src/main.py"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ main.py已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 8. 上传更新后的API Gateway main.py
Write-Host ""
Write-Host "8. 上传更新后的API Gateway..." -ForegroundColor Yellow
scp -i $SSH_KEY -o StrictHostKeyChecking=no "api-gateway/src/main.py" "${SERVER}:${SERVER_PATH}/api-gateway/src/main.py"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ API Gateway已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 9. 重启服务
Write-Host ""
Write-Host "9. 重启项目管理服务和API Gateway..." -ForegroundColor Yellow
$restartCmd = "cd $SERVER_PATH && docker compose restart project-management api-gateway"
$restartResult = ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $restartCmd 2>&1
Write-Host $restartResult
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 服务已重启" -ForegroundColor Green
} else {
    Write-Host "⚠️  重启可能有问题，请检查输出" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ API路由上传完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "已创建的API路由:" -ForegroundColor Cyan
Write-Host "  - /api/v1/tasks (任务管理)" -ForegroundColor Yellow
Write-Host "  - /api/v1/milestones (里程碑管理)" -ForegroundColor Yellow
Write-Host "  - /api/v1/weekly-reports (周报管理)" -ForegroundColor Yellow
Write-Host "  - /api/v1/monthly-reports (月报管理)" -ForegroundColor Yellow
Write-Host "  - /api/v1/risks (风险管理)" -ForegroundColor Yellow
Write-Host "  - /api/v1/project-phases (项目阶段)" -ForegroundColor Yellow












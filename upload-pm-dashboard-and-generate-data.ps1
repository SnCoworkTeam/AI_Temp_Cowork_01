# 上传项目管理仪表盘并生成测试数据

$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"
$SERVER_PATH = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  上传项目管理仪表盘并生成测试数据" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# 1. 上传仪表盘页面
Write-Host ""
Write-Host "1. 上传项目管理仪表盘..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p ${SERVER_PATH}/web-ui/src/app/admin/projects/dashboard"
scp -i $SSH_KEY -o StrictHostKeyChecking=no "web-ui/src/app/admin/projects/dashboard/page.tsx" "${SERVER}:${SERVER_PATH}/web-ui/src/app/admin/projects/dashboard/page.tsx"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 仪表盘页面已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 2. 上传更新后的侧边栏
Write-Host ""
Write-Host "2. 上传更新后的侧边栏..." -ForegroundColor Yellow
scp -i $SSH_KEY -o StrictHostKeyChecking=no "web-ui/src/components/Layout/Sidebar.tsx" "${SERVER}:${SERVER_PATH}/web-ui/src/components/Layout/Sidebar.tsx"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 侧边栏已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 3. 上传数据生成脚本
Write-Host ""
Write-Host "3. 上传数据生成脚本..." -ForegroundColor Yellow
scp -i $SSH_KEY -o StrictHostKeyChecking=no "generate_pm_test_data_on_server.py" "${SERVER}:${SERVER_PATH}/generate_pm_test_data_on_server.py"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 数据生成脚本已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 4. 上传SQL脚本并在服务器上执行
Write-Host ""
Write-Host "4. 上传SQL脚本..." -ForegroundColor Yellow
scp -i $SSH_KEY -o StrictHostKeyChecking=no "generate_pm_test_data.sql" "${SERVER}:${SERVER_PATH}/generate_pm_test_data.sql"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ SQL脚本已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 5. 在服务器上执行SQL脚本生成数据
Write-Host ""
Write-Host "5. 在服务器上生成测试数据..." -ForegroundColor Yellow
$generateResult = ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "docker exec -i enterprise-ai-postgres psql -U ai_user -d ai_platform < ${SERVER_PATH}/generate_pm_test_data.sql" 2>&1
Write-Host $generateResult

# 5. 重启web-ui服务
Write-Host ""
Write-Host "5. 重启web-ui服务..." -ForegroundColor Yellow
$restartCmd = "cd $SERVER_PATH && docker compose restart web-ui"
$restartResult = ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $restartCmd 2>&1
Write-Host $restartResult
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ web-ui服务已重启" -ForegroundColor Green
} else {
    Write-Host "⚠️  重启可能有问题，请检查输出" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ 完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "已上传:" -ForegroundColor Cyan
Write-Host "  - 项目管理仪表盘页面" -ForegroundColor Yellow
Write-Host "  - 更新后的侧边栏菜单" -ForegroundColor Yellow
Write-Host ""
Write-Host "已生成测试数据:" -ForegroundColor Cyan
Write-Host "  - 项目阶段" -ForegroundColor Yellow
Write-Host "  - 里程碑" -ForegroundColor Yellow
Write-Host "  - 周报" -ForegroundColor Yellow
Write-Host "  - 风险" -ForegroundColor Yellow
Write-Host ""
Write-Host "访问地址:" -ForegroundColor Cyan
Write-Host "  http://43.143.139.197:3000/admin/projects/dashboard" -ForegroundColor Yellow


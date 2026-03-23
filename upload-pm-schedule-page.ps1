# 上传项目进度计划页面到服务器

$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"
$SERVER_PATH = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  上传项目进度计划页面到服务器" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# 1. 上传甘特图组件
Write-Host ""
Write-Host "1. 上传甘特图组件..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p ${SERVER_PATH}/web-ui/src/components/charts"
scp -i $SSH_KEY -o StrictHostKeyChecking=no "web-ui/src/components/charts/GanttChart.tsx" "${SERVER}:${SERVER_PATH}/web-ui/src/components/charts/GanttChart.tsx"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 甘特图组件已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 2. 上传进度计划页面
Write-Host ""
Write-Host "2. 上传进度计划页面..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p ${SERVER_PATH}/web-ui/src/app/admin/projects/schedule"
scp -i $SSH_KEY -o StrictHostKeyChecking=no "web-ui/src/app/admin/projects/schedule/page.tsx" "${SERVER}:${SERVER_PATH}/web-ui/src/app/admin/projects/schedule/page.tsx"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 进度计划页面已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 3. 上传更新后的侧边栏
Write-Host ""
Write-Host "3. 上传更新后的侧边栏..." -ForegroundColor Yellow
scp -i $SSH_KEY -o StrictHostKeyChecking=no "web-ui/src/components/Layout/Sidebar.tsx" "${SERVER}:${SERVER_PATH}/web-ui/src/components/Layout/Sidebar.tsx"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 侧边栏已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 4. 重启web-ui服务
Write-Host ""
Write-Host "4. 重启web-ui服务..." -ForegroundColor Yellow
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
Write-Host "✅ 项目进度计划页面上传完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "已上传:" -ForegroundColor Cyan
Write-Host "  - 甘特图组件 (GanttChart.tsx)" -ForegroundColor Yellow
Write-Host "  - 进度计划页面 (/admin/projects/schedule)" -ForegroundColor Yellow
Write-Host "  - 更新后的侧边栏菜单" -ForegroundColor Yellow
Write-Host ""
Write-Host "访问地址:" -ForegroundColor Cyan
Write-Host "  http://43.143.139.197:3000/admin/projects/schedule" -ForegroundColor Yellow












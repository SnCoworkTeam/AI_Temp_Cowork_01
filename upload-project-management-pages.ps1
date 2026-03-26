# 上传项目管理页面到服务器
# 同步所有项目管理相关的页面文件

$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"
$SERVER_PATH = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  上传项目管理页面到服务器" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# 1. 上传项目列表页面
Write-Host ""
Write-Host "1. 上传项目列表页面..." -ForegroundColor Yellow
scp -i $SSH_KEY -o StrictHostKeyChecking=no "web-ui/src/app/admin/projects/page.tsx" "${SERVER}:${SERVER_PATH}/web-ui/src/app/admin/projects/page.tsx"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 项目列表页面已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 2. 上传项目详情页面
Write-Host ""
Write-Host "2. 上传项目详情页面..." -ForegroundColor Yellow
# 确保目录存在
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p ${SERVER_PATH}/web-ui/src/app/admin/projects/[id]"
scp -i $SSH_KEY -o StrictHostKeyChecking=no "web-ui/src/app/admin/projects/[id]/page.tsx" "${SERVER}:${SERVER_PATH}/web-ui/src/app/admin/projects/[id]/page.tsx"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 项目详情页面已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 3. 上传项目创建页面
Write-Host ""
Write-Host "3. 上传项目创建页面..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p ${SERVER_PATH}/web-ui/src/app/admin/projects/create"
scp -i $SSH_KEY -o StrictHostKeyChecking=no "web-ui/src/app/admin/projects/create/page.tsx" "${SERVER}:${SERVER_PATH}/web-ui/src/app/admin/projects/create/page.tsx"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 项目创建页面已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 4. 上传项目导入页面
Write-Host ""
Write-Host "4. 上传项目导入页面..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p ${SERVER_PATH}/web-ui/src/app/admin/projects/import"
scp -i $SSH_KEY -o StrictHostKeyChecking=no "web-ui/src/app/admin/projects/import/page.tsx" "${SERVER}:${SERVER_PATH}/web-ui/src/app/admin/projects/import/page.tsx"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 项目导入页面已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 5. 上传项目阶段页面
Write-Host ""
Write-Host "5. 上传项目阶段页面..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p ${SERVER_PATH}/web-ui/src/app/admin/projects/phases"
scp -i $SSH_KEY -o StrictHostKeyChecking=no "web-ui/src/app/admin/projects/phases/page.tsx" "${SERVER}:${SERVER_PATH}/web-ui/src/app/admin/projects/phases/page.tsx"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 项目阶段页面已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 6. 上传任务管理页面
Write-Host ""
Write-Host "6. 上传任务管理页面..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p ${SERVER_PATH}/web-ui/src/app/admin/projects/tasks"
scp -i $SSH_KEY -o StrictHostKeyChecking=no "web-ui/src/app/admin/projects/tasks/page.tsx" "${SERVER}:${SERVER_PATH}/web-ui/src/app/admin/projects/tasks/page.tsx"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 任务管理页面已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 7. 上传里程碑管理页面
Write-Host ""
Write-Host "7. 上传里程碑管理页面..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p ${SERVER_PATH}/web-ui/src/app/admin/projects/milestones"
scp -i $SSH_KEY -o StrictHostKeyChecking=no "web-ui/src/app/admin/projects/milestones/page.tsx" "${SERVER}:${SERVER_PATH}/web-ui/src/app/admin/projects/milestones/page.tsx"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 里程碑管理页面已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 8. 上传周报管理页面
Write-Host ""
Write-Host "8. 上传周报管理页面..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p ${SERVER_PATH}/web-ui/src/app/admin/projects/weekly-reports"
scp -i $SSH_KEY -o StrictHostKeyChecking=no "web-ui/src/app/admin/projects/weekly-reports/page.tsx" "${SERVER}:${SERVER_PATH}/web-ui/src/app/admin/projects/weekly-reports/page.tsx"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 周报管理页面已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 9. 上传月报管理页面
Write-Host ""
Write-Host "9. 上传月报管理页面..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p ${SERVER_PATH}/web-ui/src/app/admin/projects/monthly-reports"
scp -i $SSH_KEY -o StrictHostKeyChecking=no "web-ui/src/app/admin/projects/monthly-reports/page.tsx" "${SERVER}:${SERVER_PATH}/web-ui/src/app/admin/projects/monthly-reports/page.tsx"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 月报管理页面已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 10. 上传风险管理页面
Write-Host ""
Write-Host "10. 上传风险管理页面..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p ${SERVER_PATH}/web-ui/src/app/admin/projects/risks"
scp -i $SSH_KEY -o StrictHostKeyChecking=no "web-ui/src/app/admin/projects/risks/page.tsx" "${SERVER}:${SERVER_PATH}/web-ui/src/app/admin/projects/risks/page.tsx"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 风险管理页面已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 11. 上传侧边栏组件（包含更新的菜单）
Write-Host ""
Write-Host "11. 上传侧边栏组件..." -ForegroundColor Yellow
scp -i $SSH_KEY -o StrictHostKeyChecking=no "web-ui/src/components/Layout/Sidebar.tsx" "${SERVER}:${SERVER_PATH}/web-ui/src/components/Layout/Sidebar.tsx"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 侧边栏组件已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
}

# 12. 重启web-ui服务
Write-Host ""
Write-Host "12. 重启web-ui服务..." -ForegroundColor Yellow
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
Write-Host "✅ 项目管理页面上传完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "已上传的页面:" -ForegroundColor Cyan
Write-Host "  - 项目列表" -ForegroundColor Yellow
Write-Host "  - 项目详情" -ForegroundColor Yellow
Write-Host "  - 项目创建" -ForegroundColor Yellow
Write-Host "  - 项目导入" -ForegroundColor Yellow
Write-Host "  - 项目阶段" -ForegroundColor Yellow
Write-Host "  - 任务管理" -ForegroundColor Yellow
Write-Host "  - 里程碑管理" -ForegroundColor Yellow
Write-Host "  - 周报管理" -ForegroundColor Yellow
Write-Host "  - 月报管理" -ForegroundColor Yellow
Write-Host "  - 风险管理" -ForegroundColor Yellow
Write-Host "  - 侧边栏组件（菜单）" -ForegroundColor Yellow
Write-Host ""
Write-Host "服务器访问地址:" -ForegroundColor Cyan
Write-Host "  http://43.143.139.197:3000/admin/projects" -ForegroundColor Yellow












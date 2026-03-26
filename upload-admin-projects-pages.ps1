# 上传admin/projects页面到服务器
$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"
$SERVER_PATH = "/opt/enterprise-ai-platform"

Write-Host "上传admin/projects页面..." -ForegroundColor Cyan

# 检查密钥
if (-not (Test-Path $SSH_KEY)) {
    $SSH_KEY = "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem"
}

# 上传文件
if (Test-Path "web-ui/src/app/admin/projects") {
    Write-Host "上传admin/projects目录..." -ForegroundColor Yellow
    
    # 创建远程目录
    ssh -i $SSH_KEY -F remote.ssh enterprise-ai-server "mkdir -p $SERVER_PATH/web-ui/src/app/admin/projects/import $SERVER_PATH/web-ui/src/app/admin/projects/tasks $SERVER_PATH/web-ui/src/app/admin/projects/reports" 2>&1 | Out-Null
    
    # 上传主页面
    scp -i $SSH_KEY -F remote.ssh -o StrictHostKeyChecking=no web-ui/src/app/admin/projects/page.tsx enterprise-ai-server:$SERVER_PATH/web-ui/src/app/admin/projects/ 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ page.tsx 上传成功" -ForegroundColor Green
    }
    
    # 上传import页面
    scp -i $SSH_KEY -F remote.ssh -o StrictHostKeyChecking=no web-ui/src/app/admin/projects/import/page.tsx enterprise-ai-server:$SERVER_PATH/web-ui/src/app/admin/projects/import/ 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ import/page.tsx 上传成功" -ForegroundColor Green
    }
    
    # 上传tasks页面
    scp -i $SSH_KEY -F remote.ssh -o StrictHostKeyChecking=no web-ui/src/app/admin/projects/tasks/page.tsx enterprise-ai-server:$SERVER_PATH/web-ui/src/app/admin/projects/tasks/ 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ tasks/page.tsx 上传成功" -ForegroundColor Green
    }
    
    # 上传reports页面
    scp -i $SSH_KEY -F remote.ssh -o StrictHostKeyChecking=no web-ui/src/app/admin/projects/reports/page.tsx enterprise-ai-server:$SERVER_PATH/web-ui/src/app/admin/projects/reports/ 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ reports/page.tsx 上传成功" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "重启web-ui服务..." -ForegroundColor Yellow
    ssh -i $SSH_KEY -F remote.ssh enterprise-ai-server "cd $SERVER_PATH; docker compose restart web-ui" 2>&1
    
    Write-Host ""
    Write-Host "完成！等待服务重启..." -ForegroundColor Green
    Write-Host "请等待30秒后刷新页面: http://43.143.139.197:3000/admin/projects" -ForegroundColor Yellow
} else {
    Write-Host "错误: 找不到web-ui/src/app/admin/projects目录" -ForegroundColor Red
}


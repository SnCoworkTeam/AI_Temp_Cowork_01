# 上传API网关修复到服务器
# 修复 /admin/projects 404 错误

$SERVER = "ubuntu@43.143.139.197"
$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER_PATH = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  上传API网关修复" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 检查SSH密钥文件
if (-not (Test-Path $SSH_KEY)) {
    Write-Host "错误: SSH密钥文件不存在: $SSH_KEY" -ForegroundColor Red
    exit 1
}

Write-Host "上传API网关修复文件..." -ForegroundColor Cyan

# 上传修复后的main.py
scp -i $SSH_KEY -o StrictHostKeyChecking=no `
    "api-gateway/src/main.py" `
    "${SERVER}:${SERVER_PATH}/api-gateway/src/main.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "上传失败!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "重启API网关服务..." -ForegroundColor Cyan

# 重启API网关服务
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER `
    "cd $SERVER_PATH && docker compose restart api-gateway"

Write-Host ""
Write-Host "等待服务启动..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "检查服务状态..." -ForegroundColor Cyan
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER `
    "cd $SERVER_PATH && docker compose ps api-gateway"

Write-Host ""
Write-Host "查看服务日志（最后20行）..." -ForegroundColor Cyan
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER `
    "cd $SERVER_PATH && docker compose logs --tail=20 api-gateway"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  完成!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "测试修复:" -ForegroundColor Cyan
Write-Host "  1. 访问: http://43.143.139.197:3000/admin/projects" -ForegroundColor Yellow
Write-Host "  2. 检查API: http://43.143.139.197:8080/api/v1/projects" -ForegroundColor Yellow
Write-Host "  3. 检查日志: ssh -i $SSH_KEY $SERVER 'docker compose logs -f api-gateway'" -ForegroundColor Yellow


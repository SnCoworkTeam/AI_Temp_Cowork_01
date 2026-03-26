# 修复 Runner 标签配置
# 重新配置 Runner 并明确指定 self-hosted 标签

$SSH_KEY = if (Test-Path ".\enterprise_ai_platform.pem") { ".\enterprise_ai_platform.pem" } else { "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem" }
$SERVER = "ubuntu@43.143.139.197"
$REPO_URL = "https://github.com/PMLiuyubin/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "修复 Runner 标签配置" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "步骤 1: 停止并删除当前 Runner 配置..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "cd /opt/actions-runner && sudo ./svc.sh stop && sudo ./svc.sh uninstall" 2>&1

Write-Host ""
Write-Host "步骤 2: 删除旧配置..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "cd /opt/actions-runner && rm -f .runner .credentials .credentials_rsaparams .env" 2>&1

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "需要新的配置 Token" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "请按照以下步骤获取新的 Token:" -ForegroundColor Cyan
Write-Host "  1. 访问: https://github.com/PMLiuyubin/enterprise-ai-platform/settings/actions/runners/new" -ForegroundColor White
Write-Host "  2. 选择 'Linux' 和 'x64'" -ForegroundColor White
Write-Host "  3. 复制显示的 Token" -ForegroundColor White
Write-Host ""
Write-Host "或者，如果已有 Runner，删除后重新添加:" -ForegroundColor Cyan
Write-Host "  1. 访问: https://github.com/PMLiuyubin/enterprise-ai-platform/settings/actions/runners" -ForegroundColor White
Write-Host "  2. 删除现有的 'server-production' Runner" -ForegroundColor White
Write-Host "  3. 点击 'New runner' 获取新 Token" -ForegroundColor White
Write-Host ""
Write-Host "获取 Token 后，运行以下命令配置 Runner:" -ForegroundColor Yellow
Write-Host "  .\configure-runner-with-labels.ps1 YOUR_TOKEN_HERE" -ForegroundColor White
Write-Host ""


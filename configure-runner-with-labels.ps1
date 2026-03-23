# 配置 GitHub Actions Runner 并明确指定 self-hosted 标签
# 使用方法: .\configure-runner-with-labels.ps1 YOUR_TOKEN_HERE

param(
    [Parameter(Mandatory=$true)]
    [string]$RunnerToken
)

$SSH_KEY = if (Test-Path ".\enterprise_ai_platform.pem") { ".\enterprise_ai_platform.pem" } else { "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem" }
$SERVER = "ubuntu@43.143.139.197"
$REPO_URL = "https://github.com/PMLiuyubin/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "配置 GitHub Actions Runner（带标签）" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤1: 配置 Runner 并明确指定 self-hosted 标签
Write-Host "[1/3] 配置 Runner（明确指定 self-hosted 标签）..." -ForegroundColor Yellow
$configCommand = "cd /opt/actions-runner && echo -e '\n\n\n\n\n\n\n\n' | ./config.sh --url $REPO_URL --token $RunnerToken --name 'server-production' --work '_work' --labels 'self-hosted,linux,x64' --replace"

ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $configCommand

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Runner 配置成功（标签: self-hosted,linux,x64）" -ForegroundColor Green
} else {
    Write-Host "❌ Runner 配置失败" -ForegroundColor Red
    exit 1
}

# 步骤2: 安装为系统服务
Write-Host ""
Write-Host "[2/3] 安装为系统服务..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "cd /opt/actions-runner && sudo ./svc.sh install ubuntu"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 服务安装成功" -ForegroundColor Green
} else {
    Write-Host "❌ 服务安装失败" -ForegroundColor Red
    exit 1
}

# 步骤3: 启动服务
Write-Host ""
Write-Host "[3/3] 启动服务..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "cd /opt/actions-runner && sudo ./svc.sh start"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 服务启动成功" -ForegroundColor Green
} else {
    Write-Host "❌ 服务启动失败" -ForegroundColor Red
    exit 1
}

# 等待服务启动
Start-Sleep -Seconds 5

# 检查状态
Write-Host ""
Write-Host "检查服务状态..." -ForegroundColor Cyan
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "cd /opt/actions-runner && sudo ./svc.sh status && echo '' && sudo journalctl -u actions.runner.* -n 10 --no-pager | tail -5"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Runner 配置完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "验证 Runner 状态:" -ForegroundColor Cyan
Write-Host "  https://github.com/PMLiuyubin/enterprise-ai-platform/settings/actions/runners" -ForegroundColor Yellow
Write-Host ""
Write-Host "应该看到:" -ForegroundColor Cyan
Write-Host "  - Runner 名称: server-production" -ForegroundColor White
Write-Host "  - 状态: Online（绿色）" -ForegroundColor White
Write-Host "  - 标签: self-hosted, linux, x64" -ForegroundColor White
Write-Host ""
Write-Host "现在工作流应该可以正常接收任务了！" -ForegroundColor Green
Write-Host ""


# 配置 GitHub Actions Runner
# 使用方法: .\configure-runner.ps1 YOUR_TOKEN_HERE

param(
    [Parameter(Mandatory=$true)]
    [string]$RunnerToken
)

$SSH_KEY = if (Test-Path ".\enterprise_ai_platform.pem") { ".\enterprise_ai_platform.pem" } else { "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem" }
$SERVER = "ubuntu@43.143.139.197"
$REPO_URL = "https://github.com/PMLiuyubin/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "配置 GitHub Actions Runner" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤1: 配置 Runner
Write-Host "[1/2] 配置 Runner..." -ForegroundColor Yellow
$configCommand = "cd /opt/actions-runner && ./config.sh --url $REPO_URL --token $RunnerToken --name 'server-`$(hostname)' --work '_work' --replace"

ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $configCommand

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Runner 配置成功" -ForegroundColor Green
} else {
    Write-Host "❌ Runner 配置失败" -ForegroundColor Red
    exit 1
}

# 步骤2: 安装为系统服务
Write-Host ""
Write-Host "[2/2] 安装为系统服务..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "cd /opt/actions-runner && sudo ./svc.sh install ubuntu && sudo ./svc.sh start"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 服务安装并启动成功" -ForegroundColor Green
} else {
    Write-Host "❌ 服务安装失败" -ForegroundColor Red
    exit 1
}

# 检查状态
Write-Host ""
Write-Host "检查服务状态..." -ForegroundColor Cyan
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "cd /opt/actions-runner && sudo ./svc.sh status"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Runner 安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步:" -ForegroundColor Cyan
Write-Host "1. 在 GitHub 上验证 Runner 状态:" -ForegroundColor Yellow
Write-Host "   https://github.com/PMLiuyubin/enterprise-ai-platform/settings/actions/runners" -ForegroundColor White
Write-Host ""
Write-Host "2. 提交自托管 Runner 工作流:" -ForegroundColor Yellow
Write-Host "   git add .github/workflows/deploy-self-hosted.yml" -ForegroundColor White
Write-Host "   git commit -m '添加自托管Runner部署工作流'" -ForegroundColor White
Write-Host "   git push origin main" -ForegroundColor White
Write-Host ""


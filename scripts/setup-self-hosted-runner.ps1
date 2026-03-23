# PowerShell 脚本：在服务器上设置自托管 Runner
# 使用方法: 在本地运行，通过 SSH 在服务器上执行命令

$SSH_KEY = ".\enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"
$REPO_URL = "https://github.com/PMLiuyubin/enterprise-ai-platform"
$RUNNER_DIR = "/opt/actions-runner"
$RUNNER_VERSION = "2.311.0"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GitHub Actions 自托管 Runner 设置" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查密钥文件
if (-not (Test-Path $SSH_KEY)) {
    $SSH_KEY = "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem"
    if (-not (Test-Path $SSH_KEY)) {
        Write-Host "❌ 未找到密钥文件" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ 找到密钥文件: $SSH_KEY" -ForegroundColor Green
Write-Host ""

# 步骤1: 获取配置 Token
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "步骤1: 获取 Runner 配置 Token" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "请访问以下链接获取配置 Token:" -ForegroundColor Cyan
Write-Host "https://github.com/PMLiuyubin/enterprise-ai-platform/settings/actions/runners/new" -ForegroundColor Yellow
Write-Host ""
Write-Host "操作步骤:" -ForegroundColor Cyan
Write-Host "1. 选择操作系统: Linux" -ForegroundColor White
Write-Host "2. 选择架构: x64" -ForegroundColor White
Write-Host "3. 复制显示的配置命令中的 token" -ForegroundColor White
Write-Host ""
$RUNNER_TOKEN = Read-Host "请输入配置 Token"

if ([string]::IsNullOrWhiteSpace($RUNNER_TOKEN)) {
    Write-Host "❌ Token 不能为空" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "步骤2: 在服务器上安装 Runner" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

# 创建安装脚本
$installScript = @"
#!/bin/bash
set -e

echo "=========================================="
echo "安装 GitHub Actions Runner"
echo "=========================================="

# 创建目录
echo "[1/5] 创建安装目录..."
sudo mkdir -p $RUNNER_DIR
sudo chown ubuntu:ubuntu $RUNNER_DIR
cd $RUNNER_DIR

# 下载 Runner
echo ""
echo "[2/5] 下载 Runner..."
if [ ! -f "actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" ]; then
    curl -o actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz -L \
        https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz
fi

# 解压
echo ""
echo "[3/5] 解压安装包..."
tar xzf ./actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz
sudo chown -R ubuntu:ubuntu $RUNNER_DIR

# 配置 Runner
echo ""
echo "[4/5] 配置 Runner..."
./config.sh --url $REPO_URL --token $RUNNER_TOKEN --name "server-`$(hostname)" --work "_work" --replace

# 安装为服务
echo ""
echo "[5/5] 安装为系统服务..."
sudo ./svc.sh install ubuntu
sudo ./svc.sh start

echo ""
echo "=========================================="
echo "✅ Runner 安装完成！"
echo "=========================================="
echo ""
echo "检查服务状态..."
sudo ./svc.sh status
"@

# 将脚本上传到服务器并执行
Write-Host "上传安装脚本到服务器..." -ForegroundColor Cyan
$tempScript = [System.IO.Path]::GetTempFileName()
$installScript | Out-File -FilePath $tempScript -Encoding UTF8

# 上传脚本
scp -i $SSH_KEY -o StrictHostKeyChecking=no $tempScript "${SERVER}:/tmp/install-runner.sh" 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 上传脚本失败" -ForegroundColor Red
    Remove-Item $tempScript
    exit 1
}

# 执行安装
Write-Host "在服务器上执行安装..." -ForegroundColor Cyan
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "chmod +x /tmp/install-runner.sh && bash /tmp/install-runner.sh"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✅ Runner 安装成功！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步:" -ForegroundColor Cyan
    Write-Host "1. 在 GitHub 上验证 Runner 状态:" -ForegroundColor Yellow
    Write-Host "   https://github.com/PMLiuyubin/enterprise-ai-platform/settings/actions/runners" -ForegroundColor White
    Write-Host ""
    Write-Host "2. 使用自托管 Runner 工作流:" -ForegroundColor Yellow
    Write-Host "   - deploy-self-hosted.yml (已创建)" -ForegroundColor White
    Write-Host ""
    Write-Host "3. 测试工作流" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "❌ Runner 安装失败" -ForegroundColor Red
    Write-Host "请检查错误信息并重试" -ForegroundColor Yellow
}

# 清理临时文件
Remove-Item $tempScript

Write-Host ""


# 部署SonarQube到服务器的PowerShell脚本
# 从本地Windows机器执行，通过SSH连接到服务器并安装SonarQube

$ErrorActionPreference = "Stop"

# 服务器配置
$SERVER_IP = "124.220.181.231"
$SERVER_USER = "ubuntu"
$SSH_KEY = "E:\enterprise-ai-platform\SonarQube1.pem"
$REMOTE_SCRIPT = "/tmp/install-sonarqube.sh"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "部署SonarQube到服务器" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "服务器: ${SERVER_USER}@${SERVER_IP}" -ForegroundColor Yellow
Write-Host ""

# 检查SSH密钥文件
if (-not (Test-Path $SSH_KEY)) {
    Write-Host "错误: SSH密钥文件不存在: $SSH_KEY" -ForegroundColor Red
    exit 1
}

# 检查是否安装了OpenSSH客户端
$sshPath = Get-Command ssh -ErrorAction SilentlyContinue
if (-not $sshPath) {
    Write-Host "错误: 未找到SSH客户端，请安装OpenSSH" -ForegroundColor Red
    Write-Host "安装方法: Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0" -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/5] 测试SSH连接..." -ForegroundColor Cyan
try {
    $testResult = ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 "${SERVER_USER}@${SERVER_IP}" "echo 'SSH连接成功'" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ SSH连接正常" -ForegroundColor Green
    } else {
        throw "SSH连接失败"
    }
} catch {
    Write-Host "✗ SSH连接失败，请检查：" -ForegroundColor Red
    Write-Host "  1. 服务器IP是否正确" -ForegroundColor Yellow
    Write-Host "  2. SSH密钥文件路径是否正确" -ForegroundColor Yellow
    Write-Host "  3. 服务器是否允许SSH连接" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "[2/5] 上传安装脚本..." -ForegroundColor Cyan
$scriptPath = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "install-sonarqube.sh"
if (-not (Test-Path $scriptPath)) {
    # 尝试使用当前工作目录
    $scriptPath = Join-Path (Get-Location) "scripts\install-sonarqube.sh"
    if (-not (Test-Path $scriptPath)) {
        Write-Host "错误: 安装脚本不存在: $scriptPath" -ForegroundColor Red
        exit 1
    }
}

try {
    scp -i $SSH_KEY -o StrictHostKeyChecking=no $scriptPath "${SERVER_USER}@${SERVER_IP}:${REMOTE_SCRIPT}" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ 脚本已上传" -ForegroundColor Green
    } else {
        throw "上传失败"
    }
} catch {
    Write-Host "✗ 脚本上传失败" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[3/5] 设置脚本执行权限..." -ForegroundColor Cyan
try {
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no "${SERVER_USER}@${SERVER_IP}" "chmod +x $REMOTE_SCRIPT" 2>&1 | Out-Null
    Write-Host "✓ 权限已设置" -ForegroundColor Green
} catch {
    Write-Host "✗ 设置权限失败" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[4/5] 执行安装脚本..." -ForegroundColor Cyan
Write-Host "注意: 安装过程可能需要10-15分钟，请耐心等待..." -ForegroundColor Yellow
Write-Host ""

# 执行安装脚本（使用sudo）
try {
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no "${SERVER_USER}@${SERVER_IP}" "sudo bash $REMOTE_SCRIPT"
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✓ SonarQube安装完成" -ForegroundColor Green
    } else {
        throw "安装失败"
    }
} catch {
    Write-Host ""
    Write-Host "✗ 安装过程中出现错误，请检查服务器日志" -ForegroundColor Red
    Write-Host "查看日志命令: ssh -i `"$SSH_KEY`" ${SERVER_USER}@${SERVER_IP} 'sudo journalctl -u sonarqube -n 50'" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "[5/5] 验证安装..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

# 检查服务状态
try {
    $serviceStatus = ssh -i $SSH_KEY -o StrictHostKeyChecking=no "${SERVER_USER}@${SERVER_IP}" "sudo systemctl is-active sonarqube" 2>&1
    if ($serviceStatus -match "active") {
        Write-Host "✓ SonarQube服务运行正常" -ForegroundColor Green
    } else {
        Write-Host "⚠ SonarQube服务可能未完全启动，请稍后检查" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ 无法检查服务状态" -ForegroundColor Yellow
}

# 检查Web访问
try {
    $response = Invoke-WebRequest -Uri "http://${SERVER_IP}:9000/api/system/status" -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($null -ne $response -and $response.Content -match "UP") {
        Write-Host "✓ SonarQube Web界面可访问" -ForegroundColor Green
    } else {
        Write-Host "⚠ SonarQube Web界面可能尚未就绪" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ SonarQube Web界面可能尚未就绪，请稍后访问" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "部署完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "访问地址: http://${SERVER_IP}:9000" -ForegroundColor Yellow
Write-Host "默认登录: admin / admin (首次登录后需要修改)" -ForegroundColor Yellow
Write-Host ""
Write-Host "后续步骤:" -ForegroundColor Cyan
Write-Host "1. 访问 http://${SERVER_IP}:9000 并登录" -ForegroundColor White
Write-Host "2. 修改admin密码" -ForegroundColor White
Write-Host "3. 创建项目并生成Token" -ForegroundColor White
Write-Host "4. 运行 scripts/setup-sonarqube-project.sh 配置项目" -ForegroundColor White
Write-Host "5. 参考 docs/sonarqube-integration.md 进行集成" -ForegroundColor White
Write-Host ""


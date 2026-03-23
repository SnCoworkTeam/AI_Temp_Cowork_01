# 检查服务器并配置Jenkins自动化部署脚本
# 服务器: 1.117.62.202
# 目标部署服务器: 43.143.139.197

param(
    [string]$JenkinsServer = "ubuntu@1.117.62.202",
    [string]$JenkinsPassword = "Liu@bner1983",
    [string]$DeployServer = "ubuntu@43.143.139.197",
    [string]$DeployKeyPath = ".\enterprise_ai_platform.pem"
)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "服务器检查和Jenkins配置脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查sshpass是否安装
if (-not (Get-Command sshpass -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️  sshpass未安装，正在尝试安装..." -ForegroundColor Yellow
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        choco install sshpass -y
    } else {
        Write-Host "❌ 请手动安装sshpass或使用SSH密钥" -ForegroundColor Red
        exit 1
    }
}

# 1. 检查Jenkins服务器系统信息
Write-Host "`n[1/5] 检查Jenkins服务器系统信息..." -ForegroundColor Yellow
$systemInfo = sshpass -p $JenkinsPassword ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $JenkinsServer @"
echo "=== 系统信息 ==="
uname -a
echo ""
echo "=== 内存和CPU ==="
free -h
echo "CPU核心数: \$(nproc)"
echo ""
echo "=== 磁盘空间 ==="
df -h | grep -E '^/dev|Filesystem'
"@ 2>&1

Write-Host $systemInfo -ForegroundColor Green

# 2. 检查已安装的软件
Write-Host "`n[2/5] 检查已安装的软件..." -ForegroundColor Yellow
$installed = sshpass -p $JenkinsPassword ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $JenkinsServer @"
echo "=== Docker ==="
docker --version 2>&1 || echo "未安装"
echo ""
echo "=== Java ==="
java -version 2>&1 | head -3 || echo "未安装"
echo ""
echo "=== Git ==="
git --version 2>&1 || echo "未安装"
echo ""
echo "=== Jenkins ==="
systemctl status jenkins 2>&1 | head -3 || echo "未安装"
"@ 2>&1

Write-Host $installed -ForegroundColor Green

# 3. 检查网络连接
Write-Host "`n[3/5] 检查网络连接..." -ForegroundColor Yellow
$network = sshpass -p $JenkinsPassword ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $JenkinsServer @"
echo "=== 公网IP ==="
curl -s ifconfig.me || curl -s ipinfo.io/ip
echo ""
echo "=== 测试连接到部署服务器 ==="
ping -c 2 43.143.139.197 2>&1 | head -5
"@ 2>&1

Write-Host $network -ForegroundColor Green

# 4. 检查SSH密钥配置
Write-Host "`n[4/5] 检查SSH密钥配置..." -ForegroundColor Yellow
if (Test-Path $DeployKeyPath) {
    Write-Host "✅ 找到部署密钥: $DeployKeyPath" -ForegroundColor Green
    
    # 检查密钥是否已上传到Jenkins服务器
    $keyExists = sshpass -p $JenkinsPassword ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $JenkinsServer "test -f ~/.ssh/deploy_key && echo 'exists' || echo 'not_exists'" 2>&1
    
    if ($keyExists -match "not_exists") {
        Write-Host "⚠️  部署密钥未上传到Jenkins服务器" -ForegroundColor Yellow
        Write-Host "正在上传部署密钥..." -ForegroundColor Cyan
        sshpass -p $JenkinsPassword scp -o StrictHostKeyChecking=no $DeployKeyPath "${JenkinsServer}:~/.ssh/deploy_key" 2>&1
        sshpass -p $JenkinsPassword ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $JenkinsServer "chmod 600 ~/.ssh/deploy_key" 2>&1
        Write-Host "✅ 部署密钥已上传" -ForegroundColor Green
    } else {
        Write-Host "✅ 部署密钥已存在" -ForegroundColor Green
    }
} else {
    Write-Host "❌ 未找到部署密钥: $DeployKeyPath" -ForegroundColor Red
}

# 5. 检查Jenkins安装状态并提供安装指南
Write-Host "`n[5/5] Jenkins安装状态检查..." -ForegroundColor Yellow
$jenkinsStatus = sshpass -p $JenkinsPassword ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $JenkinsServer "systemctl is-active jenkins 2>&1" 2>&1

if ($jenkinsStatus -match "active") {
    Write-Host "✅ Jenkins已安装并运行" -ForegroundColor Green
    
    # 获取Jenkins初始密码
    $jenkinsPassword = sshpass -p $JenkinsPassword ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $JenkinsServer "sudo cat /var/lib/jenkins/secrets/initialAdminPassword 2>&1" 2>&1
    if ($jenkinsPassword -notmatch "No such file") {
        Write-Host "`nJenkins初始管理员密码:" -ForegroundColor Cyan
        Write-Host $jenkinsPassword -ForegroundColor Yellow
    }
    
    # 获取Jenkins URL
    $jenkinsUrl = sshpass -p $JenkinsPassword ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $JenkinsServer "curl -s ifconfig.me" 2>&1
    Write-Host "`nJenkins访问地址: http://$jenkinsUrl:8080" -ForegroundColor Cyan
} else {
    Write-Host "❌ Jenkins未安装" -ForegroundColor Red
    Write-Host "`n需要安装Jenkins吗？(Y/N): " -ForegroundColor Yellow -NoNewline
    $install = Read-Host
    if ($install -eq "Y" -or $install -eq "y") {
        Write-Host "`n开始安装Jenkins..." -ForegroundColor Cyan
        $installScript = @"
#!/bin/bash
# 安装Jenkins
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee /usr/share/keyrings/jenkins-keyring.asc > /dev/null
echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/ | sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt-get update
sudo apt-get install -y jenkins
sudo systemctl start jenkins
sudo systemctl enable jenkins
echo "Jenkins安装完成"
"@
        
        sshpass -p $JenkinsPassword ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30 $JenkinsServer "bash -s" <<< $installScript 2>&1 | Tee-Object -Variable installOutput
        
        if ($installOutput -match "安装完成") {
            Write-Host "✅ Jenkins安装成功" -ForegroundColor Green
            Start-Sleep -Seconds 5
            $jenkinsPassword = sshpass -p $JenkinsPassword ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $JenkinsServer "sudo cat /var/lib/jenkins/secrets/initialAdminPassword 2>&1" 2>&1
            Write-Host "`nJenkins初始管理员密码:" -ForegroundColor Cyan
            Write-Host $jenkinsPassword -ForegroundColor Yellow
        } else {
            Write-Host "❌ Jenkins安装失败" -ForegroundColor Red
            Write-Host $installOutput -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "检查完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""


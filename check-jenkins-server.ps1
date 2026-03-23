# 检查Jenkins服务器并配置自动化部署
# 服务器: 1.117.62.202
# 目标部署服务器: 43.143.139.197

param(
    [string]$JenkinsServer = "1.117.62.202",
    [string]$JenkinsUser = "ubuntu",
    [string]$JenkinsPassword = "Liu@bner1983",
    [string]$DeployServer = "43.143.139.197",
    [string]$DeployUser = "ubuntu"
)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Jenkins服务器检查和配置" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Jenkins服务器: $JenkinsUser@$JenkinsServer" -ForegroundColor Yellow
Write-Host "部署服务器: $DeployUser@$DeployServer" -ForegroundColor Yellow
Write-Host ""

# 使用PowerShell的SSH功能
$ErrorActionPreference = "Continue"

# 创建临时SSH脚本
$sshScript = @"
#!/bin/bash
echo "=== 系统信息 ==="
uname -a
echo ""
echo "=== 操作系统版本 ==="
cat /etc/os-release | head -5
echo ""
echo "=== 内存和CPU ==="
free -h
echo "CPU核心数: \$(nproc)"
echo ""
echo "=== 磁盘空间 ==="
df -h | head -6
echo ""
echo "=== Docker ==="
docker --version 2>&1 || echo "未安装Docker"
echo ""
echo "=== Java ==="
java -version 2>&1 | head -3 || echo "未安装Java"
echo ""
echo "=== Git ==="
git --version 2>&1 || echo "未安装Git"
echo ""
echo "=== Jenkins状态 ==="
systemctl is-active jenkins 2>&1 || echo "Jenkins未安装或未运行"
echo ""
echo "=== 已安装的软件包 ==="
dpkg -l | grep -E 'jenkins|docker|java|git' | head -10
echo ""
echo "=== 网络连接测试 ==="
ping -c 2 $DeployServer 2>&1 | head -5
echo ""
echo "=== 公网IP ==="
curl -s ifconfig.me || curl -s ipinfo.io/ip
echo ""
echo "=== 开放端口 ==="
ss -tuln | grep -E ':(8080|443|80|22|50000)' | head -10
"@

# 保存脚本到临时文件
$tempScript = [System.IO.Path]::GetTempFileName() + ".sh"
$sshScript | Out-File -FilePath $tempScript -Encoding UTF8 -NoNewline

Write-Host "[1/3] 检查服务器系统信息..." -ForegroundColor Yellow
Write-Host ""

try {
    # 使用plink或直接SSH（需要先配置SSH密钥或使用密码）
    # 由于Windows PowerShell SSH可能不支持密码，我们创建一个指导文档
    Write-Host "⚠️  由于Windows PowerShell SSH限制，请手动执行以下命令检查服务器：" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "SSH连接命令：" -ForegroundColor Cyan
    Write-Host "  ssh $JenkinsUser@$JenkinsServer" -ForegroundColor White
    Write-Host ""
    Write-Host "然后在服务器上执行以下脚本：" -ForegroundColor Cyan
    Write-Host $sshScript -ForegroundColor White
    Write-Host ""
    
    # 或者尝试使用PowerShell的SSH（如果可用）
    if (Get-Command ssh -ErrorAction SilentlyContinue) {
        Write-Host "尝试使用SSH连接（可能需要手动输入密码）..." -ForegroundColor Yellow
        Write-Host "密码: $JenkinsPassword" -ForegroundColor Gray
        Write-Host ""
        
        # 创建expect脚本（如果可用）
        $expectScript = @"
#!/usr/bin/expect
set timeout 30
spawn ssh -o StrictHostKeyChecking=no $JenkinsUser@$JenkinsServer
expect "password:"
send "$JenkinsPassword\r"
expect "\$ "
send "bash <(cat <<'EOF'
$sshScript
EOF
)\r"
expect "\$ "
send "exit\r"
expect eof
"@
        
        $expectFile = [System.IO.Path]::GetTempFileName() + ".exp"
        $expectScript | Out-File -FilePath $expectFile -Encoding UTF8 -NoNewline
        
        Write-Host "已创建expect脚本: $expectFile" -ForegroundColor Green
        Write-Host "如果安装了expect，可以运行: expect $expectFile" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "❌ 连接失败: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "[2/3] Jenkins安装和配置指南" -ForegroundColor Yellow
Write-Host ""

$jenkinsInstallScript = @"
#!/bin/bash
# Jenkins安装脚本

echo "=== 更新系统 ==="
sudo apt-get update

echo "=== 安装Java ==="
sudo apt-get install -y openjdk-17-jdk

echo "=== 安装Jenkins ==="
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee /usr/share/keyrings/jenkins-keyring.asc > /dev/null
echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/ | sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt-get update
sudo apt-get install -y jenkins

echo "=== 启动Jenkins ==="
sudo systemctl start jenkins
sudo systemctl enable jenkins

echo "=== 检查Jenkins状态 ==="
sudo systemctl status jenkins --no-pager | head -10

echo "=== 获取初始密码 ==="
echo "Jenkins初始管理员密码:"
sudo cat /var/lib/jenkins/secrets/initialAdminPassword

echo ""
echo "=== 防火墙配置 ==="
echo "如果需要，请开放8080端口:"
echo "  sudo ufw allow 8080"
echo ""
echo "Jenkins访问地址: http://\$(curl -s ifconfig.me):8080"
"@

$jenkinsFile = "install-jenkins.sh"
$jenkinsInstallScript | Out-File -FilePath $jenkinsFile -Encoding UTF8 -NoNewline
Write-Host "✅ 已创建Jenkins安装脚本: $jenkinsFile" -ForegroundColor Green
Write-Host ""

Write-Host "[3/3] Jenkins部署配置指南" -ForegroundColor Yellow
Write-Host ""

$deployConfigScript = @"
#!/bin/bash
# Jenkins部署配置脚本

echo "=== 配置SSH密钥 ==="
# 创建.ssh目录
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 如果已有部署密钥，复制到Jenkins用户
if [ -f /home/$JenkinsUser/.ssh/deploy_key ]; then
    sudo cp /home/$JenkinsUser/.ssh/deploy_key /var/lib/jenkins/.ssh/deploy_key
    sudo chown jenkins:jenkins /var/lib/jenkins/.ssh/deploy_key
    sudo chmod 600 /var/lib/jenkins/.ssh/deploy_key
    echo "✅ 部署密钥已配置"
fi

echo "=== 安装Jenkins插件 ==="
echo "需要在Jenkins Web界面安装以下插件:"
echo "  - SSH Pipeline Steps"
echo "  - SSH Agent Plugin"
echo "  - Git Plugin"
echo "  - Docker Pipeline Plugin"

echo ""
echo "=== 创建部署Pipeline脚本 ==="
cat > /tmp/jenkins-deploy-pipeline.groovy <<'DEPLOYEOF'
pipeline {
    agent any
    
    environment {
        DEPLOY_SERVER = '43.143.139.197'
        DEPLOY_USER = 'ubuntu'
        DEPLOY_KEY = credentials('deploy-ssh-key')
        PROJECT_DIR = '/opt/enterprise-ai-platform'
    }
    
    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/PMLiuyubin/enterprise-ai-platform.git'
            }
        }
        
        stage('Deploy') {
            steps {
                script {
                    sshagent([DEPLOY_KEY]) {
                        sh '''
                            ssh -o StrictHostKeyChecking=no \${DEPLOY_USER}@\${DEPLOY_SERVER} << 'ENDSSH'
                                cd \${PROJECT_DIR}
                                git pull origin main
                                docker compose down
                                docker compose build --parallel
                                docker compose up -d
                                docker compose ps
                            ENDSSH
                        '''
                    }
                }
            }
        }
    }
    
    post {
        success {
            echo '部署成功！'
        }
        failure {
            echo '部署失败！'
        }
    }
}
DEPLOYEOF

echo "✅ Pipeline脚本已创建: /tmp/jenkins-deploy-pipeline.groovy"
echo ""
echo "=== 配置步骤 ==="
echo "1. 在Jenkins中添加SSH凭据（deploy-ssh-key）"
echo "2. 创建新的Pipeline任务"
echo "3. 将/tmp/jenkins-deploy-pipeline.groovy的内容复制到Pipeline脚本中"
echo "4. 保存并运行"
"@

$deployFile = "configure-jenkins-deploy.sh"
$deployConfigScript | Out-File -FilePath $deployFile -Encoding UTF8 -NoNewline
Write-Host "✅ 已创建部署配置脚本: $deployFile" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "检查完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步操作：" -ForegroundColor Yellow
Write-Host "1. 手动SSH连接到服务器: ssh $JenkinsUser@$JenkinsServer" -ForegroundColor White
Write-Host "2. 上传并执行安装脚本: install-jenkins.sh" -ForegroundColor White
Write-Host "3. 访问Jenkins: http://$JenkinsServer:8080" -ForegroundColor White
Write-Host "4. 配置部署: configure-jenkins-deploy.sh" -ForegroundColor White
Write-Host ""


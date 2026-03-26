# Jenkins自动化部署配置指南

## 服务器信息

- **Jenkins服务器**: 1.117.62.202 (ubuntu/Liu@bner1983)
- **部署目标服务器**: 43.143.139.197 (ubuntu)
- **项目仓库**: https://github.com/PMLiuyubin/enterprise-ai-platform.git

## 一、服务器检查

### 1.1 连接服务器

```bash
ssh ubuntu@1.117.62.202
# 密码: Liu@bner1983
```

### 1.2 检查系统信息

```bash
# 系统信息
uname -a
cat /etc/os-release

# 资源信息
free -h
nproc
df -h

# 已安装软件
dpkg -l | grep -E 'jenkins|docker|java|git'
docker --version
java -version
git --version
```

### 1.3 检查网络连接

```bash
# 测试连接到部署服务器
ping -c 3 43.143.139.197

# 检查公网IP
curl -s ifconfig.me

# 检查开放端口
ss -tuln | grep -E ':(8080|443|80|22)'
```

## 二、安装Jenkins

### 2.1 安装Java

```bash
sudo apt-get update
sudo apt-get install -y openjdk-17-jdk
java -version
```

### 2.2 安装Jenkins

```bash
# 添加Jenkins仓库密钥
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee /usr/share/keyrings/jenkins-keyring.asc > /dev/null

# 添加Jenkins仓库
echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/ | sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null

# 更新并安装
sudo apt-get update
sudo apt-get install -y jenkins
```

### 2.3 启动Jenkins

```bash
# 启动Jenkins服务
sudo systemctl start jenkins
sudo systemctl enable jenkins

# 检查状态
sudo systemctl status jenkins

# 查看初始密码
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

### 2.4 配置防火墙

```bash
# 开放8080端口
sudo ufw allow 8080
sudo ufw status
```

### 2.5 访问Jenkins

- 访问地址: `http://1.117.62.202:8080`
- 使用初始密码登录
- 安装推荐插件
- 创建管理员账户

## 三、配置SSH密钥

### 3.1 在Jenkins服务器上配置SSH密钥

```bash
# 创建.ssh目录
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 如果有部署密钥，复制到Jenkins用户
sudo mkdir -p /var/lib/jenkins/.ssh
sudo chown jenkins:jenkins /var/lib/jenkins/.ssh
sudo chmod 700 /var/lib/jenkins/.ssh

# 复制部署密钥（如果存在）
sudo cp ~/.ssh/deploy_key /var/lib/jenkins/.ssh/deploy_key
sudo chown jenkins:jenkins /var/lib/jenkins/.ssh/deploy_key
sudo chmod 600 /var/lib/jenkins/.ssh/deploy_key

# 或者生成新的SSH密钥
sudo -u jenkins ssh-keygen -t rsa -b 4096 -f /var/lib/jenkins/.ssh/id_rsa -N ""

# 将公钥添加到部署服务器
sudo -u jenkins cat /var/lib/jenkins/.ssh/id_rsa.pub | ssh ubuntu@43.143.139.197 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

### 3.2 测试SSH连接

```bash
# 以Jenkins用户身份测试
sudo -u jenkins ssh -o StrictHostKeyChecking=no ubuntu@43.143.139.197 "echo 'SSH连接成功'"
```

## 四、安装Jenkins插件

在Jenkins Web界面安装以下插件：

1. **SSH Pipeline Steps** - SSH操作支持
2. **SSH Agent Plugin** - SSH代理支持
3. **Git Plugin** - Git集成（通常已安装）
4. **Docker Pipeline Plugin** - Docker支持
5. **Credentials Binding Plugin** - 凭据绑定

安装步骤：
1. 进入 Jenkins → Manage Jenkins → Manage Plugins
2. 在 Available 标签页搜索插件
3. 勾选插件并点击 Install without restart
4. 等待安装完成

## 五、配置Jenkins凭据

### 5.1 添加SSH私钥凭据

1. 进入 Jenkins → Manage Jenkins → Manage Credentials
2. 点击 (global) → Add Credentials
3. 配置如下：
   - **Kind**: SSH Username with private key
   - **ID**: deploy-ssh-key
   - **Username**: ubuntu
   - **Private Key**: 选择 Enter directly，粘贴私钥内容
   - **Description**: 部署服务器SSH密钥

### 5.2 添加Git凭据（如果需要）

如果仓库是私有的，需要添加Git凭据：
- **Kind**: Username with password
- **Username**: GitHub用户名
- **Password**: GitHub Personal Access Token

## 六、创建Jenkins Pipeline

### 6.1 创建Pipeline任务

1. 进入 Jenkins → New Item
2. 输入任务名称：`enterprise-ai-platform-deploy`
3. 选择 Pipeline
4. 点击 OK

### 6.2 配置Pipeline

在 Pipeline 配置中，选择 **Pipeline script**，粘贴以下脚本：

```groovy
pipeline {
    agent any

    environment {
        DEPLOY_SERVER = '43.143.139.197'
        DEPLOY_USER = 'ubuntu'
        DEPLOY_KEY = credentials('deploy-ssh-key')
        PROJECT_DIR = '/opt/enterprise-ai-platform'
    }

    triggers {
        pollSCM('H/5 * * * *')  // 每5分钟检查一次代码变更
    }

    stages {
        stage('Checkout') {
            steps {
                echo '检出代码...'
                git branch: 'main',
                    url: 'https://github.com/PMLiuyubin/enterprise-ai-platform.git',
                    credentialsId: 'github-credentials'  // 如果仓库是私有的
            }
        }

        stage('Deploy to Server') {
            steps {
                script {
                    echo '部署到服务器...'
                    sshagent([DEPLOY_KEY]) {
                        sh '''
                            ssh -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_SERVER} << 'ENDSSH'
                                set -e
                                cd ${PROJECT_DIR}
                                echo "当前目录: $(pwd)"
                                echo "拉取最新代码..."
                                git fetch origin main
                                git reset --hard origin/main
                                echo "停止旧服务..."
                                docker compose down --timeout 30 || true
                                echo "构建新镜像..."
                                docker compose build --parallel
                                echo "启动服务..."
                                docker compose up -d
                                echo "等待服务启动..."
                                sleep 30
                                echo "检查服务状态..."
                                docker compose ps
                                echo "健康检查..."
                                curl -f http://localhost:8080/health || echo "健康检查失败"
                            ENDSSH
                        '''
                    }
                }
            }
        }

        stage('Health Check') {
            steps {
                script {
                    echo '执行健康检查...'
                    sh '''
                        sleep 10
                        curl -f http://43.143.139.197:8080/health || exit 1
                        echo "✅ 部署成功，服务健康"
                    '''
                }
            }
        }
    }

    post {
        success {
            echo '✅ 部署成功！'
            emailext (
                subject: "部署成功: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "部署到 ${DEPLOY_SERVER} 成功！",
                to: "your-email@example.com"
            )
        }
        failure {
            echo '❌ 部署失败！'
            emailext (
                subject: "部署失败: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "部署到 ${DEPLOY_SERVER} 失败，请检查日志。",
                to: "your-email@example.com"
            )
        }
        always {
            echo '清理工作空间...'
            cleanWs()
        }
    }
}
```

### 6.3 保存并运行

1. 点击 Save
2. 点击 Build Now 测试部署
3. 查看 Console Output 确认部署过程

## 七、配置自动触发

### 7.1 基于GitHub Webhook的自动触发

1. 在GitHub仓库设置中添加Webhook：
   - URL: `http://1.117.62.202:8080/github-webhook/`
   - Content type: application/json
   - Events: Just the push event

2. 在Jenkins Pipeline配置中启用GitHub hook trigger

### 7.2 基于定时检查的自动触发

在Pipeline脚本中已配置 `pollSCM`，每5分钟检查一次代码变更。

## 八、监控和维护

### 8.1 查看部署日志

```bash
# 在Jenkins服务器上查看Jenkins日志
sudo tail -f /var/log/jenkins/jenkins.log

# 在部署服务器上查看服务日志
ssh ubuntu@43.143.139.197
cd /opt/enterprise-ai-platform
docker compose logs -f
```

### 8.2 备份Jenkins配置

```bash
# 备份Jenkins配置
sudo tar -czf jenkins-backup-$(date +%Y%m%d).tar.gz /var/lib/jenkins
```

### 8.3 更新Jenkins

```bash
sudo apt-get update
sudo apt-get upgrade jenkins
sudo systemctl restart jenkins
```

## 九、故障排查

### 9.1 Jenkins无法启动

```bash
# 检查Jenkins状态
sudo systemctl status jenkins

# 查看日志
sudo journalctl -u jenkins -n 50

# 检查端口占用
sudo netstat -tuln | grep 8080
```

### 9.2 SSH连接失败

```bash
# 测试SSH连接
sudo -u jenkins ssh -v ubuntu@43.143.139.197

# 检查SSH密钥权限
ls -la /var/lib/jenkins/.ssh/
```

### 9.3 部署失败

1. 检查Jenkins构建日志
2. 检查部署服务器上的服务状态
3. 检查Docker容器日志
4. 检查网络连接

## 十、安全建议

1. **更改默认端口**（可选）：
   ```bash
   sudo nano /etc/default/jenkins
   # 修改 HTTP_PORT=8080 为其他端口
   sudo systemctl restart jenkins
   ```

2. **配置HTTPS**（推荐）：
   - 使用Nginx反向代理
   - 配置SSL证书

3. **限制访问**：
   - 配置防火墙规则
   - 使用VPN或IP白名单

4. **定期更新**：
   - 保持Jenkins和插件最新版本
   - 定期检查安全公告

## 总结

完成以上配置后，Jenkins将能够：
- ✅ 自动检测代码变更
- ✅ 自动部署到目标服务器
- ✅ 执行健康检查
- ✅ 发送通知（如果配置了邮件）

访问Jenkins: `http://1.117.62.202:8080`



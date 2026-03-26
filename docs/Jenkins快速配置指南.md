# Jenkins快速配置指南

## 当前状态

✅ **Jenkins已安装并运行**
- 访问地址: `http://1.117.62.202:8080`
- 初始密码: `7915873e43a545f78e6bc38fe1bb0cbb`

✅ **应用服务器连接成功**
- 服务器: 43.143.139.197
- SSH密钥已配置

⚠️ **图数据库服务器连接失败**
- 服务器: 43.143.90.179
- 需要配置SSH密钥或使用不同的认证方式

## 快速配置步骤

### 1. 访问Jenkins并完成初始设置

1. 打开浏览器访问: `http://1.117.62.202:8080`
2. 输入初始密码: `7915873e43a545f78e6bc38fe1bb0cbb`
3. 选择 "Install suggested plugins"
4. 等待插件安装完成
5. 创建管理员账户

### 2. 配置SSH凭据

1. 进入: **Manage Jenkins** → **Manage Credentials**
2. 点击 **(global)** → **Add Credentials**
3. 配置:
   - **Kind**: SSH Username with private key
   - **ID**: `deploy-ssh-key`
   - **Username**: `ubuntu`
   - **Private Key**: 选择 **Enter directly**
   - 粘贴 `enterprise_ai_platform.pem` 文件内容
   - **Description**: 部署服务器SSH密钥
4. 点击 **OK**

### 3. 创建Pipeline任务

1. 点击 **New Item**
2. 输入任务名称: `enterprise-ai-platform-deploy`
3. 选择 **Pipeline**
4. 点击 **OK**

### 4. 配置Pipeline

在Pipeline配置页面：

**方式1: 使用Pipeline script from SCM（推荐）**

1. **Pipeline** 标签：
   - **Definition**: Pipeline script from SCM
   - **SCM**: Git
   - **Repository URL**: `https://github.com/PMLiuyubin/enterprise-ai-platform.git`
   - **Branches to build**: `*/main`
   - **Script Path**: `Jenkinsfile`

2. 点击 **Save**

**方式2: 直接使用Pipeline脚本**

1. **Pipeline** 标签：
   - **Definition**: Pipeline script
   - 将 `Jenkinsfile` 的内容粘贴到脚本框中

2. 点击 **Save**

### 5. 测试部署

1. 进入任务页面
2. 点击 **Build Now**
3. 查看构建日志

## 图数据库服务器配置（可选）

如果需要在图数据库服务器上部署，需要：

1. **获取图数据库服务器的SSH密钥**
   - 确认是否有单独的密钥文件
   - 或者使用密码认证

2. **在Jenkins中配置图数据库服务器凭据**
   - 添加新的SSH凭据（ID: `graph-deploy-key`）

3. **更新Pipeline环境变量**
   - 在Pipeline配置中添加: `GRAPH_DEPLOY_KEY = credentials('graph-deploy-key')`

## Pipeline功能说明

当前Pipeline包含以下阶段：

1. **Checkout**: 从GitHub拉取最新代码
2. **Deploy to App Server**: 部署到应用服务器 43.143.139.197
3. **Deploy to Graph Server**: 部署到图数据库服务器 43.143.90.179（如果配置了密钥）
4. **Health Check**: 并行检查两个服务器的健康状态

## 自动触发

Pipeline配置了 `pollSCM`，每5分钟检查一次代码变更，自动触发部署。

## 访问地址

- **Jenkins**: http://1.117.62.202:8080
- **应用服务器**: http://43.143.139.197:8080
- **图数据库服务器**: http://43.143.90.179:8080（如果服务运行）

## 故障排查

### Jenkins无法访问

1. 检查防火墙: `sudo ufw status`
2. 检查Jenkins服务: `sudo systemctl status jenkins`
3. 查看日志: `sudo journalctl -u jenkins -n 50`

### 部署失败

1. 查看Jenkins构建日志
2. 检查SSH连接: `sudo -u jenkins ssh -i /var/lib/jenkins/.ssh/deploy_key ubuntu@43.143.139.197`
3. 检查服务器上的Docker服务

### 图数据库服务器连接失败

1. 确认是否有正确的SSH密钥
2. 检查服务器是否允许SSH连接
3. 确认用户名是否正确（可能是 `root` 或其他用户）

## 下一步

完成以上配置后，每次推送到 `main` 分支，Jenkins将自动：
- 拉取最新代码
- 部署到应用服务器
- 执行健康检查
- 发送通知（如果配置了）



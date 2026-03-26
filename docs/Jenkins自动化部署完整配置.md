# Jenkins自动化部署完整配置指南

## 部署架构

- **Jenkins服务器**: 1.117.62.202
- **应用服务器**: 43.143.139.197
- **图数据库服务器**: 43.143.90.179

## 一、Jenkins安装状态

Jenkins已安装并运行，访问地址：`http://1.117.62.202:8080`

获取初始密码：
```bash
ssh -i Jenkins.pem ubuntu@1.117.62.202
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

## 二、Jenkins Web界面配置

### 2.1 首次登录

1. 访问 `http://1.117.62.202:8080`
2. 输入初始管理员密码
3. 选择"安装推荐的插件"
4. 等待插件安装完成
5. 创建管理员账户

### 2.2 安装必要插件

进入：**Manage Jenkins** → **Manage Plugins** → **Available**

安装以下插件：
- ✅ **SSH Pipeline Steps** - SSH操作支持
- ✅ **SSH Agent Plugin** - SSH代理支持
- ✅ **Git Plugin** - Git集成（通常已安装）
- ✅ **Docker Pipeline Plugin** - Docker支持
- ✅ **Credentials Binding Plugin** - 凭据绑定
- ✅ **Pipeline** - Pipeline支持（通常已安装）

### 2.3 配置SSH凭据

1. 进入：**Manage Jenkins** → **Manage Credentials**
2. 点击 **(global)** → **Add Credentials**
3. 配置SSH私钥凭据：
   - **Kind**: SSH Username with private key
   - **ID**: `deploy-ssh-key`
   - **Username**: `ubuntu`
   - **Private Key**: 选择 **Enter directly**
   - 粘贴 `enterprise_ai_platform.pem` 的内容
   - **Description**: 部署服务器SSH密钥
4. 点击 **OK** 保存

## 三、创建Pipeline任务

### 3.1 创建任务

1. 进入Jenkins首页
2. 点击 **New Item**
3. 输入任务名称：`enterprise-ai-platform-deploy`
4. 选择 **Pipeline**
5. 点击 **OK**

### 3.2 配置Pipeline

在Pipeline配置页面：

1. **General** 标签：
   - ✅ 勾选 **GitHub project**（可选）
   - Project url: `https://github.com/PMLiuyubin/enterprise-ai-platform`

2. **Pipeline** 标签：
   - **Definition**: Pipeline script from SCM
   - **SCM**: Git
   - **Repository URL**: `https://github.com/PMLiuyubin/enterprise-ai-platform.git`
   - **Credentials**: 如果仓库是私有的，选择Git凭据
   - **Branches to build**: `*/main`
   - **Script Path**: `Jenkinsfile`

3. 或者直接使用Pipeline脚本：
   - **Definition**: Pipeline script
   - 将 `Jenkinsfile` 的内容粘贴到脚本框中

4. 点击 **Save**

### 3.3 Pipeline脚本说明

Pipeline脚本 (`Jenkinsfile`) 包含以下阶段：

1. **Checkout**: 从GitHub拉取最新代码
2. **Deploy to App Server**: 部署到应用服务器 43.143.139.197
3. **Deploy to Graph Server**: 部署到图数据库服务器 43.143.90.179
4. **Health Check**: 并行检查两个服务器的健康状态

## 四、部署流程

### 4.1 自动触发

Pipeline配置了 `pollSCM`，每5分钟检查一次代码变更，如果有新提交会自动触发部署。

### 4.2 手动触发

1. 进入任务页面
2. 点击 **Build Now**
3. 查看构建进度和日志

### 4.3 部署过程

部署过程包括：
1. 拉取最新代码
2. 停止旧服务
3. 构建Docker镜像
4. 启动新服务
5. 健康检查

## 五、服务器配置

### 5.1 应用服务器 (43.143.139.197)

- **项目目录**: `/opt/enterprise-ai-platform`
- **部署方式**: Docker Compose
- **健康检查**: `http://43.143.139.197:8080/health`

### 5.2 图数据库服务器 (43.143.90.179)

- **项目目录**: `/opt/enterprise-ai-platform`
- **部署方式**: Docker Compose
- **健康检查**: `http://43.143.90.179:8080/health`（如果服务运行）

## 六、SSH密钥配置

### 6.1 Jenkins服务器上的密钥

部署密钥已配置在：
- `/var/lib/jenkins/.ssh/deploy_key`
- 权限：`jenkins:jenkins`，`600`

### 6.2 测试SSH连接

在Jenkins服务器上测试连接：
```bash
sudo -u jenkins ssh -i /var/lib/jenkins/.ssh/deploy_key ubuntu@43.143.139.197 "echo '应用服务器连接成功'"
sudo -u jenkins ssh -i /var/lib/jenkins/.ssh/deploy_key ubuntu@43.143.90.179 "echo '图数据库服务器连接成功'"
```

## 七、GitHub Webhook配置（可选）

### 7.1 在GitHub仓库中配置

1. 进入仓库：`https://github.com/PMLiuyubin/enterprise-ai-platform`
2. 进入 **Settings** → **Webhooks**
3. 点击 **Add webhook**
4. 配置：
   - **Payload URL**: `http://1.117.62.202:8080/github-webhook/`
   - **Content type**: `application/json`
   - **Events**: 选择 **Just the push event**
5. 点击 **Add webhook**

### 7.2 在Jenkins中启用

1. 进入Pipeline任务配置
2. 在 **Build Triggers** 中勾选 **GitHub hook trigger for GITScm polling**
3. 保存

## 八、监控和维护

### 8.1 查看构建历史

- 进入任务页面
- 查看左侧的 **Build History**
- 点击构建号查看详细日志

### 8.2 查看服务器日志

**应用服务器**:
```bash
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197
cd /opt/enterprise-ai-platform
docker compose logs -f
```

**图数据库服务器**:
```bash
ssh -i enterprise_ai_platform.pem ubuntu@43.143.90.179
cd /opt/enterprise-ai-platform
docker compose logs -f
```

### 8.3 备份Jenkins配置

```bash
ssh -i Jenkins.pem ubuntu@1.117.62.202
sudo tar -czf jenkins-backup-$(date +%Y%m%d).tar.gz /var/lib/jenkins
```

## 九、故障排查

### 9.1 部署失败

1. 查看Jenkins构建日志
2. 检查SSH连接是否正常
3. 检查服务器上的Docker服务状态
4. 检查磁盘空间是否充足

### 9.2 SSH连接失败

1. 检查密钥权限
2. 测试SSH连接
3. 检查服务器防火墙设置

### 9.3 健康检查失败

1. 检查服务是否正常启动
2. 检查端口是否正确
3. 查看服务日志

## 十、优化建议

1. **内存管理**: Jenkins服务器只有1.6GB内存，建议：
   - 限制并发构建数量
   - 定期清理构建历史
   - 关闭不必要的插件

2. **构建优化**:
   - 使用Docker缓存加速构建
   - 只构建变更的服务
   - 使用并行部署

3. **监控告警**:
   - 配置邮件通知
   - 集成监控系统
   - 设置构建失败告警

## 总结

完成以上配置后，Jenkins将能够：
- ✅ 自动检测代码变更
- ✅ 自动部署到应用服务器
- ✅ 自动部署到图数据库服务器
- ✅ 执行健康检查
- ✅ 发送通知（如果配置了）

访问Jenkins: `http://1.117.62.202:8080`



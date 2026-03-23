# Jenkins同步问题排查

**问题**: Jenkins没有自动同步代码到服务器

## 问题分析

### 发现的问题

1. **✅ Jenkins服务正常运行**
   - 服务状态: active (running)
   - 构建历史: 有构建记录（#3, #4, #5）

2. **✅ Jenkins可以访问GitHub**
   - 网络连接正常
   - 可以访问GitHub仓库

3. **❌ SSH连接失败（主要问题）**
   - 错误: `Permission denied (publickey,password)`
   - Jenkins无法SSH连接到部署服务器 `43.143.139.197`

4. **✅ SSH密钥文件存在**
   - `/var/lib/jenkins/.ssh/deploy_key` 存在
   - 权限正确 (600)

## 根本原因

**Jenkins的SSH密钥没有添加到部署服务器的authorized_keys**

Jenkins需要能够SSH连接到部署服务器来执行部署命令，但当前配置中：
- Jenkins有SSH私钥 (`deploy_key`)
- 但部署服务器上没有对应的公钥在 `authorized_keys` 中

## 解决方案

### 方案1: 添加Jenkins公钥到部署服务器（推荐）

#### 步骤1: 从Jenkins私钥生成公钥

在Jenkins服务器上执行：
```bash
sudo -u jenkins ssh-keygen -y -f /var/lib/jenkins/.ssh/deploy_key
```

这会输出公钥内容，类似：
```
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ...
```

#### 步骤2: 将公钥添加到部署服务器

在部署服务器上执行：
```bash
# 备份现有authorized_keys
cp ~/.ssh/authorized_keys ~/.ssh/authorized_keys.backup

# 添加Jenkins公钥
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ..." >> ~/.ssh/authorized_keys

# 设置正确权限
chmod 600 ~/.ssh/authorized_keys
```

#### 步骤3: 测试SSH连接

在Jenkins服务器上测试：
```bash
sudo -u jenkins ssh -i /var/lib/jenkins/.ssh/deploy_key -o StrictHostKeyChecking=no ubuntu@43.143.139.197 "echo 'SSH连接成功'"
```

### 方案2: 使用现有的部署密钥

如果 `enterprise_ai_platform.pem` 是部署服务器的SSH密钥：

#### 步骤1: 复制密钥到Jenkins

```bash
# 在Jenkins服务器上
sudo cp /path/to/enterprise_ai_platform.pem /var/lib/jenkins/.ssh/deploy_key
sudo chown jenkins:jenkins /var/lib/jenkins/.ssh/deploy_key
sudo chmod 600 /var/lib/jenkins/.ssh/deploy_key
```

#### 步骤2: 测试连接

```bash
sudo -u jenkins ssh -i /var/lib/jenkins/.ssh/deploy_key ubuntu@43.143.139.197 "echo '连接成功'"
```

### 方案3: 配置Jenkins凭据（如果使用Jenkins凭据系统）

如果Jenkins配置中使用的是凭据ID `deploy-ssh-key`：

1. 进入Jenkins: **Manage Jenkins** → **Manage Credentials**
2. 找到 `deploy-ssh-key` 凭据
3. 确保私钥内容正确
4. 确保对应的公钥已添加到部署服务器

## 验证步骤

### 1. 验证SSH连接

```bash
# 在Jenkins服务器上
sudo -u jenkins ssh -i /var/lib/jenkins/.ssh/deploy_key ubuntu@43.143.139.197 "echo '连接成功'"
```

### 2. 验证Jenkins构建

1. 进入Jenkins: http://1.117.62.202:8080
2. 找到Pipeline任务: `enterprise-ai-platform-deploy`
3. 点击 **"立即构建"** (Build Now)
4. 查看构建日志，确认SSH连接成功

### 3. 验证代码同步

构建成功后，检查部署服务器上的代码：
```bash
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197
cd /opt/enterprise-ai-platform
git log --oneline -3
```

应该看到最新的提交。

## 其他可能的问题

### 1. Jenkins凭据配置错误

检查Jenkins中的SSH凭据配置：
- 凭据ID是否正确: `deploy-ssh-key`
- 私钥内容是否正确
- 用户名是否正确: `ubuntu`

### 2. pollSCM未触发

如果Jenkins没有自动触发构建：
- 检查 `pollSCM('H/5 * * * *')` 配置
- 手动触发一次构建测试
- 配置GitHub Webhook实现实时触发

### 3. Git凭据问题

如果Git拉取失败：
- 检查 `github-credentials` 凭据配置
- 确保GitHub Personal Access Token有效
- 或者使用SSH方式拉取代码

## 快速修复脚本

创建一个修复脚本 `fix-jenkins-ssh.sh`:

```bash
#!/bin/bash
# 修复Jenkins SSH连接

echo "=== 步骤1: 生成Jenkins公钥 ==="
JENKINS_PUBKEY=$(sudo -u jenkins ssh-keygen -y -f /var/lib/jenkins/.ssh/deploy_key)
echo "Jenkins公钥:"
echo "$JENKINS_PUBKEY"
echo ""

echo "=== 步骤2: 添加到部署服务器 ==="
echo "请手动执行以下命令在部署服务器上:"
echo "echo '$JENKINS_PUBKEY' >> ~/.ssh/authorized_keys"
echo "chmod 600 ~/.ssh/authorized_keys"
echo ""

echo "=== 步骤3: 测试连接 ==="
sudo -u jenkins ssh -i /var/lib/jenkins/.ssh/deploy_key -o StrictHostKeyChecking=no ubuntu@43.143.139.197 "echo 'SSH连接成功'" || echo "SSH连接失败，请检查公钥是否已添加"
```

## 总结

**主要问题**: Jenkins无法SSH连接到部署服务器

**解决方案**:
1. 从Jenkins私钥生成公钥
2. 将公钥添加到部署服务器的 `authorized_keys`
3. 测试SSH连接
4. 手动触发Jenkins构建验证

**验证**: 构建成功后，代码会自动同步到部署服务器。



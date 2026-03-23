# 手动安装 GitHub Actions 自托管 Runner 指南

## 📥 下载地址

### GitHub Actions Runner 下载

**最新版本（推荐）**：
```
https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
```

**其他版本**：
- 查看所有版本：https://github.com/actions/runner/releases
- 选择最新的 `actions-runner-linux-x64-*.tar.gz` 文件

## 🚀 安装步骤

### 步骤1: 下载 Runner

**方法A: 在本地下载后上传到服务器**

1. 在浏览器中打开下载地址：
   ```
   https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
   ```

2. 下载文件到本地（例如：`E:\enterprise-ai-platform\`）

3. 上传到服务器：
   ```powershell
   $SSH_KEY = ".\enterprise_ai_platform.pem"
   $SERVER = "ubuntu@43.143.139.197"
   scp -i $SSH_KEY actions-runner-linux-x64-2.311.0.tar.gz ${SERVER}:/opt/actions-runner/
   ```

**方法B: 在服务器上直接下载**

```bash
# SSH 到服务器
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197

# 创建目录
sudo mkdir -p /opt/actions-runner
sudo chown ubuntu:ubuntu /opt/actions-runner
cd /opt/actions-runner

# 下载（使用 wget 或 curl）
wget https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# 或者使用 curl
curl -L -o actions-runner-linux-x64-2.311.0.tar.gz \
  https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
```

### 步骤2: 解压安装包

```bash
cd /opt/actions-runner
tar xzf actions-runner-linux-x64-2.311.0.tar.gz
sudo chown -R ubuntu:ubuntu /opt/actions-runner
```

### 步骤3: 获取配置 Token

1. **访问 GitHub 仓库设置**：
   ```
   https://github.com/PMLiuyubin/enterprise-ai-platform/settings/actions/runners/new
   ```

2. **选择配置**：
   - 操作系统：**Linux**
   - 架构：**x64**

3. **复制配置命令**：
   页面会显示类似这样的命令：
   ```bash
   ./config.sh --url https://github.com/PMLiuyubin/enterprise-ai-platform --token AXXXXXXXXXXXXXXXXXXXXX
   ```

   复制整个命令，或者只复制 token 部分（`AXXXXXXXXXXXXXXXXXXXXX`）

### 步骤4: 配置 Runner

在服务器上执行配置命令：

```bash
cd /opt/actions-runner

# 使用从 GitHub 复制的完整命令，或者：
./config.sh --url https://github.com/PMLiuyubin/enterprise-ai-platform --token YOUR_TOKEN_HERE

# 配置选项：
# - Runner name: 输入名称（如：server-production）或直接回车使用默认名称
# - Work folder: 直接回车使用默认值
# - Labels: 直接回车（可选，用于区分不同 Runner）
```

### 步骤5: 安装为系统服务

```bash
cd /opt/actions-runner

# 安装为系统服务（使用 ubuntu 用户）
sudo ./svc.sh install ubuntu

# 启动服务
sudo ./svc.sh start

# 检查状态
sudo ./svc.sh status
```

### 步骤6: 验证安装

1. **在服务器上检查**：
   ```bash
   sudo systemctl status actions.runner.*
   ```

2. **在 GitHub 上检查**：
   - 访问：`https://github.com/PMLiuyubin/enterprise-ai-platform/settings/actions/runners`
   - 应该看到 Runner 显示为 **"Online"**（绿色圆点）

## 📋 完整安装命令（一键执行）

将以下命令保存为脚本，替换 `YOUR_TOKEN_HERE` 为实际 token：

```bash
#!/bin/bash
set -e

RUNNER_VERSION="2.311.0"
REPO_URL="https://github.com/PMLiuyubin/enterprise-ai-platform"
RUNNER_TOKEN="YOUR_TOKEN_HERE"  # 替换为从 GitHub 获取的 token

# 创建目录
sudo mkdir -p /opt/actions-runner
sudo chown ubuntu:ubuntu /opt/actions-runner
cd /opt/actions-runner

# 下载 Runner
echo "下载 Runner..."
wget https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# 解压
echo "解压安装包..."
tar xzf actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz
sudo chown -R ubuntu:ubuntu /opt/actions-runner

# 配置
echo "配置 Runner..."
./config.sh --url ${REPO_URL} --token ${RUNNER_TOKEN} --name "server-$(hostname)" --work "_work" --replace

# 安装服务
echo "安装为系统服务..."
sudo ./svc.sh install ubuntu
sudo ./svc.sh start

echo "✅ 安装完成！"
sudo ./svc.sh status
```

## 🔧 服务管理命令

```bash
cd /opt/actions-runner

# 启动服务
sudo ./svc.sh start

# 停止服务
sudo ./svc.sh stop

# 重启服务
sudo ./svc.sh restart

# 查看状态
sudo ./svc.sh status

# 查看日志
sudo journalctl -u actions.runner.* -f

# 卸载服务
sudo ./svc.sh uninstall
```

## 📝 使用自托管 Runner

安装完成后，工作流文件 `.github/workflows/deploy-self-hosted.yml` 会自动使用自托管 Runner。

提交工作流文件：
```powershell
git add .github/workflows/deploy-self-hosted.yml
git commit -m "添加自托管 Runner 部署工作流"
git push origin main
```

## ✅ 验证清单

- [ ] Runner 文件已下载
- [ ] 文件已解压到 `/opt/actions-runner`
- [ ] 已从 GitHub 获取配置 Token
- [ ] Runner 已配置成功
- [ ] 服务已安装并启动
- [ ] 在 GitHub 上看到 Runner 为 "Online" 状态
- [ ] 工作流文件已提交

## 🎯 下一步

1. 测试工作流：在 GitHub Actions 页面手动触发 `deploy-self-hosted.yml`
2. 推送代码：推送代码到 main 分支，自动使用自托管 Runner 部署
3. 监控状态：定期检查 Runner 状态和日志



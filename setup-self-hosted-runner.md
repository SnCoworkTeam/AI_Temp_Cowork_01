# GitHub Actions 自托管 Runner 设置指南

## 📋 概述

自托管 Runner 是在您自己的服务器上运行的 GitHub Actions Runner，**完全免费**，无时间限制。

## ✅ 优势

- ✅ **完全免费** - 不消耗 GitHub Actions 分钟数
- ✅ **无时间限制** - 可以运行任意长时间
- ✅ **更快部署** - 直接在服务器上运行，无需 SSH
- ✅ **更多控制** - 可以访问服务器资源
- ✅ **安全性** - 代码在您的服务器上运行

## 🚀 快速设置步骤

### 步骤1: 获取 Runner 配置 Token

1. 进入 GitHub 仓库设置：
   ```
   https://github.com/PMLiuyubin/enterprise-ai-platform/settings/actions/runners/new
   ```

2. 选择操作系统：**Linux**
3. 选择架构：**x64**
4. 复制显示的配置命令（类似这样）：
   ```bash
   ./config.sh --url https://github.com/PMLiuyubin/enterprise-ai-platform --token AXXXXXXXXXXXXXXXXXXXXX
   ```

### 步骤2: 在服务器上安装 Runner

#### 方法A: 使用自动安装脚本（推荐）

已创建自动安装脚本，可以直接使用：

```bash
# 在服务器上执行
cd /opt
curl -o setup-runner.sh https://raw.githubusercontent.com/PMLiuyubin/enterprise-ai-platform/main/scripts/setup-self-hosted-runner.sh
chmod +x setup-runner.sh
./setup-runner.sh
```

#### 方法B: 手动安装

```bash
# 1. SSH 到服务器
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197

# 2. 创建 Runner 目录
cd /opt
sudo mkdir -p actions-runner
sudo chown ubuntu:ubuntu actions-runner
cd actions-runner

# 3. 下载 Runner（使用最新版本）
RUNNER_VERSION="2.311.0"
curl -o actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz \
  -L https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# 4. 解压
tar xzf ./actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# 5. 配置 Runner（使用从 GitHub 获取的 token）
./config.sh --url https://github.com/PMLiuyubin/enterprise-ai-platform --token YOUR_TOKEN_HERE

# 6. 安装为系统服务（自动启动）
sudo ./svc.sh install
sudo ./svc.sh start

# 7. 检查状态
sudo ./svc.sh status
```

### 步骤3: 验证 Runner 状态

1. **在服务器上检查**：
   ```bash
   sudo systemctl status actions.runner.*
   ```

2. **在 GitHub 上检查**：
   - 访问：`https://github.com/PMLiuyubin/enterprise-ai-platform/settings/actions/runners`
   - 应该看到 Runner 显示为 "Online"（绿色）

### 步骤4: 修改工作流使用自托管 Runner

已创建使用自托管 Runner 的工作流文件。

## 📝 详细配置说明

### Runner 目录结构

```
/opt/actions-runner/
├── actions-runner-linux-x64-2.311.0.tar.gz  # 下载的包
├── bin/                                      # 可执行文件
├── externals/                                # 依赖
├── _diag/                                    # 诊断日志
├── .runner                                   # 配置信息
└── .credentials                              # 凭据
```

### Runner 服务管理

```bash
# 启动服务
sudo ./svc.sh start

# 停止服务
sudo ./svc.sh stop

# 重启服务
sudo ./svc.sh restart

# 查看状态
sudo ./svc.sh status

# 卸载服务
sudo ./svc.sh uninstall
```

### Runner 日志位置

```bash
# 服务日志
sudo journalctl -u actions.runner.* -f

# Runner 诊断日志
tail -f /opt/actions-runner/_diag/Runner_*.log
```

## 🔧 故障排查

### 问题1: Runner 显示为 Offline

**检查服务状态**：
```bash
sudo systemctl status actions.runner.*
```

**重启服务**：
```bash
cd /opt/actions-runner
sudo ./svc.sh restart
```

### 问题2: Runner 无法连接到 GitHub

**检查网络连接**：
```bash
curl -I https://github.com
```

**检查防火墙**：
```bash
sudo ufw status
# 如果需要，允许出站连接
sudo ufw allow out 443
```

### 问题3: Runner 权限问题

**确保 Runner 有足够权限**：
```bash
# 检查用户
whoami

# 确保在 docker 组中
sudo usermod -aG docker $USER

# 确保可以访问项目目录
ls -la /opt/enterprise-ai-platform
```

## 🔒 安全建议

1. **限制 Runner 标签**：
   - 只允许特定工作流使用
   - 使用标签区分不同环境

2. **定期更新 Runner**：
   ```bash
   cd /opt/actions-runner
   ./run.sh --update
   ```

3. **监控 Runner 活动**：
   - 定期检查日志
   - 监控资源使用

4. **使用专用用户**：
   ```bash
   # 创建专用用户
   sudo useradd -m -s /bin/bash github-runner
   sudo usermod -aG docker github-runner
   ```

## 📊 资源要求

- **CPU**: 2 核心（推荐）
- **内存**: 4GB（推荐）
- **磁盘**: 10GB 可用空间
- **网络**: 稳定的互联网连接

## 🎯 下一步

设置完成后：
1. 修改工作流使用 `runs-on: self-hosted`
2. 测试工作流
3. 监控 Runner 状态


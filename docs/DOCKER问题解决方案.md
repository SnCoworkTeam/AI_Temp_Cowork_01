# Docker API版本错误解决方案

## 问题诊断

当前问题：Docker Desktop 服务未正常运行，导致无法连接到 Docker 守护进程。

**错误信息：**
```
request returned Internal Server Error for API route and version 
http://%2F%2F.%2Fpipe%2FdockerDesktopLinuxEngine/v1.46/containers/json
check if the server supports the requested API version
```

## 解决方案

### 方案1：重启 Docker Desktop（推荐，最简单）

1. **完全退出 Docker Desktop：**
   - 右键点击系统托盘中的 Docker Desktop 图标
   - 选择 "Quit Docker Desktop"（退出 Docker Desktop）
   - 等待 10-15 秒确保完全退出

2. **重新启动 Docker Desktop：**
   - 从开始菜单启动 Docker Desktop
   - **重要：** 等待 Docker Desktop 完全启动
   - 系统托盘图标应该变成绿色（表示已就绪）
   - 这通常需要 1-2 分钟

3. **验证是否修复：**
   ```powershell
   docker ps
   ```

### 方案2：设置 Docker API 版本（临时解决）

如果重启后仍有问题，设置兼容的 API 版本：

**PowerShell（当前会话）：**
```powershell
$env:DOCKER_API_VERSION = "1.40"
docker ps
```

**永久设置（添加到 PowerShell 配置文件）：**
```powershell
# 打开配置文件
notepad $PROFILE

# 添加这一行：
$env:DOCKER_API_VERSION = "1.40"
```

**系统环境变量（推荐）：**
1. 按 `Win + R`，输入 `sysdm.cpl`，回车
2. 点击"高级"选项卡 → "环境变量"
3. 在"系统变量"中点击"新建"
4. 变量名：`DOCKER_API_VERSION`
5. 变量值：`1.40`
6. 确定并重启 PowerShell

### 方案3：使用修复脚本

运行提供的 PowerShell 脚本：
```powershell
.\fix-docker-api-version.ps1
```

### 方案4：检查并启动 Docker 服务（需要管理员权限）

1. **以管理员身份运行 PowerShell：**
   - 右键点击 PowerShell
   - 选择"以管理员身份运行"

2. **启动 Docker 服务：**
   ```powershell
   Start-Service -Name "com.docker.service"
   ```

3. **检查服务状态：**
   ```powershell
   Get-Service -Name "com.docker.service"
   ```

### 方案5：更新 Docker Desktop

如果以上方法都不行，可能需要更新 Docker Desktop：

1. 打开 Docker Desktop
2. 点击设置（齿轮图标）
3. 检查更新或下载最新版本
4. 从官网下载：https://www.docker.com/products/docker-desktop

## 快速诊断命令

运行以下命令检查 Docker 状态：

```powershell
# 检查 Docker Desktop 进程
Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue

# 检查 Docker 服务状态
Get-Service | Where-Object {$_.Name -like "*docker*"}

# 检查 Docker 上下文
docker context ls

# 测试 Docker 连接
docker version
docker ps
```

## 常见问题

### Q: 为什么会出现这个错误？
A: 通常是因为：
- Docker Desktop 没有完全启动
- Docker 守护进程服务未运行
- Docker 客户端版本与守护进程版本不兼容

### Q: 设置 API 版本后仍然报错？
A: 如果设置了 API 版本仍然报错，说明问题不是版本兼容性，而是 Docker Desktop 本身没有正常运行。请按照方案1重启 Docker Desktop。

### Q: 如何知道 Docker Desktop 是否完全启动？
A: 查看系统托盘图标：
- 🟢 绿色 = 已就绪，可以使用
- 🟡 黄色 = 正在启动，请等待
- ⚪ 灰色/白色 = 未运行

### Q: 重启后还是不行？
A: 尝试：
1. 重启电脑
2. 检查 Windows 更新
3. 检查是否有杀毒软件阻止 Docker
4. 查看 Docker Desktop 的日志（设置 → 故障排除 → 查看日志）

## 验证修复

修复后，运行以下命令验证：

```powershell
# 应该能正常显示容器列表（可能为空）
docker ps

# 应该能显示客户端和服务器版本
docker version

# 应该能显示 Docker 信息
docker info
```

如果这些命令都能正常执行，说明问题已解决！




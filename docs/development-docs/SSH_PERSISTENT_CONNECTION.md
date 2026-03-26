# SSH持久化连接使用指南

## 概述

SSH持久化连接管理器使用SSH的ControlMaster功能，实现连接复用和持久化，避免每次执行命令都需要重新登录。

## 功能特性

- ✅ **连接复用**: 使用ControlMaster复用SSH连接，减少登录次数
- ✅ **自动重连**: 连接断开后自动重新建立
- ✅ **交互式对话框**: 提供友好的菜单界面
- ✅ **连接状态监控**: 实时查看连接状态
- ✅ **后台连接**: 主连接在后台保持，不影响其他操作

## 快速开始

### 方法1: 使用交互式对话框（推荐）

双击运行 `ssh-connect-persistent.bat` 或在PowerShell中运行：

```powershell
.\ssh-connect-persistent.ps1
```

这将打开一个交互式菜单，提供以下选项：

1. **建立持久连接** - 建立ControlMaster连接
2. **执行命令** - 在远程服务器执行单个命令
3. **交互式Shell** - 打开交互式SSH会话
4. **查看状态** - 查看当前连接状态
5. **断开连接** - 断开ControlMaster连接
6. **退出** - 退出程序并断开连接

### 方法2: 命令行方式

```powershell
# 建立连接
.\scripts\deployment\ssh-persistent.ps1 -Action connect

# 执行命令
.\scripts\deployment\ssh-persistent.ps1 -Action execute -Command "ls -la"

# 查看状态
.\scripts\deployment\ssh-persistent.ps1 -Action status

# 断开连接
.\scripts\deployment\ssh-persistent.ps1 -Action disconnect
```

## 工作原理

### ControlMaster机制

SSH ControlMaster允许复用单个SSH连接来执行多个命令：

1. **主连接**: 第一个连接作为"主连接"（master），在后台保持
2. **复用连接**: 后续连接作为"从连接"（slave），复用主连接
3. **自动管理**: 主连接空闲10分钟后自动关闭（可配置）

### 连接文件

ControlMaster连接信息存储在：
```
~/.ssh/control-ubuntu@43.143.139.197:22
```

## 配置说明

### remote.ssh 配置

已添加以下配置到 `remote.ssh`：

```
ControlMaster auto          # 自动启用ControlMaster
ControlPath ~/.ssh/control-%r@%h:%p  # 控制文件路径
ControlPersist 10m          # 连接保持10分钟
```

### 自定义配置

如需修改连接保持时间，编辑 `remote.ssh`：

```
ControlPersist 30m  # 改为30分钟
```

## 使用场景

### 场景1: 频繁执行命令

**之前**（每次都要登录）:
```powershell
ssh -F remote.ssh enterprise-ai-server "ls"
ssh -F remote.ssh enterprise-ai-server "pwd"
ssh -F remote.ssh enterprise-ai-server "date"
```

**现在**（复用连接）:
```powershell
# 第一次建立连接
.\scripts\deployment\ssh-persistent.ps1 -Action connect

# 后续命令复用连接，无需重新登录
.\scripts\deployment\ssh-persistent.ps1 -Action execute -Command "ls"
.\scripts\deployment\ssh-persistent.ps1 -Action execute -Command "pwd"
.\scripts\deployment\ssh-persistent.ps1 -Action execute -Command "date"
```

### 场景2: 交互式操作

使用交互式对话框，可以：
- 快速执行命令
- 查看执行结果
- 打开交互式Shell
- 管理连接状态

## 故障排除

### 问题1: ControlMaster连接失败

**症状**: 提示"ControlMaster连接建立失败"

**解决方案**:
1. 检查网络连接
2. 检查SSH密钥权限
3. 手动删除旧的连接文件：
   ```powershell
   Remove-Item ~/.ssh/control-* -Force
   ```

### 问题2: 连接文件残留

**症状**: 连接已断开但文件仍存在

**解决方案**:
```powershell
# 断开所有连接
.\scripts\deployment\ssh-persistent.ps1 -Action disconnect

# 或手动删除
Remove-Item ~/.ssh/control-* -Force
```

### 问题3: Windows路径问题

**症状**: ControlPath路径错误

**解决方案**:
- Windows上SSH会自动将 `~/.ssh` 转换为 `C:\Users\<用户名>\.ssh`
- 确保该目录存在且有写权限

## 高级用法

### 在脚本中使用

```powershell
# 建立连接
.\scripts\deployment\ssh-persistent.ps1 -Action connect

# 执行多个命令
$commands = @("ls", "pwd", "date")
foreach ($cmd in $commands) {
    $result = .\scripts\deployment\ssh-persistent.ps1 -Action execute -Command $cmd
    Write-Host "结果: $result"
}

# 断开连接
.\scripts\deployment\ssh-persistent.ps1 -Action disconnect
```

### 与其他脚本集成

其他脚本可以直接使用SSH命令，ControlMaster会自动复用连接：

```powershell
# 这些命令会自动复用ControlMaster连接
ssh -F remote.ssh enterprise-ai-server "ls"
ssh -F remote.ssh enterprise-ai-server "pwd"
```

## 性能优势

使用ControlMaster后：
- ⚡ **连接速度**: 从3-5秒降低到<1秒
- 🔄 **连接复用**: 减少服务器负载
- 💾 **资源节省**: 减少网络开销

## 注意事项

1. **连接超时**: 默认10分钟无活动后自动断开
2. **并发限制**: ControlMaster连接不支持并发写入
3. **Windows兼容**: 在Windows上需要OpenSSH客户端（Windows 10+自带）

## 相关文件

- `scripts/deployment/ssh-persistent.ps1` - 主脚本
- `remote.ssh` - SSH配置文件
- `ssh-connect-persistent.ps1` - 快速启动脚本
- `ssh-connect-persistent.bat` - Windows批处理启动脚本


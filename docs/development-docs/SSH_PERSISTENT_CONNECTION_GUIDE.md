# SSH持久化连接使用指南

## 问题说明

在Windows上，多次SSH连接后会出现卡住不动的问题。这是因为：
1. 每次SSH连接都会创建新的进程
2. 旧的连接进程没有正确清理
3. 累积的连接导致系统资源耗尽

## 解决方案

### 方案1: SSH会话管理器（推荐）

使用 `ssh-session-manager.ps1` 维护一个长期运行的SSH会话：

```powershell
# 启动持久会话
powershell -ExecutionPolicy Bypass -File "scripts\deployment\ssh-session-manager.ps1" -Action start

# 检查状态
powershell -ExecutionPolicy Bypass -File "scripts\deployment\ssh-session-manager.ps1" -Action status

# 执行命令（通过持久会话）
powershell -ExecutionPolicy Bypass -File "scripts\deployment\ssh-session-manager.ps1" -Action execute -Command "your command"

# 停止会话
powershell -ExecutionPolicy Bypass -File "scripts\deployment\ssh-session-manager.ps1" -Action stop
```

### 方案2: 直接使用SSH（简单但可能卡住）

如果会话管理器不可用，直接使用SSH命令，但要注意：
- 每次执行前手动清理旧连接
- 使用超时机制
- 避免频繁执行

```powershell
# 清理旧连接
Get-Process ssh -ErrorAction SilentlyContinue | Where-Object { $_.StartTime -lt (Get-Date).AddMinutes(-2) } | Stop-Process -Force

# 执行命令
ssh -F remote.ssh enterprise-ai-server "your command"
```

### 方案3: 使用安全执行脚本

使用 `ssh-exec-safe.ps1`，它会自动清理并处理超时：

```powershell
powershell -ExecutionPolicy Bypass -File "scripts\deployment\ssh-exec-safe.ps1" -Command "your command"
```

## 最佳实践

1. **启动会话管理器**：在开始工作前，先启动SSH会话管理器
2. **保持窗口打开**：如果使用交互式会话，保持PowerShell窗口打开
3. **定期检查状态**：使用 `status` 命令检查连接是否正常
4. **遇到卡住时**：停止会话管理器，清理旧连接，然后重新启动

## 当前推荐工作流程

```powershell
# 1. 启动持久会话
powershell -ExecutionPolicy Bypass -File "scripts\deployment\ssh-session-manager.ps1" -Action start

# 2. 运行测试（会自动使用持久会话）
powershell -ExecutionPolicy Bypass -File "scripts\deployment\run-tests-session.ps1" -Service "workflow-engine"

# 3. 工作完成后，可以选择停止会话
powershell -ExecutionPolicy Bypass -File "scripts\deployment\ssh-session-manager.ps1" -Action stop
```

## 故障排除

如果连接仍然卡住：
1. 检查是否有多个SSH进程：`Get-Process ssh`
2. 清理所有SSH进程：`Get-Process ssh | Stop-Process -Force`
3. 清理ControlMaster文件：删除 `~/.ssh/control-*` 文件
4. 重新启动会话管理器


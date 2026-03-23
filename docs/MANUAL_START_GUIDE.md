# 手动启动指南（绕过工具问题）

## 问题说明

如果通过Cursor工具执行命令一直卡住，请**直接在Windows PowerShell中手动运行**。

## 快速启动步骤

### 方法1: 使用批处理文件（最简单）

1. **双击运行** `START_COVERAGE.bat`
2. 或者右键 -> 以管理员身份运行

### 方法2: 手动在PowerShell中运行

1. **打开Windows PowerShell**（不是Cursor的终端）
   - 按 `Win + X`
   - 选择 "Windows PowerShell" 或 "终端"

2. **切换到项目目录**：
   ```powershell
   cd E:\enterprise-ai-platform
   ```

3. **清理旧进程**（可选）：
   ```powershell
   Get-Process pwsh, powershell -ErrorAction SilentlyContinue | Stop-Process -Force
   Get-Job | Remove-Job -Force
   ```

4. **运行脚本**：
   ```powershell
   pwsh -NoProfile -ExecutionPolicy Bypass -File scripts\test-coverage\coverage-improvement-loop.ps1
   ```

## 如果还是卡住

### 检查1: PowerShell进程
```powershell
Get-Process pwsh, powershell
```
如果有多个进程，停止它们：
```powershell
Get-Process pwsh, powershell | Stop-Process -Force
```

### 检查2: 后台Job
```powershell
Get-Job
Get-Job | Remove-Job -Force
```

### 检查3: SSH进程
```powershell
Get-Process ssh -ErrorAction SilentlyContinue
Get-Process ssh -ErrorAction SilentlyContinue | Stop-Process -Force
```

### 检查4: 系统资源
打开任务管理器（`Ctrl + Shift + Esc`），查看：
- CPU使用率
- 内存使用率
- PowerShell进程数量

## 最小测试

先运行最简单的测试，确认PowerShell正常：

```powershell
Write-Host "测试" -ForegroundColor Green
```

如果这个都卡住，说明PowerShell环境有问题，需要：
1. 重启计算机
2. 或者使用其他终端（如CMD）

## 使用CMD作为替代

如果PowerShell有问题，可以用CMD：

```cmd
cd /d E:\enterprise-ai-platform
pwsh.exe -NoProfile -ExecutionPolicy Bypass -File scripts\test-coverage\coverage-improvement-loop.ps1
```

## 重要提示

**不要通过Cursor的终端工具执行**，因为工具本身可能有问题。

**直接在Windows的PowerShell或CMD中运行**，这样可以：
- 看到实时输出
- 可以随时中断（Ctrl+C）
- 避免工具层面的问题


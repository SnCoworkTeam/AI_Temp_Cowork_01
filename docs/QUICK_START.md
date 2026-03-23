# 快速启动指南

## 问题诊断

如果脚本执行没反应，可能是以下原因：

1. **SSH连接问题** - 脚本在等待服务器连接
2. **语法错误** - PowerShell解析错误
3. **权限问题** - 执行策略限制

## 解决方案

### 方法1: 直接运行批处理文件（推荐）

```cmd
RUN_COVERAGE_LOOP.bat
```

### 方法2: 手动运行PowerShell

```powershell
cd E:\enterprise-ai-platform
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts\test-coverage\coverage-improvement-loop.ps1
```

### 方法3: 如果还是卡住，先测试最小版本

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts\test-coverage\coverage-improvement-loop-minimal.ps1
```

## 检查脚本语法

```powershell
# 检查语法错误
$errors = $null
$content = Get-Content scripts\test-coverage\coverage-improvement-loop.ps1 -Raw
[System.Management.Automation.PSParser]::Tokenize($content, [ref]$errors)
if ($errors) { $errors | Format-List } else { Write-Host "语法正确" }
```

## 如果脚本在等待SSH连接

脚本可能在等待服务器响应。可以：
1. 检查 `remote.ssh` 配置文件
2. 测试SSH连接：`ssh -F remote.ssh enterprise-ai-server echo "test"`
3. 如果服务器不可达，脚本会跳过服务器检查继续运行


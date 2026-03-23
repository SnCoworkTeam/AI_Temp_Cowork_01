# 解决 PowerShell 执行策略问题

## 问题描述

运行 `.\sync.ps1` 时出现错误：
```
无法加载文件，因为在此系统上禁止运行脚本
```

这是因为 Windows PowerShell 的执行策略默认不允许运行未签名的脚本。

## 解决方案

### 方案1：使用批处理文件（推荐，最简单）

直接使用 `sync.bat` 代替 `sync.ps1`：

```cmd
sync.bat
```

这个批处理文件会自动绕过执行策略限制。

### 方案2：临时绕过执行策略

在 PowerShell 中执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\sync.ps1
```

或者：

```powershell
.\sync.ps1 -ExecutionPolicy Bypass
```

### 方案3：修改当前用户的执行策略（推荐，永久解决）

在 PowerShell（管理员权限）中执行：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

这个命令会：
- 只影响当前用户（不需要管理员权限）
- 允许运行本地创建的脚本
- 仍然要求从网络下载的脚本需要签名

**验证设置：**
```powershell
Get-ExecutionPolicy -List
```

应该看到 `CurrentUser` 的值为 `RemoteSigned`。

### 方案4：修改进程级别的执行策略（仅当前会话）

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\sync.ps1
```

这个设置只在当前 PowerShell 会话中有效。

## 执行策略说明

| 策略 | 说明 | 推荐度 |
|------|------|--------|
| `Restricted` | 默认策略，不允许运行任何脚本 | ❌ |
| `RemoteSigned` | 本地脚本可运行，远程脚本需签名 | ✅ 推荐 |
| `Unrestricted` | 所有脚本都可运行（会提示） | ⚠️ 不推荐 |
| `Bypass` | 完全绕过，不检查也不提示 | ⚠️ 仅临时使用 |

## 推荐做法

### 对于个人开发环境

```powershell
# 设置当前用户策略为 RemoteSigned（推荐）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 对于企业环境

如果公司策略不允许修改执行策略，使用 `sync.bat`：

```cmd
sync.bat
```

## 验证

设置完成后，测试：

```powershell
.\sync.ps1 -DryRun
```

如果不再出现执行策略错误，说明问题已解决。

## 其他脚本

如果其他 PowerShell 脚本也遇到同样问题，可以使用相同的方法：

```powershell
# 方法1：使用批处理文件（如果有）
script.bat

# 方法2：临时绕过
powershell -ExecutionPolicy Bypass -File .\script.ps1

# 方法3：修改执行策略（永久）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 参考

- [Microsoft 官方文档：执行策略](https://docs.microsoft.com/zh-cn/powershell/module/microsoft.powershell.core/about/about_execution_policies)
- [PowerShell 执行策略详解](https://go.microsoft.com/fwlink/?LinkID=135170)


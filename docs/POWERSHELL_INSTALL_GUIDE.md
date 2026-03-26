# PowerShell 7 下载和安装指南

## 📥 下载方式

### 方式1：直接下载安装包（推荐，最简单）

访问 PowerShell 官方发布页面：
- **直接链接**：https://aka.ms/powershell-release?tag=stable
- **GitHub Releases**：https://github.com/PowerShell/PowerShell/releases/latest

**Windows 用户下载：**
- **64位系统**：下载 `PowerShell-7.5.4-win-x64.msi`
- **32位系统**：下载 `PowerShell-7.5.4-win-x86.msi`
- **ARM64系统**：下载 `PowerShell-7.5.4-win-arm64.msi`

### 方式2：使用 winget（Windows 11/10 1809+）

```powershell
# 在 PowerShell 或 CMD 中执行
winget install --id Microsoft.PowerShell --source winget
```

### 方式3：使用 Chocolatey

```powershell
# 如果已安装 Chocolatey
choco install powershell-core
```

### 方式4：使用 Scoop

```powershell
# 如果已安装 Scoop
scoop install pwsh
```

## 🚀 安装步骤

### 使用 MSI 安装包（推荐）

1. **下载安装包**
   - 访问：https://aka.ms/powershell-release?tag=stable
   - 点击 `PowerShell-7.5.4-win-x64.msi` 下载

2. **运行安装程序**
   - 双击下载的 `.msi` 文件
   - 按照安装向导完成安装
   - 建议选择"添加到 PATH"选项

3. **验证安装**
   ```powershell
   # 打开新的 PowerShell 窗口，运行：
   pwsh --version
   # 应该显示：PowerShell 7.5.4
   ```

## 🔧 安装后配置

### 1. 设置执行策略

```powershell
# 使用 PowerShell 7 (pwsh)
pwsh -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
```

### 2. 验证安装

```powershell
# 检查版本
pwsh --version

# 检查执行策略
pwsh -Command "Get-ExecutionPolicy"
```

### 3. 设置别名（可选）

如果你想让 `powershell` 命令默认使用 PowerShell 7：

```powershell
# 在 PowerShell 7 中执行
pwsh -Command "Set-Alias -Name powershell -Value pwsh -Scope Global"
```

## 📋 使用 PowerShell 7

### 运行脚本

```powershell
# 使用 PowerShell 7 运行脚本
pwsh -File .\sync.ps1

# 或者直接进入 PowerShell 7
pwsh
# 然后在其中运行
.\sync.ps1
```

### 检查当前使用的版本

```powershell
# 在 PowerShell 中运行
$PSVersionTable.PSVersion

# PowerShell 5.1 会显示：5.1.x
# PowerShell 7 会显示：7.x.x
```

## 🔄 与 Windows PowerShell 5.1 共存

PowerShell 7 与 Windows PowerShell 5.1 可以共存：

- **Windows PowerShell 5.1**：使用 `powershell` 命令
- **PowerShell 7**：使用 `pwsh` 命令

两者互不干扰，可以同时使用。

## ✅ 安装后测试

安装完成后，测试同步脚本：

```powershell
# 使用 PowerShell 7 运行
pwsh -File .\sync.ps1 -DryRun

# 或使用批处理文件（会自动使用正确的 PowerShell）
sync.bat
```

## 🎯 推荐配置

### 更新 sync.bat 以优先使用 PowerShell 7

可以修改 `sync.bat` 让它优先使用 PowerShell 7：

```batch
@echo off
REM 优先使用 PowerShell 7，如果不存在则使用 PowerShell 5.1
if exist "%ProgramFiles%\PowerShell\7\pwsh.exe" (
    "%ProgramFiles%\PowerShell\7\pwsh.exe" -ExecutionPolicy Bypass -File "%~dp0scripts\deployment\sync-to-server.ps1" %*
) else (
    powershell.exe -ExecutionPolicy Bypass -File "%~dp0scripts\deployment\sync-to-server.ps1" %*
)
```

## 📚 相关资源

- **官方下载页面**：https://aka.ms/powershell-release?tag=stable
- **GitHub Releases**：https://github.com/PowerShell/PowerShell/releases/latest
- **官方文档**：https://docs.microsoft.com/powershell/
- **安装指南**：https://docs.microsoft.com/powershell/scripting/install/installing-powershell-on-windows

## 🔍 故障排查

### 问题1：下载速度慢

**解决**：使用国内镜像或下载工具（如 IDM、迅雷）

### 问题2：安装后找不到 pwsh 命令

**解决**：
1. 重启终端/命令提示符
2. 检查 PATH 环境变量是否包含 PowerShell 7 安装路径
3. 手动添加到 PATH：`C:\Program Files\PowerShell\7`

### 问题3：仍然使用旧版本

**解决**：
```powershell
# 检查 PATH 顺序
$env:PATH -split ';' | Select-String -Pattern 'PowerShell'

# 确保 PowerShell 7 路径在 Windows PowerShell 路径之前
```

## 💡 提示

- PowerShell 7 是跨平台的，可以在 Windows、Linux、macOS 上运行
- PowerShell 7 基于 .NET Core，性能更好
- PowerShell 7 与 PowerShell 5.1 语法基本兼容，但有一些差异
- 建议新项目使用 PowerShell 7


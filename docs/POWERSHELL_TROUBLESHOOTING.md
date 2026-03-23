# PowerShell 脚本问题排查指南

## 🔍 常见问题

### 问题1：语法错误（字符串缺少终止符、缺少右括号等）

**原因分析：**
1. **PowerShell 版本过旧**：Windows 10 默认的 PowerShell 5.1 可能不支持某些语法
2. **文件编码问题**：脚本文件可能使用了错误的编码（应该是 UTF-8 with BOM 或 UTF-8）
3. **特殊字符问题**：中文字符或特殊引号字符可能导致解析错误

**解决方案：**

#### 方案1：升级到 PowerShell 7+（推荐）

PowerShell 7+ (PowerShell Core) 是跨平台的现代版本，兼容性更好：

```powershell
# 检查当前版本
$PSVersionTable.PSVersion

# 如果版本 < 7.0，建议升级
# 下载地址：https://aka.ms/powershell-release?tag=stable
```

**安装 PowerShell 7：**
1. 访问：https://github.com/PowerShell/PowerShell/releases
2. 下载 `PowerShell-7.x.x-win-x64.msi`
3. 安装后，使用 `pwsh` 命令运行新版本

#### 方案2：修复文件编码

确保脚本文件使用正确的编码：

```powershell
# 检查文件编码
Get-Content .\sync.ps1 -Encoding Byte | Select-Object -First 3

# 转换为 UTF-8 with BOM（Windows PowerShell 推荐）
$content = Get-Content .\sync.ps1 -Raw
[System.IO.File]::WriteAllText(
    (Resolve-Path .\sync.ps1),
    $content,
    [System.Text.UTF8Encoding]::new($true)
)
```

#### 方案3：使用批处理文件（最简单）

直接使用 `sync.bat`，它会自动处理编码和执行策略问题：

```cmd
sync.bat
```

### 问题2：执行策略错误

**错误信息：**
```
无法加载文件，因为在此系统上禁止运行脚本
```

**解决方案：**

```powershell
# 方案1：使用批处理文件（推荐）
sync.bat

# 方案2：临时绕过
powershell -ExecutionPolicy Bypass -File .\sync.ps1

# 方案3：永久设置（当前用户）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 问题3：PowerShell 版本过旧

**检查版本：**
```powershell
# Windows PowerShell 5.1
$PSVersionTable.PSVersion

# 如果是 5.1 或更早，建议升级
```

**升级方法：**

1. **安装 PowerShell 7（推荐）**
   - 下载：https://aka.ms/powershell-release?tag=stable
   - 安装后使用 `pwsh` 命令

2. **或者更新 Windows PowerShell 5.1**
   - Windows 10/11 会自动更新
   - 或通过 Windows Update 更新

### 问题4：中文字符显示问题

**如果脚本中的中文显示为乱码：**

```powershell
# 设置控制台编码为 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001

# 然后运行脚本
.\sync.ps1
```

## 🛠️ 推荐配置

### 1. 安装 PowerShell 7

```powershell
# 使用 winget 安装（Windows 11/10 1809+）
winget install --id Microsoft.PowerShell --source winget

# 或下载安装包
# https://aka.ms/powershell-release?tag=stable
```

### 2. 设置执行策略

```powershell
# 以管理员身份运行
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. 配置默认编码

在 PowerShell 配置文件中添加：

```powershell
# 编辑配置文件
notepad $PROFILE

# 添加以下内容
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'
```

### 4. 使用批处理文件（最简单）

项目已提供 `sync.bat`，它会：
- 自动绕过执行策略
- 处理编码问题
- 兼容所有 PowerShell 版本

**直接使用：**
```cmd
sync.bat
```

## 📋 快速诊断

运行以下命令诊断问题：

```powershell
# 1. 检查 PowerShell 版本
Write-Host "PowerShell 版本: $($PSVersionTable.PSVersion)"

# 2. 检查执行策略
Write-Host "执行策略: $(Get-ExecutionPolicy)"

# 3. 检查文件编码
$bytes = Get-Content .\sync.ps1 -Encoding Byte -TotalCount 3
Write-Host "文件编码: $($bytes -join ',')"

# 4. 测试脚本语法
$errors = $null
$null = [System.Management.Automation.PSParser]::Tokenize(
    (Get-Content .\sync.ps1 -Raw),
    [ref]$errors
)
if ($errors) {
    Write-Host "语法错误: $($errors | ConvertTo-Json)" -ForegroundColor Red
} else {
    Write-Host "语法检查通过" -ForegroundColor Green
}
```

## ✅ 推荐解决方案总结

**最简单的方法（推荐）：**

1. **直接使用 `sync.bat`**
   ```cmd
   sync.bat
   ```
   这会自动处理所有问题。

2. **如果必须使用 PowerShell 脚本：**
   ```powershell
   # 升级到 PowerShell 7
   # 然后运行
   pwsh -File .\sync.ps1
   ```

3. **如果不想升级：**
   ```powershell
   # 使用批处理文件
   sync.bat
   
   # 或临时绕过
   powershell -ExecutionPolicy Bypass -File .\sync.ps1
   ```

## 🔗 相关资源

- [PowerShell 7 下载](https://aka.ms/powershell-release?tag=stable)
- [PowerShell 文档](https://docs.microsoft.com/powershell/)
- [执行策略说明](https://docs.microsoft.com/powershell/module/microsoft.powershell.core/about/about_execution_policies)


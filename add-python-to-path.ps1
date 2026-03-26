# 将Python添加到PATH环境变量
# 需要以管理员身份运行才能修改系统PATH

param(
    [switch]$UserPath = $true,  # 默认添加到用户PATH
    [switch]$SystemPath = $false  # 添加到系统PATH（需要管理员权限）
)

$ErrorActionPreference = "Stop"

# Python路径
$pythonPath = "C:\Users\user\AppData\Local\Programs\Python\Python314"
$pythonScriptsPath = "C:\Users\user\AppData\Local\Programs\Python\Python314\Scripts"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "添加Python到PATH环境变量" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查路径是否存在
if (-not (Test-Path $pythonPath)) {
    Write-Host "错误: Python路径不存在: $pythonPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $pythonScriptsPath)) {
    Write-Host "警告: Scripts路径不存在: $pythonScriptsPath" -ForegroundColor Yellow
    Write-Host "将只添加主路径" -ForegroundColor Yellow
}

# 选择添加到用户PATH还是系统PATH
if ($SystemPath) {
    $pathType = [EnvironmentVariableTarget]::Machine
    $pathName = "系统PATH"
    
    # 检查管理员权限
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        Write-Host "错误: 修改系统PATH需要管理员权限" -ForegroundColor Red
        Write-Host "请以管理员身份运行此脚本" -ForegroundColor Yellow
        exit 1
    }
} else {
    $pathType = [EnvironmentVariableTarget]::User
    $pathName = "用户PATH"
}

Write-Host "目标: $pathName" -ForegroundColor Yellow
Write-Host ""

# 获取当前PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", $pathType)

# 检查路径是否已存在
$pathsToAdd = @()
if ($currentPath -notlike "*$pythonPath*") {
    $pathsToAdd += $pythonPath
    Write-Host "✓ 将添加: $pythonPath" -ForegroundColor Green
} else {
    Write-Host "○ 已存在: $pythonPath" -ForegroundColor Gray
}

if (Test-Path $pythonScriptsPath) {
    if ($currentPath -notlike "*$pythonScriptsPath*") {
        $pathsToAdd += $pythonScriptsPath
        Write-Host "✓ 将添加: $pythonScriptsPath" -ForegroundColor Green
    } else {
        Write-Host "○ 已存在: $pythonScriptsPath" -ForegroundColor Gray
    }
}

if ($pathsToAdd.Count -eq 0) {
    Write-Host ""
    Write-Host "所有路径已存在于PATH中，无需添加" -ForegroundColor Yellow
    exit 0
}

# 添加路径
$newPath = $currentPath
foreach ($path in $pathsToAdd) {
    if ($newPath) {
        $newPath += ";$path"
    } else {
        $newPath = $path
    }
}

try {
    [Environment]::SetEnvironmentVariable("Path", $newPath, $pathType)
    Write-Host ""
    Write-Host "✓ 成功添加到 $pathName" -ForegroundColor Green
    Write-Host ""
    Write-Host "注意: 需要重启终端或重新登录才能使更改生效" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "验证: 在新终端中运行 'python --version'" -ForegroundColor Cyan
} catch {
    Write-Host ""
    Write-Host "错误: 添加失败: $_" -ForegroundColor Red
    exit 1
}



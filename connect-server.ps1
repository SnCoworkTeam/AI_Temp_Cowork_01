# 使用 remote.ssh 配置连接服务器
# 使用方法: .\connect-server.ps1

param(
    [string]$ConfigFile = "remote.ssh"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "连接企业AI平台服务器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 读取 remote.ssh 配置
$ServerIP = ""
$ServerUser = "ubuntu"
$KeyPath = ""

if (Test-Path $ConfigFile) {
    Write-Host "读取配置文件: $ConfigFile" -ForegroundColor Green
    $configContent = Get-Content $ConfigFile -Raw
    
    if ($configContent -match "HostName\s+(\S+)") {
        $ServerIP = $matches[1]
    }
    if ($configContent -match "User\s+(\S+)") {
        $ServerUser = $matches[1]
    }
    if ($configContent -match "IdentityFile\s+(\S+)") {
        $KeyPath = $matches[1].Trim('"')
        # 如果是相对路径，转换为绝对路径
        if (-not [System.IO.Path]::IsPathRooted($KeyPath)) {
            $KeyPath = Join-Path $PWD $KeyPath
        }
    }
} else {
    Write-Host "配置文件不存在: $ConfigFile" -ForegroundColor Red
    exit 1
}

# 查找密钥文件
if ([string]::IsNullOrEmpty($KeyPath) -or -not (Test-Path $KeyPath)) {
    $possiblePaths = @(
        Join-Path $PWD "enterprise_ai_platform.pem",
        Join-Path $env:USERPROFILE ".ssh\enterprise_ai_platform.pem"
    )
    
    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            $KeyPath = $path
            Write-Host "找到密钥文件: $KeyPath" -ForegroundColor Green
            break
        }
    }
}

if ([string]::IsNullOrEmpty($KeyPath) -or -not (Test-Path $KeyPath)) {
    Write-Host "未找到密钥文件: enterprise_ai_platform.pem" -ForegroundColor Red
    Write-Host "请将密钥文件放置在以下位置之一：" -ForegroundColor Yellow
    Write-Host "  1. $PWD\enterprise_ai_platform.pem"
    Write-Host "  2. $env:USERPROFILE\.ssh\enterprise_ai_platform.pem"
    exit 1
}

if ([string]::IsNullOrEmpty($ServerIP)) {
    Write-Host "未找到服务器IP地址" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "服务器信息：" -ForegroundColor Cyan
Write-Host "  IP: $ServerIP"
Write-Host "  用户: $ServerUser"
Write-Host "  密钥: $KeyPath"
Write-Host ""
Write-Host "正在连接..." -ForegroundColor Yellow
Write-Host ""

# 构建 SSH 命令
$sshCmd = "ssh -i `"$KeyPath`" -o StrictHostKeyChecking=no $ServerUser@${ServerIP}"

# 执行 SSH 连接
Invoke-Expression $sshCmd


# 简单上传脚本 - 上传修改的文件到服务器
param(
    [string]$ConfigFile = "remote.ssh"
)

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "上传文件到服务器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 读取配置
$ServerIP = "43.143.139.197"
$ServerUser = "ubuntu"
$KeyPath = ""
$RemotePath = "/opt/enterprise-ai-platform"

if (Test-Path $ConfigFile) {
    $config = Get-Content $ConfigFile -Raw
    if ($config -match "HostName\s+(\S+)") { $ServerIP = $matches[1] }
    if ($config -match "User\s+(\S+)") { $ServerUser = $matches[1] }
    if ($config -match "IdentityFile\s+(\S+)") {
        $KeyPath = $matches[1].Trim('"')
        if (-not [System.IO.Path]::IsPathRooted($KeyPath)) {
            $KeyPath = Join-Path $PWD $KeyPath
        }
    }
}

# 查找密钥
if (-not $KeyPath -or -not (Test-Path $KeyPath)) {
    if (Test-Path "enterprise_ai_platform.pem") {
        $KeyPath = Resolve-Path "enterprise_ai_platform.pem"
    } elseif (Test-Path "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem") {
        $KeyPath = "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem"
    }
}

if (-not $KeyPath -or -not (Test-Path $KeyPath)) {
    Write-Host "错误: 未找到密钥文件" -ForegroundColor Red
    exit 1
}

Write-Host "服务器: $ServerUser@$ServerIP" -ForegroundColor Green
Write-Host "密钥: $KeyPath" -ForegroundColor Green
Write-Host ""

# 获取修改的文件 - 使用更简单的方法
$env:GIT_PAGER = ""
$env:PAGER = ""

$files = @()
$gitOutput = git status --porcelain 2>&1 | Out-String
$lines = $gitOutput -split "`n"

foreach ($line in $lines) {
    if ($line -match "^\s*M\s+(.+)$" -or $line -match "^\s*A\s+(.+)$") {
        $file = $matches[1].Trim()
        if ($file -and 
            $file -notlike "*.pem" -and 
            $file -notlike ".env*" -and
            $file -notlike "*.log" -and
            $file -notlike ".git*") {
            $files += $file
        }
    }
}

# 如果没有找到，至少上传 requirements.txt
if ($files.Count -eq 0) {
    if (Test-Path "knowledge-base/requirements.txt") {
        $files = @("knowledge-base/requirements.txt")
        Write-Host "上传修复后的 requirements.txt" -ForegroundColor Yellow
    }
}

if ($files.Count -eq 0) {
    Write-Host "没有需要上传的文件" -ForegroundColor Yellow
    exit 0
}

Write-Host "准备上传 $($files.Count) 个文件:" -ForegroundColor Cyan
$files | ForEach-Object { Write-Host "  - $_" }
Write-Host ""

# 上传文件
$success = 0
$failed = 0

foreach ($file in $files) {
    $localPath = Join-Path $PWD $file
    if (Test-Path $localPath) {
        $remoteDir = Split-Path $file -Parent
        if ($remoteDir) {
            $cmd = "mkdir -p `"$RemotePath/$remoteDir`""
            ssh -i "`"$KeyPath`" -o StrictHostKeyChecking=no -o ConnectTimeout=10 $ServerUser@${ServerIP} $cmd 2>&1 | Out-Null
        }
        
        $scpCmd = "scp -i `"$KeyPath`" -o StrictHostKeyChecking=no -o ConnectTimeout=10 `"$localPath`" $ServerUser@${ServerIP}:$RemotePath/$file"
        $result = Invoke-Expression $scpCmd 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            $success++
            Write-Host "[OK] $file" -ForegroundColor Green
        } else {
            $failed++
            Write-Host "[FAIL] $file" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "上传完成!" -ForegroundColor Green
Write-Host "成功: $success 个文件" -ForegroundColor Green
if ($failed -gt 0) {
    Write-Host "失败: $failed 个文件" -ForegroundColor Red
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步: SSH 到服务器并重启服务" -ForegroundColor Yellow
Write-Host "  ssh -i `"$KeyPath`" $ServerUser@${ServerIP}" -ForegroundColor White
Write-Host "  cd $RemotePath" -ForegroundColor White
Write-Host "  sudo docker compose up -d --build knowledge-base" -ForegroundColor White
Write-Host ""


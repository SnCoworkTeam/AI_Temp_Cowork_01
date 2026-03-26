# 直接上传文件到服务器（不使用 Git）
# 使用方法: .\upload-to-server.ps1

param(
    [string]$ConfigFile = "remote.ssh",
    [string]$RemotePath = "/opt/enterprise-ai-platform"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "上传文件到服务器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 读取 remote.ssh 配置
$ServerIP = ""
$ServerUser = "ubuntu"
$KeyPath = ""

if (Test-Path $ConfigFile) {
    $configContent = Get-Content $ConfigFile -Raw
    
    if ($configContent -match "HostName\s+(\S+)") {
        $ServerIP = $matches[1]
    }
    if ($configContent -match "User\s+(\S+)") {
        $ServerUser = $matches[1]
    }
    if ($configContent -match "IdentityFile\s+(\S+)") {
        $KeyPath = $matches[1].Trim('"')
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
            break
        }
    }
}

if ([string]::IsNullOrEmpty($KeyPath) -or -not (Test-Path $KeyPath)) {
    Write-Host "未找到密钥文件" -ForegroundColor Red
    exit 1
}

if ([string]::IsNullOrEmpty($ServerIP)) {
    $ServerIP = "43.143.139.197"
}

Write-Host "服务器: $ServerUser@$ServerIP" -ForegroundColor Green
Write-Host "远程路径: $RemotePath" -ForegroundColor Green
Write-Host ""

# 要上传的文件列表（knowledge-base 相关）
$filesToUpload = @(
    "knowledge-base/src/core/embedding_manager.py",
    "knowledge-base/src/core/vector_store.py",
    "knowledge-base/DEPENDENCY_FIX.md"
)

Write-Host "准备上传以下文件:" -ForegroundColor Yellow
foreach ($file in $filesToUpload) {
    if (Test-Path $file) {
        Write-Host "  - $file" -ForegroundColor Green
    } else {
        Write-Host "  - $file (不存在)" -ForegroundColor Red
    }
}
Write-Host ""

# 使用 scp 上传文件
$uploadCount = 0
$failedFiles = @()

foreach ($file in $filesToUpload) {
    if (Test-Path $file) {
        $remoteDir = Split-Path $file -Parent
        $remoteFile = "$RemotePath/$file"
        
        Write-Host "上传: $file ..." -NoNewline
        
        # 确保远程目录存在
        $ensureDirCmd = "mkdir -p `"$RemotePath/$remoteDir`""
        & ssh -i "`"$KeyPath`" -o StrictHostKeyChecking=no -o ConnectTimeout=10 $ServerUser@${ServerIP} $ensureDirCmd 2>&1 | Out-Null
        
        # 上传文件
        $scpArgs = @(
            "-i", "`"$KeyPath`"",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            $file,
            "$ServerUser@${ServerIP}:$remoteFile"
        )
        
        & scp @scpArgs 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host " 成功" -ForegroundColor Green
            $uploadCount++
        } else {
            Write-Host " 失败" -ForegroundColor Red
            $failedFiles += $file
        }
    }
}

Write-Host ""
if ($failedFiles.Count -eq 0) {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "上传完成！成功上传 $uploadCount 个文件" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "上传失败 $($failedFiles.Count) 个文件" -ForegroundColor Red
    $failedFiles | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    Write-Host "========================================" -ForegroundColor Red
}

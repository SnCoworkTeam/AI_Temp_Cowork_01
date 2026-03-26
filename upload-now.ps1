# 快速上传脚本 - 直接上传修改的文件
# 使用方法: powershell -ExecutionPolicy Bypass -File .\upload-now.ps1

$ServerIP = "43.143.139.197"
$ServerUser = "ubuntu"
$RemotePath = "/opt/enterprise-ai-platform"

# 查找密钥文件
$KeyPath = ""
if (Test-Path "enterprise_ai_platform.pem") {
    $KeyPath = Resolve-Path "enterprise_ai_platform.pem"
} elseif (Test-Path "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem") {
    $KeyPath = "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem"
} else {
    Write-Host "Error: Key file not found" -ForegroundColor Red
    exit 1
}

Write-Host "Uploading modified files..." -ForegroundColor Cyan
Write-Host "Server: $ServerUser@$ServerIP" -ForegroundColor Cyan
Write-Host "Remote Path: $RemotePath" -ForegroundColor Cyan
Write-Host ""

# 获取修改的文件（排除删除的文件）
$modifiedFiles = git diff --name-only --diff-filter=M
$addedFiles = git diff --cached --name-only --diff-filter=A

$filesToUpload = @()
$modifiedFiles -split "`n" | Where-Object { $_ -and $_.Trim() } | ForEach-Object { $filesToUpload += $_ }
$addedFiles -split "`n" | Where-Object { $_ -and $_.Trim() } | ForEach-Object { $filesToUpload += $_ }

# 过滤掉不需要的文件
$filesToUpload = $filesToUpload | Where-Object {
    $_ -and 
    $_ -notlike "*.pem" -and
    $_ -notlike ".env*" -and
    $_ -notlike "*.log"
} | Select-Object -Unique

if ($filesToUpload.Count -eq 0) {
    Write-Host "No files to upload" -ForegroundColor Yellow
    exit 0
}

Write-Host "Files to upload ($($filesToUpload.Count)):" -ForegroundColor Green
$filesToUpload | ForEach-Object { Write-Host "  - $_" }

Write-Host ""
Write-Host "Uploading..." -ForegroundColor Cyan

$uploadCount = 0
$failedFiles = @()

foreach ($file in $filesToUpload) {
    $filePath = Join-Path $PWD $file
    if (Test-Path $filePath) {
        $remoteDir = Split-Path $file -Parent
        if ($remoteDir) {
            $ensureDirCmd = "mkdir -p `"$RemotePath/$remoteDir`""
            & ssh -i "`"$KeyPath`" -o StrictHostKeyChecking=no -o ConnectTimeout=10 $ServerUser@${ServerIP} $ensureDirCmd 2>&1 | Out-Null
        }
        
        $scpArgs = @(
            "-i", "`"$KeyPath`"",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            $filePath,
            "$ServerUser@${ServerIP}:$RemotePath/$file"
        )
        
        & scp @scpArgs 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            $uploadCount++
            Write-Host "  [OK] $file" -ForegroundColor Green
        } else {
            $failedFiles += $file
            Write-Host "  [FAIL] $file" -ForegroundColor Red
        }
    }
}

Write-Host ""
if ($failedFiles.Count -eq 0) {
    Write-Host "Upload completed successfully!" -ForegroundColor Green
    Write-Host "Uploaded: $uploadCount files" -ForegroundColor Green
} else {
    Write-Host "Upload completed with errors" -ForegroundColor Yellow
    Write-Host "Success: $uploadCount files" -ForegroundColor Green
    Write-Host "Failed: $($failedFiles.Count) files" -ForegroundColor Red
    $failedFiles | ForEach-Object { Write-Host "  - $_" }
}


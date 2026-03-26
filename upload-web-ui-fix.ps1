# 上传 Web UI 修复文件并重启服务
# 使用方法: .\upload-web-ui-fix.ps1

param(
    [string]$ConfigFile = "remote.ssh",
    [string]$RemotePath = "/opt/enterprise-ai-platform"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "上传 Web UI 修复文件并重启服务" -ForegroundColor Cyan
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

# 要上传的文件列表（Web UI 修复文件）
$filesToUpload = @(
    "web-ui/src/components/ChatInterface.tsx",
    "web-ui/src/components/MessageList.tsx",
    "web-ui/src/components/MessageInput.tsx",
    "web-ui/src/components/ChatInterface/index.ts",
    "web-ui/src/components/ChatInterface/KnowledgeSidebar.tsx",
    "web-ui/src/components/ChatInterface/KnowledgeCitation.tsx",
    "web-ui/src/components/ChatInterface/SourceDocuments.tsx",
    "web-ui/src/components/WorkflowDesigner.tsx",
    "web-ui/src/components/nodes/LogNode.tsx",
    "web-ui/src/components/nodes/index.ts",
    "web-ui/src/types/workflow.ts",
    "web-ui/src/lib/api/client.ts"
)

Write-Host "准备上传以下文件:" -ForegroundColor Yellow
$existingFiles = @()
foreach ($file in $filesToUpload) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
        $existingFiles += $file
    } else {
        Write-Host "  ✗ $file (不存在)" -ForegroundColor Red
    }
}

if ($existingFiles.Count -eq 0) {
    Write-Host "没有文件需要上传" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "开始上传文件..." -ForegroundColor Yellow
Write-Host ""

# 使用 scp 上传文件
$uploadCount = 0
$failedFiles = @()

foreach ($file in $existingFiles) {
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

Write-Host ""

if ($failedFiles.Count -gt 0) {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "上传失败 $($failedFiles.Count) 个文件" -ForegroundColor Red
    $failedFiles | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    Write-Host "========================================" -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "上传完成！成功上传 $uploadCount 个文件" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 重启 Web UI 服务
Write-Host "重启 Web UI 服务..." -ForegroundColor Yellow
Write-Host ""

$restartCmd = "cd $RemotePath && sudo docker compose restart web-ui"
$restartOutput = & ssh -i "`"$KeyPath`" -o StrictHostKeyChecking=no -o ConnectTimeout=10 $ServerUser@${ServerIP} $restartCmd 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "Web UI 服务已重启" -ForegroundColor Green
    Write-Host $restartOutput
} else {
    Write-Host "重启服务失败" -ForegroundColor Red
    Write-Host $restartOutput
    exit 1
}

Write-Host ""
Write-Host "等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 检查服务状态
Write-Host ""
Write-Host "检查服务状态..." -ForegroundColor Yellow
$statusCmd = "cd $RemotePath && sudo docker compose ps web-ui"
$statusOutput = & ssh -i "`"$KeyPath`" -o StrictHostKeyChecking=no -o ConnectTimeout=10 $ServerUser@${ServerIP} $statusCmd 2>&1
Write-Host $statusOutput

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Web UI 地址: http://$ServerIP:3000" -ForegroundColor Cyan
Write-Host ""



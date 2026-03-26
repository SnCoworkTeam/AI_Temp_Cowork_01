# 上传阶段进度组件修改到服务器
$ErrorActionPreference = "Continue"

# 服务器配置
$SERVER_HOST = "43.143.139.197"
$SERVER_USER = "ubuntu"
$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER_PATH = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  上传阶段进度组件修改" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 检查SSH密钥
if (-not (Test-Path $SSH_KEY)) {
    Write-Host "错误: SSH密钥文件不存在: $SSH_KEY" -ForegroundColor Red
    exit 1
}

# 测试SSH连接
Write-Host "检查SSH连接..." -ForegroundColor Cyan
$testResult = ssh -i $SSH_KEY -o ConnectTimeout=5 -o StrictHostKeyChecking=no "${SERVER_USER}@${SERVER_HOST}" "echo OK" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: SSH连接失败" -ForegroundColor Red
    Write-Host $testResult
    exit 1
}
Write-Host "SSH连接成功" -ForegroundColor Green
Write-Host ""

# 需要上传的文件列表（使用相对路径，稍后转换为绝对路径）
$filesToUpload = @(
    "web-ui/src/components/ProjectPhaseProgress.tsx",
    "web-ui/src/app/projects/page.tsx",
    "web-ui/src/app/projects/dashboard/page.tsx",
    "web-ui/src/app/admin/projects/page.tsx",
    "web-ui/src/app/admin/projects/dashboard/page.tsx"
)

# 查找动态路由文件
$projectDetailPage = Get-ChildItem -Path "web-ui/src/app/projects" -Filter "page.tsx" -Recurse | Where-Object { $_.DirectoryName -like "*\[id\]*" } | Select-Object -First 1
$adminProjectDetailPage = Get-ChildItem -Path "web-ui/src/app/admin/projects" -Filter "page.tsx" -Recurse | Where-Object { $_.DirectoryName -like "*\[id\]*" } | Select-Object -First 1

if ($projectDetailPage) {
    $relativePath = $projectDetailPage.FullName.Replace((Get-Location).Path + "\", "").Replace("\", "/")
    $filesToUpload += $relativePath
}

if ($adminProjectDetailPage) {
    $relativePath = $adminProjectDetailPage.FullName.Replace((Get-Location).Path + "\", "").Replace("\", "/")
    $filesToUpload += $relativePath
}

Write-Host "准备上传以下文件:" -ForegroundColor Cyan
foreach ($file in $filesToUpload) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file (文件不存在)" -ForegroundColor Red
    }
}
Write-Host ""

# 检查rsync是否可用
$useRsync = $false
if (Get-Command rsync -ErrorAction SilentlyContinue) {
    $useRsync = $true
    Write-Host "使用 rsync 上传（推荐）" -ForegroundColor Green
} else {
    Write-Host "使用 scp 上传" -ForegroundColor Yellow
}

# 上传文件
$uploadSuccess = $true
foreach ($file in $filesToUpload) {
    if (-not (Test-Path $file)) {
        Write-Host "跳过不存在的文件: $file" -ForegroundColor Yellow
        continue
    }
    
    # 将Windows路径转换为Unix路径
    $unixPath = $file.Replace('\', '/')
    $remoteFile = "$SERVER_PATH/$unixPath"
    $remoteDir = Split-Path $remoteFile -Parent
    
    Write-Host "上传: $file" -ForegroundColor Cyan
    
    if ($useRsync) {
        # 使用 rsync
        $rsyncArgs = @(
            "-avz",
            "--progress",
            "-e", "ssh -i `"$SSH_KEY`" -o StrictHostKeyChecking=no -o ConnectTimeout=10",
            $file,
            "${SERVER_USER}@${SERVER_HOST}:$remoteFile"
        )
        
        & rsync @rsyncArgs
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ✗ 上传失败: $file" -ForegroundColor Red
            $uploadSuccess = $false
        } else {
            Write-Host "  ✓ 上传成功: $file" -ForegroundColor Green
        }
    } else {
        # 使用 scp
        # 先创建远程目录
        ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 "${SERVER_USER}@${SERVER_HOST}" "mkdir -p `"$remoteDir`"" | Out-Null
        
        # 上传文件
        $scpArgs = @(
            "-i", $SSH_KEY,
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            $file,
            "${SERVER_USER}@${SERVER_HOST}:$remoteFile"
        )
        
        & scp @scpArgs
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ✗ 上传失败: $file" -ForegroundColor Red
            $uploadSuccess = $false
        } else {
            Write-Host "  ✓ 上传成功: $file" -ForegroundColor Green
        }
    }
}

Write-Host ""
if ($uploadSuccess) {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✅ 所有文件上传成功！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "提示: 如果web-ui服务正在运行，可能需要重启服务以应用更改" -ForegroundColor Yellow
    Write-Host "      ssh -i $SSH_KEY ${SERVER_USER}@${SERVER_HOST} 'cd $SERVER_PATH && docker-compose restart web-ui'" -ForegroundColor Gray
} else {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "❌ 部分文件上传失败" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    exit 1
}


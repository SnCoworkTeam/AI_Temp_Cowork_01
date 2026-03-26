# PowerShell 脚本：上传代码到服务器并重启服务
# 使用方法: .\upload-and-restart.ps1

param(
    [string]$ServerIP = "43.143.139.197",
    [string]$ServerUser = "ubuntu",
    [string]$KeyPath = "enterprise_ai_platform.pem",
    [string]$RemotePath = "/opt/enterprise-ai-platform"
)

# 颜色输出函数
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Cyan "=========================================="
Write-ColorOutput Cyan "企业AI平台 - 上传代码并重启服务"
Write-ColorOutput Cyan "=========================================="
Write-Output "服务器: $ServerUser@$ServerIP"
Write-Output "远程路径: $RemotePath"
Write-Output ""

# 检查密钥文件
$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) {
    $ProjectRoot = Get-Location
}

$KeyPathFull = Join-Path $ProjectRoot $KeyPath
if (-not (Test-Path $KeyPathFull)) {
    Write-ColorOutput Red "❌ 未找到密钥文件: $KeyPathFull"
    Write-Output "请确保 enterprise_ai_platform.pem 文件在项目根目录下"
    exit 1
}

Write-ColorOutput Green "✅ 找到密钥文件: $KeyPathFull"

# 设置密钥文件权限（Windows）
Write-Output "设置密钥文件权限..."
icacls $KeyPathFull /inheritance:r /grant:r "$env:USERNAME:R" | Out-Null

# 构建 SSH 和 SCP 命令前缀
$sshBase = "ssh -i `"$KeyPathFull`" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
$scpBase = "scp -i `"$KeyPathFull`" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r"
$sshCmd = "$sshBase $ServerUser@${ServerIP}"

# 步骤1: 上传代码
Write-ColorOutput Blue "[1/3] 上传代码到服务器..."
Write-Output "  使用 rsync 同步代码..."

# 检查是否有 rsync
$hasRsync = Get-Command rsync -ErrorAction SilentlyContinue
if ($hasRsync) {
    # 使用 rsync（推荐，支持增量同步）
    $excludeFile = Join-Path $ProjectRoot ".rsync-exclude"
    if (-not (Test-Path $excludeFile)) {
        # 创建排除文件
        @"
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/
.venv/
venv/
env/
.env
.env.*
!.env.example
node_modules/
.git/
.gitignore
*.log
*.tmp
.DS_Store
Thumbs.db
.vscode/
.idea/
*.swp
*.swo
*~
coverage/
htmlcov/
.pytest_cache/
.mypy_cache/
*.pem
!enterprise_ai_platform.pem
"@ | Out-File -FilePath $excludeFile -Encoding UTF8
    }
    
    $rsyncArgs = @(
        "-avz",
        "--progress",
        "--exclude-from=$excludeFile",
        "-e", "ssh -i `"$KeyPathFull`" -o StrictHostKeyChecking=no",
        "./",
        "$ServerUser@${ServerIP}:$RemotePath/"
    )
    
    Push-Location $ProjectRoot
    try {
        & rsync @rsyncArgs
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput Red "❌ 代码上传失败"
            exit 1
        }
        Write-ColorOutput Green "✅ 代码上传成功"
    } finally {
        Pop-Location
    }
} else {
    # 使用 scp（需要先打包）
    Write-Output "  rsync 不可用，使用 scp 上传..."
    
    # 创建临时目录
    $tempDir = Join-Path $env:TEMP "enterprise-ai-platform-upload-$(Get-Date -Format 'yyyyMMddHHmmss')"
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    
    try {
        Write-Output "  打包文件..."
        # 排除不需要的文件
        $excludePatterns = @(
            "__pycache__",
            "*.pyc",
            "*.pyo",
            ".git",
            "node_modules",
            ".venv",
            "venv",
            "env",
            "*.log",
            "coverage",
            "htmlcov",
            ".pytest_cache",
            ".mypy_cache"
        )
        
        Get-ChildItem -Path $ProjectRoot -Recurse -File | Where-Object {
            $relativePath = $_.FullName.Substring($ProjectRoot.Length + 1)
            $shouldExclude = $false
            foreach ($pattern in $excludePatterns) {
                if ($relativePath -like "*\$pattern\*" -or $relativePath -like "*\$pattern") {
                    $shouldExclude = $true
                    break
                }
            }
            -not $shouldExclude
        } | ForEach-Object {
            $destPath = Join-Path $tempDir $_.FullName.Substring($ProjectRoot.Length + 1)
            $destDir = Split-Path $destPath -Parent
            if (-not (Test-Path $destDir)) {
                New-Item -ItemType Directory -Path $destDir -Force | Out-Null
            }
            Copy-Item $_.FullName -Destination $destPath -Force
        }
        
        # 使用 scp 上传
        Write-Output "  上传文件..."
        Push-Location $tempDir
        try {
            & scp -i "`"$KeyPathFull`" -o StrictHostKeyChecking=no -r * "$ServerUser@${ServerIP}:$RemotePath/"
            if ($LASTEXITCODE -ne 0) {
                Write-ColorOutput Red "❌ 代码上传失败"
                exit 1
            }
            Write-ColorOutput Green "✅ 代码上传成功"
        } finally {
            Pop-Location
        }
    } finally {
        # 清理临时目录
        Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# 步骤2: 重启 agent-service
Write-ColorOutput Blue "[2/3] 重启 agent-service 服务..."
$restartCmd = "cd $RemotePath && docker-compose restart agent-service"
$restartResult = & $sshCmd $restartCmd 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-ColorOutput Green "✅ agent-service 重启成功"
} else {
    Write-ColorOutput Yellow "⚠️  agent-service 重启可能失败，尝试停止后启动..."
    # 尝试停止并启动
    $stopCmd = "cd $RemotePath && docker-compose stop agent-service"
    & $sshCmd $stopCmd | Out-Null
    
    $startCmd = "cd $RemotePath && docker-compose up -d agent-service"
    $startResult = & $sshCmd $startCmd 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput Green "✅ agent-service 启动成功"
    } else {
        Write-ColorOutput Red "❌ agent-service 启动失败"
        Write-Output $startResult
    }
}

# 步骤3: 检查服务状态
Write-ColorOutput Blue "[3/3] 检查服务状态..."
$statusCmd = "cd $RemotePath && docker-compose ps agent-service"
$statusResult = & $sshCmd $statusCmd 2>&1
Write-Output $statusResult

# 检查服务日志
Write-ColorOutput Blue "查看 agent-service 最新日志..."
$logCmd = "cd $RemotePath && docker-compose logs --tail=20 agent-service"
$logResult = & $sshCmd $logCmd 2>&1
Write-Output $logResult

Write-Output ""
Write-ColorOutput Green "=========================================="
Write-ColorOutput Green "Deployment Complete!"
Write-ColorOutput Green "=========================================="
Write-Output ""
$serviceUrl = "http://$ServerIP:8010"
$apiUrl = "http://$ServerIP:8010/api/v1/agents"
Write-Output "Service URL: $serviceUrl"
Write-Output "API URL: $apiUrl"
Write-Output ""

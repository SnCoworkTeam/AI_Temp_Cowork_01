# PowerShell 脚本：上传代码到服务器
# 使用方法: .\scripts\deployment\upload-to-server.ps1

param(
    [string]$ServerIP = "43.143.139.197",
    [string]$ServerUser = "ubuntu",
    [string]$KeyPath = "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem",
    [string]$RemotePath = "/opt/enterprise-ai-platform",
    [string]$ProjectRoot = $PSScriptRoot + "\..\.."
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
Write-ColorOutput Cyan "企业AI平台 - 代码上传脚本"
Write-ColorOutput Cyan "=========================================="
Write-Output "服务器: $ServerUser@$ServerIP"
Write-Output "远程路径: $RemotePath"
Write-Output "密钥文件: $KeyPath"
Write-Output ""

# 检查密钥文件
if (-not (Test-Path $KeyPath)) {
    Write-ColorOutput Yellow "⚠️  密钥文件不存在: $KeyPath"
    Write-ColorOutput Yellow "请将 enterprise_ai_platform.pem 放置在以下位置之一："
    Write-Output "  1. $env:USERPROFILE\.ssh\enterprise_ai_platform.pem"
    Write-Output "  2. 项目根目录: $ProjectRoot\enterprise_ai_platform.pem"
    Write-Output ""
    
    # 检查项目根目录
    $ProjectKeyPath = Join-Path $ProjectRoot "enterprise_ai_platform.pem"
    if (Test-Path $ProjectKeyPath) {
        Write-ColorOutput Green "✅ 在项目根目录找到密钥文件，使用: $ProjectKeyPath"
        $KeyPath = $ProjectKeyPath
    } else {
        Write-ColorOutput Red "❌ 未找到密钥文件，请先配置密钥文件"
        exit 1
    }
}

# 设置密钥文件权限（Windows）
Write-Output "设置密钥文件权限..."
try {
    $acl = Get-Acl $KeyPath
    $acl.SetAccessRuleProtection($true, $false)
    $permission = $env:USERNAME, "Read", "Allow"
    $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule $permission
    $acl.SetAccessRule($accessRule)
    Set-Acl $KeyPath $acl
    Write-ColorOutput Green "✅ 密钥文件权限已设置"
} catch {
    Write-ColorOutput Yellow "⚠️  无法设置密钥文件权限: $_"
}

# 检查 rsync 或 scp 是否可用
$useRsync = $false
if (Get-Command rsync -ErrorAction SilentlyContinue) {
    $useRsync = $true
    Write-ColorOutput Green "✅ 检测到 rsync，使用 rsync 上传（更快）"
} elseif (Get-Command scp -ErrorAction SilentlyContinue) {
    Write-ColorOutput Green "✅ 检测到 scp，使用 scp 上传"
} else {
    Write-ColorOutput Red "❌ 未找到 rsync 或 scp 命令"
    Write-Output "请安装以下工具之一："
    Write-Output "  1. Git for Windows (包含 scp)"
    Write-Output "  2. WSL (包含 rsync)"
    Write-Output "  3. Cygwin (包含 rsync)"
    exit 1
}

# 排除文件列表
$excludeList = @(
    ".git",
    "node_modules",
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    ".venv",
    "venv",
    "*.log",
    ".next",
    "dist",
    "build",
    ".env",
    ".env.*",
    "*.pem",
    ".vscode",
    ".idea"
)

# 创建临时排除文件
$excludeFile = Join-Path $env:TEMP "rsync-exclude-$(Get-Date -Format 'yyyyMMddHHmmss').txt"
$excludeList | Out-File -FilePath $excludeFile -Encoding utf8

Write-Output ""
Write-ColorOutput Blue "开始上传代码..."

# 切换到项目根目录
Push-Location $ProjectRoot

try {
    if ($useRsync) {
        # 使用 rsync（推荐，支持增量同步）
        Write-Output "使用 rsync 上传..."
        
        # 构建 rsync 命令
        $rsyncArgs = @(
            "-avz",
            "--progress",
            "--exclude-from=$excludeFile",
            "-e", "ssh -i `"$KeyPath`" -o StrictHostKeyChecking=no",
            "./",
            "$ServerUser@${ServerIP}:$RemotePath/"
        )
        
        & rsync @rsyncArgs
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput Green "✅ 代码上传成功"
        } else {
            Write-ColorOutput Red "❌ 代码上传失败"
            exit 1
        }
    } else {
        # 使用 scp（需要先打包）
        Write-Output "使用 scp 上传（需要先打包）..."
        
        # 创建临时目录
        $tempDir = Join-Path $env:TEMP "enterprise-ai-platform-upload-$(Get-Date -Format 'yyyyMMddHHmmss')"
        New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
        
        try {
            # 复制文件（排除不需要的文件）
            Write-Output "打包文件..."
            Get-ChildItem -Path . -Recurse | Where-Object {
                $relativePath = $_.FullName.Substring($ProjectRoot.Length + 1)
                $shouldExclude = $false
                foreach ($exclude in $excludeList) {
                    if ($relativePath -like $exclude -or $relativePath -match $exclude) {
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
            Write-Output "上传文件..."
            $scpArgs = @(
                "-i", "`"$KeyPath`"",
                "-o", "StrictHostKeyChecking=no",
                "-r",
                "$tempDir\*",
                "$ServerUser@${ServerIP}:$RemotePath/"
            )
            
            & scp @scpArgs
            
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput Green "✅ 代码上传成功"
            } else {
                Write-ColorOutput Red "❌ 代码上传失败"
                exit 1
            }
        } finally {
            # 清理临时目录
            Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    
    Write-Output ""
    Write-ColorOutput Green "=========================================="
    Write-ColorOutput Green "✅ 上传完成！"
    Write-ColorOutput Green "=========================================="
    Write-Output ""
    Write-Output "下一步："
    Write-Output "1. 在 VS Code 中连接到服务器"
    Write-Output "2. 运行部署脚本: bash scripts/deployment/deploy-server.sh --env production"
    Write-Output ""
    
} finally {
    Pop-Location
    # 清理排除文件
    Remove-Item -Path $excludeFile -Force -ErrorAction SilentlyContinue
}


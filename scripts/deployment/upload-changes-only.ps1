# PowerShell 脚本：只上传修改的内容到服务器
# 使用方法: .\scripts\deployment\upload-changes-only.ps1
# 
# 功能：
# 1. 从 remote.ssh 配置文件读取服务器信息（如果存在）
# 2. 检测 Git 变更的文件
# 3. 只上传修改的文件
# 4. 使用 enterprise_ai_platform.pem 密钥

param(
    [string]$ConfigFile = "remote.ssh",
    [string]$KeyFile = "enterprise_ai_platform.pem",
    [string]$RemotePath = "/opt/enterprise-ai-platform",
    [string]$Branch = "",
    [switch]$IncludeUntracked = $false,
    [switch]$Force = $false
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
Write-ColorOutput Cyan "企业AI平台 - 增量上传脚本"
Write-ColorOutput Cyan "=========================================="
Write-Output ""

# 获取项目根目录
$ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Push-Location $ProjectRoot

try {
    # 步骤1: 读取配置文件
    Write-ColorOutput Blue "[1/5] 读取服务器配置..."
    
    $ServerIP = ""
    $ServerUser = "ubuntu"
    $KeyPath = ""
    
    # 尝试从 remote.ssh 读取配置
    $configPath = Join-Path $ProjectRoot $ConfigFile
    if (Test-Path $configPath) {
        Write-ColorOutput Green "✅ 找到配置文件: $configPath"
        $configContent = Get-Content $configPath -Raw
        
        # 解析 SSH 配置格式
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
                $KeyPath = Join-Path $ProjectRoot $KeyPath
            }
        }
    } else {
        Write-ColorOutput Yellow "⚠️  配置文件不存在: $configPath"
        Write-Output "使用默认配置或从 .ssh-config.example 读取..."
        
        # 尝试从 .ssh-config.example 读取
        $exampleConfig = Join-Path $ProjectRoot ".ssh-config.example"
        if (Test-Path $exampleConfig) {
            $exampleContent = Get-Content $exampleConfig -Raw
            if ($exampleContent -match "HostName\s+(\S+)") {
                $ServerIP = $matches[1]
            }
            if ($exampleContent -match "IdentityFile\s+(\S+)") {
                $KeyPath = $matches[1].Trim('"')
                # 替换示例路径为实际路径
                $KeyPath = $KeyPath -replace "C:\\Users\\YourUsername", $env:USERPROFILE
                $KeyPath = $KeyPath -replace "E:\\\\enterprise-ai-platform", $ProjectRoot
            }
        }
        
        # 如果还是没有，使用默认值
        if ([string]::IsNullOrEmpty($ServerIP)) {
            $ServerIP = "43.143.139.197"
        }
    }
    
    # 查找密钥文件
    if ([string]::IsNullOrEmpty($KeyPath) -or -not (Test-Path $KeyPath)) {
        # 尝试多个可能的位置
        $possibleKeyPaths = @(
            Join-Path $ProjectRoot $KeyFile,
            Join-Path $env:USERPROFILE ".ssh\$KeyFile",
            Join-Path $ProjectRoot "..\$KeyFile"
        )
        
        foreach ($path in $possibleKeyPaths) {
            if (Test-Path $path) {
                $KeyPath = $path
                Write-ColorOutput Green "✅ 找到密钥文件: $KeyPath"
                break
            }
        }
        
        if ([string]::IsNullOrEmpty($KeyPath) -or -not (Test-Path $KeyPath)) {
            Write-ColorOutput Red "❌ 未找到密钥文件: $KeyFile"
            Write-Output "请将密钥文件放置在以下位置之一："
            Write-Output "  1. $ProjectRoot\$KeyFile"
            Write-Output "  2. $env:USERPROFILE\.ssh\$KeyFile"
            exit 1
        }
    } else {
        Write-ColorOutput Green "✅ 使用密钥文件: $KeyPath"
    }
    
    Write-Output "服务器: $ServerUser@$ServerIP"
    Write-Output "远程路径: $RemotePath"
    Write-Output ""
    
    # 步骤2: 检查 Git 状态
    Write-ColorOutput Blue "[2/5] 检测 Git 变更..."
    
    if (-not (Test-Path ".git")) {
        Write-ColorOutput Red "❌ 当前目录不是 Git 仓库"
        exit 1
    }
    
    # 获取当前分支
    if ([string]::IsNullOrEmpty($Branch)) {
        $Branch = git rev-parse --abbrev-ref HEAD
    }
    Write-Output "当前分支: $Branch"
    
    # 检测变更的文件
    $changedFiles = @()
    
    # 获取已修改的文件（相对于远程分支）
    $remoteBranch = "origin/$Branch"
    try {
        git fetch origin $Branch --quiet 2>&1 | Out-Null
        $modifiedFiles = git diff --name-only $remoteBranch HEAD 2>&1
        if ($LASTEXITCODE -eq 0 -and $modifiedFiles) {
            $changedFiles += $modifiedFiles -split "`n" | Where-Object { $_ -and $_.Trim() }
        }
    } catch {
        Write-ColorOutput Yellow "⚠️  无法获取远程分支信息，使用本地变更"
    }
    
    # 获取工作区修改的文件
    $workingFiles = git diff --name-only 2>&1
    if ($LASTEXITCODE -eq 0 -and $workingFiles) {
        $changedFiles += $workingFiles -split "`n" | Where-Object { $_ -and $_.Trim() }
    }
    
    # 获取已暂存的文件
    $stagedFiles = git diff --cached --name-only 2>&1
    if ($LASTEXITCODE -eq 0 -and $stagedFiles) {
        $changedFiles += $stagedFiles -split "`n" | Where-Object { $_ -and $_.Trim() }
    }
    
    # 获取未跟踪的文件（如果指定）
    if ($IncludeUntracked) {
        $untrackedFiles = git ls-files --others --exclude-standard 2>&1
        if ($LASTEXITCODE -eq 0 -and $untrackedFiles) {
            $changedFiles += $untrackedFiles -split "`n" | Where-Object { $_ -and $_.Trim() }
        }
    }
    
    # 去重并过滤
    $changedFiles = $changedFiles | Where-Object { 
        $_ -and 
        $_.Trim() -and 
        -not ($_ -match "^\s*$") -and
        -not ($_ -like "*.pem") -and
        -not ($_ -like ".env*") -and
        -not ($_ -like "*.log")
    } | Select-Object -Unique
    
    if ($changedFiles.Count -eq 0) {
        Write-ColorOutput Yellow "⚠️  没有检测到变更的文件"
        if (-not $Force) {
            Write-Output "使用 -Force 参数强制上传所有文件"
            exit 0
        } else {
            Write-ColorOutput Yellow "使用 -Force 参数，将上传所有文件"
            $changedFiles = @("*")
        }
    } else {
        Write-ColorOutput Green "✅ 检测到 $($changedFiles.Count) 个变更文件"
        Write-Output ""
        Write-Output "变更文件列表:"
        $changedFiles | ForEach-Object { Write-Output "  - $_" }
        Write-Output ""
    }
    
    # 步骤3: 检查上传工具
    Write-ColorOutput Blue "[3/5] 检查上传工具..."
    
    $useRsync = $false
    if (Get-Command rsync -ErrorAction SilentlyContinue) {
        $useRsync = $true
        Write-ColorOutput Green "✅ 使用 rsync 上传（推荐）"
    } elseif (Get-Command scp -ErrorAction SilentlyContinue) {
        Write-ColorOutput Green "✅ 使用 scp 上传"
    } else {
        Write-ColorOutput Red "❌ 未找到 rsync 或 scp 命令"
        Write-Output "请安装以下工具之一："
        Write-Output "  1. Git for Windows (包含 scp)"
        Write-Output "  2. WSL (包含 rsync)"
        exit 1
    }
    
    # 步骤4: 上传文件
    Write-ColorOutput Blue "[4/5] 上传变更文件..."
    
    # 设置密钥文件权限
    try {
        $acl = Get-Acl $KeyPath
        $acl.SetAccessRuleProtection($true, $false)
        $permission = $env:USERNAME, "Read", "Allow"
        $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule $permission
        $acl.SetAccessRule($accessRule)
        Set-Acl $KeyPath $acl
    } catch {
        Write-ColorOutput Yellow "⚠️  无法设置密钥文件权限: $_"
    }
    
    $uploadSuccess = $false
    
    if ($useRsync) {
        # 使用 rsync 上传
        Write-Output "使用 rsync 上传变更文件..."
        
        # 创建包含文件列表的临时文件
        $fileListPath = Join-Path $env:TEMP "rsync-files-$(Get-Date -Format 'yyyyMMddHHmmss').txt"
        if ($Force) {
            # 如果强制上传，创建排除列表
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
            $excludeList | Out-File -FilePath $fileListPath -Encoding utf8
            $rsyncArgs = @(
                "-avz",
                "--progress",
                "--exclude-from=$fileListPath",
                "-e", "ssh -i `"$KeyPath`" -o StrictHostKeyChecking=no",
                "./",
                "$ServerUser@${ServerIP}:$RemotePath/"
            )
        } else {
            # 上传特定文件
            $changedFiles | Out-File -FilePath $fileListPath -Encoding utf8
            $rsyncArgs = @(
                "-avz",
                "--progress",
                "--files-from=$fileListPath",
                "-e", "ssh -i `"$KeyPath`" -o StrictHostKeyChecking=no",
                "./",
                "$ServerUser@${ServerIP}:$RemotePath/"
            )
        }
        
        & rsync @rsyncArgs
        
        if ($LASTEXITCODE -eq 0) {
            $uploadSuccess = $true
        }
        
        # 清理临时文件
        Remove-Item -Path $fileListPath -Force -ErrorAction SilentlyContinue
    } else {
        # 使用 scp 上传
        Write-Output "使用 scp 上传变更文件..."
        
        $uploadCount = 0
        $failedFiles = @()
        
        foreach ($file in $changedFiles) {
            $filePath = Join-Path $ProjectRoot $file
            if (Test-Path $filePath) {
                $remoteDir = Split-Path $file -Parent
                if ($remoteDir) {
                    # 确保远程目录存在
                    $ensureDirCmd = "mkdir -p $RemotePath/$remoteDir"
                    & ssh -i "`"$KeyPath`" -o StrictHostKeyChecking=no $ServerUser@${ServerIP} $ensureDirCmd | Out-Null
                }
                
                # 上传文件
                $scpArgs = @(
                    "-i", "`"$KeyPath`"",
                    "-o", "StrictHostKeyChecking=no",
                    $filePath,
                    "$ServerUser@${ServerIP}:$RemotePath/$file"
                )
                
                & scp @scpArgs
                
                if ($LASTEXITCODE -eq 0) {
                    $uploadCount++
                    Write-Output "  ✅ $file"
                } else {
                    $failedFiles += $file
                    Write-ColorOutput Red "  ❌ $file"
                }
            }
        }
        
        if ($failedFiles.Count -eq 0) {
            $uploadSuccess = $true
            Write-ColorOutput Green "✅ 成功上传 $uploadCount 个文件"
        } else {
            Write-ColorOutput Red "❌ $($failedFiles.Count) 个文件上传失败"
            $failedFiles | ForEach-Object { Write-Output "  - $_" }
        }
    }
    
    # 步骤5: 验证上传
    Write-ColorOutput Blue "[5/5] 验证上传结果..."
    
    if ($uploadSuccess) {
        Write-Output ""
        Write-ColorOutput Green "=========================================="
        Write-ColorOutput Green "✅ 上传完成！"
        Write-ColorOutput Green "=========================================="
        Write-Output ""
        Write-Output "已上传 $($changedFiles.Count) 个文件到服务器"
        Write-Output "服务器路径: $RemotePath"
        Write-Output ""
        Write-Output "下一步操作："
        Write-Output "1. SSH 连接到服务器: ssh -i `"$KeyPath`" $ServerUser@${ServerIP}"
        Write-Output "2. 进入项目目录: cd $RemotePath"
        Write-Output "3. 重启相关服务: sudo docker compose restart"
        Write-Output ""
    } else {
        Write-ColorOutput Red "❌ 上传失败，请检查错误信息"
        exit 1
    }
    
} catch {
    Write-ColorOutput Red "❌ 发生错误: $_"
    Write-Output $_.ScriptStackTrace
    exit 1
} finally {
    Pop-Location
}


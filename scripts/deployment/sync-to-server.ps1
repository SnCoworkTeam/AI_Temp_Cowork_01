# PowerShell 脚本：自动同步修改的文件到服务器
# 使用方法: .\scripts\deployment\sync-to-server.ps1
# 
# 功能：
# 1. 自动检测 Git 变更的文件（工作区、暂存区、已提交但未推送）
# 2. 从 remote.ssh 配置文件读取服务器信息
# 3. 使用 enterprise_ai_platform.pem 密钥
# 4. 只上传修改的文件（增量同步）
# 5. 支持排除不需要的文件（.env, .pem, node_modules 等）
# 6. 使用SSH连接管理器，支持连接池和自动重连

param(
    [string]$ConfigFile = "remote.ssh",
    [string]$KeyFile = "enterprise_ai_platform.pem",
    [string]$RemotePath = "/opt/enterprise-ai-platform",
    [string]$Branch = "",
    [switch]$IncludeUntracked = $false,
    [switch]$All = $false,
    [switch]$DryRun = $false
)

# 导入SSH连接管理器
$sshManagerPath = Join-Path $PSScriptRoot "ssh-manager.ps1"
if (Test-Path $sshManagerPath) {
    . $sshManagerPath
} else {
    Write-Warning "SSH连接管理器未找到，将使用传统方式连接"
}

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
Write-ColorOutput Cyan "企业AI平台 - 自动同步脚本"
Write-ColorOutput Cyan "=========================================="
Write-Output ""

# 获取项目根目录
$ProjectRoot = (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent)
if ($ProjectRoot -is [System.Array]) {
    $ProjectRoot = $ProjectRoot[0]
}
Push-Location $ProjectRoot

try {
    # ==========================================
    # 步骤1: 读取服务器配置
    # ==========================================
    Write-ColorOutput Blue "[1/6] 读取服务器配置..."
    
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
        Write-Output "尝试从 .ssh-config.example 读取..."
        
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
                $KeyPath = $KeyPath -replace "E:\\\\enterprise-ai-platform", $ProjectRoot -replace "\\\\", "\"
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
            Join-Path -Path $ProjectRoot -ChildPath $KeyFile,
            Join-Path -Path $env:USERPROFILE -ChildPath ".ssh\$KeyFile",
            Join-Path -Path $ProjectRoot -ChildPath "..\$KeyFile"
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
    
    # 获取SSH连接（使用连接池）
    $connection = $null
    if (Test-Path $sshManagerPath) {
        try {
            $connection = Get-SSHConnection -ConfigFile $ConfigFile
            Write-ColorOutput Green "✅ 使用SSH连接管理器（连接池）"
        } catch {
            Write-ColorOutput Yellow "⚠️  无法获取SSH连接，将使用传统方式: $_"
        }
    }
    
    # ==========================================
    # 步骤2: 检查 Git 状态
    # ==========================================
    Write-ColorOutput Blue "[2/6] 检测 Git 变更..."
    
    if (-not (Test-Path ".git")) {
        Write-ColorOutput Red "❌ 当前目录不是 Git 仓库"
        exit 1
    }
    
    # 获取当前分支
    if ([string]::IsNullOrEmpty($Branch)) {
        $Branch = git rev-parse --abbrev-ref HEAD
    }
    Write-Output "当前分支: $Branch"
    
    # ==========================================
    # 步骤3: 收集变更文件
    # ==========================================
    Write-ColorOutput Blue "[3/6] 收集变更文件..."
    
    $changedFiles = @()
    
    if ($All) {
        # 上传所有文件（排除 .git, node_modules 等）
        Write-ColorOutput Yellow "⚠️  使用 --All 参数，将上传所有文件（排除忽略项）"
        $changedFiles = @("*")
    } else {
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
        
        # 获取已提交但未推送的文件（相对于远程分支）
        try {
            $remoteBranch = "origin/$Branch"
            git fetch origin $Branch --quiet 2>&1 | Out-Null
            $committedFiles = git diff --name-only $remoteBranch HEAD 2>&1
            if ($LASTEXITCODE -eq 0 -and $committedFiles) {
                $changedFiles += $committedFiles -split "`n" | Where-Object { $_ -and $_.Trim() }
            }
        } catch {
            Write-ColorOutput Yellow "⚠️  无法获取远程分支信息，跳过已提交文件检测"
        }
        
        # 获取未跟踪的文件（如果指定）
        if ($IncludeUntracked) {
            $untrackedFiles = git ls-files --others --exclude-standard 2>&1
            if ($LASTEXITCODE -eq 0 -and $untrackedFiles) {
                $changedFiles += $untrackedFiles -split "`n" | Where-Object { $_ -and $_.Trim() }
            }
        }
    }
    
    # 排除不需要的文件
    $excludePatterns = @(
        "^\s*$",                    # 空行
        "\.pem$",                   # 密钥文件
        "^\.env",                   # 环境变量文件
        "\.log$",                   # 日志文件
        "^\.git/",                  # Git 目录
        "node_modules/",            # Node 模块
        "__pycache__/",             # Python 缓存
        "\.pyc$",                   # Python 编译文件
        "\.pytest_cache/",          # Pytest 缓存
        "^\.venv/",                 # 虚拟环境
        "^venv/",                   # 虚拟环境
        "\.next/",                  # Next.js 构建
        "^dist/",                   # 构建输出
        "^build/",                  # 构建输出
        "^\.vscode/",               # VS Code 配置
        "^\.idea/"                  # IntelliJ 配置
    )
    
    # 去重并过滤
    $changedFiles = $changedFiles | Where-Object { 
        $file = $_
        if (-not $file -or -not $file.Trim()) { return $false }
        
        # 检查排除模式
        $shouldExclude = $false
        foreach ($pattern in $excludePatterns) {
            if ($file -match $pattern) {
                $shouldExclude = $true
                break
            }
        }
        return -not $shouldExclude
    } | Select-Object -Unique
    
    if ($changedFiles.Count -eq 0 -and -not $All) {
        Write-ColorOutput Yellow "⚠️  没有检测到变更的文件"
        Write-Output ""
        Write-Output "提示："
        Write-Output "  - 使用 --IncludeUntracked 包含未跟踪的文件"
        Write-Output "  - 使用 --All 上传所有文件"
        exit 0
    }
    
    Write-ColorOutput Green "✅ 检测到 $($changedFiles.Count) 个文件需要同步"
    Write-Output ""
    
    if ($DryRun) {
        Write-ColorOutput Yellow "🔍 预览模式（不会实际上传）"
        Write-Output ""
        Write-Output "将上传的文件："
        $changedFiles | ForEach-Object { Write-Output "  - $_" }
        Write-Output ""
        Write-ColorOutput Green "预览完成，使用时不带 --DryRun 参数即可实际上传"
        exit 0
    }
    
    # 显示文件列表（限制显示前20个）
    $displayCount = [Math]::Min(20, $changedFiles.Count)
    Write-Output "文件列表（前 $displayCount 个）："
    $changedFiles | Select-Object -First $displayCount | ForEach-Object { 
        Write-Output "  - $_" 
    }
    if ($changedFiles.Count -gt $displayCount) {
        Write-Output "  ... 还有 $($changedFiles.Count - $displayCount) 个文件"
    }
    Write-Output ""
    
    # ==========================================
    # 步骤4: 检查上传工具
    # ==========================================
    Write-ColorOutput Blue "[4/6] 检查上传工具..."
    
    $useRsync = $false
    if (Get-Command rsync -ErrorAction SilentlyContinue) {
        $useRsync = $true
        Write-ColorOutput Green "✅ 使用 rsync 上传（推荐，支持增量同步）"
    } elseif (Get-Command scp -ErrorAction SilentlyContinue) {
        Write-ColorOutput Green "✅ 使用 scp 上传"
    } else {
        Write-ColorOutput Red "❌ 未找到 rsync 或 scp 命令"
        Write-Output "请安装以下工具之一："
        Write-Output "  1. Git for Windows (包含 scp)"
        Write-Output "  2. WSL (包含 rsync)"
        exit 1
    }
    
    # ==========================================
    # 步骤5: 上传文件
    # ==========================================
    Write-ColorOutput Blue "[5/6] 上传文件到服务器..."
    
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
    $uploadCount = 0
    $startTime = Get-Date
    
    if ($useRsync) {
        # 使用 rsync 上传（推荐）
        Write-Output "使用 rsync 同步文件..."
        
        # 创建排除文件列表
        $excludeFile = Join-Path $env:TEMP "rsync-exclude-$(Get-Date -Format 'yyyyMMddHHmmss').txt"
        $excludePatterns | Where-Object { $_ -notmatch "^\s*$" } | ForEach-Object {
            $pattern = $_ -replace '\^', '' -replace '\$', ''
            if ($pattern -match '/') {
                $pattern = "**/$pattern"
            }
            $pattern
        } | Out-File -FilePath $excludeFile -Encoding utf8
        
        if ($All) {
            # 上传所有文件（使用排除列表）
            $rsyncArgs = @(
                "-avz",
                "--progress",
                "--exclude-from=$excludeFile",
                "-e", "ssh -i `"$KeyPath`" -o StrictHostKeyChecking=no -o ConnectTimeout=10",
                "./",
                "$ServerUser@${ServerIP}:$RemotePath/"
            )
        } else {
            # 上传特定文件列表
            $fileListPath = Join-Path $env:TEMP "rsync-files-$(Get-Date -Format 'yyyyMMddHHmmss').txt"
            $changedFiles | Out-File -FilePath $fileListPath -Encoding utf8
            
            $rsyncArgs = @(
                "-avz",
                "--progress",
                "--files-from=$fileListPath",
                "--exclude-from=$excludeFile",
                "-e", "ssh -i `"$KeyPath`" -o StrictHostKeyChecking=no -o ConnectTimeout=10",
                "./",
                "$ServerUser@${ServerIP}:$RemotePath/"
            )
        }
        
        Write-Output "执行 rsync 命令..."
        & rsync @rsyncArgs
        
        if ($LASTEXITCODE -eq 0) {
            $uploadSuccess = $true
            $uploadCount = $changedFiles.Count
        } else {
            Write-ColorOutput Red "❌ rsync 上传失败 (退出码: $LASTEXITCODE)"
        }
        
        # 清理临时文件
        Remove-Item -Path $excludeFile -Force -ErrorAction SilentlyContinue
        if (Test-Path $fileListPath) {
            Remove-Item -Path $fileListPath -Force -ErrorAction SilentlyContinue
        }
    } else {
        # 使用 scp 上传
        Write-Output "使用 scp 上传文件..."
        
        $failedFiles = @()
        $totalFiles = $changedFiles.Count
        $currentFile = 0
        
        foreach ($file in $changedFiles) {
            $currentFile++
            $filePath = Join-Path $ProjectRoot $file
            
            if (Test-Path $filePath) {
                # 确保远程目录存在
                $remoteDir = Split-Path $file -Parent
                if ($remoteDir) {
                    $ensureDirCmd = "mkdir -p `"$RemotePath/$remoteDir`""
                    & ssh -i "`"$KeyPath`" -o StrictHostKeyChecking=no -o ConnectTimeout=10 $ServerUser@${ServerIP} $ensureDirCmd 2>&1 | Out-Null
                }
                
                # 上传文件
                $scpArgs = @(
                    "-i", "`"$KeyPath`"",
                    "-o", "StrictHostKeyChecking=no",
                    "-o", "ConnectTimeout=10",
                    $filePath,
                    "$ServerUser@${ServerIP}:$RemotePath/$file"
                )
                
                Write-Progress -Activity "上传文件" -Status "$file" -PercentComplete (($currentFile / $totalFiles) * 100)
                
                & scp @scpArgs 2>&1 | Out-Null
                
                if ($LASTEXITCODE -eq 0) {
                    $uploadCount++
                } else {
                    $failedFiles += $file
                    Write-ColorOutput Red "  ❌ $file"
                }
            } else {
                Write-ColorOutput Yellow "  ⚠️  文件不存在: $file"
            }
        }
        
        Write-Progress -Activity "上传文件" -Completed
        
        if ($failedFiles.Count -eq 0) {
            $uploadSuccess = $true
        } else {
            Write-ColorOutput Red "❌ $($failedFiles.Count) 个文件上传失败"
            $failedFiles | ForEach-Object { Write-Output "  - $_" }
        }
    }
    
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    # ==========================================
    # 步骤6: 验证和总结
    # ==========================================
    Write-ColorOutput Blue "[6/6] 验证上传结果..."
    
    if ($uploadSuccess) {
        Write-Output ""
        Write-ColorOutput Green "=========================================="
        Write-ColorOutput Green "✅ 同步完成！"
        Write-ColorOutput Green "=========================================="
        Write-Output ""
        Write-Output "统计信息："
        Write-Output "  - 上传文件数: $uploadCount"
        Write-Output "  - 耗时: $($duration.TotalSeconds.ToString('F2')) 秒"
        Write-Output "  - 服务器: $ServerUser@$ServerIP"
        Write-Output "  - 远程路径: $RemotePath"
        Write-Output ""
        Write-Output '下一步操作：'
        Write-Output "  1. SSH 连接: ssh -i `"$KeyPath`" $ServerUser@${ServerIP}"
        Write-Output "  2. 进入目录: cd $RemotePath"
        Write-Output "  3. 重启服务: sudo docker compose restart [service-name]"
        Write-Output ''
        Write-ColorOutput Cyan '提示：修改 requirements.txt 后，需要重新构建 Docker 镜像'
        Write-Output ""
    } else {
        Write-ColorOutput Red 'Sync failed, please check error messages'
        exit 1
    }
    
} catch {
    $errorMsg = $_.Exception.Message
    Write-Host 'Error occurred: ' -NoNewline -ForegroundColor Red
    Write-Host $errorMsg -ForegroundColor Red
    if ($_.ScriptStackTrace) {
        Write-Output $_.ScriptStackTrace
    }
    exit 1
} finally {
    Pop-Location
}


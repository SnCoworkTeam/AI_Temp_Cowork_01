# PowerShell 脚本：监控文件变更并自动上传到服务器（热加载）
# 使用方法: .\scripts\deployment\watch-and-sync.ps1 [-ServiceName <service>] [-Interval <seconds>]
#
# 功能：
# 1. 监控本地代码文件变更
# 2. 自动上传变更的文件到服务器
# 3. 可选：自动重启服务器上的Docker服务
# 4. 支持排除不需要监控的文件

param(
    [string]$ConfigFile = "remote.ssh",
    [string]$KeyFile = "enterprise_ai_platform.pem",
    [string]$RemotePath = "/opt/enterprise-ai-platform",
    [string]$ServiceName = "",  # 如果指定，只监控该服务的文件
    [int]$Interval = 2,  # 检查间隔（秒）
    [switch]$AutoRestart = $false,  # 是否自动重启服务
    [switch]$WatchAll = $false  # 监控所有文件
)

# 导入必要的模块
Add-Type -AssemblyName System.IO.FileSystemWatcher

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
Write-ColorOutput Cyan "文件监控和自动同步工具（热加载）"
Write-ColorOutput Cyan "=========================================="
Write-Output ""
Write-ColorOutput Yellow "按 Ctrl+C 停止监控"
Write-Output ""

# 获取项目根目录
$ProjectRoot = if ($PSScriptRoot) {
    Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
} else {
    $PWD
}

Push-Location $ProjectRoot

try {
    # ==========================================
    # 步骤1: 读取服务器配置
    # ==========================================
    Write-ColorOutput Blue "[1/4] 读取服务器配置..."
    
    $ServerIP = ""
    $ServerUser = "ubuntu"
    $KeyPath = ""
    
    $configPath = Join-Path $ProjectRoot $ConfigFile
    if (Test-Path $configPath) {
        $configContent = Get-Content $configPath -Raw
        
        if ($configContent -match "HostName\s+(\S+)") {
            $ServerIP = $matches[1]
        }
        if ($configContent -match "User\s+(\S+)") {
            $ServerUser = $matches[1]
        }
        if ($configContent -match "IdentityFile\s+(\S+)") {
            $KeyPath = $matches[1].Trim('"')
            if (-not [System.IO.Path]::IsPathRooted($KeyPath)) {
                $KeyPath = Join-Path $ProjectRoot $KeyPath
            }
        }
    } else {
        $ServerIP = "43.143.139.197"
    }
    
    # 查找密钥文件
    if ([string]::IsNullOrEmpty($KeyPath) -or -not (Test-Path $KeyPath)) {
        $possibleKeyPaths = @(
            Join-Path $ProjectRoot $KeyFile,
            Join-Path $env:USERPROFILE ".ssh\$KeyFile"
        )
        
        foreach ($path in $possibleKeyPaths) {
            if (Test-Path $path) {
                $KeyPath = $path
                break
            }
        }
        
        if ([string]::IsNullOrEmpty($KeyPath) -or -not (Test-Path $KeyPath)) {
            Write-ColorOutput Red "❌ 未找到密钥文件: $KeyFile"
            exit 1
        }
    }
    
    Write-Output "服务器: $ServerUser@$ServerIP"
    Write-Output "远程路径: $RemotePath"
    Write-Output ""
    
    # ==========================================
    # 步骤2: 确定监控目录
    # ==========================================
    Write-ColorOutput Blue "[2/4] 确定监控目录..."
    
    $watchDirs = @()
    $excludePatterns = @(
        "^\s*$",
        "\.git/",
        "node_modules/",
        "__pycache__/",
        "\.pyc$",
        "\.pytest_cache/",
        "^\.venv/",
        "^venv/",
        "\.next/",
        "^dist/",
        "^build/",
        "\.env",
        "\.pem$",
        "\.log$",
        "^\.vscode/",
        "^\.idea/"
    )
    
    if (-not [string]::IsNullOrEmpty($ServiceName)) {
        # 只监控指定服务的目录
        $serviceDir = Join-Path $ProjectRoot $ServiceName
        if (Test-Path $serviceDir) {
            $watchDirs += $serviceDir
            Write-ColorOutput Green "✅ 监控服务目录: $ServiceName"
        } else {
            Write-ColorOutput Red "❌ 服务目录不存在: $ServiceName"
            exit 1
        }
    } else {
        # 监控所有服务目录
        $serviceDirs = @(
            "registry-service",
            "api-gateway",
            "config-center",
            "mcp-gateway",
            "workflow-engine",
            "auth-service",
            "knowledge-base",
            "metadata-service",
            "chat-service",
            "agent-service",
            "agent-orchestrator",
            "memory-service",
            "shared_libs",
            "database"
        )
        
        foreach ($dir in $serviceDirs) {
            $fullPath = Join-Path $ProjectRoot $dir
            if (Test-Path $fullPath) {
                $watchDirs += $fullPath
            }
        }
        
        Write-ColorOutput Green "✅ 监控 $($watchDirs.Count) 个目录"
    }
    
    Write-Output ""
    
    # ==========================================
    # 步骤3: 设置文件监控
    # ==========================================
    Write-ColorOutput Blue "[3/4] 设置文件监控..."
    
    $changedFiles = [System.Collections.Generic.HashSet[string]]::new()
    $lastSyncTime = Get-Date
    
    # 设置脚本级变量供事件处理使用
    $script:ProjectRoot = $ProjectRoot
    $script:excludePatterns = $excludePatterns
    
    # 文件变更处理函数
    $actionBlock = {
        param($e)
        $filePath = $e.FullPath
        $relativePath = $filePath.Replace($script:ProjectRoot, "").TrimStart('\', '/')
        
        # 检查是否应该排除
        $shouldExclude = $false
        foreach ($pattern in $script:excludePatterns) {
            if ($relativePath -match $pattern) {
                $shouldExclude = $true
                break
            }
        }
        
        if (-not $shouldExclude) {
            $script:changedFiles.Add($relativePath) | Out-Null
            Write-Host "📝 检测到变更: $relativePath" -ForegroundColor Yellow
        }
    }
    
    # 创建文件监控器
    $watchers = @()
    foreach ($dir in $watchDirs) {
        $watcher = New-Object System.IO.FileSystemWatcher
        $watcher.Path = $dir
        $watcher.IncludeSubdirectories = $true
        $watcher.EnableRaisingEvents = $true
        $watcher.NotifyFilter = [System.IO.NotifyFilters]::FileName -bor `
                                [System.IO.NotifyFilters]::LastWrite -bor `
                                [System.IO.NotifyFilters]::DirectoryName
        
        Register-ObjectEvent -InputObject $watcher -EventName "Changed" -Action $actionBlock | Out-Null
        Register-ObjectEvent -InputObject $watcher -EventName "Created" -Action $actionBlock | Out-Null
        Register-ObjectEvent -InputObject $watcher -EventName "Deleted" -Action $actionBlock | Out-Null
        
        $watchers += $watcher
        Write-ColorOutput Green "✅ 监控目录: $dir"
    }
    
    Write-ColorOutput Green "✅ 文件监控已启动"
    Write-Output ""
    
    # ==========================================
    # 步骤4: 自动同步循环
    # ==========================================
    Write-ColorOutput Blue "[4/4] 开始自动同步..."
    Write-ColorOutput Cyan "监控中... (检查间隔: ${Interval}秒)"
    Write-Output ""
    
    $syncScript = Join-Path $PSScriptRoot "sync-to-server.ps1"
    if (-not (Test-Path $syncScript)) {
        $syncScript = Join-Path $ProjectRoot "scripts\deployment\sync-to-server.ps1"
    }
    
    while ($true) {
        Start-Sleep -Seconds $Interval
        
        # 检查是否有变更的文件
        if ($script:changedFiles.Count -gt 0) {
            $now = Get-Date
            $timeSinceLastSync = ($now - $lastSyncTime).TotalSeconds
            
            # 等待一段时间，避免频繁同步（防抖）
            if ($timeSinceLastSync -ge 5) {
                Write-Output ""
                Write-ColorOutput Cyan "=========================================="
                Write-ColorOutput Cyan "检测到 $($script:changedFiles.Count) 个文件变更，开始同步..."
                Write-ColorOutput Cyan "=========================================="
                Write-Output ""
                
                # 复制文件列表（避免在同步过程中被修改）
                $filesToSync = $script:changedFiles | ForEach-Object { $_ }
                $script:changedFiles.Clear()
                
                # 使用sync-to-server脚本上传文件
                if (Test-Path $syncScript) {
                    # 创建临时文件列表
                    $tempFileList = Join-Path $env:TEMP "sync-files-$(Get-Date -Format 'yyyyMMddHHmmss').txt"
                    $filesToSync | Out-File -FilePath $tempFileList -Encoding utf8
                    
                    # 使用rsync或scp上传文件
                    $uploadSuccess = $true
                    foreach ($file in $filesToSync) {
                        $filePath = Join-Path $ProjectRoot $file
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
                                Write-ColorOutput Green "  ✅ $file"
                            } else {
                                Write-ColorOutput Red "  ❌ $file"
                                $uploadSuccess = $false
                            }
                        }
                    }
                    
                    Remove-Item -Path $tempFileList -Force -ErrorAction SilentlyContinue
                    
                    if ($uploadSuccess) {
                        Write-ColorOutput Green "✅ 同步完成！"
                        
                        # 如果需要，自动重启服务
                        if ($AutoRestart -and -not [string]::IsNullOrEmpty($ServiceName)) {
                            Write-Output ""
                            Write-ColorOutput Yellow "重启服务: $ServiceName"
                            $restartCmd = "cd $RemotePath && docker compose restart $ServiceName"
                            & ssh -i "`"$KeyPath`" -o StrictHostKeyChecking=no -o ConnectTimeout=10 $ServerUser@${ServerIP} $restartCmd 2>&1 | Out-Null
                            
                            if ($LASTEXITCODE -eq 0) {
                                Write-ColorOutput Green "✅ 服务已重启"
                            } else {
                                Write-ColorOutput Yellow "⚠️  服务重启失败"
                            }
                        }
                    } else {
                        Write-ColorOutput Yellow "⚠️  部分文件同步失败"
                    }
                } else {
                    Write-ColorOutput Yellow "⚠️  同步脚本不存在，使用简单上传方式"
                    
                    foreach ($file in $filesToSync) {
                        $filePath = Join-Path $ProjectRoot $file
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
                                Write-ColorOutput Green "  ✅ $file"
                            } else {
                                Write-ColorOutput Red "  ❌ $file"
                            }
                        }
                    }
                }
                
                $lastSyncTime = Get-Date
                Write-Output ""
                Write-ColorOutput Cyan "继续监控... (按 Ctrl+C 停止)"
                Write-Output ""
            }
        }
    }
    
} catch {
    Write-ColorOutput Red "❌ 发生错误: $_"
    Write-Output $_.ScriptStackTrace
} finally {
    # 清理监控器
    foreach ($watcher in $watchers) {
        $watcher.EnableRaisingEvents = $false
        $watcher.Dispose()
    }
    
    # 清理事件注册
    Get-EventSubscriber | Where-Object { $_.SourceObject -is [System.IO.FileSystemWatcher] } | Unregister-Event
    
    Pop-Location
    Write-ColorOutput Yellow "监控已停止"
}


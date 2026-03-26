# 部署任务执行器 - Windows端
# 监控智能体工作目录中的任务文件并自动执行

param(
    [string]$Workdir = ".\deployment-agent\workdir",
    [int]$Interval = 5,  # 检查间隔（秒）
    [switch]$RunOnce = $false  # 只执行一次
)

$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "部署任务执行器" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "工作目录: $Workdir" -ForegroundColor Yellow
Write-Host "检查间隔: $Interval 秒" -ForegroundColor Yellow
Write-Host "按 Ctrl+C 停止" -ForegroundColor Gray
Write-Host ""

# 获取项目根目录
$ProjectRoot = if ($PSScriptRoot) {
    Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
} else {
    $PWD
}

$WorkdirPath = if ([System.IO.Path]::IsPathRooted($Workdir)) {
    $Workdir
} else {
    Join-Path $ProjectRoot $Workdir
}

if (-not (Test-Path $WorkdirPath)) {
    Write-Host "工作目录不存在: $WorkdirPath" -ForegroundColor Red
    exit 1
}

$ProcessedTasks = @{}

function Execute-Task {
    param($TaskFile)
    
    $taskId = $TaskFile.Name
    
    # 检查是否已处理
    if ($ProcessedTasks.ContainsKey($taskId)) {
        return
    }
    
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 发现新任务: $taskId" -ForegroundColor Cyan
    
    try {
        # 读取任务文件
        $task = Get-Content $TaskFile.FullName -Raw | ConvertFrom-Json
        
        Write-Host "  类型: $($task.type)" -ForegroundColor Yellow
        Write-Host "  脚本: $($task.script)" -ForegroundColor Yellow
        Write-Host "  服务: $($task.services -join ', ')" -ForegroundColor Yellow
        Write-Host ""
        
        # 切换到项目根目录
        Push-Location $ProjectRoot
        
        try {
            # 根据任务类型执行不同的脚本
            if ($task.type -eq "deployment") {
                # 执行完整部署
                $scriptPath = Join-Path $ProjectRoot "scripts\deployment\complete-sync.ps1"
                
                if (Test-Path $scriptPath) {
                    $cmd = "powershell -ExecutionPolicy Bypass -File `"$scriptPath`" -RemotePath /opt/enterprise-ai-platform"
                    
                    if ($task.services -and $task.services -ne @("all")) {
                        $cmd += " -Services $($task.services -join ',')"
                    }
                    
                    if ($task.skip_data_sync) {
                        $cmd += " -SkipDataSync"
                    }
                    
                    if ($task.skip_migration) {
                        $cmd += " -SkipMigration"
                    }
                    
                    Write-Host "  执行命令: $cmd" -ForegroundColor Gray
                    Write-Host ""
                    
                    Invoke-Expression $cmd
                    
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "  ✅ 任务执行成功" -ForegroundColor Green
                        $ProcessedTasks[$taskId] = "success"
                    } else {
                        Write-Host "  ❌ 任务执行失败 (退出码: $LASTEXITCODE)" -ForegroundColor Red
                        $ProcessedTasks[$taskId] = "failed"
                    }
                } else {
                    Write-Host "  ❌ 脚本不存在: $scriptPath" -ForegroundColor Red
                    $ProcessedTasks[$taskId] = "error"
                }
            } elseif ($task.type -eq "sync") {
                # 执行同步
                $scriptPath = Join-Path $ProjectRoot "scripts\deployment\sync-to-server.ps1"
                
                if (Test-Path $scriptPath) {
                    $services = if ($task.services) { $task.services -join " " } else { "" }
                    $cmd = "powershell -ExecutionPolicy Bypass -File `"$scriptPath`" $services"
                    
                    Write-Host "  执行命令: $cmd" -ForegroundColor Gray
                    Write-Host ""
                    
                    Invoke-Expression $cmd
                    
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "  ✅ 任务执行成功" -ForegroundColor Green
                        $ProcessedTasks[$taskId] = "success"
                    } else {
                        Write-Host "  ❌ 任务执行失败" -ForegroundColor Red
                        $ProcessedTasks[$taskId] = "failed"
                    }
                } else {
                    Write-Host "  ❌ 脚本不存在: $scriptPath" -ForegroundColor Red
                    $ProcessedTasks[$taskId] = "error"
                }
            }
        } finally {
            Pop-Location
        }
        
        Write-Host ""
        
    } catch {
        Write-Host "  ❌ 执行错误: $_" -ForegroundColor Red
        $ProcessedTasks[$taskId] = "error"
    }
}

# 主循环
try {
    while ($true) {
        # 查找任务文件
        $taskFiles = Get-ChildItem -Path $WorkdirPath -Filter "*task*.json" -ErrorAction SilentlyContinue |
            Where-Object { -not $ProcessedTasks.ContainsKey($_.Name) } |
            Sort-Object LastWriteTime
        
        foreach ($taskFile in $taskFiles) {
            Execute-Task -TaskFile $taskFile
        }
        
        if ($RunOnce) {
            break
        }
        
        Start-Sleep -Seconds $Interval
    }
} catch {
    Write-Host "`n执行器停止: $_" -ForegroundColor Red
}





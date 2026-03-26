# 测试覆盖率任务监控脚本
# 每10分钟检查一次任务状态，如果卡住则创建继续执行指令

param(
    [int]$CheckInterval = 600,  # 10分钟（秒）
    [int]$StuckThreshold = 600,  # 卡住阈值（秒）
    [string]$ProgressFile = ".coverage-progress.json",
    [string]$InstructionFile = "continue-coverage-improvement.txt",
    [switch]$RunOnce = $false
)

$ErrorActionPreference = "Continue"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptRoot)

# 日志函数
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Write-Host $logMessage
}

# 检查进度文件最后修改时间
function Check-ProgressFileActivity {
    $progressPath = Join-Path $ProjectRoot $ProgressFile
    
    if (-not (Test-Path $progressPath)) {
        return $false
    }
    
    $fileInfo = Get-Item $progressPath
    $lastWrite = $fileInfo.LastWriteTime
    $timeSinceUpdate = (Get-Date) - $lastWrite
    
    return $timeSinceUpdate.TotalSeconds -lt $StuckThreshold
}

# 检查相关进程是否运行
function Check-RunningProcesses {
    $processNames = @("python", "pytest", "coverage", "git", "ssh")
    $found = $false
    
    foreach ($procName in $processNames) {
        $processes = Get-Process | Where-Object {
            $_.ProcessName -like "*$procName*" -and
            ($_.CommandLine -like "*coverage*" -or
             $_.CommandLine -like "*test*" -or
             $_.CommandLine -like "*improve*")
        } -ErrorAction SilentlyContinue
        
        if ($processes) {
            $found = $true
            break
        }
    }
    
    return $found
}

# 检查git提交历史
function Check-GitActivity {
    try {
        Push-Location $ProjectRoot
        $recentCommits = git log --since="10 minutes ago" --oneline --grep="test\|coverage" 2>&1
        
        if ($LASTEXITCODE -eq 0 -and $recentCommits) {
            return $true
        }
        
        # 检查是否有未提交的测试文件修改
        $modifiedFiles = git status --porcelain 2>&1 | Select-String "test"
        if ($modifiedFiles) {
            return $true
        }
        
        return $false
    } catch {
        return $false
    } finally {
        Pop-Location
    }
}

# 检查任务是否卡住
function Check-IfStuck {
    Write-Log "检查任务状态..." "INFO"
    
    # 方式1: 检查进度文件活动
    $progressActive = Check-ProgressFileActivity
    Write-Log "进度文件活动: $progressActive" "DEBUG"
    
    # 方式2: 检查进程状态
    $processRunning = Check-RunningProcesses
    Write-Log "相关进程运行: $processRunning" "DEBUG"
    
    # 方式3: 检查git活动
    $gitActive = Check-GitActivity
    Write-Log "Git活动: $gitActive" "DEBUG"
    
    # 如果所有检查都显示无活动，则认为卡住
    if (-not $progressActive -and -not $processRunning -and -not $gitActive) {
        Write-Log "检测到任务可能卡住（无活动超过阈值）" "WARNING"
        return $true
    }
    
    return $false
}

# 创建继续执行指令
function Create-ContinueInstruction {
    $instructionPath = Join-Path $ProjectRoot $InstructionFile
    
    $instruction = @"
继续执行测试覆盖率提升计划，为所有未达到80%覆盖率的服务添加测试，直到所有服务都达到80%覆盖率。

当前任务状态：
- 检测到任务可能已停止
- 需要继续执行测试覆盖率提升循环
- 目标：所有服务达到80%覆盖率
- 执行环境：服务器Docker容器

请继续执行计划，不要停止，直到所有服务都达到80%覆盖率。
"@
    
    Set-Content -Path $instructionPath -Value $instruction -Force
    Write-Log "已创建继续执行指令文件: $instructionPath" "INFO"
    
    # 更新进度文件，标记需要继续
    $progressPath = Join-Path $ProjectRoot $ProgressFile
    if (Test-Path $progressPath) {
        try {
            $progress = Get-Content $progressPath | ConvertFrom-Json
            $progress.last_updated = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
            $progress.needs_continue = $true
            $progress | ConvertTo-Json -Depth 10 | Set-Content $progressPath
        } catch {
            Write-Log "更新进度文件失败: $_" "WARNING"
        }
    }
}

# 主监控循环
function Start-Monitoring {
    Write-Log "==========================================" "INFO"
    Write-Log "测试覆盖率任务监控启动" "INFO"
    Write-Log "检查间隔: $CheckInterval 秒 (10分钟)" "INFO"
    Write-Log "卡住阈值: $StuckThreshold 秒 (10分钟)" "INFO"
    Write-Log "==========================================" "INFO"
    Write-Log ""
    
    $iteration = 0
    
    while ($true) {
        $iteration++
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        
        Write-Log "--- 第 $iteration 次检查 ($timestamp) ---" "INFO"
        
        $isStuck = Check-IfStuck
        
        if ($isStuck) {
            Write-Log "检测到任务卡住，创建继续执行指令..." "WARNING"
            Create-ContinueInstruction
        } else {
            Write-Log "任务正常运行中" "INFO"
        }
        
        if ($RunOnce) {
            Write-Log "单次运行模式，退出" "INFO"
            break
        }
        
        Write-Log "等待 $CheckInterval 秒后进行下次检查..." "INFO"
        Write-Log ""
        Start-Sleep -Seconds $CheckInterval
    }
    
    Write-Log "监控结束" "INFO"
}

# 启动监控
Start-Monitoring


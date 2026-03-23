# 测试覆盖率监控和自动恢复脚本
# 每5分钟检查一次，如果停止则自动继续执行

param(
    [int]$CheckInterval = 300,  # 5分钟（秒）
    [string]$LogFile = "coverage-monitor.log",
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
    Add-Content -Path (Join-Path $ProjectRoot $LogFile) -Value $logMessage
}

# 检查覆盖率状态
function Check-CoverageStatus {
    Write-Log "检查测试覆盖率状态..."
    
    $checkScript = Join-Path $ScriptRoot "check-coverage-status.py"
    if (-not (Test-Path $checkScript)) {
        Write-Log "覆盖率检查脚本不存在: $checkScript" "ERROR"
        return $null
    }
    
    try {
        $result = & python $checkScript 2>&1
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -eq 0) {
            Write-Log "所有服务已达到80%覆盖率！" "SUCCESS"
            return @{
                "all_above_80" = $true
                "results" = $result | ConvertFrom-Json
            }
        } else {
            $results = $result | ConvertFrom-Json
            $needsImprovement = $results.PSObject.Properties | Where-Object {
                $_.Value.coverage -lt 80 -and $_.Value.status -ne "NO_TESTS"
            }
            
            Write-Log "需要改进的服务数量: $($needsImprovement.Count)" "WARNING"
            return @{
                "all_above_80" = $false
                "results" = $results
                "needs_improvement" = $needsImprovement
            }
        }
    } catch {
        Write-Log "检查覆盖率时出错: $_" "ERROR"
        return $null
    }
}

# 检查是否有正在运行的测试覆盖率提升进程
function Check-RunningProcess {
    $processName = "improve-coverage"
    $processes = Get-Process | Where-Object {
        $_.ProcessName -like "*python*" -and 
        $_.CommandLine -like "*improve-coverage*"
    } -ErrorAction SilentlyContinue
    
    return $processes.Count -gt 0
}

# 执行测试覆盖率提升
function Start-CoverageImprovement {
    param([string]$Service = $null)
    
    Write-Log "开始执行测试覆盖率提升..." "INFO"
    
    $improveScript = Join-Path $ScriptRoot "improve-coverage.py"
    if (-not (Test-Path $improveScript)) {
        Write-Log "覆盖率提升脚本不存在: $improveScript" "ERROR"
        return $false
    }
    
    try {
        if ($Service) {
            Write-Log "为服务 $Service 提升覆盖率..." "INFO"
            $result = & python $improveScript --service $Service 2>&1
        } else {
            Write-Log "为所有服务提升覆盖率..." "INFO"
            $result = & python $improveScript --all 2>&1
        }
        
        Write-Log "覆盖率提升执行完成" "INFO"
        Write-Log "输出: $result" "DEBUG"
        return $true
    } catch {
        Write-Log "执行覆盖率提升时出错: $_" "ERROR"
        return $false
    }
}

# 发送继续执行指令（模拟用户输入）
function Send-ContinueInstruction {
    Write-Log "检测到停止，发送继续执行指令..." "INFO"
    
    # 创建继续执行的指令文件
    $instructionFile = Join-Path $ProjectRoot "continue-coverage-improvement.txt"
    $instruction = @"
继续执行测试覆盖率提升计划，为所有未达到80%覆盖率的服务添加测试，直到所有服务都达到80%覆盖率。
"@
    
    Set-Content -Path $instructionFile -Value $instruction -Force
    Write-Log "已创建继续执行指令文件: $instructionFile" "INFO"
    
    # 如果是在Cursor环境中，可以尝试通过API发送消息
    # 这里我们创建一个标记文件，让主脚本检测
    $markerFile = Join-Path $ProjectRoot ".coverage-improvement-active"
    Set-Content -Path $markerFile -Value (Get-Date -Format "yyyy-MM-dd HH:mm:ss") -Force
}

# 主监控循环
function Start-Monitoring {
    Write-Log "==========================================" "INFO"
    Write-Log "测试覆盖率监控启动" "INFO"
    Write-Log "检查间隔: $CheckInterval 秒" "INFO"
    Write-Log "==========================================" "INFO"
    
    $iteration = 0
    
    while ($true) {
        $iteration++
        Write-Log "--- 第 $iteration 次检查 ---" "INFO"
        
        # 检查覆盖率状态
        $status = Check-CoverageStatus
        
        if ($null -eq $status) {
            Write-Log "无法获取覆盖率状态，跳过本次检查" "WARNING"
        } elseif ($status.all_above_80) {
            Write-Log "✓ 所有服务已达到80%覆盖率！任务完成！" "SUCCESS"
            break
        } else {
            Write-Log "检测到需要改进的服务" "WARNING"
            
            # 检查是否有正在运行的进程
            $isRunning = Check-RunningProcess
            
            if (-not $isRunning) {
                Write-Log "未检测到正在运行的覆盖率提升进程" "INFO"
                Write-Log "启动覆盖率提升..." "INFO"
                
                # 发送继续执行指令
                Send-ContinueInstruction
                
                # 启动覆盖率提升（在后台运行）
                $improveScript = Join-Path $ScriptRoot "improve-coverage.py"
                Start-Process -FilePath "python" -ArgumentList $improveScript, "--all" -WindowStyle Hidden
                
                Write-Log "已启动覆盖率提升进程" "INFO"
            } else {
                Write-Log "覆盖率提升进程正在运行中..." "INFO"
            }
        }
        
        if ($RunOnce) {
            Write-Log "单次运行模式，退出" "INFO"
            break
        }
        
        Write-Log "等待 $CheckInterval 秒后进行下次检查..." "INFO"
        Start-Sleep -Seconds $CheckInterval
    }
    
    Write-Log "监控结束" "INFO"
}

# 启动监控
Start-Monitoring


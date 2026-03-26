# 测试覆盖率提升主循环
# 持续运行直到所有服务达到80%覆盖率

param(
    [int]$LoopInterval = 600,
    [string]$ProgressFile = ".coverage-progress.json",
    [string]$ConfigFile = "remote.ssh",
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Continue"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptRoot)

$SERVICES = @(
    "auth-service",
    "knowledge-base",
    "metadata-service",
    "workflow-engine",
    "mcp-gateway",
    "database"
)

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Write-Host $logMessage
}

function Update-Progress {
    param(
        [string]$Service = $null,
        [float]$Coverage = 0,
        [string]$Status = "processing"
    )
    
    $progressPath = Join-Path $ProjectRoot $ProgressFile
    
    try {
        if (Test-Path $progressPath) {
            $progress = Get-Content $progressPath | ConvertFrom-Json
        } else {
            $templatePath = Join-Path $ScriptRoot "..\..\.coverage-progress.json"
            if (Test-Path $templatePath) {
                $progress = Get-Content $templatePath | ConvertFrom-Json
            } else {
                return
            }
        }
        
        $progress.last_updated = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        if ($null -ne $progress.iteration) {
            $progress.iteration = ($progress.iteration + 1)
        } else {
            $progress.iteration = 1
        }
        
        if ($Service) {
            $progress.services.$Service.coverage = $Coverage
            $progress.services.$Service.status = $Status
            $progress.services.$Service.last_check = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
            $progress.current_service = $Service
        }
        
        $progress | ConvertTo-Json -Depth 10 | Set-Content $progressPath
    } catch {
        Write-Log "更新进度文件失败: $_" "ERROR"
    }
}

function Check-CoverageFromServer {
    Write-Log "从服务器检查覆盖率状态..." "INFO"
    
    $SessionScript = Join-Path (Split-Path $ScriptRoot -Parent) "deployment\ssh-session-manager.ps1"
    $RemotePath = "/opt/enterprise-ai-platform"
    $ConfigPath = Join-Path $ProjectRoot $ConfigFile
    
    if (-not (Test-Path $SessionScript)) {
        Write-Log "SSH会话管理器未找到，跳过服务器检查" "WARNING"
        return $null
    }
    
    $closeSSH = {
        param($config)
        try {
            if (Test-Path $config) {
                ssh -F $config -O exit enterprise-ai-server 2>&1 | Out-Null
                Start-Sleep -Seconds 2
            }
        } catch {
        }
    }
    
    $checkCommand = "cd $RemotePath; bash scripts/test-coverage/check-coverage-server.sh"
    $maxRetries = 3
    $retryCount = 0
    $output = $null
    
    while ($retryCount -lt $maxRetries) {
        $retryCount++
        
        if ($retryCount -gt 1) {
            Write-Log "第 $retryCount 次尝试连接服务器..." "WARNING"
            Write-Log "关闭现有SSH连接..." "INFO"
            & $closeSSH $ConfigPath
            Start-Sleep -Seconds 3
        }
        
        try {
            # 使用ssh-exec-safe脚本，避免卡住
            $safeScript = Join-Path (Split-Path $ScriptRoot -Parent) "deployment\ssh-exec-safe.ps1"
            if (Test-Path $safeScript) {
                $fullCommand = "cd $RemotePath; bash scripts/test-coverage/check-coverage-server.sh"
                try {
                    $output = & powershell -ExecutionPolicy Bypass -File $safeScript -Command $fullCommand -Timeout 30 2>&1
                    if ($LASTEXITCODE -ne 0 -and $null -eq $output) {
                        $output = $null
                    }
                } catch {
                    Write-Log "SSH执行出错: $_" "WARNING"
                    $output = $null
                }
            } else {
                # 降级方案：直接使用ssh，但设置超时
                $fullCommand = "cd $RemotePath; bash scripts/test-coverage/check-coverage-server.sh"
                $job = Start-Job -ScriptBlock {
                    param($config, $cmd)
                    ssh -F $config -o ConnectTimeout=10 -o ServerAliveInterval=5 -o ServerAliveCountMax=3 enterprise-ai-server $cmd 2>&1
                } -ArgumentList $ConfigPath, $fullCommand
                
                $completed = Wait-Job $job -Timeout 30
                if ($completed) {
                    $output = Receive-Job $job
                    Remove-Job $job -ErrorAction SilentlyContinue
                } else {
                    Write-Log "服务器连接超时（30秒）" "WARNING"
                    Stop-Job $job -ErrorAction SilentlyContinue
                    Remove-Job $job -ErrorAction SilentlyContinue
                    $output = $null
                }
            }
            
            if ($null -ne $output -and $output -ne "") {
                break
            } else {
                if ($retryCount -ge $maxRetries) {
                    Write-Log "已达到最大重试次数，跳过服务器检查" "ERROR"
                    return $null
                }
            }
        } catch {
            Write-Log "服务器连接失败: $_" "WARNING"
            
            if ($retryCount -ge $maxRetries) {
                Write-Log "已达到最大重试次数，跳过服务器检查" "ERROR"
                return $null
            }
        }
    }
    
    $remoteStatusFile = "$RemotePath/.coverage-status.json"
    $localStatusFile = Join-Path $ProjectRoot ".coverage-status.json"
    
    if (Test-Path $ConfigPath) {
        scp -F $ConfigPath "enterprise-ai-server:$remoteStatusFile" $localStatusFile 2>&1 | Out-Null
    }
    
    if (Test-Path $localStatusFile) {
        try {
            $status = Get-Content $localStatusFile | ConvertFrom-Json
            return $status
        } catch {
            Write-Log "解析覆盖率状态失败: $_" "ERROR"
        }
    }
    
    return $null
}

function Generate-TestFiles {
    param([string]$Service)
    
    Write-Log "为 $Service 生成测试文件..." "INFO"
    
    $improveScript = Join-Path $ScriptRoot "improve-coverage.py"
    if (-not (Test-Path $improveScript)) {
        Write-Log "测试生成脚本不存在" "ERROR"
        return $false
    }
    
    try {
        $result = & python $improveScript --service $Service 2>&1
        Write-Log "测试文件生成完成" "INFO"
        return $true
    } catch {
        Write-Log "生成测试文件失败: $_" "ERROR"
        return $false
    }
}

function Sync-TestsToServer {
    Write-Log "同步测试文件到服务器..." "INFO"
    
    $syncScript = Join-Path $ScriptRoot "sync-tests-to-server.ps1"
    if (-not (Test-Path $syncScript)) {
        Write-Log "同步脚本不存在" "ERROR"
        return $false
    }
    
    try {
        if ($DryRun) {
            & powershell -ExecutionPolicy Bypass -File $syncScript -DryRun
        } else {
            & powershell -ExecutionPolicy Bypass -File $syncScript
        }
        Write-Log "测试文件同步完成" "INFO"
        return $true
    } catch {
        Write-Log "同步失败: $_" "ERROR"
        return $false
    }
}

function Run-TestsInDocker {
    Write-Log "在服务器Docker中执行测试..." "INFO"
    
    $SessionScript = Join-Path (Split-Path $ScriptRoot -Parent) "deployment\ssh-session-manager.ps1"
    $RemotePath = "/opt/enterprise-ai-platform"
    $ConfigPath = Join-Path $ProjectRoot $ConfigFile
    
    if (-not (Test-Path $SessionScript)) {
        Write-Log "SSH会话管理器未找到" "ERROR"
        return $false
    }
    
    $closeSSH = {
        param($config)
        try {
            if (Test-Path $config) {
                ssh -F $config -O exit enterprise-ai-server 2>&1 | Out-Null
                Start-Sleep -Seconds 2
            }
        } catch {
        }
    }
    
    $testCommand = "cd $RemotePath; bash scripts/test-coverage/run-tests-in-docker.sh"
    $maxRetries = 3
    $retryCount = 0
    
    while ($retryCount -lt $maxRetries) {
        $retryCount++
        
        if ($retryCount -gt 1) {
            Write-Log "第 $retryCount 次尝试连接服务器..." "WARNING"
            Write-Log "关闭现有SSH连接..." "INFO"
            & $closeSSH $ConfigPath
            Start-Sleep -Seconds 3
        }
        
        try {
            # 使用ssh-exec-safe脚本，避免卡住
            $safeScript = Join-Path (Split-Path $ScriptRoot -Parent) "deployment\ssh-exec-safe.ps1"
            if (Test-Path $safeScript) {
                $fullCommand = "cd $RemotePath; bash scripts/test-coverage/run-tests-in-docker.sh"
                try {
                    $output = & powershell -ExecutionPolicy Bypass -File $safeScript -Command $fullCommand -Timeout 60 2>&1
                    
                    if ($null -ne $output -and $output.Count -gt 0) {
                        Write-Log "测试执行完成" "INFO"
                        Write-Log ($output -join "`n")
                        return $true
                    }
                } catch {
                    Write-Log "SSH执行出错: $_" "WARNING"
                }
            } else {
                # 降级方案：直接使用ssh，但设置超时
                $fullCommand = "cd $RemotePath; bash scripts/test-coverage/run-tests-in-docker.sh"
                $job = Start-Job -ScriptBlock {
                    param($config, $cmd)
                    ssh -F $config -o ConnectTimeout=10 -o ServerAliveInterval=5 -o ServerAliveCountMax=3 enterprise-ai-server $cmd 2>&1
                } -ArgumentList $ConfigPath, $fullCommand
                
                $completed = Wait-Job $job -Timeout 60
                if ($completed) {
                    $output = Receive-Job $job
                    Remove-Job $job -ErrorAction SilentlyContinue
                    
                    Write-Log "测试执行完成" "INFO"
                    Write-Log $output
                    return $true
                } else {
                    Write-Log "服务器连接超时（60秒）" "WARNING"
                    Stop-Job $job -ErrorAction SilentlyContinue
                    Remove-Job $job -ErrorAction SilentlyContinue
                }
            }
            
            if ($retryCount -ge $maxRetries) {
                Write-Log "已达到最大重试次数，测试执行失败" "ERROR"
                return $false
            }
        } catch {
            Write-Log "服务器连接失败: $_" "WARNING"
            
            if ($retryCount -ge $maxRetries) {
                Write-Log "已达到最大重试次数，测试执行失败" "ERROR"
                return $false
            }
        }
    }
    
    return $false
}

function Fix-TestErrors {
    Write-Log "分析并修复测试错误..." "INFO"
    
    $fixScript = Join-Path $ScriptRoot "auto-fix-tests.py"
    if (-not (Test-Path $fixScript)) {
        Write-Log "修复脚本不存在" "ERROR"
        return $false
    }
    
    $testResultsFile = Join-Path $ProjectRoot ".test-results.json"
    if (Test-Path $testResultsFile) {
        try {
            & python $fixScript --test-results $testResultsFile
            Write-Log "错误修复完成" "INFO"
            return $true
        } catch {
            Write-Log "修复失败: $_" "ERROR"
        }
    }
    
    return $false
}

function Start-ImprovementLoop {
    $separator = "=========================================="
    Write-Log $separator "INFO"
    Write-Log "测试覆盖率提升循环启动" "INFO"
    Write-Log "目标: 所有服务达到80%覆盖率" "INFO"
    Write-Log "循环间隔: $LoopInterval 秒 (10分钟)" "INFO"
    Write-Log $separator "INFO"
    Write-Log ""
    
    # 设置全局错误处理，避免卡住
    $global:ErrorActionPreference = "Continue"
    $script:lastActivityTime = Get-Date
    
    $progressPath = Join-Path $ProjectRoot $ProgressFile
    if (-not (Test-Path $progressPath)) {
        $templatePath = Join-Path $ScriptRoot "..\..\.coverage-progress.json"
        if (Test-Path $templatePath) {
            Copy-Item $templatePath $progressPath
        }
    }
    
    Update-Progress -Status "starting"
    $progress = Get-Content $progressPath | ConvertFrom-Json
    $progress.start_time = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    $progress | ConvertTo-Json -Depth 10 | Set-Content $progressPath
    
    $iteration = 0
    $maxIterations = 10000
    
    while ($iteration -lt $maxIterations) {
        $iteration++
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $script:lastActivityTime = Get-Date
        
        # 检查是否卡住（超过30分钟无活动）
        $timeSinceLastActivity = (Get-Date) - $script:lastActivityTime
        if ($timeSinceLastActivity.TotalMinutes -gt 30) {
            Write-Log "检测到脚本可能卡住，重启循环..." "WARNING"
            $script:lastActivityTime = Get-Date
        }
        
        Write-Log $separator "INFO"
        Write-Log "第 $iteration 轮循环 ($timestamp)" "INFO"
        Write-Log $separator "INFO"
        Write-Log ""
        
        Write-Log "[1/6] 检查覆盖率状态..." "INFO"
        $script:lastActivityTime = Get-Date
        try {
            $coverageStatus = Check-CoverageFromServer
        } catch {
            Write-Log "检查覆盖率时出错: $_" "ERROR"
            $coverageStatus = $null
        }
        
        # 如果无法获取覆盖率状态，使用默认值继续执行
        if ($null -eq $coverageStatus) {
            Write-Log "无法从服务器获取覆盖率状态，使用默认值继续执行..." "WARNING"
            Write-Log "将为首个服务生成测试文件..." "INFO"
            
            # 创建默认的覆盖率状态
            $coverageStatus = @{
                all_above_80 = $false
                services = @{}
            }
            
            foreach ($service in $SERVICES) {
                $coverageStatus.services[$service] = @{
                    coverage = 0
                    status = "not_checked"
                    total = 0
                    covered = 0
                    missed = 0
                }
            }
        }
        
        if ($coverageStatus.all_above_80) {
            Write-Log "✓ 所有服务已达到80%覆盖率！任务完成！" "SUCCESS"
            Update-Progress -Status "completed"
            break
        }
        
        Write-Log "[2/6] 识别需要改进的服务..." "INFO"
        $needsImprovement = @()
        
        foreach ($service in $SERVICES) {
            $serviceData = $coverageStatus.services.$service
            $currentCoverage = 0
            if ($null -ne $serviceData.coverage) {
                $currentCoverage = $serviceData.coverage
            }
            
            if ($currentCoverage -lt 80 -and $serviceData.status -ne "container_not_running") {
                $gap = 80 - $currentCoverage
                $needsImprovement += @{
                    "name" = $service
                    "coverage" = $currentCoverage
                    "gap" = $gap
                }
                Write-Log "  - $service : $currentCoverage% (需要 +$gap%)" "WARNING"
            }
        }
        
        # 如果没有需要改进的服务，检查是否真的都达到80%
        if ($needsImprovement.Count -eq 0) {
            $allAbove80 = $true
            foreach ($service in $SERVICES) {
                $serviceData = $coverageStatus.services.$service
                $coverage = 0
                if ($null -ne $serviceData.coverage) {
                    $coverage = $serviceData.coverage
                }
                if ($coverage -lt 80) {
                    $allAbove80 = $false
                    break
                }
            }
            
            if ($allAbove80) {
                Write-Log "所有服务已达到80%覆盖率！" "SUCCESS"
                break
            } else {
                # 如果无法确定，默认选择第一个服务
                Write-Log "无法确定覆盖率，默认处理第一个服务..." "WARNING"
                $needsImprovement = @(@{
                    "name" = $SERVICES[0]
                    "coverage" = 0
                    "gap" = 80
                })
            }
        }
        
        # 选择目标服务
        if ($needsImprovement.Count -gt 0) {
            $targetService = ($needsImprovement | Sort-Object coverage | Select-Object -First 1).name
        } else {
            $targetService = $SERVICES[0]
        }
        
        Write-Log "目标服务: $targetService" "INFO"
        Write-Log ""
        
        Write-Log "[3/6] 生成测试文件..." "INFO"
        $script:lastActivityTime = Get-Date
        try {
            Generate-TestFiles -Service $targetService
            Update-Progress -Service $targetService -Status "generating_tests"
        } catch {
            Write-Log "生成测试文件时出错: $_" "ERROR"
        }
        Write-Log ""
        
        Write-Log "[4/6] 同步测试文件到服务器..." "INFO"
        $script:lastActivityTime = Get-Date
        try {
            Sync-TestsToServer
            Update-Progress -Service $targetService -Status "syncing"
        } catch {
            Write-Log "同步测试文件时出错: $_" "ERROR"
        }
        Write-Log ""
        
        Write-Log "[5/6] 在服务器Docker中执行测试..." "INFO"
        $script:lastActivityTime = Get-Date
        try {
            Run-TestsInDocker
            Update-Progress -Service $targetService -Status "testing"
        } catch {
            Write-Log "执行测试时出错: $_" "ERROR"
        }
        Write-Log ""
        
        Write-Log "[6/6] 自动修复测试错误..." "INFO"
        $script:lastActivityTime = Get-Date
        try {
            Fix-TestErrors
            Update-Progress -Service $targetService -Status "fixing"
        } catch {
            Write-Log "修复测试错误时出错: $_" "ERROR"
        }
        Write-Log ""
        
        Update-Progress -Service $targetService -Coverage $coverageStatus.services.$targetService.coverage
        
        Write-Log "本轮循环完成，等待 $LoopInterval 秒后继续..." "INFO"
        Write-Log ""
        
        Start-Sleep -Seconds $LoopInterval
    }
    
    Write-Log $separator "INFO"
    Write-Log "测试覆盖率提升循环结束" "INFO"
    Write-Log $separator "INFO"
}

Start-ImprovementLoop

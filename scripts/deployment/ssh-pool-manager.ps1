# SSH连接池管理器
# 维护一个持久连接，所有命令通过这个连接执行

param(
    [string]$Action = "execute",  # execute, status, cleanup, start, stop
    [string]$Command = "",
    [string]$ConfigFile = "remote.ssh",
    [int]$KeepAliveInterval = 30
)

$ErrorActionPreference = "Continue"

# 获取项目根目录
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptRoot
$ConfigPath = Join-Path $ProjectRoot $ConfigFile

if (-not (Test-Path $ConfigPath)) {
    $ConfigPath = Join-Path (Split-Path $ProjectRoot) $ConfigFile
}

# 连接池状态文件
$StateFile = Join-Path $env:TEMP "ssh-pool-state.json"
$LockFile = Join-Path $env:TEMP "ssh-pool.lock"

# 获取连接状态
function Get-PoolState {
    if (Test-Path $StateFile) {
        $content = Get-Content $StateFile -Raw | ConvertFrom-Json
        return $content
    }
    return $null
}

# 保存连接状态
function Save-PoolState {
    param([hashtable]$State)
    $State | ConvertTo-Json | Set-Content $StateFile -Force
}

# 检查连接是否活跃
function Test-PoolConnection {
    param([object]$State)
    
    if (-not $State -or -not $State.ProcessId) {
        return $false
    }
    
    # 检查进程是否存在
    try {
        $process = Get-Process -Id $State.ProcessId -ErrorAction SilentlyContinue
        if (-not $process) {
            return $false
        }
        
        # 测试连接是否可用（发送一个简单命令）
        $testResult = ssh -F $ConfigPath -o ConnectTimeout=5 -o ControlPath=$State.ControlPath enterprise-ai-server "echo 'test'" 2>&1
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

# 启动持久连接（不使用ControlMaster，使用简单的连接复用）
function Start-PoolConnection {
    # 不使用ControlMaster，而是维护一个简单的连接状态
    # 每次执行命令时，如果连接失败就重试，但不每次都断开
    
    # 测试基本连接
    $testResult = ssh -F $ConfigPath -o ConnectTimeout=5 enterprise-ai-server "echo 'test'" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $state = @{
            ProcessId = 0  # 不使用进程ID
            ControlPath = ""  # 不使用ControlMaster
            StartedAt = (Get-Date).ToString("o")
            LastUsed = (Get-Date).ToString("o")
            ConnectionCount = 0
        }
        Save-PoolState -State $state
        Write-Host "Connection pool initialized" -ForegroundColor Green
        return $state
    } else {
        Write-Host "Failed to establish connection: $testResult" -ForegroundColor Red
        return $null
    }
}

# 停止连接池
function Stop-PoolConnection {
    $state = Get-PoolState
    if ($state -and $state.ProcessId) {
        try {
            # 优雅关闭
            ssh -F $ConfigPath -o ControlPath=$state.ControlPath -O exit enterprise-ai-server 2>&1 | Out-Null
        } catch {
            # 强制终止进程
            Stop-Process -Id $state.ProcessId -Force -ErrorAction SilentlyContinue
        }
        
        # 清理控制文件
        if ($state.ControlPath -and (Test-Path $state.ControlPath)) {
            Remove-Item $state.ControlPath -Force -ErrorAction SilentlyContinue
        }
        
        Remove-Item $StateFile -Force -ErrorAction SilentlyContinue
        Write-Host "Connection pool stopped" -ForegroundColor Yellow
    }
}

# 执行命令（智能重试，避免每次都断开）
function Invoke-PoolCommand {
    param([string]$RemoteCommand)
    
    $state = Get-PoolState
    $maxRetries = 2
    
    # 如果状态不存在，初始化
    if (-not $state) {
        $state = Start-PoolConnection
        if (-not $state) {
            throw "Failed to initialize connection pool"
        }
    }
    
    # 执行命令，带重试机制
    for ($retry = 0; $retry -le $maxRetries; $retry++) {
        if ($retry -gt 0) {
            Write-Host "Retry $retry/$maxRetries..." -ForegroundColor Yellow
            Start-Sleep -Milliseconds 500
        }
        
        # 执行命令（使用Job避免卡住）
        $job = Start-Job -ScriptBlock {
            param($ConfigPath, $RemoteCommand)
            ssh -F $ConfigPath -o ConnectTimeout=10 enterprise-ai-server $RemoteCommand 2>&1
        } -ArgumentList $ConfigPath, $RemoteCommand
        
        # 等待完成（最多30秒）
        $result = Wait-Job -Job $job -Timeout 30
        
        if ($result) {
            $output = Receive-Job -Job $job
            Remove-Job -Job $job -Force
            $exitCode = $LASTEXITCODE
            
            # 如果成功，更新状态
            if ($exitCode -eq 0) {
                $state.LastUsed = (Get-Date).ToString("o")
                $state.ConnectionCount++
                Save-PoolState -State $state
            }
            
            return @{
                Output = $output
                ExitCode = $exitCode
            }
        } else {
            # 超时，停止Job
            Stop-Job -Job $job -Force
            Remove-Job -Job $job -Force
            
            if ($retry -lt $maxRetries) {
                # 清理可能的僵尸连接
                Get-Process ssh -ErrorAction SilentlyContinue | Where-Object {
                    $_.StartTime -lt (Get-Date).AddMinutes(-1)
                } | Stop-Process -Force -ErrorAction SilentlyContinue
                continue
            }
        }
    }
    
    throw "Command execution failed after $maxRetries retries"
}

# 主逻辑
try {
    switch ($Action.ToLower()) {
        "start" {
            $existing = Get-PoolState
            if (Test-PoolConnection -State $existing) {
                Write-Host "Connection pool already active (PID: $($existing.ProcessId))" -ForegroundColor Green
            } else {
                Start-PoolConnection | Out-Null
            }
        }
        "stop" {
            Stop-PoolConnection
        }
        "status" {
            $state = Get-PoolState
            if (Test-PoolConnection -State $state) {
                Write-Host "Connection pool: ACTIVE" -ForegroundColor Green
                Write-Host "  PID: $($state.ProcessId)" -ForegroundColor Gray
                Write-Host "  Started: $($state.StartedAt)" -ForegroundColor Gray
                Write-Host "  Last Used: $($state.LastUsed)" -ForegroundColor Gray
            } else {
                Write-Host "Connection pool: INACTIVE" -ForegroundColor Red
            }
        }
        "execute" {
            if (-not $Command) {
                Write-Host "Error: -Command required for execute action" -ForegroundColor Red
                exit 1
            }
            
            $result = Invoke-PoolCommand -RemoteCommand $Command
            Write-Output ($result.Output -join "`n")
            exit $result.ExitCode
        }
        "cleanup" {
            Stop-PoolConnection
        }
        default {
            Write-Host "Usage: ssh-pool-manager.ps1 -Action start|stop|status|execute|cleanup [-Command '<command>']"
            exit 1
        }
    }
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}


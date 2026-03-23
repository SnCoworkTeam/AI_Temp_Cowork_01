# SSH会话管理器
# 使用长期运行的SSH进程，通过stdin/stdout进行交互

param(
    [string]$Action = "execute",  # execute, status, restart, stop
    [string]$Command = "",
    [string]$ConfigFile = "remote.ssh"
)

$ErrorActionPreference = "Continue"

# 获取项目根目录
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptRoot
$ConfigPath = Join-Path $ProjectRoot $ConfigFile

if (-not (Test-Path $ConfigPath)) {
    $ConfigPath = Join-Path (Split-Path $ProjectRoot) $ConfigFile
}

# 会话状态文件
$SessionFile = Join-Path $env:TEMP "ssh-session.pid"
$LockFile = Join-Path $env:TEMP "ssh-session.lock"

# 获取会话进程
function Get-SessionProcess {
    if (Test-Path $SessionFile) {
        $processId = Get-Content $SessionFile -ErrorAction SilentlyContinue
        if ($processId) {
            try {
                $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
                if ($process -and -not $process.HasExited) {
                    return $process
                }
            } catch {
                # 进程不存在
            }
        }
    }
    return $null
}

# 启动SSH会话（使用交互式shell保持连接）
function Start-SSHSession {
    # 检查是否已有会话
    $existing = Get-SessionProcess
    if ($existing) {
        Write-Host "SSH session already running (PID: $($existing.Id))" -ForegroundColor Green
        return $existing
    }
    
    # 清理旧的锁文件
    if (Test-Path $LockFile) {
        Remove-Item $LockFile -Force -ErrorAction SilentlyContinue
    }
    
    # 启动SSH进程（使用bash保持连接）
    # 使用 -t 强制分配伪终端，保持连接活跃
    $sshArgs = @(
        "-F", $ConfigPath,
        "-t",  # 强制分配伪终端
        "-o", "ServerAliveInterval=30",
        "-o", "ServerAliveCountMax=5",
        "-o", "TCPKeepAlive=yes",
        "enterprise-ai-server",
        "bash -c 'while true; do sleep 60; done'"  # 保持连接活跃
    )
    
    try {
        $process = Start-Process -FilePath "ssh" -ArgumentList $sshArgs -PassThru -WindowStyle Hidden
        
        # 等待进程启动
        Start-Sleep -Seconds 2
        
        # 检查进程是否还在运行
        if (-not $process.HasExited) {
            $process.Id | Set-Content $SessionFile -Force
            Write-Host "SSH session started (PID: $($process.Id))" -ForegroundColor Green
            return $process
        } else {
            Write-Host "SSH session failed to start" -ForegroundColor Red
            return $null
        }
    } catch {
        Write-Host "Failed to start SSH session: $_" -ForegroundColor Red
        return $null
    }
}

# 停止SSH会话
function Stop-SSHSession {
    $process = Get-SessionProcess
    if ($process) {
        try {
            $process.Kill()
            Write-Host "SSH session stopped (PID: $($process.Id))" -ForegroundColor Yellow
        } catch {
            Write-Host "Failed to stop SSH session: $_" -ForegroundColor Red
        }
    }
    
    if (Test-Path $SessionFile) {
        Remove-Item $SessionFile -Force -ErrorAction SilentlyContinue
    }
}

# 执行命令（通过新的SSH连接，但复用配置）
function Invoke-SSHCommand {
    param([string]$RemoteCommand)
    
    # 确保会话存在（用于保持连接活跃）
    $session = Start-SSHSession
    
    # 执行实际命令（使用新连接，但配置相同）
    # 由于有活跃会话，新连接应该更快
    $output = ssh -F $ConfigPath -o ConnectTimeout=10 enterprise-ai-server $RemoteCommand 2>&1
    $exitCode = $LASTEXITCODE
    
    return @{
        Output = $output
        ExitCode = $exitCode
    }
}

# 主逻辑
try {
    switch ($Action.ToLower()) {
        "start" {
            Start-SSHSession | Out-Null
        }
        "stop" {
            Stop-SSHSession
        }
        "restart" {
            Stop-SSHSession
            Start-Sleep -Seconds 1
            Start-SSHSession | Out-Null
        }
        "status" {
            $process = Get-SessionProcess
            if ($process) {
                Write-Host "SSH session: ACTIVE (PID: $($process.Id))" -ForegroundColor Green
                Write-Host "  Started: $($process.StartTime)" -ForegroundColor Gray
                Write-Host "  Uptime: $((Get-Date) - $process.StartTime)" -ForegroundColor Gray
            } else {
                Write-Host "SSH session: INACTIVE" -ForegroundColor Red
            }
        }
        "execute" {
            if (-not $Command) {
                Write-Host "Error: -Command required for execute action" -ForegroundColor Red
                exit 1
            }
            
            $result = Invoke-SSHCommand -RemoteCommand $Command
            Write-Output ($result.Output -join "`n")
            exit $result.ExitCode
        }
        default {
            Write-Host "Usage: ssh-session-manager.ps1 -Action start|stop|restart|status|execute [-Command '<command>']"
            exit 1
        }
    }
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}


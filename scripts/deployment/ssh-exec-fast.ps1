# 快速SSH执行脚本
# 每次执行前清理，使用超时，确保不卡住

param(
    [string]$Command,
    [string]$ConfigFile = "remote.ssh",
    [int]$Timeout = 120
)

$ErrorActionPreference = "Stop"

# 获取项目根目录
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptRoot
$ConfigPath = Join-Path $ProjectRoot $ConfigFile

if (-not (Test-Path $ConfigPath)) {
    $ConfigPath = Join-Path (Split-Path $ProjectRoot) $ConfigFile
}

if (-not $Command) {
    Write-Host "Usage: ssh-exec-fast.ps1 -Command '<command>'"
    exit 1
}

# 快速清理旧连接（不等待）
function Clear-OldConnections {
    # 清理ControlMaster文件
    $controlDir = Join-Path $env:USERPROFILE ".ssh"
    if (Test-Path $controlDir) {
        Get-ChildItem -Path $controlDir -Filter "control-*" -ErrorAction SilentlyContinue | 
            Remove-Item -Force -ErrorAction SilentlyContinue
    }
    
    # 清理超过1分钟的SSH进程（快速，不等待）
    Get-Process ssh -ErrorAction SilentlyContinue | Where-Object {
        $_.StartTime -lt (Get-Date).AddMinutes(-1)
    } | Stop-Process -Force -ErrorAction SilentlyContinue | Out-Null
}

# 执行命令（带超时和重试）
function Invoke-SSHFast {
    param([string]$RemoteCommand, [int]$MaxTimeout)
    
    # 快速清理
    Clear-OldConnections
    
    # 使用Job执行，支持超时
    $job = Start-Job -ScriptBlock {
        param($ConfigPath, $RemoteCommand)
        ssh -F $ConfigPath -o ConnectTimeout=5 -o ServerAliveInterval=10 enterprise-ai-server $RemoteCommand 2>&1
    } -ArgumentList $ConfigPath, $RemoteCommand
    
    # 等待完成或超时
    $result = Wait-Job -Job $job -Timeout $MaxTimeout
    
    if ($result) {
        $output = Receive-Job -Job $job
        Remove-Job -Job $job -Force
        return @{
            Success = $true
            Output = $output
            ExitCode = 0
        }
    } else {
        # 超时 - 强制停止
        Stop-Job -Job $job -Force
        Remove-Job -Job $job -Force
        Clear-OldConnections
        return @{
            Success = $false
            Output = @("Command timeout after $MaxTimeout seconds")
            ExitCode = -1
        }
    }
}

# 主逻辑
try {
    $result = Invoke-SSHFast -RemoteCommand $Command -MaxTimeout $Timeout
    
    if ($result.Success) {
        Write-Output ($result.Output -join "`n")
        exit 0
    } else {
        Write-Error ($result.Output -join "`n")
        exit $result.ExitCode
    }
} catch {
    Clear-OldConnections
    Write-Error "Execution failed: $_"
    exit 1
}


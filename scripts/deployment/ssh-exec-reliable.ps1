# 可靠的SSH执行脚本
# 每次执行前清理旧连接，使用超时机制，避免卡住

param(
    [string]$Command,
    [string]$ConfigFile = "remote.ssh",
    [int]$Timeout = 120,
    [switch]$CleanBeforeExecute = $true
)

$ErrorActionPreference = "Stop"

# 获取项目根目录
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptRoot
# 配置文件在项目根目录，不是scripts目录
$ConfigPath = Join-Path $ProjectRoot $ConfigFile

# 如果不在项目根目录，尝试在上级目录
if (-not (Test-Path $ConfigPath)) {
    $ConfigPath = Join-Path (Split-Path $ProjectRoot) $ConfigFile
}

if (-not (Test-Path $ConfigPath)) {
    throw "SSH config file not found. Tried: $ConfigPath"
}

# 清理旧连接
function Clear-OldSSHConnections {
    $controlDir = Join-Path $env:USERPROFILE ".ssh"
    if (Test-Path $controlDir) {
        $controlFiles = Get-ChildItem -Path $controlDir -Filter "control-*" -ErrorAction SilentlyContinue
        foreach ($file in $controlFiles) {
            try {
                # 尝试优雅关闭
                ssh -F $ConfigPath -O exit enterprise-ai-server 2>&1 | Out-Null
            } catch {
                # 忽略错误
            }
            # 强制删除
            Remove-Item $file.FullName -Force -ErrorAction SilentlyContinue
        }
    }
    
    # 清理可能的僵尸进程（只清理超过5分钟的）
    $oldProcesses = Get-Process ssh -ErrorAction SilentlyContinue | Where-Object {
        $_.StartTime -lt (Get-Date).AddMinutes(-5)
    }
    if ($oldProcesses) {
        $oldProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
    }
}

# 执行SSH命令（带超时）
function Invoke-SSHWithTimeout {
    param(
        [string]$RemoteCommand,
        [int]$TimeoutSeconds
    )
    
    # 清理旧连接
    if ($CleanBeforeExecute) {
        Clear-OldSSHConnections
        Start-Sleep -Milliseconds 500
    }
    
    # 使用Job执行，支持超时
    $job = Start-Job -ScriptBlock {
        param($ConfigPath, $RemoteCommand)
        ssh -F $ConfigPath -o ConnectTimeout=10 -o ServerAliveInterval=30 enterprise-ai-server $RemoteCommand 2>&1
    } -ArgumentList $ConfigPath, $RemoteCommand
    
    # 等待完成或超时
    $result = Wait-Job -Job $job -Timeout $TimeoutSeconds
    
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
        Write-Host "Command timeout after $TimeoutSeconds seconds, stopping..." -ForegroundColor Yellow
        Stop-Job -Job $job -Force
        Remove-Job -Job $job -Force
        
        # 清理连接
        Clear-OldSSHConnections
        
        return @{
            Success = $false
            Output = @("Command execution timeout")
            ExitCode = -1
        }
    }
}

# 主逻辑
try {
    if (-not $Command) {
        Write-Host "Usage: ssh-exec-reliable.ps1 -Command '<command>' [-Timeout <seconds>]"
        exit 1
    }
    
    $result = Invoke-SSHWithTimeout -RemoteCommand $Command -TimeoutSeconds $Timeout
    
    if ($result.Success) {
        Write-Output ($result.Output -join "`n")
        exit 0
    } else {
        Write-Error ($result.Output -join "`n")
        exit $result.ExitCode
    }
} catch {
    Write-Error "Execution failed: $_"
    Clear-OldSSHConnections
    exit 1
}


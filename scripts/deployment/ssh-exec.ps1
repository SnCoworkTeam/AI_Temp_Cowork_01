# SSH执行辅助函数
# 使用持久化连接执行SSH命令，避免重复登录

param(
    [string]$Command,
    [string]$ConfigFile = "remote.ssh",
    [int]$Timeout = 60
)

$ErrorActionPreference = "Stop"

# 获取脚本目录
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptRoot
$ConfigPath = Join-Path $ProjectRoot $ConfigFile

# 读取SSH配置
function Get-SSHConfig {
    if (-not (Test-Path $ConfigPath)) {
        throw "SSH配置文件不存在: $ConfigPath"
    }
    
    $config = @{
        HostName = ""
        User = "ubuntu"
        IdentityFile = ""
        Port = 22
    }
    
    $content = Get-Content $ConfigPath -Raw
    if ($content -match "HostName\s+(\S+)") {
        $config.HostName = $matches[1]
    }
    if ($content -match "User\s+(\S+)") {
        $config.User = $matches[1]
    }
    if ($content -match "IdentityFile\s+(\S+)") {
        $keyFile = $matches[1]
        $keyPath = Join-Path $ProjectRoot $keyFile
        if (Test-Path $keyPath) {
            $config.IdentityFile = $keyPath
        }
    }
    if ($content -match "Port\s+(\d+)") {
        $config.Port = [int]$matches[1]
    }
    
    return $config
}

# 执行SSH命令（使用持久化连接）
function Invoke-SSHCommand {
    param(
        [string]$RemoteCommand,
        [int]$TimeoutSeconds = 60
    )
    
    $config = Get-SSHConfig
    
    # 构建SSH命令，使用ControlMaster
    $sshArgs = @(
        "-F", $ConfigPath,
        "-o", "ControlMaster=auto",
        "-o", "ControlPath=~/.ssh/control-%r@%h:%p",
        "-o", "ControlPersist=10m",
        "-o", "ConnectTimeout=$TimeoutSeconds",
        "enterprise-ai-server",
        $RemoteCommand
    )
    
    try {
        # 执行命令，设置超时
        $job = Start-Job -ScriptBlock {
            param($Args)
            & ssh $Args 2>&1
        } -ArgumentList (,$sshArgs)
        
        # 等待完成或超时
        $result = Wait-Job -Job $job -Timeout $TimeoutSeconds
        
        if ($result) {
            $output = Receive-Job -Job $job
            Remove-Job -Job $job -Force
            return @{
                Success = $true
                Output = $output
                ExitCode = $LASTEXITCODE
            }
        } else {
            # 超时
            Stop-Job -Job $job -Force
            Remove-Job -Job $job -Force
            return @{
                Success = $false
                Output = @("命令执行超时")
                ExitCode = -1
            }
        }
    } catch {
        return @{
            Success = $false
            Output = @("执行错误: $_")
            ExitCode = -1
        }
    }
}

# 主逻辑
if ($Command) {
    $result = Invoke-SSHCommand -RemoteCommand $Command -TimeoutSeconds $Timeout
    if ($result.Success) {
        Write-Output $result.Output
        exit $result.ExitCode
    } else {
        Write-Error ($result.Output -join "`n")
        exit $result.ExitCode
    }
} else {
    Write-Host "用法: ssh-exec.ps1 -Command '<命令>' [-Timeout <秒数>]"
    exit 1
}


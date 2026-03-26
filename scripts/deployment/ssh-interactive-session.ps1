# SSH交互式持久会话
# 打开一个交互式窗口，保持连接，通过命名管道通信

param(
    [string]$Action = "start",  # start, stop, status, execute
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

# 会话状态
$SessionFile = Join-Path $env:TEMP "ssh-interactive-session.pid"
$CommandPipe = Join-Path $env:TEMP "ssh-command-pipe.txt"
$ResultPipe = Join-Path $env:TEMP "ssh-result-pipe.txt"

# 启动交互式SSH会话窗口
function Start-InteractiveSession {
    # 检查是否已有会话
    if (Test-Path $SessionFile) {
        $pid = Get-Content $SessionFile -ErrorAction SilentlyContinue
        if ($pid) {
            try {
                $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
                if ($process -and -not $process.HasExited) {
                    Write-Host "SSH interactive session already running (PID: $pid)" -ForegroundColor Green
                    return $process
                }
            } catch {
                # 进程不存在
            }
        }
    }
    
    # 创建命令和结果管道文件
    "" | Out-File $CommandPipe -Force
    "" | Out-File $ResultPipe -Force
    
    # 启动交互式SSH窗口（使用PowerShell窗口）
    $psScript = @"
`$ErrorActionPreference = 'Continue'
`$ConfigPath = '$ConfigPath'
`$CommandPipe = '$CommandPipe'
`$ResultPipe = '$ResultPipe'

Write-Host 'SSH Interactive Session Started' -ForegroundColor Green
Write-Host 'Connection will be kept alive...' -ForegroundColor Yellow
Write-Host ''

# 建立SSH连接（后台保持）
`$sshProcess = Start-Process -FilePath 'ssh' -ArgumentList @(
    '-F', `$ConfigPath,
    '-o', 'ServerAliveInterval=30',
    '-o', 'ServerAliveCountMax=5',
    'enterprise-ai-server',
    'bash -c "while true; do sleep 60; done"'
) -PassThru -WindowStyle Hidden

Write-Host "SSH connection established (PID: `$(`$sshProcess.Id))" -ForegroundColor Green
Write-Host ''

# 监控命令管道
while (`$true) {
    Start-Sleep -Milliseconds 500
    
    if (Test-Path `$CommandPipe) {
        `$cmd = Get-Content `$CommandPipe -Raw -ErrorAction SilentlyContinue
        if (`$cmd -and `$cmd.Trim() -ne '') {
            Write-Host "Executing: `$cmd" -ForegroundColor Cyan
            
            # 执行命令
            `$result = ssh -F `$ConfigPath -o ConnectTimeout=10 enterprise-ai-server `$cmd 2>&1
            `$exitCode = `$LASTEXITCODE
            
            # 写入结果
            @{
                Output = `$result
                ExitCode = `$exitCode
            } | ConvertTo-Json -Compress | Out-File `$ResultPipe -Force
            
            # 清空命令管道
            '' | Out-File `$CommandPipe -Force
            
            Write-Host "Command completed (Exit: `$exitCode)" -ForegroundColor Green
        }
    }
    
    # 检查SSH进程是否还在运行
    if (`$sshProcess.HasExited) {
        Write-Host 'SSH connection lost, restarting...' -ForegroundColor Yellow
        `$sshProcess = Start-Process -FilePath 'ssh' -ArgumentList @(
            '-F', `$ConfigPath,
            '-o', 'ServerAliveInterval=30',
            'enterprise-ai-server',
            'bash -c "while true; do sleep 60; done"'
        ) -PassThru -WindowStyle Hidden
    }
}
"@
    
    # 启动新的PowerShell窗口
    $psScript | Out-File (Join-Path $env:TEMP "ssh-session-script.ps1") -Force
    
    $process = Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-File", (Join-Path $env:TEMP "ssh-session-script.ps1")
    ) -PassThru
    
    # 保存进程ID
    $process.Id | Out-File $SessionFile -Force
    
    Write-Host "SSH interactive session started (Window PID: $($process.Id))" -ForegroundColor Green
    Write-Host "A new PowerShell window has been opened to maintain the connection." -ForegroundColor Yellow
    Write-Host "You can minimize it, but don't close it." -ForegroundColor Yellow
    
    return $process
}

# 停止会话
function Stop-InteractiveSession {
    if (Test-Path $SessionFile) {
        $pid = Get-Content $SessionFile -ErrorAction SilentlyContinue
        if ($pid) {
            try {
                $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
                if ($process) {
                    $process.Kill()
                    Write-Host "SSH interactive session stopped" -ForegroundColor Yellow
                }
            } catch {
                # 忽略错误
            }
        }
        Remove-Item $SessionFile -Force -ErrorAction SilentlyContinue
    }
    
    # 清理管道文件
    Remove-Item $CommandPipe -Force -ErrorAction SilentlyContinue
    Remove-Item $ResultPipe -Force -ErrorAction SilentlyContinue
}

# 执行命令（通过管道）
function Invoke-CommandViaPipe {
    param([string]$RemoteCommand)
    
    # 检查会话是否运行
    if (-not (Test-Path $SessionFile)) {
        Write-Host "SSH session not running, starting..." -ForegroundColor Yellow
        Start-InteractiveSession | Out-Null
        Start-Sleep -Seconds 2
    }
    
    # 写入命令
    $RemoteCommand | Out-File $CommandPipe -Force
    
    # 等待结果（最多30秒）
    $timeout = 30
    $elapsed = 0
    while ($elapsed -lt $timeout) {
        Start-Sleep -Milliseconds 500
        $elapsed += 0.5
        
        if (Test-Path $ResultPipe) {
            $resultJson = Get-Content $ResultPipe -Raw -ErrorAction SilentlyContinue
            if ($resultJson -and $resultJson.Trim() -ne '') {
                try {
                    $result = $resultJson | ConvertFrom-Json
                    # 清空结果文件
                    '' | Out-File $ResultPipe -Force
                    return @{
                        Output = $result.Output
                        ExitCode = $result.ExitCode
                    }
                } catch {
                    # JSON解析失败，继续等待
                }
            }
        }
    }
    
    throw "Command execution timeout"
}

# 主逻辑
try {
    switch ($Action.ToLower()) {
        "start" {
            Start-InteractiveSession | Out-Null
        }
        "stop" {
            Stop-InteractiveSession
        }
        "status" {
            if (Test-Path $SessionFile) {
                $pid = Get-Content $SessionFile -ErrorAction SilentlyContinue
                if ($pid) {
                    try {
                        $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
                        if ($process -and -not $process.HasExited) {
                            Write-Host "SSH interactive session: ACTIVE (Window PID: $pid)" -ForegroundColor Green
                        } else {
                            Write-Host "SSH interactive session: INACTIVE" -ForegroundColor Red
                        }
                    } catch {
                        Write-Host "SSH interactive session: INACTIVE" -ForegroundColor Red
                    }
                }
            } else {
                Write-Host "SSH interactive session: NOT STARTED" -ForegroundColor Yellow
            }
        }
        "execute" {
            if (-not $Command) {
                Write-Host "Error: -Command required for execute action" -ForegroundColor Red
                exit 1
            }
            
            $result = Invoke-CommandViaPipe -RemoteCommand $Command
            Write-Output ($result.Output -join "`n")
            exit $result.ExitCode
        }
        default {
            Write-Host "Usage: ssh-interactive-session.ps1 -Action start|stop|status|execute [-Command '<command>']"
            exit 1
        }
    }
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}


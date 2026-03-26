# SSH持久化连接管理器
# 使用ControlMaster实现SSH连接复用，避免重复登录

param(
    [string]$ConfigFile = "remote.ssh",
    [string]$Action = "connect",  # connect, disconnect, status, execute
    [string]$Command = "",
    [switch]$Interactive = $false
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
        } else {
            throw "密钥文件不存在: $keyPath"
        }
    }
    if ($content -match "Port\s+(\d+)") {
        $config.Port = [int]$matches[1]
    }
    
    return $config
}

# 确保ControlPath目录存在
function Initialize-ControlPath {
    # Windows上使用USERPROFILE，Linux/Mac使用HOME
    if ($env:USERPROFILE) {
        $controlDir = Join-Path $env:USERPROFILE ".ssh"
    } else {
        $controlDir = Join-Path $env:HOME ".ssh"
    }
    
    if (-not (Test-Path $controlDir)) {
        New-Item -ItemType Directory -Path $controlDir -Force | Out-Null
    }
    return $controlDir
}

# 构建SSH命令
function Build-SSHCommand {
    param(
        [hashtable]$Config,
        [string]$RemoteCommand = "",
        [switch]$UseControlMaster = $true
    )
    
    $controlDir = Initialize-ControlPath
    
    # Windows路径需要特殊处理
    if ($IsWindows -or $env:OS -like "*Windows*") {
        # Windows上使用绝对路径，但SSH配置中使用~/.ssh会被自动转换
        $controlPath = "~/.ssh/control-%r@%h:%p"
    } else {
        $controlPath = Join-Path $controlDir "control-%r@%h:%p"
    }
    
    $sshArgs = @(
        "-F", $ConfigPath
    )
    
    if ($UseControlMaster) {
        $sshArgs += @(
            "-o", "ControlMaster=auto",
            "-o", "ControlPath=$controlPath",
            "-o", "ControlPersist=10m"
        )
    }
    
    $sshArgs += @(
        "-o", "ServerAliveInterval=30",
        "-o", "ServerAliveCountMax=5",
        "-o", "TCPKeepAlive=yes",
        "-o", "Compression=yes"
    )
    
    if ($RemoteCommand) {
        $sshArgs += "enterprise-ai-server", $RemoteCommand
    } else {
        $sshArgs += "enterprise-ai-server"
    }
    
    return $sshArgs
}

# 检查ControlMaster连接是否活跃
function Test-ControlMasterConnection {
    param([hashtable]$Config)
    
    $controlDir = Initialize-ControlPath
    # 构建实际的控制文件路径
    $controlFileName = "control-$($Config.User)@$($Config.HostName):$($Config.Port)"
    $actualPath = Join-Path $controlDir $controlFileName
    
    if (Test-Path $actualPath) {
        # 尝试执行一个简单命令测试连接
        try {
            $testCmd = Build-SSHCommand -Config $Config -RemoteCommand "echo 'test'" -UseControlMaster $true
            $result = & ssh $testCmd 2>&1
            if ($LASTEXITCODE -eq 0) {
                return $true
            }
        } catch {
            # 连接文件存在但连接已失效，删除它
            Remove-Item $actualPath -Force -ErrorAction SilentlyContinue
        }
    }
    return $false
}

# 建立ControlMaster连接
function Establish-ControlMaster {
    param([hashtable]$Config)
    
    if (Test-ControlMasterConnection -Config $Config) {
        Write-Host "✓ ControlMaster连接已存在" -ForegroundColor Green
        return $true
    }
    
    Write-Host "正在建立ControlMaster连接..." -ForegroundColor Yellow
    
    # 在后台建立主连接
    $sshArgs = Build-SSHCommand -Config $Config -UseControlMaster $true
    $sshArgs += "-N"  # 不执行远程命令，只建立连接
    
    $job = Start-Job -ScriptBlock {
        param($Args)
        & ssh $Args
    } -ArgumentList (,$sshArgs)
    
    # 等待连接建立
    Start-Sleep -Seconds 2
    
    # 测试连接
    if (Test-ControlMasterConnection -Config $Config) {
        Write-Host "✓ ControlMaster连接已建立" -ForegroundColor Green
        return $true
    } else {
        Write-Host "✗ ControlMaster连接建立失败" -ForegroundColor Red
        return $false
    }
}

# 执行SSH命令
function Invoke-SSHCommand {
    param(
        [hashtable]$Config,
        [string]$RemoteCommand,
        [switch]$Interactive = $false
    )
    
    # 确保ControlMaster连接存在
    if (-not (Test-ControlMasterConnection -Config $Config)) {
        Establish-ControlMaster -Config $Config | Out-Null
    }
    
    $sshArgs = Build-SSHCommand -Config $Config -RemoteCommand $RemoteCommand -UseControlMaster $true
    
    if ($Interactive) {
        # 交互式模式
        & ssh $sshArgs
    } else {
        # 非交互式模式
        $output = & ssh $sshArgs 2>&1
        return $output
    }
}

# 断开ControlMaster连接
function Disconnect-ControlMaster {
    param([hashtable]$Config)
    
    $controlDir = Initialize-ControlPath
    $controlFileName = "control-$($Config.User)@$($Config.HostName):$($Config.Port)"
    $actualPath = Join-Path $controlDir $controlFileName
    
    if (Test-Path $actualPath) {
        # 使用 -O exit 关闭ControlMaster连接
        $sshArgs = Build-SSHCommand -Config $Config -UseControlMaster $false
        $sshArgs += "-O", "exit", "enterprise-ai-server"
        & ssh $sshArgs 2>&1 | Out-Null
        
        # 删除控制文件
        Remove-Item $actualPath -Force -ErrorAction SilentlyContinue
        Write-Host "✓ ControlMaster连接已断开" -ForegroundColor Green
    } else {
        Write-Host "没有活动的ControlMaster连接" -ForegroundColor Yellow
    }
}

# 显示连接状态
function Show-ConnectionStatus {
    param([hashtable]$Config)
    
    $isConnected = Test-ControlMasterConnection -Config $Config
    
    Write-Host "`n=== SSH连接状态 ===" -ForegroundColor Cyan
    Write-Host "服务器: $($Config.User)@$($Config.HostName):$($Config.Port)" -ForegroundColor White
    Write-Host "状态: " -NoNewline
    
    if ($isConnected) {
        Write-Host "已连接 (ControlMaster活跃)" -ForegroundColor Green
    } else {
        Write-Host "未连接" -ForegroundColor Red
    }
    Write-Host ""
}

# 交互式对话框
function Show-InteractiveDialog {
    param([hashtable]$Config)
    
    $choices = @(
        [System.Management.Automation.Host.ChoiceDescription]::new("&1. 建立持久连接", "建立ControlMaster连接"),
        [System.Management.Automation.Host.ChoiceDescription]::new("&2. 执行命令", "在远程服务器执行命令"),
        [System.Management.Automation.Host.ChoiceDescription]::new("&3. 交互式Shell", "打开交互式SSH会话"),
        [System.Management.Automation.Host.ChoiceDescription]::new("&4. 查看状态", "查看连接状态"),
        [System.Management.Automation.Host.ChoiceDescription]::new("&5. 断开连接", "断开ControlMaster连接"),
        [System.Management.Automation.Host.ChoiceDescription]::new("&Q. 退出", "退出程序")
    )
    
    while ($true) {
        Clear-Host
        Write-Host "`n=== SSH持久化连接管理器 ===" -ForegroundColor Cyan
        Write-Host "服务器: $($Config.User)@$($Config.HostName):$($Config.Port)`n" -ForegroundColor White
        
        $choice = $Host.UI.PromptForChoice("", "请选择操作:", $choices, 0)
        
        switch ($choice) {
            0 {
                # 建立连接
                Establish-ControlMaster -Config $Config
                Write-Host "`n按任意键继续..."
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            }
            1 {
                # 执行命令
                $cmd = Read-Host "`n请输入要执行的命令"
                if ($cmd) {
                    Write-Host "`n执行结果:" -ForegroundColor Yellow
                    $result = Invoke-SSHCommand -Config $Config -RemoteCommand $cmd
                    Write-Host $result
                }
                Write-Host "`n按任意键继续..."
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            }
            2 {
                # 交互式Shell
                Write-Host "`n正在打开交互式SSH会话..." -ForegroundColor Yellow
                Write-Host "输入 'exit' 退出会话`n" -ForegroundColor Gray
                Invoke-SSHCommand -Config $Config -Interactive $true
            }
            3 {
                # 查看状态
                Show-ConnectionStatus -Config $Config
                Write-Host "按任意键继续..."
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            }
            4 {
                # 断开连接
                Disconnect-ControlMaster -Config $Config
                Write-Host "`n按任意键继续..."
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            }
            5 {
                # 退出
                Disconnect-ControlMaster -Config $Config
                Write-Host "`n再见！" -ForegroundColor Green
                exit 0
            }
        }
    }
}

# 主逻辑
try {
    $config = Get-SSHConfig
    
    switch ($Action.ToLower()) {
        "connect" {
            if ($Interactive) {
                Show-InteractiveDialog -Config $config
            } else {
                Establish-ControlMaster -Config $config
            }
        }
        "disconnect" {
            Disconnect-ControlMaster -Config $config
        }
        "status" {
            Show-ConnectionStatus -Config $config
        }
        "execute" {
            if (-not $Command) {
                throw "执行命令时，必须提供 -Command 参数"
            }
            $result = Invoke-SSHCommand -Config $config -RemoteCommand $Command
            Write-Output $result
        }
        default {
            Write-Host "用法: ssh-persistent.ps1 [-Action connect|disconnect|status|execute] [-Command <命令>] [-Interactive]"
            Write-Host ""
            Write-Host "示例:"
            Write-Host "  .\ssh-persistent.ps1 -Action connect -Interactive    # 打开交互式对话框"
            Write-Host "  .\ssh-persistent.ps1 -Action execute -Command 'ls'   # 执行命令"
            Write-Host "  .\ssh-persistent.ps1 -Action status                  # 查看状态"
            Write-Host "  .\ssh-persistent.ps1 -Action disconnect              # 断开连接"
        }
    }
} catch {
    Write-Host "错误: $_" -ForegroundColor Red
    exit 1
}


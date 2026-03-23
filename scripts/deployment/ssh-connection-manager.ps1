# SSH连接管理器 - 智能连接池
# 自动检测连接健康，失效时自动重建，避免多次连接后卡住

param(
    [string]$ConfigFile = "remote.ssh",
    [string]$Action = "execute",  # execute, test, cleanup
    [string]$Command = "",
    [int]$ConnectionTimeout = 10,
    [int]$HealthCheckInterval = 5  # 每5次使用后检查一次连接健康
)

$ErrorActionPreference = "Continue"

# 获取脚本目录
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptRoot
# 配置文件在项目根目录
$ConfigPath = Join-Path $ProjectRoot $ConfigFile
if (-not (Test-Path $ConfigPath)) {
    # 如果不在项目根目录，尝试在脚本目录的上级目录
    $ConfigPath = Join-Path (Split-Path $ProjectRoot) $ConfigFile
}

# 连接状态跟踪
$script:ConnectionState = @{
    LastHealthCheck = $null
    UseCount = 0
    LastError = $null
}

# 获取SSH配置
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

# 检查连接健康
function Test-ConnectionHealth {
    param([hashtable]$Config)
    
    try {
        $testCmd = "echo 'health_check_$(Get-Random)'"
        $result = ssh -F $ConfigPath -o ConnectTimeout=$ConnectionTimeout enterprise-ai-server $testCmd 2>&1
        
        if ($LASTEXITCODE -eq 0 -and $result -match "health_check_") {
            return $true
        }
        return $false
    } catch {
        return $false
    }
}

# 清理旧的连接
function Clear-OldConnections {
    param([hashtable]$Config)
    
    # 清理ControlMaster连接文件
    $controlDir = Join-Path $env:USERPROFILE ".ssh"
    if (Test-Path $controlDir) {
        $controlFiles = Get-ChildItem -Path $controlDir -Filter "control-*" -ErrorAction SilentlyContinue
        foreach ($file in $controlFiles) {
            try {
                # 尝试关闭连接
                ssh -F $ConfigPath -O exit enterprise-ai-server 2>&1 | Out-Null
            } catch {
                # 忽略错误
            }
            # 删除文件
            Remove-Item $file.FullName -Force -ErrorAction SilentlyContinue
        }
    }
    
    Write-Host "Cleaned old connection files" -ForegroundColor Yellow
}

# 执行SSH命令（带连接健康检查）
function Invoke-SSHWithHealthCheck {
    param(
        [string]$RemoteCommand,
        [hashtable]$Config,
        [int]$MaxRetries = 2
    )
    
    $retryCount = 0
    $lastError = $null
    
    while ($retryCount -le $MaxRetries) {
        # 检查是否需要健康检查
        $needsHealthCheck = $false
        if ($script:ConnectionState.UseCount % $HealthCheckInterval -eq 0 -and $script:ConnectionState.UseCount -gt 0) {
            $needsHealthCheck = $true
        }
        
        # 如果上次有错误，强制健康检查
        if ($script:ConnectionState.LastError) {
            $needsHealthCheck = $true
            $script:ConnectionState.LastError = $null
        }
        
        # 执行健康检查
        if ($needsHealthCheck) {
            Write-Host "[Health Check] Checking connection..." -ForegroundColor Gray
            $isHealthy = Test-ConnectionHealth -Config $Config
            
            if (-not $isHealthy) {
                Write-Host "[Health Check] Connection unhealthy, cleaning..." -ForegroundColor Yellow
                Clear-OldConnections -Config $Config
                Start-Sleep -Seconds 1
            } else {
                Write-Host "[Health Check] Connection OK" -ForegroundColor Green
            }
        }
        
        # 执行命令
        try {
            $script:ConnectionState.UseCount++
            $script:ConnectionState.LastHealthCheck = Get-Date
            
            $output = ssh -F $ConfigPath -o ConnectTimeout=$ConnectionTimeout enterprise-ai-server $RemoteCommand 2>&1
            $exitCode = $LASTEXITCODE
            
            if ($exitCode -eq 0) {
                return @{
                    Success = $true
                    Output = $output
                    ExitCode = 0
                }
            } else {
                # 检查是否是连接问题
                $errorStr = $output -join "`n"
                if ($errorStr -match "Connection.*refused|Connection.*reset|getsockname|Not a socket") {
                    $lastError = "Connection error: $errorStr"
                    $script:ConnectionState.LastError = $lastError
                    
                    if ($retryCount -lt $MaxRetries) {
                        $retryMsg = "[Retry] Connection error, cleaning and retrying ($($retryCount + 1)/$MaxRetries)..."
                        Write-Host $retryMsg -ForegroundColor Yellow
                        Clear-OldConnections -Config $Config
                        Start-Sleep -Seconds 2
                        $retryCount++
                        continue
                    }
                }
                
                return @{
                    Success = $false
                    Output = $output
                    ExitCode = $exitCode
                }
            }
        } catch {
            $lastError = "Execution error: $_"
            $script:ConnectionState.LastError = $lastError
            
            if ($retryCount -lt $MaxRetries) {
                $retryMsg = "[Retry] Execution error, cleaning and retrying ($($retryCount + 1)/$MaxRetries)..."
                Write-Host $retryMsg -ForegroundColor Yellow
                Clear-OldConnections -Config $Config
                Start-Sleep -Seconds 2
                $retryCount++
                continue
            }
            
            return @{
                Success = $false
                Output = @($lastError)
                ExitCode = -1
            }
        }
    }
    
    $failMsg = "Execution failed after $MaxRetries retries: $lastError"
    return @{
        Success = $false
        Output = @($failMsg)
        ExitCode = -1
    }
}

# 主逻辑
try {
    $config = Get-SSHConfig
    
    switch ($Action.ToLower()) {
        "execute" {
            if (-not $Command) {
                Write-Host "Error: -Command parameter required for execute action" -ForegroundColor Red
                exit 1
            }
            
            $result = Invoke-SSHWithHealthCheck -RemoteCommand $Command -Config $config
            Write-Output ($result.Output -join "`n")
            exit $result.ExitCode
        }
        "test" {
            $isHealthy = Test-ConnectionHealth -Config $config
            if ($isHealthy) {
                Write-Host "Connection healthy" -ForegroundColor Green
                exit 0
            } else {
                Write-Host "Connection unhealthy" -ForegroundColor Red
                exit 1
            }
        }
        "cleanup" {
            Clear-OldConnections -Config $config
            exit 0
        }
        default {
            Write-Host "Usage: ssh-connection-manager.ps1 -Action execute|test|cleanup [-Command '<command>']"
            exit 1
        }
    }
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}


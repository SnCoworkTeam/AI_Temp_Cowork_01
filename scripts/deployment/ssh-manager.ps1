# SSH连接管理器
# 实现连接池机制，自动重连，避免长时间无响应

param(
    [string]$ConfigFile = "remote.ssh",
    [int]$ConnectionTimeout = 30,
    [int]$MaxRetries = 3,
    [int]$RetryDelay = 2
)

# 连接池
$script:ConnectionPool = @{}
$script:ConnectionLock = [System.Threading.ReaderWriterLockSlim]::new()

# 读取SSH配置
function Get-SSHConfig {
    param([string]$ConfigFile)
    
    $configPath = Join-Path $PSScriptRoot "..\..\$ConfigFile"
    if (-not (Test-Path $configPath)) {
        throw "配置文件不存在: $configPath"
    }
    
    $config = @{
        HostName = ""
        User = "ubuntu"
        IdentityFile = ""
        Port = 22
    }
    
    $content = Get-Content $configPath -Raw
    if ($content -match "HostName\s+(\S+)") {
        $config.HostName = $matches[1]
    }
    if ($content -match "User\s+(\S+)") {
        $config.User = $matches[1]
    }
    if ($content -match "IdentityFile\s+(\S+)") {
        $keyFile = $matches[1]
        $keyPath = Join-Path $PSScriptRoot "..\..\$keyFile"
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

# 检查SSH连接是否活跃
function Test-SSHConnection {
    param(
        [string]$HostName,
        [string]$User,
        [string]$IdentityFile
    )
    
    $connectionKey = "$User@$HostName"
    
    try {
        # 使用SSH连接测试命令
        $testCmd = "echo 'connection_test'"
        $result = ssh -i $IdentityFile -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$User@$HostName" $testCmd 2>&1
        
        if ($LASTEXITCODE -eq 0 -and $result -eq "connection_test") {
            return $true
        }
        return $false
    } catch {
        return $false
    }
}

# 获取或创建SSH连接
function Get-SSHConnection {
    param(
        [string]$ConfigFile = "remote.ssh"
    )
    
    $config = Get-SSHConfig -ConfigFile $ConfigFile
    $connectionKey = "$($config.User)@$($config.HostName)"
    
    $script:ConnectionLock.EnterReadLock()
    try {
        if ($script:ConnectionPool.ContainsKey($connectionKey)) {
            $conn = $script:ConnectionPool[$connectionKey]
            
            # 检查连接是否仍然有效
            if (Test-SSHConnection -HostName $config.HostName -User $config.User -IdentityFile $config.IdentityFile) {
                $conn.LastUsed = Get-Date
                return $conn
            } else {
                # 连接已失效，移除
                $script:ConnectionLock.ExitReadLock()
                $script:ConnectionLock.EnterWriteLock()
                try {
                    $script:ConnectionPool.Remove($connectionKey)
                } finally {
                    $script:ConnectionLock.ExitWriteLock()
                    $script:ConnectionLock.EnterReadLock()
                }
            }
        }
    } finally {
        $script:ConnectionLock.ExitReadLock()
    }
    
    # 创建新连接
    $script:ConnectionLock.EnterWriteLock()
    try {
        $conn = @{
            HostName = $config.HostName
            User = $config.User
            IdentityFile = $config.IdentityFile
            Port = $config.Port
            Created = Get-Date
            LastUsed = Get-Date
            Config = $config
        }
        
        $script:ConnectionPool[$connectionKey] = $conn
        return $conn
    } finally {
        $script:ConnectionLock.ExitWriteLock()
    }
}

# 执行SSH命令（带自动重连）
function Invoke-SSHCommand {
    param(
        [hashtable]$Connection,
        [string]$Command,
        [int]$Timeout = 30,
        [switch]$NoRetry = $false
    )
    
    $retryCount = 0
    $maxRetries = if ($NoRetry) { 0 } else { $MaxRetries }
    
    while ($retryCount -le $maxRetries) {
        try {
            # 检查连接健康
            if (-not (Test-SSHConnection -HostName $Connection.HostName -User $Connection.User -IdentityFile $Connection.IdentityFile)) {
                Write-Warning "SSH连接不活跃，尝试重新连接..."
                $Connection = Get-SSHConnection -ConfigFile "remote.ssh"
            }
            
            # 执行命令
            $sshCmd = "ssh -i `"$($Connection.IdentityFile)`" -o ConnectTimeout=$Timeout -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ServerAliveCountMax=3 `"$($Connection.User)@$($Connection.HostName)`" `"$Command`""
            
            $result = Invoke-Expression $sshCmd 2>&1
            $exitCode = $LASTEXITCODE
            
            if ($exitCode -eq 0) {
                $Connection.LastUsed = Get-Date
                return @{
                    Success = $true
                    Output = $result
                    ExitCode = 0
                }
            } else {
                throw "SSH命令执行失败，退出码: $exitCode"
            }
            
        } catch {
            $retryCount++
            if ($retryCount -le $maxRetries) {
                Write-Warning "SSH命令执行失败，$RetryDelay秒后重试 ($retryCount/$maxRetries): $_"
                Start-Sleep -Seconds $RetryDelay
                
                # 尝试重新获取连接
                $Connection = Get-SSHConnection -ConfigFile "remote.ssh"
            } else {
                return @{
                    Success = $false
                    Output = $_.Exception.Message
                    ExitCode = -1
                }
            }
        }
    }
}

# 执行SCP命令（带自动重连）
function Invoke-SCPCommand {
    param(
        [hashtable]$Connection,
        [string]$Source,
        [string]$Destination,
        [switch]$Recursive = $false,
        [int]$Timeout = 30
    )
    
    $retryCount = 0
    
    while ($retryCount -le $MaxRetries) {
        try {
            # 检查连接健康
            if (-not (Test-SSHConnection -HostName $Connection.HostName -User $Connection.User -IdentityFile $Connection.IdentityFile)) {
                Write-Warning "SSH连接不活跃，尝试重新连接..."
                $Connection = Get-SSHConnection -ConfigFile "remote.ssh"
            }
            
            # 构建SCP命令
            $recursiveFlag = if ($Recursive) { "-r" } else { "" }
            $scpCmd = "scp -i `"$($Connection.IdentityFile)`" -o ConnectTimeout=$Timeout -o StrictHostKeyChecking=no $recursiveFlag `"$Source`" `"$($Connection.User)@$($Connection.HostName):$Destination`""
            
            $result = Invoke-Expression $scpCmd 2>&1
            $exitCode = $LASTEXITCODE
            
            if ($exitCode -eq 0) {
                $Connection.LastUsed = Get-Date
                return @{
                    Success = $true
                    Output = $result
                    ExitCode = 0
                }
            } else {
                throw "SCP命令执行失败，退出码: $exitCode"
            }
            
        } catch {
            $retryCount++
            if ($retryCount -le $MaxRetries) {
                Write-Warning "SCP命令执行失败，$RetryDelay秒后重试 ($retryCount/$MaxRetries): $_"
                Start-Sleep -Seconds $RetryDelay
                
                # 尝试重新获取连接
                $Connection = Get-SSHConnection -ConfigFile "remote.ssh"
            } else {
                return @{
                    Success = $false
                    Output = $_.Exception.Message
                    ExitCode = -1
                }
            }
        }
    }
}

# 清理连接池
function Clear-SSHConnectionPool {
    $script:ConnectionLock.EnterWriteLock()
    try {
        $script:ConnectionPool.Clear()
        Write-Host "SSH连接池已清空"
    } finally {
        $script:ConnectionLock.ExitWriteLock()
    }
}

# 注意：此脚本通过 dot-sourcing 方式导入，函数会自动可用
# 不需要使用 Export-ModuleMember（仅用于模块文件）


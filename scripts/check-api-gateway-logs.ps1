# PowerShell script: Check API Gateway logs on server
param(
    [string]$ConfigFile = "remote.ssh",
    [string]$RemotePath = "/opt/enterprise-ai-platform"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Checking API Gateway logs on server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Read remote.ssh config
$ServerIP = ""
$ServerUser = "ubuntu"
$KeyPath = ""

if (Test-Path $ConfigFile) {
    $configContent = Get-Content $ConfigFile -Raw
    
    if ($configContent -match "HostName\s+(\S+)") {
        $ServerIP = $matches[1]
    }
    if ($configContent -match "User\s+(\S+)") {
        $ServerUser = $matches[1]
    }
    if ($configContent -match "IdentityFile\s+(\S+)") {
        $KeyPath = $matches[1].Trim('"')
        if (-not [System.IO.Path]::IsPathRooted($KeyPath)) {
            $KeyPath = Join-Path $PWD $KeyPath
        }
    }
} else {
    Write-Host "Config file not found: $ConfigFile" -ForegroundColor Yellow
    Write-Host "Using default values..." -ForegroundColor Yellow
}

# Find key file
if ([string]::IsNullOrEmpty($KeyPath) -or -not (Test-Path $KeyPath)) {
    $possiblePaths = @(
        Join-Path $PWD "enterprise_ai_platform.pem",
        Join-Path $env:USERPROFILE ".ssh\enterprise_ai_platform.pem"
    )
    
    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            $KeyPath = $path
            break
        }
    }
}

if ([string]::IsNullOrEmpty($KeyIP)) {
    $ServerIP = "43.143.139.197"
}

if ([string]::IsNullOrEmpty($KeyPath) -or -not (Test-Path $KeyPath)) {
    Write-Host "Key file not found, trying without key..." -ForegroundColor Yellow
    $KeyPath = $null
}

Write-Host "Server: ${ServerUser}@${ServerIP}" -ForegroundColor Green
Write-Host "Remote path: $RemotePath" -ForegroundColor Green
Write-Host ""

# Build SSH command
$sshCmd = ""
if ($KeyPath) {
    $sshCmd = "ssh -i `"$KeyPath`" -o StrictHostKeyChecking=no -o ConnectTimeout=10 ${ServerUser}@${ServerIP}"
} else {
    $sshCmd = "ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ${ServerUser}@${ServerIP}"
}

# Check API Gateway container status
Write-Host "=== Checking API Gateway container status ===" -ForegroundColor Cyan
$checkStatusCmd = "cd $RemotePath && docker ps -a | grep api-gateway"
$statusResult = & $sshCmd $checkStatusCmd 2>&1
Write-Host $statusResult
Write-Host ""

# Get API Gateway logs (last 100 lines)
Write-Host "=== API Gateway logs (last 100 lines) ===" -ForegroundColor Cyan
$getLogsCmd = "cd $RemotePath && docker-compose logs --tail=100 api-gateway"
$logsResult = & $sshCmd $getLogsCmd 2>&1
Write-Host $logsResult
Write-Host ""

# Check if API Gateway is running
Write-Host "=== Checking if API Gateway is running ===" -ForegroundColor Cyan
$checkRunningCmd = "cd $RemotePath && docker ps | grep api-gateway"
$runningResult = & $sshCmd $checkRunningCmd 2>&1
if ($runningResult) {
    Write-Host "API Gateway container is running" -ForegroundColor Green
} else {
    Write-Host "API Gateway container is NOT running" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Checking API Gateway health ===" -ForegroundColor Cyan
$healthCheckCmd = "curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/health || echo 'Failed'"
$healthResult = & $sshCmd $healthCheckCmd 2>&1
Write-Host "Health check result: $healthResult" -ForegroundColor $(if ($healthResult -eq "200") { "Green" } else { "Red" })


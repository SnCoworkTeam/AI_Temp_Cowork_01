# Fix Docker API Version Compatibility Issue
# This script sets a compatible Docker API version and restarts Docker Desktop if needed

Write-Host "Checking Docker Desktop status..." -ForegroundColor Cyan

# Check if Docker Desktop is running
Write-Host "Testing Docker connection..." -ForegroundColor Cyan
$testResult = docker ps 2>&1
$isRunning = $testResult -notmatch "Cannot connect|Internal Server Error"

if (-not $isRunning) {
    Write-Host "`nDocker Desktop may not be running or responding properly." -ForegroundColor Yellow
    Write-Host "Please ensure Docker Desktop is:" -ForegroundColor Yellow
    Write-Host "  1. Running (green icon in system tray)" -ForegroundColor White
    Write-Host "  2. Fully started (not just starting)" -ForegroundColor White
    Write-Host "  3. Try restarting Docker Desktop manually" -ForegroundColor White
    Write-Host "`nAttempting to start Docker Desktop..." -ForegroundColor Yellow
    
    # Try to start Docker Desktop (if it's installed in the default location)
    $dockerDesktopPath = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerDesktopPath) {
        Write-Host "Starting Docker Desktop..." -ForegroundColor Yellow
        Start-Process $dockerDesktopPath
        Write-Host "Waiting for Docker Desktop to start (60 seconds)..." -ForegroundColor Yellow
        Write-Host "Please wait for the Docker Desktop icon to turn green in the system tray." -ForegroundColor Yellow
        Start-Sleep -Seconds 60
    } else {
        Write-Host "Docker Desktop not found at default location." -ForegroundColor Red
        Write-Host "Please start Docker Desktop manually and wait for it to fully start." -ForegroundColor Red
    }
}

# Set compatible API version (1.40 is widely supported)
Write-Host "Setting Docker API version to 1.40..." -ForegroundColor Cyan
$env:DOCKER_API_VERSION = "1.40"

# Test Docker connection
Write-Host "Testing Docker connection..." -ForegroundColor Cyan
$testResult = docker version 2>&1
if ($testResult -match "Server:") {
    Write-Host "Docker is working correctly!" -ForegroundColor Green
    Write-Host "`nTo make this permanent, add the following to your PowerShell profile:" -ForegroundColor Yellow
    Write-Host '  $env:DOCKER_API_VERSION = "1.40"' -ForegroundColor White
    Write-Host "`nOr add it to your system environment variables." -ForegroundColor Yellow
} else {
    Write-Host "Docker is still not responding. Please:" -ForegroundColor Red
    Write-Host "1. Restart Docker Desktop manually" -ForegroundColor Yellow
    Write-Host "2. Wait for it to fully start (check the system tray)" -ForegroundColor Yellow
    Write-Host "3. Run this script again" -ForegroundColor Yellow
}

# Display current Docker version info
Write-Host "`nCurrent Docker configuration:" -ForegroundColor Cyan
docker version 2>&1 | Select-Object -First 10


# Restart services to apply frontend changes
$ErrorActionPreference = "Stop"

$APP_SERVER = "43.143.139.197"
$APP_SERVER_KEY = ".\enterprise_ai_platform.pem"
$APP_SERVER_USER = "ubuntu"
$REMOTE_BASE = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Restarting services to apply changes" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Change to project root
Set-Location (Split-Path -Parent $PSScriptRoot)

$sshTarget = "${APP_SERVER_USER}@${APP_SERVER}"

# Restart web-ui to apply frontend changes
Write-Host "`n[1/2] Restarting web-ui service..." -ForegroundColor Yellow
try {
    $restartCmd = "cd $REMOTE_BASE; docker compose restart web-ui 2>&1"
    $restartOutput = ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget $restartCmd 2>&1
    
    if ($LASTEXITCODE -eq 0 -or $restartOutput -match "Restarting") {
        Write-Host "  ✅ Web-ui service restart initiated" -ForegroundColor Green
        Write-Host "  ⏳ Waiting 15 seconds for service to rebuild..." -ForegroundColor Yellow
        Start-Sleep -Seconds 15
    } else {
        Write-Host "  ⚠️  Service restart may have issues, but continuing..." -ForegroundColor Yellow
        Start-Sleep -Seconds 15
    }
} catch {
    Write-Host "  ⚠️  Restart command error: $_" -ForegroundColor Yellow
}

# Verify metadata-service is running (should already be restarted)
Write-Host "`n[2/2] Verifying metadata-service status..." -ForegroundColor Yellow
try {
    $statusCmd = "cd $REMOTE_BASE; docker compose ps metadata-service --format '{{.Status}}'"
    $statusOutput = ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget $statusCmd 2>&1
    
    if ($statusOutput -match "Up|running") {
        Write-Host "  ✅ Metadata-service is running" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Metadata-service status: $statusOutput" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠️  Could not check metadata-service status" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Service restart completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nNote: Frontend changes may take a few minutes to rebuild." -ForegroundColor Yellow
Write-Host "Please refresh the browser page after a minute or two." -ForegroundColor Yellow
Write-Host "`n"


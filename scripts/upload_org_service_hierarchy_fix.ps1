# Upload organization service hierarchy fix
$ErrorActionPreference = "Stop"

$APP_SERVER = "43.143.139.197"
$APP_SERVER_KEY = ".\enterprise_ai_platform.pem"
$APP_SERVER_USER = "ubuntu"
$REMOTE_BASE = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Uploading organization service hierarchy fix" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Change to project root
Set-Location (Split-Path -Parent $PSScriptRoot)

$sshTarget = "${APP_SERVER_USER}@${APP_SERVER}"

# Upload service file
$serviceFile = "metadata-service/src/services/organization_architecture_service.py"
$remoteFile = "$REMOTE_BASE/$serviceFile"
$remoteDir = Split-Path -Path $remoteFile -Parent

Write-Host "`nUploading: $serviceFile" -ForegroundColor Yellow

try {
    ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget "mkdir -p $remoteDir" 2>&1 | Out-Null
    scp -i $APP_SERVER_KEY -o ConnectTimeout=10 $serviceFile "${sshTarget}:$remoteFile" 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Uploaded successfully" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Upload failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ❌ Upload error: $_" -ForegroundColor Red
    exit 1
}

# Restart metadata-service
Write-Host "`nRestarting metadata-service..." -ForegroundColor Yellow
try {
    $restartCmd = "cd $REMOTE_BASE; docker compose restart metadata-service 2>&1"
    $restartOutput = ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget $restartCmd 2>&1
    
    if ($LASTEXITCODE -eq 0 -or $restartOutput -match "Restarting") {
        Write-Host "  ✅ Service restart initiated" -ForegroundColor Green
        Write-Host "  ⏳ Waiting 8 seconds for service to start..." -ForegroundColor Yellow
        Start-Sleep -Seconds 8
    }
} catch {
    Write-Host "  ⚠️  Restart error: $_" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Upload completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`n"


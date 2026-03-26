# Upload organization architecture fix to server
$ErrorActionPreference = "Stop"

$APP_SERVER = "43.143.139.197"
$APP_SERVER_KEY = ".\enterprise_ai_platform.pem"
$APP_SERVER_USER = "ubuntu"
$REMOTE_BASE = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Uploading organization architecture fix" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Files to upload
$files = @(
    "metadata-service/src/services/enterprise_architecture_service.py",
    "api-gateway/src/routes/enterprise_architecture.py",
    "web-ui/src/app/enterprise-architecture/page.tsx",
    "web-ui/src/services/enterpriseArchitectureService.ts"
)

$sshTarget = "${APP_SERVER_USER}@${APP_SERVER}"

# Upload files
Write-Host "`nUploading files..." -ForegroundColor Yellow
$successCount = 0
$failCount = 0

foreach ($file in $files) {
    $remoteFile = "$REMOTE_BASE/$file"
    $remoteDir = Split-Path -Path $remoteFile -Parent
    
    Write-Host "`nUploading: $file" -ForegroundColor Cyan
    
    try {
        # Create remote directory
        ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget "mkdir -p $remoteDir" 2>&1 | Out-Null
        
        # Upload file
        scp -i $APP_SERVER_KEY -o ConnectTimeout=10 $file "${sshTarget}:$remoteFile" 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Success" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "  Failed (exit code: $LASTEXITCODE)" -ForegroundColor Red
            $failCount++
        }
    } catch {
        Write-Host "  Failed: $_" -ForegroundColor Red
        $failCount++
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Upload result: Success $successCount, Failed $failCount" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Yellow" })
Write-Host "========================================" -ForegroundColor Cyan

if ($failCount -gt 0) {
    Write-Host "`nWarning: Some files failed to upload" -ForegroundColor Yellow
    exit 1
}

# Restart services
Write-Host "`nRestarting services..." -ForegroundColor Yellow

# Restart metadata-service
Write-Host "Restarting metadata-service..." -ForegroundColor Cyan
try {
    ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget "cd $REMOTE_BASE && docker compose restart metadata-service" 2>&1
    Write-Host "  Metadata service restarted" -ForegroundColor Green
} catch {
    Write-Host "  Metadata service restart failed: $_" -ForegroundColor Red
}

# Restart api-gateway
Write-Host "Restarting api-gateway..." -ForegroundColor Cyan
try {
    ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget "cd $REMOTE_BASE && docker compose restart api-gateway" 2>&1
    Write-Host "  API Gateway restarted" -ForegroundColor Green
} catch {
    Write-Host "  API Gateway restart failed: $_" -ForegroundColor Red
}

# Restart web-ui
Write-Host "Restarting web-ui..." -ForegroundColor Cyan
try {
    ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget "cd $REMOTE_BASE && docker compose restart web-ui" 2>&1
    Write-Host "  Web UI restarted" -ForegroundColor Green
} catch {
    Write-Host "  Web UI restart failed: $_" -ForegroundColor Red
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Upload and deployment completed" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan


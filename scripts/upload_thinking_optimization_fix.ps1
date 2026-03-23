# Upload thinking chunk optimization fix to server
$ErrorActionPreference = "Stop"

# Change to project root directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

$APP_SERVER = "43.143.139.197"
$APP_SERVER_KEY = ".\enterprise_ai_platform.pem"
$APP_SERVER_USER = "ubuntu"
$REMOTE_BASE = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Uploading thinking chunk optimization fix" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Files to upload
$files = @(
    "agent-service/src/core/dynamic_workflow_designer.py",
    "web-ui/src/components/ChatInterface.tsx"
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
try {
    ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget "cd $REMOTE_BASE && docker compose restart agent-service web-ui" 2>&1
    Write-Host "  Services restarted" -ForegroundColor Green
} catch {
    Write-Host "  Service restart failed: $_" -ForegroundColor Red
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Upload and deployment completed" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan


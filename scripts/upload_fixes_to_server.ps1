# Upload fixed files to server
$ErrorActionPreference = "Stop"

$APP_SERVER = "43.143.139.197"
$APP_SERVER_KEY = ".\enterprise_ai_platform.pem"
$APP_SERVER_USER = "ubuntu"
$REMOTE_BASE = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Uploading fixed files to server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Files to upload
$files = @(
    "web-ui/src/components/ChatInterface.tsx",
    "web-ui/src/components/DynamicWorkflowDisplay.tsx",
    "agent-service/src/core/agents/data_clean_agent.py",
    "agent-service/src/core/dynamic_execution_engine.py"
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

# Restart agent-service
Write-Host "Restarting agent-service..." -ForegroundColor Cyan
try {
    ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget "cd $REMOTE_BASE && docker compose restart agent-service" 2>&1
    Write-Host "  Agent service restarted" -ForegroundColor Green
} catch {
    Write-Host "  Agent service restart failed: $_" -ForegroundColor Red
}

# Restart web-ui (may need rebuild)
Write-Host "Restarting web-ui..." -ForegroundColor Cyan
try {
    ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget "cd $REMOTE_BASE && docker compose restart web-ui" 2>&1
    Write-Host "  Web UI restarted (may need rebuild)" -ForegroundColor Green
} catch {
    Write-Host "  Web UI restart failed: $_" -ForegroundColor Red
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Upload and deployment completed" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan


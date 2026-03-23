# Upload analysis result beautification
$ErrorActionPreference = "Stop"

$APP_SERVER = "43.143.139.197"
$APP_SERVER_KEY = ".\enterprise_ai_platform.pem"
$APP_SERVER_USER = "ubuntu"
$REMOTE_BASE = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Uploading analysis result beautification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Change to project root
Set-Location (Split-Path -Parent $PSScriptRoot)

$sshTarget = "${APP_SERVER_USER}@${APP_SERVER}"

# Files to upload
$files = @(
    "web-ui/src/components/MessageContent.tsx",
    "web-ui/src/app/message-styles.css"
)

$successCount = 0
$failCount = 0

foreach ($file in $files) {
    $remoteFile = "$REMOTE_BASE/$file"
    $remoteDir = Split-Path -Path $remoteFile -Parent
    
    Write-Host "`nUploading: $file" -ForegroundColor Yellow
    
    try {
        ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget "mkdir -p $remoteDir" 2>&1 | Out-Null
        scp -i $APP_SERVER_KEY -o ConnectTimeout=10 $file "${sshTarget}:$remoteFile" 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ Uploaded successfully" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "  ❌ Upload failed" -ForegroundColor Red
            $failCount++
        }
    } catch {
        Write-Host "  ❌ Upload error: $_" -ForegroundColor Red
        $failCount++
    }
}

# Restart web-ui
Write-Host "`nRestarting web-ui service..." -ForegroundColor Yellow
try {
    $restartCmd = "cd $REMOTE_BASE; docker compose restart web-ui 2>&1"
    $restartOutput = ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget $restartCmd 2>&1
    
    if ($LASTEXITCODE -eq 0 -or $restartOutput -match "Restarting") {
        Write-Host "  ✅ Service restart initiated" -ForegroundColor Green
        Write-Host "  ⏳ Waiting 20 seconds for rebuild..." -ForegroundColor Yellow
        Start-Sleep -Seconds 20
    }
} catch {
    Write-Host "  ⚠️  Restart error: $_" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Upload Summary: Success $successCount, Failed $failCount" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Yellow" })
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nNote: Please refresh the browser page after rebuild completes to see the beautified analysis results." -ForegroundColor Yellow
Write-Host "`n"


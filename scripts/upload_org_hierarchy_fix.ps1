# Upload organization hierarchy fix
$ErrorActionPreference = "Stop"

$APP_SERVER = "43.143.139.197"
$APP_SERVER_KEY = ".\enterprise_ai_platform.pem"
$APP_SERVER_USER = "ubuntu"
$REMOTE_BASE = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Uploading organization hierarchy fix" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Change to project root
Set-Location (Split-Path -Parent $PSScriptRoot)

$sshTarget = "${APP_SERVER_USER}@${APP_SERVER}"

# Files to upload
$files = @(
    "web-ui/src/services/enterpriseArchitectureService.ts",
    "web-ui/src/app/enterprise-architecture/organization/page.tsx"
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
    ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget $restartCmd 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Service restart initiated" -ForegroundColor Green
        Write-Host "  ⏳ Waiting 15 seconds for rebuild..." -ForegroundColor Yellow
        Start-Sleep -Seconds 15
    }
} catch {
    Write-Host "  ⚠️  Restart error: $_" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Upload Summary: Success $successCount, Failed $failCount" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Yellow" })
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nNote: Please refresh the browser page after a minute to see the changes." -ForegroundColor Yellow
Write-Host "`n"


# Verify that modified files are uploaded to server
$ErrorActionPreference = "Stop"

$APP_SERVER = "43.143.139.197"
$APP_SERVER_KEY = ".\enterprise_ai_platform.pem"
$APP_SERVER_USER = "ubuntu"
$REMOTE_BASE = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verifying uploaded files on server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Change to project root
Set-Location (Split-Path -Parent $PSScriptRoot)

$sshTarget = "${APP_SERVER_USER}@${APP_SERVER}"

# Files to check
$filesToCheck = @(
    @{
        LocalPath = "metadata-service/src/services/organization_architecture_service.py"
        RemotePath = "$REMOTE_BASE/metadata-service/src/services/organization_architecture_service.py"
        CheckContent = "get_all_organizations"
        Description = "Organization Architecture Service (with get_all_organizations method)"
    },
    @{
        LocalPath = "web-ui/src/components/MessageContent.tsx"
        RemotePath = "$REMOTE_BASE/web-ui/src/components/MessageContent.tsx"
        CheckContent = "status-icon"
        Description = "MessageContent component (with status icons)"
    },
    @{
        LocalPath = "web-ui/src/app/message-styles.css"
        RemotePath = "$REMOTE_BASE/web-ui/src/app/message-styles.css"
        CheckContent = "status-icon.status-success"
        Description = "Message styles (with status icon styles)"
    },
    @{
        LocalPath = "web-ui/src/components/DynamicWorkflowDisplay.tsx"
        RemotePath = "$REMOTE_BASE/web-ui/src/components/DynamicWorkflowDisplay.tsx"
        CheckContent = "prose prose-lg"
        Description = "DynamicWorkflowDisplay (with beautified final result)"
    },
    @{
        LocalPath = "web-ui/src/components/ChatInterface.tsx"
        RemotePath = "$REMOTE_BASE/web-ui/src/components/ChatInterface.tsx"
        CheckContent = "thinkingContent = rawMessage"
        Description = "ChatInterface (with thinking content persistence fix)"
    }
)

$allPassed = $true
$passedCount = 0
$failedCount = 0

foreach ($file in $filesToCheck) {
    Write-Host "`nChecking: $($file.Description)" -ForegroundColor Yellow
    Write-Host "  Local:  $($file.LocalPath)" -ForegroundColor Gray
    Write-Host "  Remote: $($file.RemotePath)" -ForegroundColor Gray
    
    try {
        # Check if file exists on server
        $checkCmd = "test -f '$($file.RemotePath)' && echo 'EXISTS' || echo 'NOT_FOUND'"
        $existsResult = ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget $checkCmd 2>&1
        
        if ($existsResult -match "NOT_FOUND") {
            Write-Host "  ❌ File not found on server" -ForegroundColor Red
            $allPassed = $false
            $failedCount++
            continue
        }
        
        # Check if file contains expected content
        $contentCheckCmd = "grep -q '$($file.CheckContent)' '$($file.RemotePath)' && echo 'FOUND' || echo 'NOT_FOUND'"
        $contentResult = ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget $contentCheckCmd 2>&1
        
        if ($contentResult -match "FOUND") {
            Write-Host "  ✅ File exists and contains expected content" -ForegroundColor Green
            $passedCount++
        } else {
            Write-Host "  ⚠️  File exists but may not contain expected content" -ForegroundColor Yellow
            Write-Host "     Expected: $($file.CheckContent)" -ForegroundColor Gray
            $allPassed = $false
            $failedCount++
        }
    } catch {
        Write-Host "  ❌ Error checking file: $_" -ForegroundColor Red
        $allPassed = $false
        $failedCount++
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Verification Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Passed: $passedCount" -ForegroundColor Green
Write-Host "Failed: $failedCount" -ForegroundColor $(if ($failedCount -eq 0) { "Green" } else { "Red" })
Write-Host "Total:  $($filesToCheck.Count)" -ForegroundColor Cyan

if ($allPassed) {
    Write-Host "`n✅ All files verified successfully!" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Some files may need to be re-uploaded" -ForegroundColor Yellow
    Write-Host "`nTo upload missing files, run:" -ForegroundColor Yellow
    Write-Host "  scripts\upload_and_init_org_data.ps1" -ForegroundColor White
    Write-Host "  (or create a new upload script for frontend files)" -ForegroundColor White
}

Write-Host "`n"


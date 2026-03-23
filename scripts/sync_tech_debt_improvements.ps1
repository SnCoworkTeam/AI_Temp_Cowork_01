# Sync Technical Debt Improvements to Server
# 同步技术债务改进文件到服务器

param(
    [string]$ServerHost = "43.143.139.197",
    [string]$ServerUser = "ubuntu",
    [string]$ServerKey = "E:\enterprise-ai-platform\enterprise_ai_platform.pem",
    [string]$RemotePath = "/opt/enterprise-ai-platform",
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Sync Technical Debt Improvements" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check key file
if (-not (Test-Path $ServerKey)) {
    Write-Host "[ERROR] Server key file not found: $ServerKey" -ForegroundColor Red
    exit 1
}

# Test SSH connection
Write-Host "[INFO] Testing SSH connection..." -ForegroundColor Yellow
try {
    $testResult = ssh -i $ServerKey -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$ServerUser@$ServerHost" "echo 'Connection OK'" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] SSH connection successful" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] SSH connection failed: $testResult" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "[ERROR] SSH connection test failed: $_" -ForegroundColor Red
    exit 1
}

# Files to sync
$PROJECT_ROOT = "E:\enterprise-ai-platform"
$filesToSync = @(
    "os-core/monitoring.py",
    "os-core/resource_registry.py",
    "os-core/__init__.py",
    "agent-service/src/services/metadata_client.py",
    "tests/milestone_integration_test.py",
    "tests/test_performance.py",
    "scripts/init_ea_data_automated.py",
    "docs/API_ENDPOINTS.md"
)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Syncing Files" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$successCount = 0
$failCount = 0

foreach ($file in $filesToSync) {
    $localPath = Join-Path $PROJECT_ROOT $file
    
    if (-not (Test-Path $localPath)) {
        Write-Host "[WARN] File not found: $file" -ForegroundColor Yellow
        $failCount++
        continue
    }
    
    $remoteFile = "$RemotePath/$file"
    $remoteDir = $remoteFile -replace '/[^/]+$', ''
    
    Write-Host "[INFO] Syncing: $file" -ForegroundColor Yellow
    Write-Host "       Local: $localPath" -ForegroundColor Gray
    Write-Host "       Remote: $remoteFile" -ForegroundColor Gray
    
    if (-not $DryRun) {
        # Create remote directory
        $createDirCmd = "mkdir -p `"$remoteDir`""
        ssh -i $ServerKey -o StrictHostKeyChecking=no "$ServerUser@$ServerHost" $createDirCmd | Out-Null
        
        # Copy file
        scp -i $ServerKey -o StrictHostKeyChecking=no "$localPath" "${ServerUser}@${ServerHost}:${remoteFile}" 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] Sync successful" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "[ERROR] Sync failed" -ForegroundColor Red
            $failCount++
        }
    } else {
        Write-Host "[DRY-RUN] Would sync this file" -ForegroundColor Cyan
        $successCount++
    }
    
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Sync Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Success: $successCount" -ForegroundColor Green
Write-Host "Failed: $failCount" -ForegroundColor $(if ($failCount -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($failCount -eq 0) {
    Write-Host "[OK] All files synced successfully!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "[WARN] Some files failed to sync" -ForegroundColor Yellow
    exit 1
}


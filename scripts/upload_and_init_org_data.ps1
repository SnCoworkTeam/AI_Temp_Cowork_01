# Upload organization service fix and initialize data
$ErrorActionPreference = "Stop"

$APP_SERVER = "43.143.139.197"
$APP_SERVER_KEY = ".\enterprise_ai_platform.pem"
$APP_SERVER_USER = "ubuntu"
$REMOTE_BASE = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Uploading organization service fix and initializing data" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Change to project root
Set-Location (Split-Path -Parent $PSScriptRoot)

$sshTarget = "${APP_SERVER_USER}@${APP_SERVER}"

# Step 1: Upload fixed service file
Write-Host "`n[1/4] Uploading fixed service file..." -ForegroundColor Yellow
$serviceFile = "metadata-service/src/services/organization_architecture_service.py"
$remoteFile = "$REMOTE_BASE/$serviceFile"
$remoteDir = Split-Path -Path $remoteFile -Parent

try {
    ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget "mkdir -p $remoteDir" 2>&1 | Out-Null
    scp -i $APP_SERVER_KEY -o ConnectTimeout=10 $serviceFile "${sshTarget}:$remoteFile" 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Service file uploaded successfully" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Service file upload failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ❌ Upload failed: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Upload initialization script
Write-Host "`n[2/4] Uploading initialization script..." -ForegroundColor Yellow
$initScript = "scripts/init_organization_data.py"
$remoteInitScript = "$REMOTE_BASE/$initScript"
$remoteInitDir = Split-Path -Path $remoteInitScript -Parent

try {
    ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget "mkdir -p $remoteInitDir" 2>&1 | Out-Null
    scp -i $APP_SERVER_KEY -o ConnectTimeout=10 $initScript "${sshTarget}:$remoteInitScript" 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Initialization script uploaded successfully" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Initialization script upload failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ❌ Upload failed: $_" -ForegroundColor Red
    exit 1
}

# Step 3: Restart metadata-service
Write-Host "`n[3/4] Restarting metadata-service..." -ForegroundColor Yellow
try {
    $restartCmd = "cd $REMOTE_BASE; docker compose restart metadata-service 2>&1"
    $restartOutput = ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget $restartCmd 2>&1
    
    # Check if restart command succeeded (exit code 0) or if container is restarting
    if ($LASTEXITCODE -eq 0 -or $restartOutput -match "Restarting") {
        Write-Host "  ✅ Service restart initiated" -ForegroundColor Green
        Write-Host "  ⏳ Waiting 10 seconds for service to start..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
    } else {
        Write-Host "  ⚠️  Service restart may have issues, but continuing..." -ForegroundColor Yellow
        Write-Host "  ⏳ Waiting 10 seconds..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
    }
} catch {
    Write-Host "  ⚠️  Restart command error: $_" -ForegroundColor Yellow
    Write-Host "  ⏳ Waiting 10 seconds anyway..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
}

# Step 4: Run initialization script inside container
Write-Host "`n[4/4] Running initialization script in container..." -ForegroundColor Yellow
try {
    # Read the Python script content
    $scriptContent = Get-Content -Path $initScript -Raw -Encoding UTF8
    $scriptContent = $scriptContent -replace '"', '\"' -replace "`n", "`n" -replace "`r", ""
    
    # Create a Python one-liner command to execute the script
    # We'll use a simpler approach: copy file and run it
    $copyCmd = "cd $REMOTE_BASE; docker compose cp $remoteInitScript metadata-service:/tmp/init_org_data.py 2>&1"
    $copyOutput = ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget $copyCmd 2>&1
    
    if ($copyOutput -match "Copying|Error") {
        Write-Host "  File copy status: $copyOutput" -ForegroundColor Cyan
    }
    
    # Wait a moment for file to be available
    Start-Sleep -Seconds 2
    
    # Run the script inside container
    $runCmd = "cd $REMOTE_BASE; docker compose exec -T metadata-service python /tmp/init_org_data.py 2>&1"
    $output = ssh -i $APP_SERVER_KEY -o ConnectTimeout=30 $sshTarget $runCmd 2>&1
    
    Write-Host $output
    
    if ($LASTEXITCODE -eq 0 -or $output -match "成功创建|already exists|Created|Successfully") {
        Write-Host "`n  ✅ Data initialization completed" -ForegroundColor Green
    } else {
        Write-Host "`n  ⚠️  Data initialization may have issues, check output above" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠️  Data initialization error: $_" -ForegroundColor Yellow
    Write-Host "  You may need to run the script manually on the server" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Deployment completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Check the organization page: http://43.143.139.197:3000/enterprise-architecture/organization" -ForegroundColor White
Write-Host "2. Refresh the page to see the new data" -ForegroundColor White
Write-Host "`n"


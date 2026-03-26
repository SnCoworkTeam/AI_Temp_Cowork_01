# Upload project management service to server and start it
$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"
$SERVER_PATH = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  Upload Project Management Service" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check key file
if (-not (Test-Path $SSH_KEY)) {
    $SSH_KEY = "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem"
    if (-not (Test-Path $SSH_KEY)) {
        Write-Host "Error: Key file not found" -ForegroundColor Red
        exit 1
    }
}

# Test SSH connection
Write-Host "Testing SSH connection..." -ForegroundColor Cyan
$test = ssh -i $SSH_KEY -o ConnectTimeout=5 -o StrictHostKeyChecking=no $SERVER "echo OK" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "SSH connection failed!" -ForegroundColor Red
    Write-Host $test
    exit 1
}
Write-Host "SSH connection successful" -ForegroundColor Green
Write-Host ""

# Upload project management service
Write-Host "Uploading project management service..." -ForegroundColor Cyan
if (Test-Path "project-management") {
    Write-Host "  Uploading project-management directory..." -ForegroundColor Yellow
    scp -i $SSH_KEY -r -o StrictHostKeyChecking=no "project-management" "${SERVER}:${SERVER_PATH}/" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  project-management uploaded successfully" -ForegroundColor Green
    } else {
        Write-Host "  project-management upload failed" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  project-management directory not found" -ForegroundColor Yellow
}

# Upload web-ui menu changes
Write-Host ""
Write-Host "Uploading web-ui menu..." -ForegroundColor Cyan
if (Test-Path "web-ui/src/components/Layout/Sidebar.tsx") {
    Write-Host "  Uploading Sidebar.tsx..." -ForegroundColor Yellow
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "web-ui/src/components/Layout/Sidebar.tsx" "${SERVER}:${SERVER_PATH}/web-ui/src/components/Layout/" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Sidebar.tsx uploaded successfully" -ForegroundColor Green
    } else {
        Write-Host "  Sidebar.tsx upload failed" -ForegroundColor Red
    }
}

# Upload docker-compose.yml if needed
Write-Host ""
Write-Host "Checking docker-compose.yml..." -ForegroundColor Cyan
if (Test-Path "docker-compose.yml") {
    Write-Host "  Uploading docker-compose.yml..." -ForegroundColor Yellow
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "docker-compose.yml" "${SERVER}:${SERVER_PATH}/" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  docker-compose.yml uploaded successfully" -ForegroundColor Green
    }
}

# Upload database models if needed
Write-Host ""
Write-Host "Checking database models..." -ForegroundColor Cyan
if (Test-Path "database/src/models/project_models.py") {
    Write-Host "  Uploading project_models.py..." -ForegroundColor Yellow
    $remoteDir = "$SERVER_PATH/database/src/models"
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p $remoteDir" 2>&1 | Out-Null
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "database/src/models/project_models.py" "${SERVER}:${remoteDir}/" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  project_models.py uploaded successfully" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Starting service on server..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Execute commands on server
Write-Host "Checking project management service status..." -ForegroundColor Cyan
$cmd1 = 'cd ' + $SERVER_PATH + '; docker compose ps project-management'
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $cmd1

Write-Host ""
Write-Host "Starting project management service..." -ForegroundColor Cyan
$cmd2 = 'cd ' + $SERVER_PATH + '; docker compose up -d --build project-management'
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $cmd2

Write-Host ""
Write-Host "Waiting for service to start..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "Checking service status..." -ForegroundColor Cyan
$cmd3 = 'cd ' + $SERVER_PATH + '; docker compose ps project-management'
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $cmd3

Write-Host ""
Write-Host "Checking service logs (last 20 lines)..." -ForegroundColor Cyan
$cmd4 = 'cd ' + $SERVER_PATH + '; docker compose logs --tail=20 project-management'
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $cmd4

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Access service: http://43.143.139.197:8016/api/health" -ForegroundColor Yellow
Write-Host "  2. Access admin panel: http://43.143.139.197/admin/projects" -ForegroundColor Yellow
Write-Host "  3. Check service logs: ssh -i $SSH_KEY $SERVER 'docker compose logs -f project-management'" -ForegroundColor Yellow

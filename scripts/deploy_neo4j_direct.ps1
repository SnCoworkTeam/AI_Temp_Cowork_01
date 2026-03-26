# Direct Neo4j Deployment - No Interactive Prompts

$ErrorActionPreference = "Stop"

# Configuration
$NEO4J_KEY = ".\Neo4j.pem"
$NEO4J_SERVER_HOST = "43.143.90.179"
$NEO4J_SERVER_USER = "ubuntu"
$NEO4J_PROJECT_DIR = "/opt/neo4j-enterprise-ai"
$NEO4J_PASSWORD = "neo4j_password"

Write-Host "========================================" -ForegroundColor Green
Write-Host "Neo4j Deployment" -ForegroundColor Green
Write-Host "Server: $NEO4J_SERVER_USER@$NEO4J_SERVER_HOST" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green

# Check key file
if (-not (Test-Path $NEO4J_KEY)) {
    Write-Host "Error: Key file not found: $NEO4J_KEY" -ForegroundColor Red
    exit 1
}

# 1. Test connection
Write-Host "`n1. Testing connection..." -ForegroundColor Yellow
$result = ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$NEO4J_SERVER_USER@$NEO4J_SERVER_HOST" "echo 'OK'" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Connected" -ForegroundColor Green
} else {
    Write-Host "Connection failed: $result" -ForegroundColor Red
    exit 1
}

# 2. Create directory
Write-Host "`n2. Creating directory..." -ForegroundColor Yellow
ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no "$NEO4J_SERVER_USER@$NEO4J_SERVER_HOST" "mkdir -p $NEO4J_PROJECT_DIR"

# 3. Upload docker-compose
Write-Host "`n3. Uploading docker-compose file..." -ForegroundColor Yellow
if (Test-Path "docker-compose.neo4j-standalone.yml") {
    scp -i $NEO4J_KEY -o StrictHostKeyChecking=no "docker-compose.neo4j-standalone.yml" "${NEO4J_SERVER_USER}@${NEO4J_SERVER_HOST}:${NEO4J_PROJECT_DIR}/"
    Write-Host "Uploaded" -ForegroundColor Green
}

# 4. Create .env
Write-Host "`n4. Creating .env file..." -ForegroundColor Yellow
$envContent = "NEO4J_PASSWORD=$NEO4J_PASSWORD`nNEO4J_HTTP_PORT=7474`nNEO4J_BOLT_PORT=7687`nNEO4J_HTTPS_PORT=7473"
ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no "$NEO4J_SERVER_USER@$NEO4J_SERVER_HOST" "cat > $NEO4J_PROJECT_DIR/.env << 'EOF'
$envContent
EOF
"
Write-Host "Created" -ForegroundColor Green

# 5. Stop existing
Write-Host "`n5. Stopping existing service..." -ForegroundColor Yellow
ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no "$NEO4J_SERVER_USER@$NEO4J_SERVER_HOST" "cd $NEO4J_PROJECT_DIR; docker-compose -f docker-compose.neo4j-standalone.yml down 2>/dev/null; docker stop enterprise-ai-neo4j-standalone 2>/dev/null; echo 'Stopped'"

# 6. Start Neo4j
Write-Host "`n6. Starting Neo4j..." -ForegroundColor Yellow
ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no "$NEO4J_SERVER_USER@$NEO4J_SERVER_HOST" "cd $NEO4J_PROJECT_DIR; docker-compose -f docker-compose.neo4j-standalone.yml up -d"

# 7. Wait
Write-Host "`n7. Waiting 15 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# 8. Check status
Write-Host "`n8. Checking status..." -ForegroundColor Yellow
ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no "$NEO4J_SERVER_USER@$NEO4J_SERVER_HOST" "docker ps | grep neo4j"

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "Deployment Complete" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "HTTP: http://$NEO4J_SERVER_HOST`:7474" -ForegroundColor Cyan
Write-Host "Bolt: bolt://$NEO4J_SERVER_HOST`:7687" -ForegroundColor Cyan
Write-Host "User: neo4j" -ForegroundColor Cyan
Write-Host "Pass: $NEO4J_PASSWORD" -ForegroundColor Cyan


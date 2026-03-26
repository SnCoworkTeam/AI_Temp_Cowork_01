# Neo4j Graph Database Deployment Script

param(
    [string]$Neo4jHost = "43.143.90.179",
    [string]$Neo4jUser = "ubuntu",
    [string]$ProjectDir = "/opt/neo4j-enterprise-ai",
    [string]$Neo4jPassword = "neo4j_password"
)

$ErrorActionPreference = "Stop"

# Use Neo4j.pem key file
$NEO4J_KEY = ".\Neo4j.pem"
if (-not (Test-Path $NEO4J_KEY)) {
    Write-Host "Error: Neo4j key file not found: $NEO4J_KEY" -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "Neo4j Graph Database Deployment" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Using key file: $NEO4J_KEY" -ForegroundColor Green

# Get Neo4j host if not provided
if ([string]::IsNullOrWhiteSpace($Neo4jHost)) {
    $Neo4jHost = Read-Host "Neo4j Server Address (IP or Domain) [default: 43.143.90.179]"
    if ([string]::IsNullOrWhiteSpace($Neo4jHost)) {
        $Neo4jHost = "43.143.90.179"
    }
}

Write-Host "`nDeployment Configuration:" -ForegroundColor Blue
Write-Host "  Neo4j Server: $Neo4jUser@$Neo4jHost"
Write-Host "  Project Dir: $ProjectDir"
Write-Host "  Key File: $NEO4J_KEY"

$CONFIRM = Read-Host "`nConfirm deployment? (y/n)"
if ($CONFIRM -ne "y" -and $CONFIRM -ne "Y") {
    Write-Host "Deployment cancelled" -ForegroundColor Yellow
    exit 0
}

# 1. Test SSH connection
Write-Host "`n1. Testing SSH connection..." -ForegroundColor Yellow
$result = ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$Neo4jUser@$Neo4jHost" "echo 'Connected'" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Success: Neo4j server connected" -ForegroundColor Green
} else {
    Write-Host "Failed: Neo4j server connection failed" -ForegroundColor Red
    Write-Host "Error: $result" -ForegroundColor Red
    exit 1
}

# 2. Check Docker
Write-Host "`n2. Checking Docker environment..." -ForegroundColor Yellow
ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no "$Neo4jUser@$Neo4jHost" "docker --version; docker-compose --version"

# 3. Create project directory
Write-Host "`n3. Creating project directory..." -ForegroundColor Yellow
ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no "$Neo4jUser@$Neo4jHost" "mkdir -p $ProjectDir; echo 'Directory created: $ProjectDir'"

# 4. Upload docker-compose file
Write-Host "`n4. Uploading Neo4j config files..." -ForegroundColor Yellow
if (Test-Path "docker-compose.neo4j-standalone.yml") {
    Write-Host "  Uploading docker-compose.neo4j-standalone.yml..."
    scp -i $NEO4J_KEY -o StrictHostKeyChecking=no "docker-compose.neo4j-standalone.yml" "${Neo4jUser}@${Neo4jHost}:${ProjectDir}/"
    Write-Host "  File uploaded successfully" -ForegroundColor Green
} else {
    Write-Host "  Warning: docker-compose.neo4j-standalone.yml not found" -ForegroundColor Yellow
}

# 5. Create .env file
Write-Host "`n5. Creating environment file..." -ForegroundColor Yellow
$envContent = "NEO4J_PASSWORD=$Neo4jPassword`nNEO4J_HTTP_PORT=7474`nNEO4J_BOLT_PORT=7687`nNEO4J_HTTPS_PORT=7473"
$envFile = [System.IO.Path]::GetTempFileName()
$envContent | Out-File -FilePath $envFile -Encoding UTF8
scp -i $NEO4J_KEY -o StrictHostKeyChecking=no $envFile "${Neo4jUser}@${Neo4jHost}:${ProjectDir}/.env"
Remove-Item $envFile
Write-Host "Environment file created" -ForegroundColor Green

# 6. Stop existing service
Write-Host "`n6. Stopping existing Neo4j service..." -ForegroundColor Yellow
ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no "$Neo4jUser@$Neo4jHost" "cd $ProjectDir; if [ -f 'docker-compose.neo4j-standalone.yml' ]; then docker-compose -f docker-compose.neo4j-standalone.yml down 2>/dev/null; fi; docker stop enterprise-ai-neo4j-standalone 2>/dev/null; echo 'Existing service stopped'"

# 7. Start Neo4j service
Write-Host "`n7. Starting Neo4j service..." -ForegroundColor Yellow
ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no "$Neo4jUser@$Neo4jHost" "cd $ProjectDir; docker-compose -f docker-compose.neo4j-standalone.yml up -d; echo 'Neo4j service start command executed'"

# 8. Wait for service
Write-Host "`n8. Waiting for Neo4j service to start (15 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# 9. Check service status
Write-Host "`n9. Checking Neo4j service status..." -ForegroundColor Yellow
ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no "$Neo4jUser@$Neo4jHost" "echo 'Docker containers:'; docker ps | grep neo4j; echo ''; echo 'Ports:'; netstat -tlnp 2>/dev/null | grep -E '7474|7687' || ss -tlnp 2>/dev/null | grep -E '7474|7687' || echo 'Port check done'"

# 10. Test connection
Write-Host "`n10. Testing Neo4j connection..." -ForegroundColor Yellow
ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no "$Neo4jUser@$Neo4jHost" "docker exec enterprise-ai-neo4j-standalone cypher-shell -u neo4j -p $Neo4jPassword 'RETURN 1' 2>/dev/null && echo 'Neo4j connection test successful' || echo 'Neo4j may still be starting, please check later'"

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "Neo4j Deployment Complete" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nNeo4j Connection Info:" -ForegroundColor Cyan
Write-Host "  HTTP Web UI: http://$Neo4jHost`:7474"
Write-Host "  Bolt: bolt://$Neo4jHost`:7687"
Write-Host "  Username: neo4j"
Write-Host "  Password: $Neo4jPassword"
Write-Host "`nProject Directory: $ProjectDir"
Write-Host "`nPlease verify:" -ForegroundColor Yellow
Write-Host "  1. Web UI: http://$Neo4jHost`:7474"
Write-Host "  2. Bolt: bolt://$Neo4jHost`:7687"
Write-Host "  3. Logs: docker logs enterprise-ai-neo4j-standalone"

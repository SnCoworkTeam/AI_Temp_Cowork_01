# Quick Neo4j Deployment Script

param(
    [string]$Neo4jHost = "",
    [string]$Neo4jUser = "ubuntu",
    [string]$ProjectDir = "/opt/neo4j-enterprise-ai",
    [string]$Neo4jPassword = "neo4j_password"
)

$ErrorActionPreference = "Stop"

# Check key file
$NEO4J_KEY = "./Neo4j.pem"
if (-not (Test-Path $NEO4J_KEY)) {
    $NEO4J_KEY = "./enterprise_ai_platform.pem"
}

if (-not (Test-Path $NEO4J_KEY)) {
    Write-Host "Error: Key file not found" -ForegroundColor Red
    exit 1
}

# Get Neo4j host if not provided
if ([string]::IsNullOrWhiteSpace($Neo4jHost)) {
    $Neo4jHost = Read-Host "Neo4j Server Address (IP or Domain)"
}

if ([string]::IsNullOrWhiteSpace($Neo4jHost)) {
    Write-Host "Error: Neo4j server address required" -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "Deploying Neo4j to: $Neo4jHost" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# 1. Test connection
Write-Host "`n1. Testing connection..." -ForegroundColor Yellow
ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$Neo4jUser@$Neo4jHost" "echo 'Connected'" | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Connected successfully" -ForegroundColor Green
} else {
    Write-Host "Connection failed" -ForegroundColor Red
    exit 1
}

# 2. Create directory
Write-Host "`n2. Creating project directory..." -ForegroundColor Yellow
ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no "$Neo4jUser@$Neo4jHost" "mkdir -p $ProjectDir"

# 3. Upload docker-compose file
Write-Host "`n3. Uploading docker-compose file..." -ForegroundColor Yellow
if (Test-Path "docker-compose.neo4j-standalone.yml") {
    scp -i $NEO4J_KEY -o StrictHostKeyChecking=no "docker-compose.neo4j-standalone.yml" "$Neo4jUser@$Neo4jHost`:$ProjectDir/"
    Write-Host "Uploaded docker-compose.neo4j-standalone.yml" -ForegroundColor Green
}

# 4. Create .env file
Write-Host "`n4. Creating .env file..." -ForegroundColor Yellow
$envContent = "NEO4J_PASSWORD=$Neo4jPassword`nNEO4J_HTTP_PORT=7474`nNEO4J_BOLT_PORT=7687`nNEO4J_HTTPS_PORT=7473"
ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no "$Neo4jUser@$Neo4jHost" "cat > $ProjectDir/.env << 'EOF'
$envContent
EOF
"

# 5. Stop existing service
Write-Host "`n5. Stopping existing service..." -ForegroundColor Yellow
ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no "$Neo4jUser@$Neo4jHost" "cd $ProjectDir && docker-compose -f docker-compose.neo4j-standalone.yml down 2>/dev/null; docker stop enterprise-ai-neo4j-standalone 2>/dev/null; echo 'Stopped'"

# 6. Start Neo4j
Write-Host "`n6. Starting Neo4j service..." -ForegroundColor Yellow
ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no "$Neo4jUser@$Neo4jHost" "cd $ProjectDir && docker-compose -f docker-compose.neo4j-standalone.yml up -d"

# 7. Wait and check
Write-Host "`n7. Waiting for service to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

Write-Host "`n8. Checking service status..." -ForegroundColor Yellow
ssh -i $NEO4J_KEY -o StrictHostKeyChecking=no "$Neo4jUser@$Neo4jHost" "docker ps | grep neo4j"

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "Neo4j Deployment Complete" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nConnection Info:" -ForegroundColor Cyan
Write-Host "  HTTP: http://$Neo4jHost`:7474"
Write-Host "  Bolt: bolt://$Neo4jHost`:7687"
Write-Host "  User: neo4j"
Write-Host "  Password: $Neo4jPassword"


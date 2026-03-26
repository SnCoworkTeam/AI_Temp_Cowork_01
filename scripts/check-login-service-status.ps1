# PowerShell script: Check login service status
# For diagnosing login timeout issues

$serverIp = "43.143.139.197"

Write-Host "=== Checking services on server $serverIp ===" -ForegroundColor Cyan
Write-Host ""

# 1. Check API Gateway
Write-Host "1. Checking API Gateway (http://${serverIp}:8080)" -ForegroundColor Yellow
try {
    $apiGatewayUrl = "http://${serverIp}:8080/health"
    $response = Invoke-WebRequest -Uri $apiGatewayUrl -Method GET -TimeoutSec 5 -UseBasicParsing
    Write-Host "   [OK] API Gateway is healthy: $($response.StatusCode)" -ForegroundColor Green
    $healthData = $response.Content | ConvertFrom-Json
    Write-Host "   Status: $($healthData.status)" -ForegroundColor Green
    Write-Host "   Registry connection: $($healthData.registry_connection)" -ForegroundColor Green
} catch {
    Write-Host "   [FAIL] API Gateway is not accessible: $_" -ForegroundColor Red
    Write-Host "   Possible cause: API Gateway container is not running or port is not open" -ForegroundColor Red
}

Write-Host ""

# 2. Check Auth Service (via API Gateway)
Write-Host "2. Checking Auth Service (via API Gateway: http://${serverIp}:8080/api/auth/health)" -ForegroundColor Yellow
try {
    $authViaGatewayUrl = "http://${serverIp}:8080/api/auth/health"
    $response = Invoke-WebRequest -Uri $authViaGatewayUrl -Method GET -TimeoutSec 5 -UseBasicParsing
    Write-Host "   [OK] Auth Service (via API Gateway) is healthy: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "   [FAIL] Auth Service (via API Gateway) is not accessible: $_" -ForegroundColor Red
    Write-Host "   Possible cause: API Gateway cannot route to Auth Service or Auth Service is not running" -ForegroundColor Red
}

Write-Host ""

# 3. Check Auth Service (direct access)
Write-Host "3. Checking Auth Service (direct access: http://${serverIp}:8003)" -ForegroundColor Yellow
try {
    $authDirectUrl = "http://${serverIp}:8003/health"
    $response = Invoke-WebRequest -Uri $authDirectUrl -Method GET -TimeoutSec 5 -UseBasicParsing
    Write-Host "   [OK] Auth Service (direct access) is healthy: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "   [FAIL] Auth Service (direct access) is not accessible: $_" -ForegroundColor Red
    Write-Host "   Possible cause: Auth Service container is not running or port is not open" -ForegroundColor Red
}

Write-Host ""

# 4. Test login endpoint (via API Gateway)
Write-Host "4. Testing login endpoint (via API Gateway: http://${serverIp}:8080/api/auth/login)" -ForegroundColor Yellow
try {
    $body = @{
        username = "test"
        password = "test"
    } | ConvertTo-Json

    $loginViaGatewayUrl = "http://${serverIp}:8080/api/auth/login"
    $response = Invoke-WebRequest -Uri $loginViaGatewayUrl `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 5 `
        -UseBasicParsing
    
    Write-Host "   [OK] Login endpoint is accessible: $($response.StatusCode)" -ForegroundColor Green
    if ($response.StatusCode -eq 401) {
        Write-Host "   [INFO] 401 response is normal (invalid username or password)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   [FAIL] Login endpoint is not accessible: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "   HTTP Status Code: $statusCode" -ForegroundColor Red
    }
    Write-Host "   Possible cause: API Gateway cannot route to Auth Service or Auth Service is not running" -ForegroundColor Red
}

Write-Host ""

# 5. Test login endpoint (direct access to Auth Service)
Write-Host "5. Testing login endpoint (direct access: http://${serverIp}:8003/auth/login)" -ForegroundColor Yellow
try {
    $body = @{
        username = "test"
        password = "test"
    } | ConvertTo-Json

    $loginDirectUrl = "http://${serverIp}:8003/auth/login"
    $response = Invoke-WebRequest -Uri $loginDirectUrl `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 5 `
        -UseBasicParsing
    
    Write-Host "   [OK] Login endpoint is accessible: $($response.StatusCode)" -ForegroundColor Green
    if ($response.StatusCode -eq 401) {
        Write-Host "   [INFO] 401 response is normal (invalid username or password)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   [FAIL] Login endpoint is not accessible: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "   HTTP Status Code: $statusCode" -ForegroundColor Red
    }
    Write-Host "   Possible cause: Auth Service is not running or port is not open" -ForegroundColor Red
}

Write-Host ""

# 6. Check Web UI
Write-Host "6. Checking Web UI (http://${serverIp}:3000)" -ForegroundColor Yellow
try {
    $webUiUrl = "http://${serverIp}:3000"
    $response = Invoke-WebRequest -Uri $webUiUrl -Method GET -TimeoutSec 5 -UseBasicParsing
    Write-Host "   [OK] Web UI is accessible: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "   [FAIL] Web UI is not accessible: $_" -ForegroundColor Red
    Write-Host "   Possible cause: Web UI container is not running or port is not open" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Diagnosis complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Suggested fix steps:" -ForegroundColor Yellow
Write-Host "1. If API Gateway is not accessible, check container status: docker ps | grep api-gateway" -ForegroundColor White
Write-Host "2. If Auth Service is not accessible, check container status: docker ps | grep auth-service" -ForegroundColor White
Write-Host "3. Check service logs: docker-compose logs api-gateway" -ForegroundColor White
Write-Host "4. Check service logs: docker-compose logs auth-service" -ForegroundColor White
Write-Host "5. Check service registry: curl http://${serverIp}:8000/api/services" -ForegroundColor White
Write-Host "6. Restart services: docker-compose restart api-gateway auth-service" -ForegroundColor White


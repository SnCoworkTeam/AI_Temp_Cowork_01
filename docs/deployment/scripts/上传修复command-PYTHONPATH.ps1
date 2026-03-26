# PowerShell Script - Upload fixed docker-compose.yml to server
# Fixes PYTHONPATH in both environment and command sections
$keyPath = "E:\enterprise-ai-platform\enterprise_ai_platform.pem"
$server = "ubuntu@43.143.139.197"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Uploading fixed docker-compose.yml to server" -ForegroundColor Cyan
Write-Host "Fixing PYTHONPATH in command section" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Uploading docker-compose.yml..." -ForegroundColor Yellow
$result = scp -i $keyPath -o StrictHostKeyChecking=no docker-compose.yml "${server}:/opt/enterprise-ai-platform/" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] docker-compose.yml uploaded successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. SSH to server" -ForegroundColor White
    Write-Host "2. Execute: cd /opt/enterprise-ai-platform && sudo docker compose stop mcp-gateway && sudo docker compose rm -f mcp-gateway && sudo docker compose up -d mcp-gateway" -ForegroundColor White
    Write-Host "3. Wait 20 seconds and check logs: sudo docker compose logs --tail=30 mcp-gateway" -ForegroundColor White
} else {
    Write-Host "[FAIL] Upload failed: $result" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan


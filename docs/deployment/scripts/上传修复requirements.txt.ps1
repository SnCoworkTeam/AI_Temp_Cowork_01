# PowerShell Script - Upload fixed requirements.txt to server
$keyPath = "E:\enterprise-ai-platform\enterprise_ai_platform.pem"
$server = "ubuntu@43.143.139.197"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Uploading fixed mcp-gateway/requirements.txt to server" -ForegroundColor Cyan
Write-Host "Added cryptography dependency" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Uploading mcp-gateway/requirements.txt..." -ForegroundColor Yellow
$result = scp -i $keyPath -o StrictHostKeyChecking=no "mcp-gateway/requirements.txt" "${server}:/opt/enterprise-ai-platform/mcp-gateway/" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] requirements.txt uploaded successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. SSH to server" -ForegroundColor White
    Write-Host "2. Execute: cd /opt/enterprise-ai-platform && sudo docker compose stop mcp-gateway && sudo docker compose rm -f mcp-gateway && sudo docker compose up -d --build mcp-gateway" -ForegroundColor White
    Write-Host "3. Wait 60 seconds for build and check logs: sudo docker compose logs --tail=30 mcp-gateway" -ForegroundColor White
} else {
    Write-Host "[FAIL] Upload failed: $result" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan


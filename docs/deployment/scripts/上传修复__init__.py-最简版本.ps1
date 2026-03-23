# PowerShell Script - Upload minimal shared_libs/__init__.py to server
$keyPath = "E:\enterprise-ai-platform\enterprise_ai_platform.pem"
$server = "ubuntu@43.143.139.197"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Uploading minimal shared_libs/__init__.py to server" -ForegroundColor Cyan
Write-Host "Removing relative imports to fix package recognition" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Uploading shared_libs/__init__.py..." -ForegroundColor Yellow
$result = scp -i $keyPath -o StrictHostKeyChecking=no "shared_libs/__init__.py" "${server}:/opt/enterprise-ai-platform/shared_libs/" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] shared_libs/__init__.py uploaded successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. SSH to server" -ForegroundColor White
    Write-Host "2. Execute: cd /opt/enterprise-ai-platform && sudo docker compose restart mcp-gateway" -ForegroundColor White
    Write-Host "3. Wait 20 seconds and check logs: sudo docker compose logs --tail=30 mcp-gateway" -ForegroundColor White
} else {
    Write-Host "[FAIL] Upload failed: $result" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan


# PowerShell Script - Upload docker-compose.yml to server
$keyPath = "E:\enterprise-ai-platform\enterprise_ai_platform.pem"
$server = "ubuntu@43.143.139.197"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Uploading docker-compose.yml to server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Uploading docker-compose.yml..." -ForegroundColor Yellow
$result = scp -i $keyPath -o StrictHostKeyChecking=no docker-compose.yml "${server}:/opt/enterprise-ai-platform/" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] docker-compose.yml uploaded successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. SSH to server" -ForegroundColor White
    Write-Host "2. Execute the rebuild commands (see 立即修复-上传docker-compose并重建.txt)" -ForegroundColor White
} else {
    Write-Host "[FAIL] Upload failed: $result" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan


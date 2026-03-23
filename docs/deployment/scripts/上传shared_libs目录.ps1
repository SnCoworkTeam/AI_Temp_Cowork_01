# PowerShell Script - Upload shared_libs directory to server
$keyPath = "E:\enterprise-ai-platform\enterprise_ai_platform.pem"
$server = "ubuntu@43.143.139.197"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Uploading shared_libs directory to server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 使用 scp 递归上传整个目录
Write-Host "Uploading shared_libs directory (this may take a while)..." -ForegroundColor Yellow
$result = scp -i $keyPath -o StrictHostKeyChecking=no -r "shared_libs" "${server}:/opt/enterprise-ai-platform/" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] shared_libs directory uploaded successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. SSH to server" -ForegroundColor White
    Write-Host "2. Execute: cd /opt/enterprise-ai-platform && sudo docker compose restart mcp-gateway" -ForegroundColor White
    Write-Host "3. Wait 20 seconds and check logs: sudo docker compose logs --tail=30 mcp-gateway" -ForegroundColor White
} else {
    Write-Host "[FAIL] Upload failed: $result" -ForegroundColor Red
    Write-Host ""
    Write-Host "Try using rsync instead:" -ForegroundColor Yellow
    Write-Host "rsync -avz -e 'ssh -i $keyPath' shared_libs/ ${server}:/opt/enterprise-ai-platform/shared_libs/" -ForegroundColor White
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan


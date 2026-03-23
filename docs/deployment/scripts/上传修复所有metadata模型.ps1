# PowerShell Script - Upload all fixed model files to server
$keyPath = "E:\enterprise-ai-platform\enterprise_ai_platform.pem"
$server = "ubuntu@43.143.139.197"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Uploading fixed model files to server" -ForegroundColor Cyan
Write-Host "Fixing metadata reserved word in all models" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$files = @(
    @{Source="database/src/models/workflow_models.py"; Name="workflow_models.py"},
    @{Source="database/src/models/mcp_models.py"; Name="mcp_models.py"},
    @{Source="database/src/models/knowledge_models.py"; Name="knowledge_models.py"}
)

$successCount = 0
$failCount = 0

foreach ($file in $files) {
    Write-Host "Uploading $($file.Name)..." -ForegroundColor Yellow
    $result = scp -i $keyPath -o StrictHostKeyChecking=no $file.Source "${server}:/opt/enterprise-ai-platform/database/src/models/" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Success" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host "  [FAIL] Failed: $result" -ForegroundColor Red
        $failCount++
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Upload Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Success: $successCount" -ForegroundColor Green
Write-Host "Failed: $failCount" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($successCount -eq $files.Count) {
    Write-Host "All files uploaded successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. SSH to server" -ForegroundColor White
    Write-Host "2. Execute: cd /opt/enterprise-ai-platform && sudo docker compose restart mcp-gateway" -ForegroundColor White
    Write-Host "3. Wait 20 seconds and check logs: sudo docker compose logs --tail=30 mcp-gateway" -ForegroundColor White
} else {
    Write-Host "Some files failed to upload. Please check errors above." -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan


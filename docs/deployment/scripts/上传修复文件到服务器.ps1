# PowerShell Script - Upload fixed files to server
# Execute this script to upload all fixed files

$keyPath = "E:\enterprise-ai-platform\enterprise_ai_platform.pem"
$server = "ubuntu@43.143.139.197"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Uploading fixed files to server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$files = @(
    # Main compose file with redis-commander and LOG_LEVEL fix
    @{Source="docker-compose.yml"; Dest=""},
    # Requirements files with version fixes
    @{Source="shared_libs/requirements.txt"; Dest="shared_libs/"},
    @{Source="mcp-gateway/requirements.txt"; Dest="mcp-gateway/"},
    @{Source="workflow-engine/requirements.txt"; Dest="workflow-engine/"},
    @{Source="auth-service/requirements.txt"; Dest="auth-service/"},
    @{Source="knowledge-base/requirements.txt"; Dest="knowledge-base/"},
    @{Source="metadata-service/requirements.txt"; Dest="metadata-service/"},
    @{Source="database/requirements.txt"; Dest="database/"},
    # Dockerfile.dev files with pip mirror source
    @{Source="mcp-gateway/Dockerfile.dev"; Dest="mcp-gateway/"},
    @{Source="workflow-engine/Dockerfile.dev"; Dest="workflow-engine/"},
    @{Source="auth-service/Dockerfile.dev"; Dest="auth-service/"},
    @{Source="knowledge-base/Dockerfile.dev"; Dest="knowledge-base/"},
    @{Source="metadata-service/Dockerfile.dev"; Dest="metadata-service/"},
    # README
    @{Source="README.md"; Dest=""},
    # env.example
    @{Source="env.example"; Dest=""}
)

$successCount = 0
$failCount = 0

foreach ($file in $files) {
    Write-Host "Uploading $($file.Source)..." -ForegroundColor Yellow
    $destPath = if ($file.Dest) { "/opt/enterprise-ai-platform/$($file.Dest)" } else { "/opt/enterprise-ai-platform/" }
    
    $result = scp -i $keyPath -o StrictHostKeyChecking=no $file.Source "${server}:${destPath}" 2>&1
    
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
    Write-Host "1. SSH to server and execute the fix commands" -ForegroundColor White
    Write-Host "2. See '服务器修复命令.txt' for detailed steps" -ForegroundColor White
} else {
    Write-Host "Some files failed to upload. Please check errors above." -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan


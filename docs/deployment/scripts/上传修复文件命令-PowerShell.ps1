# PowerShell Script - Upload fixed requirements.txt files to server

$keyPath = "E:\enterprise-ai-platform\enterprise_ai_platform.pem"
$server = "ubuntu@43.143.139.197"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Uploading fixed requirements.txt files" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$files = @(
    @{Source="shared_libs/requirements.txt"; Dest="shared_libs/"},
    @{Source="mcp-gateway/requirements.txt"; Dest="mcp-gateway/"},
    @{Source="workflow-engine/requirements.txt"; Dest="workflow-engine/"},
    @{Source="auth-service/requirements.txt"; Dest="auth-service/"},
    @{Source="knowledge-base/requirements.txt"; Dest="knowledge-base/"},
    @{Source="metadata-service/requirements.txt"; Dest="metadata-service/"},
    @{Source="database/requirements.txt"; Dest="database/"},
    @{Source="README.md"; Dest=""}
)

foreach ($file in $files) {
    Write-Host "Uploading $($file.Source)..." -ForegroundColor Yellow
    $destPath = if ($file.Dest) { "/opt/enterprise-ai-platform/$($file.Dest)" } else { "/opt/enterprise-ai-platform/" }
    
    scp -i $keyPath -o StrictHostKeyChecking=no $file.Source "${server}:${destPath}" 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Success" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] Failed" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verifying upload..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$verify = ssh -i $keyPath -o StrictHostKeyChecking=no $server "cd /opt/enterprise-ai-platform && grep -h 'pydantic>=' shared_libs/requirements.txt mcp-gateway/requirements.txt 2>&1 | head -2"
if ($verify) {
    Write-Host "[OK] Verification successful:" -ForegroundColor Green
    $verify
} else {
    Write-Host "[WARN] Verification failed, please check files" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Upload completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

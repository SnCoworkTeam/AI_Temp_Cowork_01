# 检查服务状态
Write-Host "检查服务状态..." -ForegroundColor Cyan

# 检查sap-metadata-agent
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8015/api/sap-metadata/discover" -Method POST -ContentType "application/json" -Body '{"include_database":false,"include_odata":false,"build_semantic_index":false,"sync_to_metadata_service":false,"limit":1}' -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✓ sap-metadata-agent 运行正常" -ForegroundColor Green
} catch {
    Write-Host "✗ sap-metadata-agent 未运行或无法访问" -ForegroundColor Red
}

# 检查metadata-service
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8005/api/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✓ metadata-service 运行正常" -ForegroundColor Green
} catch {
    Write-Host "✗ metadata-service 未运行或无法访问" -ForegroundColor Red
}

# 检查dag-orchestrator
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8009/api/v1/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✓ dag-orchestrator 运行正常" -ForegroundColor Green
} catch {
    Write-Host "✗ dag-orchestrator 未运行或无法访问" -ForegroundColor Red
}



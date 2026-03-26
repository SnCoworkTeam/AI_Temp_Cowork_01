# 快速检查构建进度
Write-Host "`n检查SAP元数据构建进度..." -ForegroundColor Cyan
Write-Host ("=" * 50) -ForegroundColor Gray

# 1. 检查构建脚本
$pythonProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*python*"}
if ($pythonProcess) {
    $runtime = (Get-Date) - $pythonProcess.StartTime
    Write-Host "`n[运行中] 构建脚本" -ForegroundColor Green
    Write-Host "  进程ID: $($pythonProcess.Id)" -ForegroundColor White
    Write-Host "  运行时间: $([math]::Round($runtime.TotalMinutes, 1)) 分钟" -ForegroundColor White
} else {
    Write-Host "`n[未运行] 构建脚本已停止" -ForegroundColor Yellow
}

# 2. 检查服务处理进度
try {
    $body = '{"include_database":false,"include_odata":true,"build_semantic_index":false,"sync_to_metadata_service":false,"limit":1,"offset":0}'
    $response = Invoke-WebRequest -Uri "http://localhost:8015/api/sap-metadata/discover" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 10
    $result = $response.Content | ConvertFrom-Json
    $meta = $result.metadata
    
    $total = $meta.total_services
    $processed = $meta.processed_services
    $remaining = $total - $processed
    $progress = [math]::Round(($processed / $total) * 100, 1)
    $batches = [math]::Ceiling($remaining / 10)
    
    Write-Host "`nOData服务处理:" -ForegroundColor Cyan
    Write-Host "  总服务数: $total" -ForegroundColor White
    Write-Host "  已处理: $processed" -ForegroundColor Green
    Write-Host "  剩余: $remaining" -ForegroundColor $(if ($remaining -eq 0) { "Green" } else { "Yellow" })
    Write-Host "  进度: $progress%" -ForegroundColor $(if ($progress -ge 100) { "Green" } else { "Cyan" })
    
    if ($remaining -gt 0) {
        Write-Host "  预计剩余批次: $batches" -ForegroundColor Cyan
        $estimatedMinutes = [math]::Round(($batches * 60) / 60, 1)
        Write-Host "  预计剩余时间: ~$estimatedMinutes 分钟" -ForegroundColor Yellow
    } else {
        Write-Host "`n  [SUCCESS] 所有服务已处理完成！" -ForegroundColor Green
    }
} catch {
    Write-Host "`n[ERROR] 无法获取服务处理进度: $_" -ForegroundColor Red
}

# 3. 检查数据资产总数
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8005/api/data-assets?limit=1&include_total=True" -TimeoutSec 10
    $total = [int]$response.Headers['X-Total-Count']
    Write-Host "`n数据资产总数: $total" -ForegroundColor Cyan
} catch {
    Write-Host "`n[ERROR] 无法获取数据资产总数" -ForegroundColor Red
}

Write-Host "`n" -ForegroundColor White

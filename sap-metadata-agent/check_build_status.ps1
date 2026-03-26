# 检查元数据构建状态
Write-Host "`n检查元数据构建状态..." -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# 1. 检查metadata-service中的数据资产总数
Write-Host "`n1. 检查metadata-service中的数据资产..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8005/api/data-assets?limit=1&include_total=True" -TimeoutSec 10 -ErrorAction Stop
    $totalAssets = $response.Headers['X-Total-Count']
    Write-Host "   数据资产总数: $totalAssets" -ForegroundColor Green
} catch {
    Write-Host "   无法连接到metadata-service" -ForegroundColor Red
    $totalAssets = 0
}

# 2. 检查sap-metadata-agent的服务总数和已处理数
Write-Host "`n2. 检查SAP OData服务处理状态..." -ForegroundColor Yellow
try {
    $body = @{
        include_database = $false
        include_odata = $true
        build_semantic_index = $false
        sync_to_metadata_service = $false
        limit = 1
        offset = 0
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "http://localhost:8015/api/sap-metadata/discover" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 10 -ErrorAction Stop
    $result = $response.Content | ConvertFrom-Json
    $metadata = $result.metadata
    
    $totalServices = $metadata.total_services
    $processedServices = $metadata.processed_services
    $hasMore = $metadata.has_more
    
    Write-Host "   总服务数: $totalServices" -ForegroundColor White
    Write-Host "   已处理服务数: $processedServices" -ForegroundColor White
    Write-Host "   还有更多: $hasMore" -ForegroundColor $(if ($hasMore) { "Yellow" } else { "Green" })
    
    if ($totalServices -gt 0) {
        $progress = [math]::Round(($processedServices / $totalServices) * 100, 1)
        Write-Host "   处理进度: $progress%" -ForegroundColor $(if ($progress -ge 100) { "Green" } else { "Yellow" })
    }
} catch {
    Write-Host "   无法连接到sap-metadata-agent" -ForegroundColor Red
    $totalServices = 0
    $processedServices = 0
}

# 3. 检查业务术语映射
Write-Host "`n3. 检查业务术语映射..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8005/api/search?q=客户&limit=5" -TimeoutSec 10 -ErrorAction Stop
    $result = $response.Content | ConvertFrom-Json
    $count = if ($result.results) { $result.results.Count } else { 0 }
    Write-Host "   找到包含'客户'的资产: $count" -ForegroundColor $(if ($count -gt 0) { "Green" } else { "Yellow" })
} catch {
    Write-Host "   无法搜索业务术语" -ForegroundColor Red
}

# 4. 检查语义索引
Write-Host "`n4. 检查语义索引..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8004/api/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "   knowledge-base服务运行正常" -ForegroundColor Green
} catch {
    Write-Host "   knowledge-base服务未运行" -ForegroundColor Yellow
}

# 总结
Write-Host "`n" + "=" * 60 -ForegroundColor Cyan
Write-Host "构建状态总结:" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

if ($totalAssets -gt 20000) {
    Write-Host "[OK] 数据资产数量充足 ($totalAssets)" -ForegroundColor Green
} elseif ($totalAssets -gt 0) {
    Write-Host "[WARN] 数据资产数量较少 ($totalAssets)，可能需要继续构建" -ForegroundColor Yellow
} else {
    Write-Host "[ERROR] 没有数据资产，需要开始构建" -ForegroundColor Red
}

if ($totalServices -gt 0 -and $processedServices -ge $totalServices) {
    Write-Host "[OK] 所有OData服务已处理 ($processedServices/$totalServices)" -ForegroundColor Green
} elseif ($totalServices -gt 0) {
    Write-Host "[WARN] OData服务处理未完成 ($processedServices/$totalServices)" -ForegroundColor Yellow
}

Write-Host "`n"



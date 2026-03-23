# 监控元数据构建进度
param(
    [int]$CheckInterval = 30  # 检查间隔（秒）
)

Write-Host "`n开始监控元数据构建进度..." -ForegroundColor Cyan
Write-Host "检查间隔: $CheckInterval 秒`n" -ForegroundColor Yellow

$lastTotal = 0
$iteration = 0

while ($true) {
    $iteration++
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    Write-Host "[$timestamp] 第 $iteration 次检查" -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Gray
    
    # 1. 检查Python进程
    $pythonProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*python*"}
    if ($pythonProcess) {
        $runtime = (Get-Date) - $pythonProcess.StartTime
        Write-Host "[OK] 构建脚本正在运行 (运行时间: $([math]::Round($runtime.TotalMinutes, 1)) 分钟)" -ForegroundColor Green
    } else {
        Write-Host "[WARN] 构建脚本未运行" -ForegroundColor Yellow
    }
    
    # 2. 检查数据资产总数
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8005/api/data-assets?limit=1&include_total=True" -TimeoutSec 10 -ErrorAction Stop
        $currentTotal = [int]$response.Headers['X-Total-Count']
        
        Write-Host "数据资产总数: $currentTotal" -ForegroundColor White
        if ($lastTotal -gt 0) {
            $newAssets = $currentTotal - $lastTotal
            if ($newAssets -gt 0) {
                Write-Host "  新增: +$newAssets 个资产" -ForegroundColor Green
            } else {
                Write-Host "  无新增" -ForegroundColor Yellow
            }
        }
        $lastTotal = $currentTotal
    } catch {
        Write-Host "[ERROR] 无法获取数据资产总数" -ForegroundColor Red
    }
    
    # 3. 检查OData服务处理进度
    try {
        $body = '{"include_database":false,"include_odata":true,"build_semantic_index":false,"sync_to_metadata_service":false,"limit":1,"offset":0}'
        $response = Invoke-WebRequest -Uri "http://localhost:8015/api/sap-metadata/discover" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 10 -ErrorAction Stop
        $result = $response.Content | ConvertFrom-Json
        $meta = $result.metadata
        
        $totalServices = $meta.total_services
        $processedServices = $meta.processed_services
        
        if ($totalServices -gt 0) {
            $progress = [math]::Round(($processedServices / $totalServices) * 100, 1)
            $remaining = $totalServices - $processedServices
            $batches = [math]::Ceiling($remaining / 10)
            
            Write-Host "OData服务: $processedServices/$totalServices ($progress%)" -ForegroundColor $(if ($progress -ge 100) { "Green" } else { "Yellow" })
            Write-Host "  剩余: $remaining 个服务 (~$batches 批次)" -ForegroundColor White
            
            if ($progress -ge 100) {
                Write-Host "`n[SUCCESS] 所有服务已处理完成！" -ForegroundColor Green
                break
            }
        }
    } catch {
        Write-Host "[WARN] 无法获取服务处理进度" -ForegroundColor Yellow
    }
    
    # 4. 检查是否需要重新启动构建
    if (-not $pythonProcess -and $remaining -gt 0) {
        Write-Host "`n[INFO] 构建脚本已停止，但还有未处理的服务" -ForegroundColor Yellow
        Write-Host "建议重新运行: python build_complete_enhanced_metadata.py" -ForegroundColor Cyan
    }
    
    Write-Host ""
    
    # 如果已完成，退出
    if ($progress -ge 100) {
        break
    }
    
    # 等待下次检查
    Start-Sleep -Seconds $CheckInterval
}

Write-Host "`n监控结束" -ForegroundColor Cyan



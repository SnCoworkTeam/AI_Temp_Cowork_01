# SAP元数据批量构建脚本
# 自动处理所有批次直到完成

$ErrorActionPreference = "Continue"
$apiUrl = "http://localhost:8015/api/sap-metadata/discover"
$batchSize = 10
$totalServices = 348
$totalBatches = [math]::Ceiling($totalServices / $batchSize)
$completedBatches = 0
$failedBatches = 0
$totalAssets = 0
$startTime = Get-Date

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "SAP元数据批量构建" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "总服务数: $totalServices" -ForegroundColor White
Write-Host "批次大小: $batchSize" -ForegroundColor White
Write-Host "总批次数: $totalBatches" -ForegroundColor White
Write-Host "开始时间: $($startTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor White
Write-Host "========================================`n" -ForegroundColor Cyan

# 从批次0开始（已完成的0-9批次会快速跳过）
for ($batch = 0; $batch -lt $totalBatches; $batch++) {
    $offset = $batch * $batchSize
    $limit = [math]::Min($batchSize, $totalServices - $offset)
    $batchNum = $batch + 1
    
    Write-Host "[$batchNum/$totalBatches] 处理批次 $batch (offset=$offset, limit=$limit)..." -ForegroundColor Yellow
    
    $body = @{
        include_database = $false
        include_odata = $true
        build_semantic_index = $false
        sync_to_metadata_service = $true
        limit = $limit
        offset = $offset
    } | ConvertTo-Json -Depth 10
    
    $retryCount = 0
    $maxRetries = 3
    $success = $false
    
    while ($retryCount -lt $maxRetries -and -not $success) {
        try {
            $requestStart = Get-Date
            $response = Invoke-RestMethod -Method Post -Uri $apiUrl `
                -Body $body -ContentType "application/json" `
                -TimeoutSec 600 `
                -ErrorAction Stop
            
            $requestDuration = (Get-Date) - $requestStart
            $assetsCount = $response.data_assets.Count
            $totalAssets += $assetsCount
            
            # 检查同步结果
            $syncResult = $response.metadata.sync_result
            $assetsCreated = $syncResult.data_assets.created
            $assetsFailed = $syncResult.data_assets.failed
            $entitiesCreated = $syncResult.business_entities.created
            $entitiesFailed = $syncResult.business_entities.failed
            
            Write-Host "  ✅ 成功完成 (耗时: $([math]::Round($requestDuration.TotalSeconds, 1))秒)" -ForegroundColor Green
            Write-Host "     发现数据资产: $assetsCount" -ForegroundColor White
            Write-Host "     同步数据资产: $assetsCreated/$($syncResult.data_assets.total) (失败: $assetsFailed)" -ForegroundColor $(if ($assetsFailed -eq 0) { "Green" } else { "Yellow" })
            Write-Host "     同步业务实体: $entitiesCreated/$($syncResult.business_entities.total) (失败: $entitiesFailed)" -ForegroundColor $(if ($entitiesFailed -eq 0) { "Green" } else { "Yellow" })
            
            $completedBatches++
            $success = $true
            
            # 检查是否还有更多批次
            $hasMore = $response.metadata.has_more
            if (-not $hasMore) {
                Write-Host "`n  ℹ️  所有服务已处理完成！" -ForegroundColor Cyan
                break
            }
            
        } catch {
            $retryCount++
            $errorMsg = $_.Exception.Message
            
            if ($retryCount -lt $maxRetries) {
                Write-Host "  ⚠️  失败 (尝试 $retryCount/$maxRetries): $errorMsg" -ForegroundColor Yellow
                Write-Host "     等待5秒后重试..." -ForegroundColor Yellow
                Start-Sleep -Seconds 5
            } else {
                Write-Host "  ❌ 最终失败: $errorMsg" -ForegroundColor Red
                $failedBatches++
                
                # 询问是否继续
                Write-Host "     跳过此批次，继续下一批次..." -ForegroundColor Yellow
            }
        }
    }
    
    # 批次间短暂休息，避免过载
    if ($batch -lt $totalBatches - 1) {
        Start-Sleep -Seconds 2
    }
    
    # 每10个批次显示一次进度
    if (($batch + 1) % 10 -eq 0) {
        $elapsed = (Get-Date) - $startTime
        $avgTime = $elapsed.TotalSeconds / ($batch + 1)
        $remainingBatches = $totalBatches - ($batch + 1)
        $estimatedRemaining = [TimeSpan]::FromSeconds($avgTime * $remainingBatches)
        
        Write-Host "`n--- 进度报告 ---" -ForegroundColor Cyan
        Write-Host "已完成: $($batch + 1)/$totalBatches 批次" -ForegroundColor White
        Write-Host "成功: $completedBatches, 失败: $failedBatches" -ForegroundColor White
        Write-Host "累计数据资产: $totalAssets" -ForegroundColor White
        Write-Host "已用时间: $([math]::Round($elapsed.TotalMinutes, 1)) 分钟" -ForegroundColor White
        Write-Host "预计剩余: $([math]::Round($estimatedRemaining.TotalMinutes, 1)) 分钟" -ForegroundColor White
        Write-Host "----------------`n" -ForegroundColor Cyan
    }
}

$endTime = Get-Date
$totalDuration = $endTime - $startTime

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "构建完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "总批次数: $totalBatches" -ForegroundColor White
Write-Host "成功批次: $completedBatches" -ForegroundColor Green
Write-Host "失败批次: $failedBatches" -ForegroundColor $(if ($failedBatches -eq 0) { "Green" } else { "Red" })
Write-Host "累计数据资产: $totalAssets" -ForegroundColor White
Write-Host "总耗时: $([math]::Round($totalDuration.TotalMinutes, 1)) 分钟" -ForegroundColor White
Write-Host "结束时间: $($endTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor White
Write-Host "========================================`n" -ForegroundColor Cyan

if ($failedBatches -gt 0) {
    Write-Host "⚠️  有 $failedBatches 个批次失败，请检查日志" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "✅ 所有批次构建成功！" -ForegroundColor Green
    exit 0
}


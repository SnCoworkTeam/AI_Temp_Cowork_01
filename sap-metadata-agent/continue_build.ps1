# 继续构建元数据（确保分批完成）
Write-Host "`n继续构建SAP元数据..." -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# 检查当前进度
$body = '{"include_database":false,"include_odata":true,"build_semantic_index":false,"sync_to_metadata_service":false,"limit":1,"offset":0}'
$response = try {
    Invoke-WebRequest -Uri "http://localhost:8015/api/sap-metadata/discover" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 10 -ErrorAction Stop
} catch {
    $null
}

if ($response) {
    $result = $response.Content | ConvertFrom-Json
    $meta = $result.metadata
    $total = $meta.total_services
    $processed = $meta.processed_services
    $remaining = $total - $processed
    
    Write-Host "`n当前状态:" -ForegroundColor Yellow
    Write-Host "  总服务数: $total" -ForegroundColor White
    Write-Host "  已处理: $processed" -ForegroundColor Green
    Write-Host "  剩余: $remaining" -ForegroundColor $(if ($remaining -eq 0) { "Green" } else { "Yellow" })
    
    if ($remaining -gt 0) {
        $batches = [math]::Ceiling($remaining / 10)
        Write-Host "`n需要继续处理 $batches 个批次" -ForegroundColor Cyan
        
        # 检查构建脚本是否运行
        $pythonProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*python*"}
        
        if ($pythonProcess) {
            Write-Host "`n[INFO] 构建脚本正在运行中..." -ForegroundColor Green
            Write-Host "进程ID: $($pythonProcess.Id)" -ForegroundColor White
            $runtime = (Get-Date) - $pythonProcess.StartTime
            Write-Host "运行时间: $([math]::Round($runtime.TotalMinutes, 1)) 分钟" -ForegroundColor White
            Write-Host "`n建议: 等待构建完成，或运行监控脚本查看进度" -ForegroundColor Yellow
            Write-Host "命令: powershell -ExecutionPolicy Bypass -File monitor_build.ps1" -ForegroundColor Cyan
        } else {
            Write-Host "`n[INFO] 构建脚本未运行，正在启动..." -ForegroundColor Yellow
            Set-Location $PSScriptRoot
            Start-Process python -ArgumentList "build_complete_enhanced_metadata.py" -NoNewWindow
            Start-Sleep -Seconds 3
            Write-Host "[OK] 构建脚本已启动" -ForegroundColor Green
            Write-Host "`n构建将分批进行，每批处理10个服务" -ForegroundColor Cyan
            Write-Host "预计总时间: ~$([math]::Round(($batches * 60) / 60, 1)) 分钟" -ForegroundColor Yellow
        }
    } else {
        Write-Host "`n[SUCCESS] 所有服务已处理完成！" -ForegroundColor Green
        Write-Host "现在可以测试任务编排功能" -ForegroundColor Cyan
    }
} else {
    Write-Host "[ERROR] 无法连接到sap-metadata-agent服务" -ForegroundColor Red
    Write-Host "请确保服务正在运行: docker-compose up sap-metadata-agent" -ForegroundColor Yellow
}

Write-Host "`n" -ForegroundColor White



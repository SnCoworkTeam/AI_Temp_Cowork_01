# 完整监控和测试流程：监控构建进度 -> 验证元数据 -> 测试任务编排
param(
    [int]$CheckInterval = 30,  # 检查间隔（秒）
    [int]$MaxWaitMinutes = 60   # 最大等待时间（分钟）
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "SAP元数据构建监控和测试流程" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$startTime = Get-Date
$maxWaitTime = $startTime.AddMinutes($MaxWaitMinutes)
$iteration = 0
$lastProcessed = 0
$buildCompleted = $false

# 阶段1: 监控构建进度
Write-Host "[阶段1] 监控构建进度..." -ForegroundColor Yellow
Write-Host ("=" * 50) -ForegroundColor Gray

while (-not $buildCompleted -and (Get-Date) -lt $maxWaitTime) {
    $iteration++
    $elapsed = (Get-Date) - $startTime
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    Write-Host "`n[$timestamp] 检查 #$iteration (已运行: $([math]::Round($elapsed.TotalMinutes, 1)) 分钟)" -ForegroundColor Cyan
    
    # 检查Python进程
    $pythonProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*python*"}
    
    # 检查OData服务处理进度
    try {
        $body = '{"include_database":false,"include_odata":true,"build_semantic_index":false,"sync_to_metadata_service":false,"limit":1,"offset":0}'
        $response = Invoke-WebRequest -Uri "http://localhost:8015/api/sap-metadata/discover" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 10 -ErrorAction Stop
        $result = $response.Content | ConvertFrom-Json
        $meta = $result.metadata
        
        $totalServices = $meta.total_services
        $processedServices = $meta.processed_services
        $remaining = $totalServices - $processedServices
        $progress = [math]::Round(($processedServices / $totalServices) * 100, 1)
        
        Write-Host "  进度: $processedServices/$totalServices ($progress%)" -ForegroundColor $(if ($progress -ge 100) { "Green" } else { "Yellow" })
        Write-Host "  剩余: $remaining 个服务" -ForegroundColor White
        
        if ($processedServices -ne $lastProcessed) {
            $newServices = $processedServices - $lastProcessed
            Write-Host "  新增: +$newServices 个服务" -ForegroundColor Green
            $lastProcessed = $processedServices
        }
        
        # 检查是否完成
        if ($progress -ge 100 -or $remaining -eq 0) {
            Write-Host "`n[SUCCESS] 所有服务已处理完成！" -ForegroundColor Green
            $buildCompleted = $true
            break
        }
        
        # 检查构建脚本状态
        if (-not $pythonProcess) {
            Write-Host "  [WARN] 构建脚本未运行，但还有未处理的服务" -ForegroundColor Yellow
            Write-Host "  重新启动构建脚本..." -ForegroundColor Cyan
            Set-Location $PSScriptRoot
            Start-Process python -ArgumentList "build_complete_enhanced_metadata.py" -NoNewWindow
            Start-Sleep -Seconds 5
        }
        
    } catch {
        Write-Host "  [ERROR] 无法获取构建进度: $_" -ForegroundColor Red
    }
    
    # 等待下次检查
    if (-not $buildCompleted) {
        Start-Sleep -Seconds $CheckInterval
    }
}

if (-not $buildCompleted) {
    Write-Host "`n[WARN] 达到最大等待时间，但构建未完成" -ForegroundColor Yellow
    Write-Host "当前进度: $lastProcessed/$totalServices" -ForegroundColor Yellow
    exit 1
}

# 等待语义索引构建完成
Write-Host "`n[INFO] 等待语义索引构建..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

# 阶段2: 验证元数据质量
Write-Host "`n[阶段2] 验证元数据质量..." -ForegroundColor Yellow
Write-Host ("=" * 50) -ForegroundColor Gray

$validationPassed = $false

try {
    # 检查数据资产总数
    $response = Invoke-WebRequest -Uri "http://localhost:8005/api/data-assets?limit=1&include_total=True" -TimeoutSec 10
    $totalAssets = [int]$response.Headers['X-Total-Count']
    Write-Host "  数据资产总数: $totalAssets" -ForegroundColor $(if ($totalAssets -gt 20000) { "Green" } else { "Yellow" })
    
    # 检查增强字段
    $response = Invoke-WebRequest -Uri "http://localhost:8005/api/data-assets?classification=sap_master_data_customer&limit=1" -TimeoutSec 10
    $assets = $response.Content | ConvertFrom-Json
    
    if ($assets.Count -gt 0) {
        $asset = $assets[0]
        $hasAbap = $asset.schema_info -and $asset.schema_info.abap_dictionary
        $hasTerms = $asset.metadata -and $asset.metadata.business_terms
        $hasRels = $asset.metadata -and $asset.metadata.semantic_relationships
        $hasClassification = $asset.classification -and $asset.classification -ne "sap_odata_entity"
        
        Write-Host "  检查示例资产: $($asset.name)" -ForegroundColor White
        Write-Host "    包含ABAP字典: $hasAbap" -ForegroundColor $(if ($hasAbap) { "Green" } else { "Yellow" })
        Write-Host "    包含业务术语: $hasTerms" -ForegroundColor $(if ($hasTerms) { "Green" } else { "Yellow" })
        Write-Host "    包含语义关系: $hasRels" -ForegroundColor $(if ($hasRels) { "Green" } else { "Yellow" })
        Write-Host "    细化分类: $hasClassification" -ForegroundColor $(if ($hasClassification) { "Green" } else { "Yellow" })
        
        if ($hasAbap -or $hasTerms -or $hasRels -or $hasClassification) {
            $validationPassed = $true
            Write-Host "`n  [OK] 元数据包含增强字段" -ForegroundColor Green
        } else {
            Write-Host "`n  [WARN] 元数据可能缺少增强字段" -ForegroundColor Yellow
        }
    }
    
} catch {
    Write-Host "  [ERROR] 验证失败: $_" -ForegroundColor Red
}

# 阶段3: 测试任务编排
Write-Host "`n[阶段3] 测试任务编排功能..." -ForegroundColor Yellow
Write-Host ("=" * 50) -ForegroundColor Gray

$testResults = @()

# 测试1: 简单业务术语识别
Write-Host "`n测试1: 简单业务术语识别 (查询客户主数据)" -ForegroundColor Cyan
try {
    $body = @{
        user_input = "查询客户主数据"
        context = @{}
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "http://localhost:8009/api/v1/tasks/decompose" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30 -ErrorAction Stop
    $result = $response.Content | ConvertFrom-Json
    
    Write-Host "  [OK] 任务分解成功" -ForegroundColor Green
    Write-Host "  任务节点数: $($result.task_nodes.PSObject.Properties.Count)" -ForegroundColor White
    
    $testResults += @{
        Test = "简单业务术语识别"
        Status = "PASSED"
        Details = "任务分解成功，生成 $($result.task_nodes.PSObject.Properties.Count) 个节点"
    }
} catch {
    Write-Host "  [FAIL] 测试失败: $_" -ForegroundColor Red
    $testResults += @{
        Test = "简单业务术语识别"
        Status = "FAILED"
        Details = $_.Exception.Message
    }
}

# 测试2: 复杂任务依赖关系
Write-Host "`n测试2: 复杂任务依赖关系 (查询客户订单)" -ForegroundColor Cyan
try {
    $body = @{
        user_input = "查询客户主数据，然后查询该客户的销售订单"
        context = @{}
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "http://localhost:8009/api/v1/tasks/decompose" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30 -ErrorAction Stop
    $result = $response.Content | ConvertFrom-Json
    
    Write-Host "  [OK] 任务分解成功" -ForegroundColor Green
    Write-Host "  任务节点数: $($result.task_nodes.PSObject.Properties.Count)" -ForegroundColor White
    
    # 检查依赖关系
    $hasDependencies = $false
    foreach ($node in $result.task_nodes.PSObject.Properties) {
        $nodeData = $node.Value
        if ($nodeData.dependencies -and $nodeData.dependencies.Count -gt 0) {
            $hasDependencies = $true
            Write-Host "  节点 $($node.Name) 依赖: $($nodeData.dependencies -join ', ')" -ForegroundColor White
        }
    }
    
    if ($hasDependencies) {
        Write-Host "  [OK] 检测到任务依赖关系" -ForegroundColor Green
    } else {
        Write-Host "  [WARN] 未检测到任务依赖关系" -ForegroundColor Yellow
    }
    
    $testResults += @{
        Test = "复杂任务依赖关系"
        Status = if ($hasDependencies) { "PASSED" } else { "WARNING" }
        Details = "任务分解成功，依赖关系: $hasDependencies"
    }
} catch {
    Write-Host "  [FAIL] 测试失败: $_" -ForegroundColor Red
    $testResults += @{
        Test = "复杂任务依赖关系"
        Status = "FAILED"
        Details = $_.Exception.Message
    }
}

# 测试3: 业务术语搜索
Write-Host "`n测试3: 业务术语搜索 (搜索'客户')" -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8005/api/search?q=客户&limit=5" -TimeoutSec 10 -ErrorAction Stop
    $result = $response.Content | ConvertFrom-Json
    
    $count = if ($result.results) { $result.results.Count } else { 0 }
    Write-Host "  [OK] 搜索成功，找到 $count 个结果" -ForegroundColor Green
    
    if ($count -gt 0) {
        Write-Host "  示例结果:" -ForegroundColor White
        $result.results | Select-Object -First 3 | ForEach-Object {
            Write-Host "    - $($_.name): $($_.display_name)" -ForegroundColor Gray
        }
    }
    
    $testResults += @{
        Test = "业务术语搜索"
        Status = if ($count -gt 0) { "PASSED" } else { "WARNING" }
        Details = "找到 $count 个结果"
    }
} catch {
    Write-Host "  [FAIL] 测试失败: $_" -ForegroundColor Red
    $testResults += @{
        Test = "业务术语搜索"
        Status = "FAILED"
        Details = $_.Exception.Message
    }
}

# 总结报告
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "测试总结报告" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$totalTests = $testResults.Count
$passedTests = ($testResults | Where-Object { $_.Status -eq "PASSED" }).Count
$failedTests = ($testResults | Where-Object { $_.Status -eq "FAILED" }).Count
$warningTests = ($testResults | Where-Object { $_.Status -eq "WARNING" }).Count

Write-Host "总测试数: $totalTests" -ForegroundColor White
Write-Host "通过: $passedTests" -ForegroundColor Green
Write-Host "警告: $warningTests" -ForegroundColor Yellow
Write-Host "失败: $failedTests" -ForegroundColor $(if ($failedTests -gt 0) { "Red" } else { "White" })

Write-Host "`n详细结果:" -ForegroundColor Cyan
$testResults | ForEach-Object {
    $color = switch ($_.Status) {
        "PASSED" { "Green" }
        "WARNING" { "Yellow" }
        "FAILED" { "Red" }
        default { "White" }
    }
    Write-Host "  [$($_.Status)] $($_.Test)" -ForegroundColor $color
    Write-Host "    $($_.Details)" -ForegroundColor Gray
}

$totalTime = (Get-Date) - $startTime
Write-Host "`n总耗时: $([math]::Round($totalTime.TotalMinutes, 1)) 分钟" -ForegroundColor Cyan

if ($failedTests -eq 0) {
    Write-Host "`n[SUCCESS] 所有测试完成！" -ForegroundColor Green
} else {
    Write-Host "`n[WARN] 部分测试失败，请检查日志" -ForegroundColor Yellow
}



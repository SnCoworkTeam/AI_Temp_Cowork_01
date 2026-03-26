# SAP元数据完整构建脚本
# 自动检测总服务数，处理所有批次，确保所有元数据构建完成

$ErrorActionPreference = "Continue"
$apiUrl = "http://localhost:8015/api/sap-metadata/discover"
$statusFile = "build_status.json"
$batchSize = 10
$maxRetries = 3
$retryDelay = 5

# 颜色输出函数
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# 加载保存的进度
function Load-Progress {
    if (Test-Path $statusFile) {
        try {
            $progress = Get-Content $statusFile | ConvertFrom-Json
            Write-ColorOutput "找到保存的进度: 已完成 $($progress.completedBatches) 批次" "Cyan"
            return $progress
        } catch {
            Write-ColorOutput "无法加载进度文件，将从头开始" "Yellow"
        }
    }
    return $null
}

# 保存进度
function Save-Progress {
    param($Progress)
    $Progress | ConvertTo-Json -Depth 10 | Set-Content $statusFile
}

# 获取总服务数
function Get-TotalServices {
    Write-ColorOutput "`n正在检测SAP OData服务总数..." "Cyan"
    try {
        # 先调用一次发现API获取总服务数
        $testBody = @{
            include_database = $false
            include_odata = $true
            build_semantic_index = $false
            sync_to_metadata_service = $false
            limit = 1
            offset = 0
        } | ConvertTo-Json -Depth 10
        
        $testResponse = Invoke-RestMethod -Method Post -Uri $apiUrl `
            -Body $testBody -ContentType "application/json" `
            -TimeoutSec 60 -ErrorAction Stop
        
        $totalServices = $testResponse.metadata.total_services
        if ($totalServices -and $totalServices -gt 0) {
            Write-ColorOutput "检测到总服务数: $totalServices" "Green"
            return $totalServices
        }
    } catch {
        Write-ColorOutput "无法自动检测服务数，使用默认值348" "Yellow"
    }
    return 348
}

# 处理单个批次
function Process-Batch {
    param(
        [int]$Batch,
        [int]$Offset,
        [int]$Limit,
        [int]$TotalBatches
    )
    
    $batchNum = $Batch + 1
    Write-ColorOutput "[$batchNum/$TotalBatches] 处理批次 $Batch (offset=$Offset, limit=$Limit)..." "Yellow"
    
    $body = @{
        include_database = $false
        include_odata = $true
        build_semantic_index = $false
        sync_to_metadata_service = $true
        limit = $Limit
        offset = $Offset
    } | ConvertTo-Json -Depth 10
    
    $retryCount = 0
    $success = $false
    $result = $null
    
    while ($retryCount -lt $maxRetries -and -not $success) {
        try {
            $requestStart = Get-Date
            $response = Invoke-RestMethod -Method Post -Uri $apiUrl `
                -Body $body -ContentType "application/json" `
                -TimeoutSec 600 -ErrorAction Stop
            
            $requestDuration = (Get-Date) - $requestStart
            $assetsCount = $response.data_assets.Count
            $entitiesCount = $response.business_entities.Count
            $processesCount = $response.business_processes.Count
            
            # 检查同步结果
            $syncResult = $response.metadata.sync_result
            $assetsCreated = $syncResult.data_assets.created
            $assetsFailed = $syncResult.data_assets.failed
            $entitiesCreated = $syncResult.business_entities.created
            $entitiesFailed = $syncResult.business_entities.failed
            
            Write-ColorOutput "  ✅ 成功完成 (耗时: $([math]::Round($requestDuration.TotalSeconds, 1))秒)" "Green"
            Write-ColorOutput "     发现数据资产: $assetsCount" "White"
            Write-ColorOutput "     发现业务实体: $entitiesCount" "White"
            Write-ColorOutput "     发现业务流程: $processesCount" "White"
            Write-ColorOutput "     同步数据资产: $assetsCreated/$($syncResult.data_assets.total) (失败: $assetsFailed)" $(if ($assetsFailed -eq 0) { "Green" } else { "Yellow" })
            Write-ColorOutput "     同步业务实体: $entitiesCreated/$($syncResult.business_entities.total) (失败: $entitiesFailed)" $(if ($entitiesFailed -eq 0) { "Green" } else { "Yellow" })
            
            $success = $true
            $result = @{
                assetsCount = $assetsCount
                entitiesCount = $entitiesCount
                processesCount = $processesCount
                assetsCreated = $assetsCreated
                assetsFailed = $assetsFailed
                entitiesCreated = $entitiesCreated
                entitiesFailed = $entitiesFailed
                hasMore = $response.metadata.has_more
            }
            
        } catch {
            $retryCount++
            $errorMsg = $_.Exception.Message
            
            if ($retryCount -lt $maxRetries) {
                Write-ColorOutput "  ⚠️  失败 (尝试 $retryCount/$maxRetries): $errorMsg" "Yellow"
                Write-ColorOutput "     等待 $retryDelay 秒后重试..." "Yellow"
                Start-Sleep -Seconds $retryDelay
            } else {
                Write-ColorOutput "  ❌ 最终失败: $errorMsg" "Red"
                Write-ColorOutput "     跳过此批次，继续下一批次..." "Yellow"
            }
        }
    }
    
    return $result
}

# 构建语义索引
function Build-SemanticIndex {
    Write-ColorOutput "`n开始构建语义索引..." "Cyan"
    try {
        $body = @{
            include_database = $false
            include_odata = $false
            build_semantic_index = $true
            sync_to_metadata_service = $false
        } | ConvertTo-Json -Depth 10
        
        $response = Invoke-RestMethod -Method Post -Uri $apiUrl `
            -Body $body -ContentType "application/json" `
            -TimeoutSec 1800 -ErrorAction Stop
        
        $indexResult = $response.metadata.semantic_index
        Write-ColorOutput "  ✅ 语义索引构建完成" "Green"
        Write-ColorOutput "     已索引文档: $($indexResult.indexed)" "White"
        Write-ColorOutput "     失败: $($indexResult.failed)" $(if ($indexResult.failed -eq 0) { "Green" } else { "Yellow" })
        
        return $true
    } catch {
        Write-ColorOutput "  ⚠️  语义索引构建失败: $($_.Exception.Message)" "Yellow"
        return $false
    }
}

# 验证元数据同步
function Verify-MetadataSync {
    Write-ColorOutput "`n验证元数据同步状态..." "Cyan"
    try {
        $metadataServiceUrl = "http://localhost:8005"
        
        # 检查数据资产
        $assetsResponse = Invoke-RestMethod -Method Get `
            -Uri "$metadataServiceUrl/api/data-assets?limit=1" `
            -TimeoutSec 30 -ErrorAction Stop
        
        $totalAssets = $assetsResponse.total
        Write-ColorOutput "  ✅ 元数据服务中的数据资产: $totalAssets" "Green"
        
        # 检查业务实体
        $entitiesResponse = Invoke-RestMethod -Method Get `
            -Uri "$metadataServiceUrl/api/business-entities?limit=1" `
            -TimeoutSec 30 -ErrorAction Stop
        
        $totalEntities = $entitiesResponse.total
        Write-ColorOutput "  ✅ 元数据服务中的业务实体: $totalEntities" "Green"
        
        return @{
            assets = $totalAssets
            entities = $totalEntities
        }
    } catch {
        Write-ColorOutput "  ⚠️  无法验证元数据同步状态: $($_.Exception.Message)" "Yellow"
        return $null
    }
}

# 主程序
Write-ColorOutput "`n========================================" "Cyan"
Write-ColorOutput "SAP元数据完整构建" "Cyan"
Write-ColorOutput "========================================" "Cyan"

# 加载进度
$progress = Load-Progress
$startOffset = 0
$completedBatches = 0
$totalAssets = 0
$totalEntities = 0
$totalProcesses = 0
$failedBatches = 0

if ($progress) {
    $startOffset = $progress.lastOffset + $progress.batchSize
    $completedBatches = $progress.completedBatches
    $totalAssets = $progress.totalAssets
    $totalEntities = $progress.totalEntities
    $totalProcesses = $progress.totalProcesses
    $failedBatches = $progress.failedBatches
    Write-ColorOutput "从批次 $($startOffset / $batchSize) 继续构建..." "Cyan"
}

# 获取总服务数
$totalServices = Get-TotalServices
$totalBatches = [math]::Ceiling($totalServices / $batchSize)

Write-ColorOutput "总服务数: $totalServices" "White"
Write-ColorOutput "批次大小: $batchSize" "White"
Write-ColorOutput "总批次数: $totalBatches" "White"
Write-ColorOutput "开始时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "White"
Write-ColorOutput "========================================`n" "Cyan"

$startTime = Get-Date

# 处理所有批次
for ($batch = [math]::Floor($startOffset / $batchSize); $batch -lt $totalBatches; $batch++) {
    $offset = $batch * $batchSize
    $limit = [math]::Min($batchSize, $totalServices - $offset)
    
    $result = Process-Batch -Batch $batch -Offset $offset -Limit $limit -TotalBatches $totalBatches
    
    if ($result) {
        $totalAssets += $result.assetsCount
        $totalEntities += $result.entitiesCount
        $totalProcesses += $result.processesCount
        $completedBatches++
        
        # 保存进度
        $progress = @{
            lastOffset = $offset
            batchSize = $batchSize
            completedBatches = $completedBatches
            totalAssets = $totalAssets
            totalEntities = $totalEntities
            totalProcesses = $totalProcesses
            failedBatches = $failedBatches
            timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
        }
        Save-Progress -Progress $progress
        
        # 检查是否还有更多批次
        if (-not $result.hasMore -and ($offset + $limit) >= $totalServices) {
            Write-ColorOutput "`n  ℹ️  所有服务已处理完成！" "Cyan"
            break
        }
    } else {
        $failedBatches++
    }
    
    # 批次间短暂休息
    if ($batch -lt $totalBatches - 1) {
        Start-Sleep -Seconds 2
    }
    
    # 每10个批次显示一次进度
    if (($batch + 1) % 10 -eq 0) {
        $elapsed = (Get-Date) - $startTime
        $avgTime = $elapsed.TotalSeconds / ($batch + 1)
        $remainingBatches = $totalBatches - ($batch + 1)
        $estimatedRemaining = [TimeSpan]::FromSeconds($avgTime * $remainingBatches)
        
        Write-ColorOutput "`n--- 进度报告 ---" "Cyan"
        Write-ColorOutput "已完成: $($batch + 1)/$totalBatches 批次" "White"
        Write-ColorOutput "成功: $completedBatches, 失败: $failedBatches" "White"
        Write-ColorOutput "累计数据资产: $totalAssets" "White"
        Write-ColorOutput "累计业务实体: $totalEntities" "White"
        Write-ColorOutput "累计业务流程: $totalProcesses" "White"
        Write-ColorOutput "已用时间: $([math]::Round($elapsed.TotalMinutes, 1)) 分钟" "White"
        Write-ColorOutput "预计剩余: $([math]::Round($estimatedRemaining.TotalMinutes, 1)) 分钟" "White"
        Write-ColorOutput "----------------`n" "Cyan"
    }
}

$endTime = Get-Date
$totalDuration = $endTime - $startTime

Write-ColorOutput "`n========================================" "Cyan"
Write-ColorOutput "批次构建完成" "Cyan"
Write-ColorOutput "========================================" "Cyan"
Write-ColorOutput "总批次数: $totalBatches" "White"
Write-ColorOutput "成功批次: $completedBatches" "Green"
Write-ColorOutput "失败批次: $failedBatches" $(if ($failedBatches -eq 0) { "Green" } else { "Red" })
Write-ColorOutput "累计数据资产: $totalAssets" "White"
Write-ColorOutput "累计业务实体: $totalEntities" "White"
Write-ColorOutput "累计业务流程: $totalProcesses" "White"
Write-ColorOutput "总耗时: $([math]::Round($totalDuration.TotalMinutes, 1)) 分钟" "White"
Write-ColorOutput "========================================`n" "Cyan"

# 构建语义索引
if ($completedBatches -gt 0) {
    $indexSuccess = Build-SemanticIndex
} else {
    Write-ColorOutput "`n⚠️  没有成功构建的批次，跳过语义索引构建" "Yellow"
    $indexSuccess = $false
}

# 验证元数据同步
$syncStatus = Verify-MetadataSync

# 最终报告
Write-ColorOutput "`n========================================" "Cyan"
Write-ColorOutput "构建完成报告" "Cyan"
Write-ColorOutput "========================================" "Cyan"
Write-ColorOutput "数据资产发现: $totalAssets" "White"
Write-ColorOutput "业务实体提取: $totalEntities" "White"
Write-ColorOutput "业务流程分析: $totalProcesses" "White"
Write-ColorOutput "语义索引构建: $(if ($indexSuccess) { '✅ 完成' } else { '❌ 失败' })" $(if ($indexSuccess) { "Green" } else { "Red" })

if ($syncStatus) {
    Write-ColorOutput "元数据服务同步:" "White"
    Write-ColorOutput "  - 数据资产: $($syncStatus.assets)" "White"
    Write-ColorOutput "  - 业务实体: $($syncStatus.entities)" "White"
}

Write-ColorOutput "结束时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "White"
Write-ColorOutput "========================================`n" "Cyan"

# 清理进度文件
if (Test-Path $statusFile) {
    Remove-Item $statusFile
    Write-ColorOutput "已清理进度文件" "Cyan"
}

if ($failedBatches -gt 0) {
    Write-ColorOutput "⚠️  有 $failedBatches 个批次失败，请检查日志" "Yellow"
    exit 1
} else {
    Write-ColorOutput "✅ 所有元数据构建成功！" "Green"
    exit 0
}




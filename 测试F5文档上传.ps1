# 测试F5业务蓝图报告文档上传和处理
# 包括上传、监控进度、查看日志和错误诊断

param(
    [string]$DocumentFile = "F5业务蓝图报告_TJJ_SD_V1.1.docx",
    [int]$MaxWaitTime = 600,
    [int]$CheckInterval = 3
)

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "F5文档上传测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$BASE_URL = "http://localhost:8004/api"

# 1. 检查服务
Write-Host "1. 检查知识库服务..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "$BASE_URL/health" -Method Get -TimeoutSec 5
    Write-Host "   ✓ 知识库服务正在运行" -ForegroundColor Green
} catch {
    Write-Host "   ✗ 无法连接到知识库服务" -ForegroundColor Red
    Write-Host "   请先运行: .\启动知识库服务.ps1" -ForegroundColor Yellow
    exit 1
}

# 2. 检查文件
Write-Host "`n2. 检查测试文件..." -ForegroundColor Yellow
if (-not (Test-Path $DocumentFile)) {
    Write-Host "   ✗ 文件不存在: $DocumentFile" -ForegroundColor Red
    exit 1
}

$fileSize = (Get-Item $DocumentFile).Length / 1MB
Write-Host "   ✓ 找到文件: $DocumentFile (大小: $([math]::Round($fileSize, 2)) MB)" -ForegroundColor Green

# 3. 上传文档
Write-Host "`n3. 上传文档..." -ForegroundColor Yellow
try {
    $formData = @{
        file = Get-Item $DocumentFile
        process_async = "true"
    }
    
    $uploadResponse = Invoke-RestMethod -Uri "$BASE_URL/documents/upload" -Method Post -Form $formData -TimeoutSec 60
    
    $documentId = $uploadResponse.document_id
    $status = $uploadResponse.status
    
    Write-Host "   ✓ 文档上传成功" -ForegroundColor Green
    Write-Host "   文档ID: $documentId" -ForegroundColor Cyan
    Write-Host "   初始状态: $status" -ForegroundColor Cyan
    
} catch {
    Write-Host "   ✗ 上传失败: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "   响应: $responseBody" -ForegroundColor Red
    }
    exit 1
}

# 4. 监控处理进度
Write-Host "`n4. 监控处理进度（最多等待 $MaxWaitTime 秒）..." -ForegroundColor Yellow
Write-Host "   按 Ctrl+C 可提前退出" -ForegroundColor Gray
Write-Host ("   " + ("-" * 50)) -ForegroundColor Gray

$startTime = Get-Date
$lastStatus = $null
$lastStage = $null
$lastProgress = $null

function Get-DocumentStatus {
    param([string]$DocId)
    try {
        $doc = Invoke-RestMethod -Uri "$BASE_URL/documents/$DocId" -Method Get -TimeoutSec 5
        return $doc
    } catch {
        return $null
    }
}

function Get-DocumentProgress {
    param([string]$DocId)
    try {
        $progress = Invoke-RestMethod -Uri "$BASE_URL/documents/$DocId/progress" -Method Get -TimeoutSec 5
        return $progress
    } catch {
        return $null
    }
}

$completed = $false
$failed = $false

while (-not $completed -and -not $failed) {
    $elapsed = (Get-Date) - $startTime
    
    if ($elapsed.TotalSeconds -gt $MaxWaitTime) {
        Write-Host "`n   ⚠ 已达到最大等待时间（$MaxWaitTime秒），停止监控" -ForegroundColor Yellow
        break
    }
    
    # 获取文档状态
    $docInfo = Get-DocumentStatus -DocId $documentId
    if (-not $docInfo) {
        Write-Host "   [等待中] 无法获取文档状态... ($([math]::Round($elapsed.TotalSeconds, 0))秒)" -ForegroundColor Gray
        Start-Sleep -Seconds $CheckInterval
        continue
    }
    
    $currentStatus = $docInfo.status
    $chunkCount = $docInfo.total_chunks
    $errorMessage = $docInfo.error_message
    
    # 获取处理进度
    $progressInfo = Get-DocumentProgress -DocId $documentId
    $currentStage = if ($progressInfo) { $progressInfo.stage } else { "unknown" }
    $progressPercent = if ($progressInfo) { $progressInfo.progress_percentage } else { 0 }
    $completedSteps = if ($progressInfo) { $progressInfo.completed_steps } else { 0 }
    $totalSteps = if ($progressInfo) { $progressInfo.total_steps } else { 0 }
    
    # 显示状态变化
    $statusChanged = $currentStatus -ne $lastStatus
    $stageChanged = $currentStage -ne $lastStage
    $progressChanged = $progressPercent -ne $lastProgress
    
    if ($statusChanged -or $stageChanged -or ($progressChanged -and $progressPercent -gt 0)) {
        $statusColor = switch ($currentStatus) {
            "processing" { "Yellow" }
            "completed" { "Green" }
            "failed" { "Red" }
            default { "Gray" }
        }
        
        Write-Host ""
        Write-Host "   [状态] $currentStatus | [阶段] $currentStage | [进度] $([math]::Round($progressPercent, 1))%" -ForegroundColor $statusColor
        if ($totalSteps -gt 0) {
            Write-Host "   [块数] $completedSteps/$totalSteps | [耗时] $([math]::Round($elapsed.TotalSeconds, 0))秒" -ForegroundColor Cyan
        }
        
        $lastStatus = $currentStatus
        $lastStage = $currentStage
        $lastProgress = $progressPercent
    } else {
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
    
    # 检查完成状态
    if ($currentStatus -eq "completed") {
        Write-Host "`n`n   ✓ 文档处理完成！" -ForegroundColor Green
        Write-Host "   最终状态: $currentStatus" -ForegroundColor Green
        Write-Host "   总块数: $chunkCount" -ForegroundColor Green
        Write-Host "   总耗时: $([math]::Round($elapsed.TotalSeconds, 2))秒" -ForegroundColor Green
        $completed = $true
        break
    } elseif ($currentStatus -eq "failed") {
        Write-Host "`n`n   ✗ 文档处理失败！" -ForegroundColor Red
        Write-Host "   状态: $currentStatus" -ForegroundColor Red
        if ($errorMessage) {
            Write-Host "   错误信息: $errorMessage" -ForegroundColor Red
        }
        $failed = $true
        break
    }
    
    Start-Sleep -Seconds $CheckInterval
}

# 5. 显示最新日志
Write-Host "`n5. 查看知识库服务最新日志（最近100行）..." -ForegroundColor Yellow
Write-Host ("   " + ("=" * 50)) -ForegroundColor Gray

try {
    $logs = docker logs enterprise-ai-knowledge-base --tail 100 2>&1
    Write-Host $logs -ForegroundColor Gray
} catch {
    Write-Host "   无法获取日志（可能需要手动执行: docker logs enterprise-ai-knowledge-base --tail 100）" -ForegroundColor Yellow
}

# 6. 显示错误摘要（如果有）
if ($failed) {
    Write-Host "`n6. 错误诊断..." -ForegroundColor Yellow
    Write-Host ("   " + ("=" * 50)) -ForegroundColor Gray
    
    # 查找错误日志
    try {
        $errorLogs = docker logs enterprise-ai-knowledge-base --tail 200 2>&1 | Select-String -Pattern "error|Error|ERROR|exception|Exception|EXCEPTION|failed|Failed|FAILED" -Context 2,2
        if ($errorLogs) {
            Write-Host "   发现错误日志:" -ForegroundColor Red
            $errorLogs | ForEach-Object {
                Write-Host "   $_" -ForegroundColor Red
            }
        } else {
            Write-Host "   未在日志中发现明显的错误信息" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   无法分析错误日志" -ForegroundColor Yellow
    }
}

# 7. 性能分析
Write-Host "`n7. 性能分析..." -ForegroundColor Yellow
Write-Host ("   " + ("=" * 50)) -ForegroundColor Gray

$totalTime = (Get-Date) - $startTime
Write-Host "   总耗时: $([math]::Round($totalTime.TotalSeconds, 2))秒" -ForegroundColor Cyan
Write-Host "   文件大小: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Cyan
if ($chunkCount -gt 0) {
    $timePerChunk = $totalTime.TotalSeconds / $chunkCount
    Write-Host "   块数: $chunkCount" -ForegroundColor Cyan
    Write-Host "   平均每块耗时: $([math]::Round($timePerChunk, 2))秒" -ForegroundColor Cyan
}

if ($totalTime.TotalSeconds -gt 300) {
    Write-Host "   ⚠ 处理时间较长，可能的原因:" -ForegroundColor Yellow
    Write-Host "   - 文档较大，需要更多时间解析" -ForegroundColor Yellow
    Write-Host "   - 向量化模型在CPU上运行较慢" -ForegroundColor Yellow
    Write-Host "   - 系统资源不足" -ForegroundColor Yellow
    Write-Host "   建议: 检查docker容器资源使用情况" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
if ($completed) {
    Write-Host "测试完成！文档处理成功" -ForegroundColor Green
} elseif ($failed) {
    Write-Host "测试完成，但文档处理失败" -ForegroundColor Red
    Write-Host "请查看上面的日志和错误信息" -ForegroundColor Yellow
} else {
    Write-Host "测试完成，但文档处理可能仍在进行中" -ForegroundColor Yellow
    Write-Host "请手动检查文档状态或查看日志" -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "查看实时日志: docker logs -f enterprise-ai-knowledge-base" -ForegroundColor Green
Write-Host "检查文档状态: curl http://localhost:8004/api/documents/$documentId" -ForegroundColor Green
Write-Host "检查处理进度: curl http://localhost:8004/api/documents/$documentId/progress" -ForegroundColor Green
Write-Host ""


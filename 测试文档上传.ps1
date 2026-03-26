# 测试文档上传处理过程
# 功能：启动知识库服务，上传f5业务蓝图报告，监控处理过程

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "知识库文档上传测试脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Docker是否运行
Write-Host "1. 检查Docker状态..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "   ✓ Docker正在运行" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Docker未运行，请先启动Docker" -ForegroundColor Red
    exit 1
}

# 检查必要的服务是否运行
Write-Host "`n2. 检查依赖服务（PostgreSQL, Redis）..." -ForegroundColor Yellow
$postgresRunning = docker ps --filter "name=enterprise-ai-postgres" --format "{{.Names}}" | Select-String "postgres"
$redisRunning = docker ps --filter "name=enterprise-ai-redis" --format "{{.Names}}" | Select-String "redis"

if (-not $postgresRunning) {
    Write-Host "   启动PostgreSQL..." -ForegroundColor Yellow
    docker-compose up -d postgres
    Start-Sleep -Seconds 5
}

if (-not $redisRunning) {
    Write-Host "   启动Redis..." -ForegroundColor Yellow
    docker-compose up -d redis
    Start-Sleep -Seconds 3
}

Write-Host "   ✓ 依赖服务已就绪" -ForegroundColor Green

# 启动知识库服务
Write-Host "`n3. 启动知识库服务..." -ForegroundColor Yellow
$kbRunning = docker ps --filter "name=enterprise-ai-knowledge-base" --format "{{.Names}}" | Select-String "knowledge-base"

if (-not $kbRunning) {
    Write-Host "   正在启动知识库服务..." -ForegroundColor Yellow
    docker-compose up -d knowledge-base
    
    Write-Host "   等待服务启动（最多60秒）..." -ForegroundColor Yellow
    $maxWait = 60
    $waited = 0
    $isReady = $false
    
    while ($waited -lt $maxWait) {
        Start-Sleep -Seconds 2
        $waited += 2
        
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8004/api/health" -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                $isReady = $true
                break
            }
        } catch {
            # 继续等待
        }
        
        Write-Host "   ." -NoNewline -ForegroundColor Gray
    }
    Write-Host ""
    
    if ($isReady) {
        Write-Host "   ✓ 知识库服务已启动" -ForegroundColor Green
    } else {
        Write-Host "   ⚠ 服务可能还在启动中，继续测试..." -ForegroundColor Yellow
    }
} else {
    Write-Host "   ✓ 知识库服务已在运行" -ForegroundColor Green
}

# 检查测试文件是否存在
Write-Host "`n4. 检查测试文件..." -ForegroundColor Yellow
$testFile = "F5业务蓝图报告_TJJ_SD_V1.1.docx"
if (-not (Test-Path $testFile)) {
    Write-Host "   ✗ 测试文件不存在: $testFile" -ForegroundColor Red
    exit 1
}

$fileSize = (Get-Item $testFile).Length / 1MB
Write-Host "   ✓ 找到测试文件: $testFile (大小: $([math]::Round($fileSize, 2)) MB)" -ForegroundColor Green

# 上传文档
Write-Host "`n5. 上传文档到知识库..." -ForegroundColor Yellow
$uploadUrl = "http://localhost:8004/api/documents/upload"

try {
    $formData = @{
        file = Get-Item $testFile
        process_async = "true"
    }
    
    Write-Host "   正在上传..." -ForegroundColor Gray
    $response = Invoke-RestMethod -Uri $uploadUrl -Method Post -Form $formData -ContentType "multipart/form-data"
    
    $documentId = $response.document_id
    $status = $response.status
    
    Write-Host "   ✓ 文档上传成功" -ForegroundColor Green
    Write-Host "   文档ID: $documentId" -ForegroundColor Cyan
    Write-Host "   初始状态: $status" -ForegroundColor Cyan
    
} catch {
    Write-Host "   ✗ 上传失败: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "   错误详情: $responseBody" -ForegroundColor Red
    }
    exit 1
}

# 监控处理过程
Write-Host "`n6. 监控文档处理过程..." -ForegroundColor Yellow
Write-Host "   (按Ctrl+C可提前退出监控)" -ForegroundColor Gray
Write-Host ""

$maxWaitTime = 600  # 最多等待10分钟
$checkInterval = 5  # 每5秒检查一次
$startTime = Get-Date
$lastStatus = $status

while ($true) {
    $elapsed = (Get-Date) - $startTime
    
    if ($elapsed.TotalSeconds -gt $maxWaitTime) {
        Write-Host "`n   ⚠ 已达到最大等待时间（$maxWaitTime秒），停止监控" -ForegroundColor Yellow
        break
    }
    
    try {
        $docUrl = "http://localhost:8004/api/documents/$documentId"
        $docInfo = Invoke-RestMethod -Uri $docUrl -Method Get
        
        $currentStatus = $docInfo.status
        $chunkCount = $docInfo.total_chunks
        
        if ($currentStatus -ne $lastStatus) {
            Write-Host "   [状态变化] $lastStatus -> $currentStatus (已处理 $chunkCount 个块, 耗时: $([math]::Round($elapsed.TotalSeconds, 0))秒)" -ForegroundColor Cyan
            $lastStatus = $currentStatus
        } else {
            Write-Host "   [监控中] 状态: $currentStatus, 块数: $chunkCount, 耗时: $([math]::Round($elapsed.TotalSeconds, 0))秒" -ForegroundColor Gray
        }
        
        # 检查是否完成
        if ($currentStatus -eq "completed") {
            Write-Host "`n   ✓ 文档处理完成！" -ForegroundColor Green
            Write-Host "   最终状态: $currentStatus" -ForegroundColor Green
            Write-Host "   总块数: $chunkCount" -ForegroundColor Green
            Write-Host "   总耗时: $([math]::Round($elapsed.TotalSeconds, 2))秒" -ForegroundColor Green
            break
        } elseif ($currentStatus -eq "failed") {
            Write-Host "`n   ✗ 文档处理失败！" -ForegroundColor Red
            Write-Host "   状态: $currentStatus" -ForegroundColor Red
            if ($docInfo.error_message) {
                Write-Host "   错误信息: $($docInfo.error_message)" -ForegroundColor Red
            }
            break
        }
        
    } catch {
        Write-Host "   ⚠ 查询文档状态失败: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    Start-Sleep -Seconds $checkInterval
}

# 显示最新日志
Write-Host "`n7. 查看知识库服务最新日志（最近50行）..." -ForegroundColor Yellow
Write-Host "   ========================================" -ForegroundColor Gray
docker logs enterprise-ai-knowledge-base --tail 50
Write-Host "   ========================================" -ForegroundColor Gray

Write-Host "`n测试完成！" -ForegroundColor Green
Write-Host "提示：可以使用以下命令查看实时日志：" -ForegroundColor Cyan
Write-Host "   docker logs enterprise-ai-knowledge-base -f" -ForegroundColor White


# 分类体系阶段1和阶段2完整测试脚本
# 在本地Docker环境中启动服务并完成所有测试

param(
    [switch]$SkipBuild = $false,
    [switch]$SkipMigration = $false,
    [switch]$SkipAPITests = $false,
    [switch]$SkipFrontendTests = $false
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "分类体系阶段1和阶段2完整测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Docker是否运行
Write-Host "[1/8] 检查Docker环境..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "✓ Docker正在运行" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker未运行，请先启动Docker" -ForegroundColor Red
    exit 1
}

# 1. 启动基础服务
Write-Host ""
Write-Host "[2/8] 启动基础服务（PostgreSQL, Redis）..." -ForegroundColor Yellow
docker-compose up -d postgres redis
Start-Sleep -Seconds 10

# 检查服务健康状态
$maxRetries = 30
$retryCount = 0
while ($retryCount -lt $maxRetries) {
    try {
        $pgHealth = docker exec enterprise-ai-postgres pg_isready -U ai_user -d ai_platform 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ PostgreSQL已就绪" -ForegroundColor Green
            break
        }
    } catch {
        # 继续重试
    }
    $retryCount++
    Write-Host "等待PostgreSQL启动... ($retryCount/$maxRetries)" -ForegroundColor Gray
    Start-Sleep -Seconds 2
}

if ($retryCount -eq $maxRetries) {
    Write-Host "✗ PostgreSQL启动超时" -ForegroundColor Red
    exit 1
}

# 2. 执行数据库迁移
if (-not $SkipMigration) {
    Write-Host ""
    Write-Host "[3/8] 执行数据库迁移..." -ForegroundColor Yellow
    
    # 检查迁移脚本是否存在
    $migrationFile = "database/src/migrations/versions/028_add_classification_dimensions.py"
    if (-not (Test-Path $migrationFile)) {
        Write-Host "✗ 迁移脚本不存在: $migrationFile" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "执行Alembic迁移..." -ForegroundColor Gray
    docker-compose run --rm -e DB_HOST=postgres -e DB_PORT=5432 -e DB_USER=ai_user -e DB_PASSWORD=ai_password -e DB_NAME=ai_platform metadata-service sh -c "cd /database/src; alembic upgrade head"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ 数据库迁移完成" -ForegroundColor Green
    } else {
        Write-Host "✗ 数据库迁移失败" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[3/8] 跳过数据库迁移" -ForegroundColor Gray
}

# 3. 启动metadata-service
Write-Host ""
Write-Host "[4/8] 启动metadata-service..." -ForegroundColor Yellow
if (-not $SkipBuild) {
    docker-compose up -d --build metadata-service
} else {
    docker-compose up -d metadata-service
}

# 等待服务启动
$maxRetries = 30
$retryCount = 0
while ($retryCount -lt $maxRetries) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8005/api/health" -Method GET -TimeoutSec 5 -UseBasicParsing 2>&1
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ metadata-service已就绪" -ForegroundColor Green
            break
        }
    } catch {
        # 继续重试
    }
    $retryCount++
    Write-Host "等待metadata-service启动... ($retryCount/$maxRetries)" -ForegroundColor Gray
    Start-Sleep -Seconds 2
}

if ($retryCount -eq $maxRetries) {
    Write-Host "✗ metadata-service启动超时" -ForegroundColor Red
    Write-Host "查看日志: docker-compose logs metadata-service" -ForegroundColor Yellow
    exit 1
}

# 4. 测试API接口
if (-not $SkipAPITests) {
    Write-Host ""
    Write-Host "[5/8] 测试API接口..." -ForegroundColor Yellow
    
    $baseUrl = "http://localhost:8005/api"
    $testResults = @{}
    
    # 测试1: 健康检查
    Write-Host "  测试健康检查..." -ForegroundColor Gray
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl/health" -Method GET -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✓ 健康检查通过" -ForegroundColor Green
            $testResults["health"] = $true
        }
    } catch {
        Write-Host "  ✗ 健康检查失败: $_" -ForegroundColor Red
        $testResults["health"] = $false
    }
    
    # 测试2: 列出数据资产（带维度分类参数）
    Write-Host "  测试数据资产列表API（维度分类）..." -ForegroundColor Gray
    try {
        $uri = "$baseUrl/data-assets?limit=5`&business_domain=finance"
        $response = Invoke-WebRequest -Uri $uri -Method GET -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✓ 数据资产列表API通过" -ForegroundColor Green
            $testResults["data_assets"] = $true
        }
    } catch {
        Write-Host "  ✗ 数据资产列表API失败: $_" -ForegroundColor Red
        $testResults["data_assets"] = $false
    }
    
    # 测试3: 分类迁移预览API
    Write-Host "  测试分类迁移预览API..." -ForegroundColor Gray
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl/classification/migration/preview?limit=5" -Method GET -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            $content = $response.Content | ConvertFrom-Json
            if ($content.status -eq "success") {
                Write-Host "  ✓ 分类迁移预览API通过" -ForegroundColor Green
                $testResults["migration_preview"] = $true
            } else {
                Write-Host "  ✗ 分类迁移预览API返回错误状态" -ForegroundColor Red
                $testResults["migration_preview"] = $false
            }
        }
    } catch {
        Write-Host "  ✗ 分类迁移预览API失败: $_" -ForegroundColor Red
        $testResults["migration_preview"] = $false
    }
    
    # 测试4: 分类迁移试运行
    Write-Host "  测试分类迁移试运行..." -ForegroundColor Gray
    try {
        $body = @{
            dry_run = $true
            batch_size = 10
        } | ConvertTo-Json
        
        $response = Invoke-WebRequest -Uri "$baseUrl/classification/migrate" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            $content = $response.Content | ConvertFrom-Json
            if ($content.status -eq "success") {
                Write-Host "  ✓ 分类迁移试运行通过" -ForegroundColor Green
                Write-Host "    统计信息: $($content.stats | ConvertTo-Json -Compress)" -ForegroundColor Gray
                $testResults["migration_dry_run"] = $true
            } else {
                Write-Host "  ✗ 分类迁移试运行返回错误状态" -ForegroundColor Red
                $testResults["migration_dry_run"] = $false
            }
        }
    } catch {
        Write-Host "  ✗ 分类迁移试运行失败: $_" -ForegroundColor Red
        $testResults["migration_dry_run"] = $false
    }
    
    # 汇总测试结果
    Write-Host ""
    Write-Host "API测试结果汇总:" -ForegroundColor Cyan
    $passed = ($testResults.Values | Where-Object { $_ -eq $true }).Count
    $total = $testResults.Count
    foreach ($test in $testResults.Keys) {
        $status = if ($testResults[$test]) { "✓" } else { "✗" }
        if ($testResults[$test]) {
            $color = "Green"
        } else {
            $color = "Red"
        }
        Write-Host "  $status $test" -ForegroundColor $color
    }
    if ($passed -eq $total) {
        $summaryColor = "Green"
    } else {
        $summaryColor = "Yellow"
    }
    Write-Host "  通过: $passed/$total" -ForegroundColor $summaryColor
} else {
    Write-Host "[5/8] 跳过API测试" -ForegroundColor Gray
}

# 5. 启动web-ui（可选）
Write-Host ""
Write-Host "[6/8] 启动web-ui（用于前端测试）..." -ForegroundColor Yellow
if (-not $SkipFrontendTests) {
    if (-not $SkipBuild) {
        docker-compose up -d --build web-ui
    } else {
        docker-compose up -d web-ui
    }
    
    # 等待web-ui启动
    $maxRetries = 60
    $retryCount = 0
    while ($retryCount -lt $maxRetries) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:3000/api/health" -Method GET -TimeoutSec 5 -UseBasicParsing 2>&1
            if ($response.StatusCode -eq 200) {
                Write-Host "✓ web-ui已就绪" -ForegroundColor Green
                break
            }
        } catch {
            # 继续重试
        }
        $retryCount++
        if ($retryCount % 10 -eq 0) {
            Write-Host "等待web-ui启动... ($retryCount/$maxRetries)" -ForegroundColor Gray
        }
        Start-Sleep -Seconds 2
    }
    
    if ($retryCount -lt $maxRetries) {
        Write-Host ""
        Write-Host "[7/8] 前端测试说明..." -ForegroundColor Yellow
        Write-Host "  前端已启动，请手动测试以下功能:" -ForegroundColor Cyan
        Write-Host "  1. 访问 http://localhost:3000/admin/metadata" -ForegroundColor White
        Write-Host "  2. 切换到不同标签页（data-assets, workflows, ai-models, business-entities）" -ForegroundColor White
        Write-Host "  3. 点击任意元数据项查看详情" -ForegroundColor White
        Write-Host "  4. 检查'分类维度'部分是否正确显示" -ForegroundColor White
        Write-Host "  5. 验证分类维度编辑器是否正常渲染" -ForegroundColor White
    } else {
        Write-Host "⚠ web-ui启动超时，但可以继续测试" -ForegroundColor Yellow
    }
} else {
    Write-Host "[6/8] 跳过前端测试" -ForegroundColor Gray
}

# 6. 验证数据库字段
Write-Host ""
Write-Host "[7/8] 验证数据库字段..." -ForegroundColor Yellow
try {
    $sql = @"
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'data_assets' 
AND column_name IN ('classification_dimensions', 'standardized_tags');
"@
    
    $result = docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -t -c $sql 2>&1
    if ($result -match "classification_dimensions" -and $result -match "standardized_tags") {
        Write-Host "✓ 数据库字段验证通过" -ForegroundColor Green
        Write-Host "  找到字段: classification_dimensions, standardized_tags" -ForegroundColor Gray
    } else {
        Write-Host "⚠ 部分字段可能未找到，请检查迁移是否成功" -ForegroundColor Yellow
        Write-Host "  查询结果: $result" -ForegroundColor Gray
    }
} catch {
    Write-Host "⚠ 数据库字段验证失败: $_" -ForegroundColor Yellow
}

# 7. 生成测试报告
Write-Host ""
Write-Host "[8/8] 生成测试报告..." -ForegroundColor Yellow
$report = @{
    timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    tests = $testResults
    services = @{
        postgres = "运行中"
        redis = "运行中"
        metadata_service = "运行中"
    }
    if (-not $SkipFrontendTests) {
        $report.services.web_ui = "运行中"
    } else {
        $report.services.web_ui = "未启动"
    }
}

$reportPath = "docs/testing/classification-phase1-phase2-test-report.json"
$reportDir = Split-Path -Parent $reportPath
if (-not (Test-Path $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
}

$report | ConvertTo-Json -Depth 10 | Out-File -FilePath $reportPath -Encoding UTF8
Write-Host "✓ 测试报告已保存: $reportPath" -ForegroundColor Green

# 完成
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "服务状态:" -ForegroundColor Yellow
Write-Host "  - PostgreSQL: http://localhost:5432" -ForegroundColor White
Write-Host "  - Redis: http://localhost:6379" -ForegroundColor White
Write-Host "  - Metadata Service: http://localhost:8005" -ForegroundColor White
Write-Host "  - Metadata Service API Docs: http://localhost:8005/api/docs" -ForegroundColor White
if (-not $SkipFrontendTests) {
    Write-Host "  - Web UI: http://localhost:3000" -ForegroundColor White
    Write-Host "  - Metadata Admin: http://localhost:3000/admin/metadata" -ForegroundColor White
}
Write-Host ""
Write-Host "查看服务日志:" -ForegroundColor Yellow
Write-Host "  docker-compose logs -f metadata-service" -ForegroundColor White
Write-Host ""
Write-Host "停止所有服务:" -ForegroundColor Yellow
Write-Host "  docker-compose down" -ForegroundColor White

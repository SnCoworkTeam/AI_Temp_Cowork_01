# 企业架构功能测试脚本

Write-Host "========================================" -ForegroundColor Green
Write-Host "  企业架构功能测试" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 1. 检查并启动服务
Write-Host "[1/5] 检查并启动服务..." -ForegroundColor Cyan
docker-compose up -d postgres metadata-service api-gateway 2>&1 | Out-Null
Start-Sleep -Seconds 5
Write-Host "  ✓ 服务启动命令已执行" -ForegroundColor Green
Write-Host ""

# 2. 等待服务就绪
Write-Host "[2/5] 等待服务就绪..." -ForegroundColor Cyan
$maxWait = 30
$waited = 0
while ($waited -lt $maxWait) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8005/api/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✓ Metadata Service 已就绪" -ForegroundColor Green
            break
        }
    } catch {
        Start-Sleep -Seconds 2
        $waited += 2
        Write-Host "  等待中... ($waited/$maxWait 秒)" -ForegroundColor Gray
    }
}
Write-Host ""

# 3. 运行数据库迁移
Write-Host "[3/5] 运行数据库迁移..." -ForegroundColor Cyan
$env:PYTHONPATH = "$PWD;$PWD/database;$PWD/shared_libs"
cd database
python -m alembic upgrade head 2>&1 | Out-String | Write-Host
cd ..
Write-Host "  ✓ 数据库迁移完成" -ForegroundColor Green
Write-Host ""

# 4. 测试企业架构API
Write-Host "[4/5] 测试企业架构API..." -ForegroundColor Cyan

# 测试总览API
Write-Host "  测试总览API..." -ForegroundColor Gray
try {
    $overview = Invoke-RestMethod -Uri "http://localhost:8080/api/enterprise-architecture/overview" -Method Get -ErrorAction Stop
    Write-Host "    ✓ 总览API正常" -ForegroundColor Green
    Write-Host "      业务架构: $($overview.business_architecture.processes_count) 流程, $($overview.business_architecture.capabilities_count) 能力" -ForegroundColor Gray
    Write-Host "      应用架构: $($overview.application_architecture.systems_count) 系统" -ForegroundColor Gray
    Write-Host "      数据架构: $($overview.data_architecture.entities_count) 实体" -ForegroundColor Gray
    Write-Host "      技术架构: $($overview.technology_architecture.components_count) 组件" -ForegroundColor Gray
} catch {
    Write-Host "    ✗ 总览API失败: $_" -ForegroundColor Red
}

# 测试业务架构API
Write-Host "  测试业务架构API..." -ForegroundColor Gray
try {
    $business = Invoke-RestMethod -Uri "http://localhost:8080/api/enterprise-architecture/business" -Method Get -ErrorAction Stop
    Write-Host "    ✓ 业务架构API正常 (返回 $($business.processes.Count) 流程)" -ForegroundColor Green
} catch {
    Write-Host "    ✗ 业务架构API失败: $_" -ForegroundColor Red
}

# 测试关系图API
Write-Host "  测试关系图API..." -ForegroundColor Gray
try {
    $graph = Invoke-RestMethod -Uri "http://localhost:8080/api/enterprise-architecture/graph" -Method Get -ErrorAction Stop
    Write-Host "    ✓ 关系图API正常 (返回 $($graph.nodes.Count) 节点, $($graph.links.Count) 关系)" -ForegroundColor Green
} catch {
    Write-Host "    ✗ 关系图API失败: $_" -ForegroundColor Red
}

Write-Host ""

# 5. 创建知识库和分类
Write-Host "[5/5] 创建知识库和分类..." -ForegroundColor Cyan
Write-Host "  运行知识库初始化脚本..." -ForegroundColor Gray
python scripts/create_ea_knowledge_bases.py --url http://localhost:8004/api 2>&1 | Write-Host

Write-Host "  运行分类初始化脚本..." -ForegroundColor Gray
python scripts/create_ea_metadata_classifications.py --url http://localhost:8005/api/metadata 2>&1 | Write-Host

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  测试完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "访问地址:" -ForegroundColor Cyan
Write-Host "  前端: http://localhost:3000/enterprise-architecture" -ForegroundColor Yellow
Write-Host "  API文档: http://localhost:8005/api/docs" -ForegroundColor Yellow
Write-Host "  API Gateway: http://localhost:8080/api/enterprise-architecture/overview" -ForegroundColor Yellow
Write-Host ""


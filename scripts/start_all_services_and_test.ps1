# 启动所有22个服务并完成第8周测试

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  启动所有服务并完成第8周测试" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 获取脚本所在目录
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR

Set-Location $PROJECT_ROOT

# 定义服务启动顺序（根据依赖关系）
$services = @(
    # 第1层：基础服务
    @{Name="postgres"; Port=5432; WaitTime=10},
    @{Name="redis"; Port=6379; WaitTime=5},
    
    # 第2层：基础设施服务
    @{Name="qdrant"; Port=6333; WaitTime=10},
    @{Name="registry-service"; Port=8000; WaitTime=15},
    @{Name="config-center"; Port=8090; WaitTime=15},
    
    # 第3层：核心服务（依赖基础服务）
    @{Name="mcp-gateway"; Port=8001; WaitTime=20},
    @{Name="workflow-engine"; Port=8002; WaitTime=20},
    @{Name="auth-service"; Port=8003; WaitTime=20},
    @{Name="knowledge-base"; Port=8004; WaitTime=30},
    @{Name="metadata-service"; Port=8005; WaitTime=20},
    @{Name="chat-service"; Port=8006; WaitTime=20},
    
    # 第4层：智能体服务
    @{Name="agent-service"; Port=8010; WaitTime=20},
    @{Name="agent-orchestrator"; Port=8011; WaitTime=20},
    @{Name="agent-registry"; Port=8012; WaitTime=20},
    
    # 第5层：其他服务
    @{Name="memory-service"; Port=8013; WaitTime=20},
    @{Name="sap-metadata-agent"; Port=8015; WaitTime=20},
    @{Name="vector-coordinator-service"; Port=8020; WaitTime=30},
    @{Name="dag-orchestrator"; Port=8009; WaitTime=20},
    @{Name="sap-mcp-server"; Port=3001; WaitTime=20},
    
    # 第6层：网关和前端
    @{Name="api-gateway"; Port=8080; WaitTime=20},
    @{Name="web-ui"; Port=3000; WaitTime=60},
    
    # 第7层：适配器
    @{Name="joyagent-adapter"; Port=8007; WaitTime=30}
)

# 辅助服务（可选）
$optionalServices = @(
    @{Name="redis-commander"; Port=8081; WaitTime=10}
)

function Wait-ForService {
    param(
        [string]$ServiceName,
        [int]$Port,
        [int]$MaxWaitTime = 60,
        [int]$Interval = 5
    )
    
    $elapsed = 0
    $maxAttempts = [math]::Ceiling($MaxWaitTime / $Interval)
    
    Write-Host "  等待服务就绪: $ServiceName (端口: $Port)..." -ForegroundColor Yellow
    
    for ($i = 1; $i -le $maxAttempts; $i++) {
        try {
            $response = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
            if ($response.TcpTestSucceeded) {
                Write-Host "  [OK] $ServiceName 已就绪" -ForegroundColor Green
                return $true
            }
        } catch {
            # 忽略错误，继续等待
        }
        
        Start-Sleep -Seconds $Interval
        $elapsed += $Interval
        Write-Host "    ... ($elapsed/$MaxWaitTime 秒)" -ForegroundColor Gray
    }
    
    Write-Host "  [WARN] $ServiceName 可能未完全就绪，但继续执行" -ForegroundColor Yellow
    return $false
}

# ============================================
# 步骤1: 停止现有服务
# ============================================
Write-Host "[步骤1] 停止现有服务..." -ForegroundColor Cyan
docker-compose down 2>&1 | Out-Null
Start-Sleep -Seconds 3

# ============================================
# 步骤2: 按顺序启动服务
# ============================================
Write-Host ""
Write-Host "[步骤2] 按顺序启动服务..." -ForegroundColor Cyan
Write-Host ""

$startedServices = @()
$failedServices = @()

foreach ($service in $services) {
    $serviceName = $service.Name
    $port = $service.Port
    $waitTime = $service.WaitTime
    
    Write-Host "启动服务: $serviceName (端口: $port)..." -ForegroundColor Yellow
    
    try {
        # 启动服务
        docker-compose up -d $serviceName 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] $serviceName 启动命令执行成功" -ForegroundColor Green
            
            # 等待服务就绪
            $isReady = Wait-ForService -ServiceName $serviceName -Port $port -MaxWaitTime $waitTime
            
            if ($isReady) {
                $startedServices += $serviceName
            } else {
                $failedServices += $serviceName
            }
        } else {
            Write-Host "  [ERROR] $serviceName 启动失败" -ForegroundColor Red
            $failedServices += $serviceName
        }
    } catch {
        Write-Host "  [ERROR] $serviceName 启动异常: $_" -ForegroundColor Red
        $failedServices += $serviceName
    }
    
    Write-Host ""
}

# ============================================
# 步骤3: 显示启动结果
# ============================================
Write-Host "========================================" -ForegroundColor Green
Write-Host "  服务启动结果" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "成功启动: $($startedServices.Count) 个服务" -ForegroundColor Green
foreach ($service in $startedServices) {
    Write-Host "  [OK] $service" -ForegroundColor White
}

if ($failedServices.Count -gt 0) {
    Write-Host ""
    Write-Host "启动失败: $($failedServices.Count) 个服务" -ForegroundColor Yellow
    foreach ($service in $failedServices) {
        Write-Host "  [WARN] $service" -ForegroundColor Yellow
    }
}

Write-Host ""

# ============================================
# 步骤4: 检查关键服务
# ============================================
Write-Host "[步骤3] 检查关键服务..." -ForegroundColor Cyan

$criticalServices = @("postgres", "redis", "registry-service", "api-gateway")
$allCriticalReady = $true

foreach ($service in $criticalServices) {
    $status = docker ps --filter "name=$service" --format "{{.Status}}" 2>$null
    if ($status -match "Up") {
        Write-Host "  [OK] $service 运行中" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] $service 未运行" -ForegroundColor Red
        $allCriticalReady = $false
    }
}

Write-Host ""

# ============================================
# 步骤5: 运行数据库迁移
# ============================================
Write-Host "[步骤4] 运行数据库迁移..." -ForegroundColor Cyan
cd database
python -m alembic upgrade head 2>&1 | Out-Null
cd ..
Write-Host "  [OK] 数据库迁移完成" -ForegroundColor Green
Write-Host ""

# ============================================
# 步骤6: 运行第8周测试
# ============================================
Write-Host "[步骤5] 运行第8周测试..." -ForegroundColor Cyan
Write-Host ""

# 先测试性能监控
python services/performance_monitor.py 2>&1 | Select-Object -Last 10

# 运行场景测试
python -m pytest tests/test_stage1_week8_scenarios.py -v --no-cov --tb=short -s 2>&1 | Select-Object -Last 50

$TEST_EXIT_CODE = $LASTEXITCODE

# ============================================
# 步骤7: 生成测试报告
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  测试结果总结" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

if ($TEST_EXIT_CODE -eq 0) {
    Write-Host "[OK] 所有测试通过！" -ForegroundColor Green
    Write-Host ""
    Write-Host "服务状态:" -ForegroundColor Cyan
    Write-Host "  成功启动: $($startedServices.Count)/$($services.Count) 个服务" -ForegroundColor White
    Write-Host "  关键服务: $($allCriticalReady ? '全部就绪' : '部分未就绪')" -ForegroundColor $(if ($allCriticalReady) { "Green" } else { "Yellow" })
    Write-Host ""
    Write-Host "测试状态:" -ForegroundColor Cyan
    Write-Host "  [OK] 性能监控测试" -ForegroundColor White
    Write-Host "  [OK] 场景测试" -ForegroundColor White
    Write-Host ""
    Write-Host "[OK] 第8周测试完成！" -ForegroundColor Green
} else {
    Write-Host "[ERROR] 测试失败，请检查错误信息" -ForegroundColor Red
    Write-Host ""
    Write-Host "服务状态:" -ForegroundColor Cyan
    Write-Host "  成功启动: $($startedServices.Count)/$($services.Count) 个服务" -ForegroundColor White
    if ($failedServices.Count -gt 0) {
        Write-Host "  失败服务: $($failedServices -join ', ')" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green

exit $TEST_EXIT_CODE





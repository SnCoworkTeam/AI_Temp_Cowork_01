# 启动所有服务并完成未测试部分

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  启动所有服务并完成测试" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 获取项目根目录
$PROJECT_ROOT = $PSScriptRoot | Split-Path -Parent
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
    
    # 第3层：核心服务
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
    @{Name="web-ui"; Port=3000; WaitTime=60}
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
        if ($i % 3 -eq 0) {
            Write-Host "    ... ($elapsed/$MaxWaitTime seconds)" -ForegroundColor Gray
        }
    }
    
    Write-Host "  [WARN] $ServiceName 可能未完全就绪，但继续执行" -ForegroundColor Yellow
    return $false
}

# ============================================
# 步骤1: 启动基础服务
# ============================================
Write-Host "[步骤1] 启动基础服务..." -ForegroundColor Cyan
docker-compose up -d postgres redis qdrant 2>&1 | Out-Null
Start-Sleep -Seconds 15

# 等待基础服务就绪
Wait-ForService -ServiceName "postgres" -Port 5432 -MaxWaitTime 30
Wait-ForService -ServiceName "redis" -Port 6379 -MaxWaitTime 20
Wait-ForService -ServiceName "qdrant" -Port 6333 -MaxWaitTime 30

# ============================================
# 步骤2: 启动基础设施服务
# ============================================
Write-Host "`n[步骤2] 启动基础设施服务..." -ForegroundColor Cyan
docker-compose up -d registry-service config-center 2>&1 | Out-Null
Start-Sleep -Seconds 10

Wait-ForService -ServiceName "registry-service" -Port 8000 -MaxWaitTime 30
Wait-ForService -ServiceName "config-center" -Port 8090 -MaxWaitTime 30

# ============================================
# 步骤3: 启动核心服务
# ============================================
Write-Host "`n[步骤3] 启动核心服务..." -ForegroundColor Cyan
docker-compose up -d mcp-gateway workflow-engine auth-service knowledge-base metadata-service chat-service 2>&1 | Out-Null
Start-Sleep -Seconds 15

# ============================================
# 步骤4: 启动智能体服务
# ============================================
Write-Host "`n[步骤4] 启动智能体服务..." -ForegroundColor Cyan
docker-compose up -d agent-service agent-orchestrator agent-registry 2>&1 | Out-Null
Start-Sleep -Seconds 15

# ============================================
# 步骤5: 启动其他服务
# ============================================
Write-Host "`n[步骤5] 启动其他服务..." -ForegroundColor Cyan
docker-compose up -d memory-service sap-metadata-agent vector-coordinator-service dag-orchestrator sap-mcp-server 2>&1 | Out-Null
Start-Sleep -Seconds 15

# ============================================
# 步骤6: 启动网关和前端
# ============================================
Write-Host "`n[步骤6] 启动网关和前端..." -ForegroundColor Cyan
docker-compose up -d api-gateway web-ui 2>&1 | Out-Null
Start-Sleep -Seconds 20

# ============================================
# 步骤7: 检查服务状态
# ============================================
Write-Host "`n[步骤7] 检查服务状态..." -ForegroundColor Cyan
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" | Select-Object -First 25

# ============================================
# 步骤8: 安装测试依赖
# ============================================
Write-Host "`n[步骤8] 安装测试依赖..." -ForegroundColor Cyan
pip install fastapi uvicorn httpx --quiet 2>&1 | Out-Null
Write-Host "  [OK] 依赖安装完成" -ForegroundColor Green

# ============================================
# 步骤9: 运行未完成的测试
# ============================================
Write-Host "`n[步骤9] 运行未完成的测试..." -ForegroundColor Cyan
Write-Host ""

# 运行增强路由器测试（修复导入后）
Write-Host "  运行增强路由器测试..." -ForegroundColor Yellow
python -m pytest tests/test_enhanced_intelligent_router.py -v --no-cov --tb=line 2>&1 | Select-String -Pattern "PASSED|FAILED|SKIPPED|passed|failed|skipped|====" | Select-Object -Last 15

# 运行API测试
Write-Host "`n  运行统一意图API测试..." -ForegroundColor Yellow
python -m pytest tests/test_unified_intent_api.py -v --no-cov --tb=line 2>&1 | Select-String -Pattern "PASSED|FAILED|SKIPPED|passed|failed|skipped|====" | Select-Object -Last 15

Write-Host "`n  运行协同界面API测试..." -ForegroundColor Yellow
python -m pytest tests/test_collaborative_interface_api.py -v --no-cov --tb=line 2>&1 | Select-String -Pattern "PASSED|FAILED|SKIPPED|passed|failed|skipped|====" | Select-Object -Last 15

# 运行所有测试并生成报告
Write-Host "`n  运行所有测试..." -ForegroundColor Yellow
python -m pytest tests/test_enhanced_intelligent_router.py tests/test_unified_intent_api.py tests/test_collaborative_interface_api.py tests/test_e2e_procurement.py -v --no-cov --tb=line 2>&1 | Tee-Object -FilePath "test_results.txt"

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  测试完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nTest results saved to: test_results.txt" -ForegroundColor Cyan


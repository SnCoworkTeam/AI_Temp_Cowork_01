# 按顺序启动所有21个服务
# 根据依赖关系分批启动，避免内存不足

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  启动所有21个服务" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 获取项目根目录
$PROJECT_ROOT = $PSScriptRoot | Split-Path -Parent
Set-Location $PROJECT_ROOT

# 检查Docker内存
Write-Host "[检查] Docker资源使用情况..." -ForegroundColor Cyan
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}" | Select-Object -First 10
Write-Host ""

# 定义服务启动顺序（根据依赖关系）
$serviceBatches = @(
    # 第1批：基础服务（必须最先启动）
    @{
        Name = "Base Services"
        Services = @("postgres", "redis", "qdrant")
        WaitTime = 15
    },
    # 第2批：基础设施服务
    @{
        Name = "Infrastructure Services"
        Services = @("registry-service", "config-center")
        WaitTime = 20
    },
    # 第3批：核心服务（依赖基础服务）
    @{
        Name = "Core Services - Group 1"
        Services = @("mcp-gateway", "workflow-engine")
        WaitTime = 20
    },
    @{
        Name = "Core Services - Group 2"
        Services = @("auth-service", "knowledge-base", "metadata-service")
        WaitTime = 20
    },
    @{
        Name = "Core Services - Group 3"
        Services = @("chat-service", "memory-service")
        WaitTime = 20
    },
    # 第4批：智能体服务（依赖核心服务）
    @{
        Name = "Agent Services"
        Services = @("agent-service", "agent-orchestrator", "agent-registry")
        WaitTime = 25
    },
    # 第5批：其他服务
    @{
        Name = "Other Services - Group 1"
        Services = @("dag-orchestrator", "sap-mcp-server")
        WaitTime = 20
    },
    @{
        Name = "Other Services - Group 2"
        Services = @("sap-metadata-agent", "vector-coordinator-service")
        WaitTime = 20
    },
    # 第6批：网关和前端（最后启动）
    @{
        Name = "Gateway and Frontend"
        Services = @("api-gateway", "web-ui")
        WaitTime = 30
    }
)

function Wait-ForService {
    param(
        [string]$ServiceName,
        [int]$MaxWaitTime = 60,
        [int]$Interval = 5
    )
    
    $elapsed = 0
    $maxAttempts = [math]::Ceiling($MaxWaitTime / $Interval)
    
    for ($i = 1; $i -le $maxAttempts; $i++) {
        $status = docker inspect --format='{{.State.Status}}' "enterprise-ai-$($ServiceName -replace '_', '-')" 2>$null
        if ($status -eq "running") {
            Write-Host "  [OK] $ServiceName 已启动" -ForegroundColor Green
            return $true
        }
        
        Start-Sleep -Seconds $Interval
        $elapsed += $Interval
        if ($i % 3 -eq 0) {
            Write-Host "    ... 等待中 ($elapsed/$MaxWaitTime 秒)" -ForegroundColor Gray
        }
    }
    
    Write-Host "  [WARN] $ServiceName 可能未完全启动" -ForegroundColor Yellow
    return $false
}

# 启动服务批次
$totalBatches = $serviceBatches.Count
$currentBatch = 0

foreach ($batch in $serviceBatches) {
    $currentBatch++
    Write-Host "[批次 $currentBatch/$totalBatches] 启动 $($batch.Name)..." -ForegroundColor Cyan
    Write-Host "  服务: $($batch.Services -join ', ')" -ForegroundColor Yellow
    
    try {
        # 启动服务
        $servicesArg = $batch.Services -join " "
        docker-compose up -d $servicesArg 2>&1 | Out-Null
        
        # 等待服务启动
        Write-Host "  等待服务就绪..." -ForegroundColor Yellow
        Start-Sleep -Seconds $batch.WaitTime
        
        # 检查服务状态
        $allRunning = $true
        foreach ($service in $batch.Services) {
            $containerName = "enterprise-ai-$($service -replace '_', '-')"
            $status = docker inspect --format='{{.State.Status}}' $containerName 2>$null
            if ($status -eq "running") {
                Write-Host "  [OK] $service - Running" -ForegroundColor Green
            } else {
                Write-Host "  [WARN] $service - $status" -ForegroundColor Yellow
                $allRunning = $false
            }
        }
        
        if ($allRunning) {
            Write-Host "  [OK] $($batch.Name) 启动成功" -ForegroundColor Green
        } else {
            Write-Host "  [WARN] $($batch.Name) 部分服务未启动" -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host "  [ERROR] 启动失败: $_" -ForegroundColor Red
    }
    
    Write-Host ""
}

# 最终状态检查
Write-Host "========================================" -ForegroundColor Green
Write-Host "  最终服务状态" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" | Select-Object -First 25

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  服务启动完成" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# 统计
$running = (docker-compose ps --format "{{.Status}}" | Where-Object { $_ -match "Up" }).Count
$total = (docker-compose config --services).Count
Write-Host "运行中: $running/$total 个服务" -ForegroundColor Cyan


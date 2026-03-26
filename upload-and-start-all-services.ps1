# 上传项目管理服务并启动所有服务
$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"
$SERVER_PATH = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  上传项目管理服务并启动所有服务" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 检查密钥文件
if (-not (Test-Path $SSH_KEY)) {
    $SSH_KEY = "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem"
    if (-not (Test-Path $SSH_KEY)) {
        Write-Host "错误: 找不到密钥文件" -ForegroundColor Red
        exit 1
    }
}

# 测试SSH连接
Write-Host "[1/8] 测试SSH连接..." -ForegroundColor Cyan
$test = ssh -i $SSH_KEY -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server "echo OK" 2>&1
if ($LASTEXITCODE -ne 0) {
    $test = ssh -i $SSH_KEY -o ConnectTimeout=10 -o StrictHostKeyChecking=no $SERVER "echo OK" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "SSH连接失败!" -ForegroundColor Red
        Write-Host $test
        exit 1
    }
}
Write-Host "✓ SSH连接成功" -ForegroundColor Green
Write-Host ""

# 上传项目管理服务
Write-Host "[2/8] 上传项目管理服务..." -ForegroundColor Cyan
if (Test-Path "project-management") {
    Write-Host "  正在上传 project-management 目录..." -ForegroundColor Yellow
    scp -i $SSH_KEY -F remote.ssh -r -o StrictHostKeyChecking=no project-management enterprise-ai-server:$SERVER_PATH/ 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        scp -i $SSH_KEY -r -o StrictHostKeyChecking=no project-management $SERVER`:$SERVER_PATH/ 2>&1 | Out-Null
    }
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ project-management 上传成功" -ForegroundColor Green
    } else {
        Write-Host "  ✗ project-management 上传失败" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  ✗ 找不到 project-management 目录" -ForegroundColor Red
    exit 1
}

# 上传数据库模型
Write-Host ""
Write-Host "[3/8] 上传数据库模型..." -ForegroundColor Cyan
if (Test-Path "database/src/models/project_models.py") {
    $remoteDir = "$SERVER_PATH/database/src/models"
    ssh -i $SSH_KEY -F remote.ssh enterprise-ai-server "mkdir -p $remoteDir" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p $remoteDir" 2>&1 | Out-Null
    }
    scp -i $SSH_KEY -F remote.ssh -o StrictHostKeyChecking=no database/src/models/project_models.py enterprise-ai-server:$remoteDir/ 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        scp -i $SSH_KEY -o StrictHostKeyChecking=no database/src/models/project_models.py $SERVER`:$remoteDir/ 2>&1 | Out-Null
    }
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ project_models.py 上传成功" -ForegroundColor Green
    }
}

# 上传前端菜单修改
Write-Host ""
Write-Host "[3.5/8] 上传前端菜单修改..." -ForegroundColor Cyan
if (Test-Path "web-ui/src/components/Layout/Sidebar.tsx") {
    $remoteDir = "$SERVER_PATH/web-ui/src/components/Layout"
    ssh -i $SSH_KEY -F remote.ssh enterprise-ai-server "mkdir -p $remoteDir" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p $remoteDir" 2>&1 | Out-Null
    }
    scp -i $SSH_KEY -F remote.ssh -o StrictHostKeyChecking=no web-ui/src/components/Layout/Sidebar.tsx enterprise-ai-server:$remoteDir/ 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        scp -i $SSH_KEY -o StrictHostKeyChecking=no web-ui/src/components/Layout/Sidebar.tsx $SERVER`:$remoteDir/ 2>&1 | Out-Null
    }
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Sidebar.tsx 上传成功" -ForegroundColor Green
    }
}

# 上传前端项目管理页面（如果存在）
Write-Host ""
Write-Host "[3.6/8] 检查并上传前端项目管理页面..." -ForegroundColor Cyan
$frontendProjectPaths = @(
    "web-ui/src/app/admin/projects",
    "web-ui/src/app/projects"
)
foreach ($path in $frontendProjectPaths) {
    if (Test-Path $path) {
        Write-Host "  发现前端页面: $path" -ForegroundColor Yellow
        $remoteDir = "$SERVER_PATH/$path"
        ssh -i $SSH_KEY -F remote.ssh enterprise-ai-server "mkdir -p $remoteDir" 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p $remoteDir" 2>&1 | Out-Null
        }
        scp -i $SSH_KEY -F remote.ssh -r -o StrictHostKeyChecking=no $path/* enterprise-ai-server:$remoteDir/ 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            scp -i $SSH_KEY -r -o StrictHostKeyChecking=no $path/* $SERVER`:$remoteDir/ 2>&1 | Out-Null
        }
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ $path 上传成功" -ForegroundColor Green
        }
    }
}

# 上传docker-compose.yml
Write-Host ""
Write-Host "[4/8] 更新 docker-compose.yml..." -ForegroundColor Cyan
if (Test-Path "docker-compose.yml") {
    scp -i $SSH_KEY -F remote.ssh -o StrictHostKeyChecking=no docker-compose.yml enterprise-ai-server:$SERVER_PATH/ 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        scp -i $SSH_KEY -o StrictHostKeyChecking=no docker-compose.yml $SERVER`:$SERVER_PATH/ 2>&1 | Out-Null
    }
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ docker-compose.yml 上传成功" -ForegroundColor Green
    }
}

# 构建项目管理服务
Write-Host ""
Write-Host "[5/8] 构建项目管理服务..." -ForegroundColor Cyan
$buildCmd = "cd $SERVER_PATH; docker compose build project-management"
ssh -i $SSH_KEY -F remote.ssh enterprise-ai-server $buildCmd 2>&1
if ($LASTEXITCODE -ne 0) {
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $buildCmd 2>&1
}
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ 构建成功" -ForegroundColor Green
} else {
    Write-Host "  ✗ 构建失败" -ForegroundColor Red
}

# 检查所有服务状态
Write-Host ""
Write-Host "[6/8] 检查所有服务状态..." -ForegroundColor Cyan
$statusCmd = "cd $SERVER_PATH; docker compose ps"
$stoppedServices = ssh -i $SSH_KEY -F remote.ssh enterprise-ai-server $statusCmd 2>&1
if ($LASTEXITCODE -ne 0) {
    $stoppedServices = ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $statusCmd 2>&1
}

Write-Host "当前服务状态:" -ForegroundColor Yellow
ssh -i $SSH_KEY -F remote.ssh enterprise-ai-server "cd $SERVER_PATH; docker compose ps" 2>&1
if ($LASTEXITCODE -ne 0) {
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "cd $SERVER_PATH; docker compose ps" 2>&1
}

# 按顺序启动所有服务
Write-Host ""
Write-Host "[7/8] 按顺序启动所有服务..." -ForegroundColor Cyan

# 定义服务启动批次
$serviceBatches = @(
    @{
        Name = "基础服务 (Level 1)"
        Services = @("postgres", "redis", "qdrant")
        WaitTime = 15
    },
    @{
        Name = "基础设施服务 (Level 2)"
        Services = @("registry-service", "config-center")
        WaitTime = 20
    },
    @{
        Name = "核心服务 - 第1组 (Level 3)"
        Services = @("mcp-gateway", "workflow-engine")
        WaitTime = 20
    },
    @{
        Name = "核心服务 - 第2组 (Level 3)"
        Services = @("auth-service", "knowledge-base", "metadata-service")
        WaitTime = 20
    },
    @{
        Name = "核心服务 - 第3组 (Level 3)"
        Services = @("chat-service", "memory-service")
        WaitTime = 20
    },
    @{
        Name = "项目管理服务 (Level 3)"
        Services = @("project-management")
        WaitTime = 20
    },
    @{
        Name = "智能体服务 (Level 4)"
        Services = @("agent-service", "agent-orchestrator", "agent-registry")
        WaitTime = 25
    },
    @{
        Name = "其他服务 - 第1组 (Level 5)"
        Services = @("dag-orchestrator", "sap-mcp-server")
        WaitTime = 20
    },
    @{
        Name = "其他服务 - 第2组 (Level 5)"
        Services = @("sap-metadata-agent", "vector-coordinator-service")
        WaitTime = 20
    },
    @{
        Name = "网关和前端 (Level 6)"
        Services = @("api-gateway", "web-ui")
        WaitTime = 30
    }
)

foreach ($batch in $serviceBatches) {
    Write-Host ""
    Write-Host "启动批次: $($batch.Name)" -ForegroundColor Yellow
    $servicesStr = $batch.Services -join " "
    $startCmd = "cd $SERVER_PATH; docker compose up -d $servicesStr"
    
    ssh -i $SSH_KEY -F remote.ssh enterprise-ai-server $startCmd 2>&1
    if ($LASTEXITCODE -ne 0) {
        ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $startCmd 2>&1
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ $($batch.Name) 启动成功" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ $($batch.Name) 启动可能有问题" -ForegroundColor Yellow
    }
    
    Write-Host "  等待 $($batch.WaitTime) 秒..." -ForegroundColor Cyan
    Start-Sleep -Seconds $batch.WaitTime
}

# 最终状态检查
Write-Host ""
Write-Host "[8/8] 最终服务状态检查..." -ForegroundColor Cyan
$finalStatusCmd = "cd $SERVER_PATH; docker compose ps"
ssh -i $SSH_KEY -F remote.ssh enterprise-ai-server $finalStatusCmd 2>&1
if ($LASTEXITCODE -ne 0) {
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $finalStatusCmd 2>&1
}

# 检查项目管理服务健康状态
Write-Host ""
Write-Host "检查项目管理服务健康状态..." -ForegroundColor Cyan
$healthCmd = 'curl -s http://localhost:8016/api/health || echo "Service not ready yet"'
$health = ssh -i $SSH_KEY -F remote.ssh enterprise-ai-server $healthCmd 2>&1
if ($LASTEXITCODE -ne 0) {
    $health = ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $healthCmd 2>&1
}
Write-Host $health

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "服务访问地址:" -ForegroundColor Cyan
Write-Host "  - 项目管理服务: http://43.143.139.197:8016/api/health" -ForegroundColor Yellow
Write-Host "  - API网关: http://43.143.139.197:8080/health" -ForegroundColor Yellow
Write-Host "  - Web UI: http://43.143.139.197:3000" -ForegroundColor Yellow
Write-Host ""
Write-Host "查看日志命令:" -ForegroundColor Cyan
Write-Host "  ssh -i $SSH_KEY -F remote.ssh enterprise-ai-server 'cd $SERVER_PATH; docker compose logs -f project-management'" -ForegroundColor White
Write-Host ""


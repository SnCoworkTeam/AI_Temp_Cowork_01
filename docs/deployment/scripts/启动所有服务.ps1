# 启动所有服务的PowerShell脚本
$key = "E:\enterprise-ai-platform\enterprise_ai_platform.pem"
$host = "ubuntu@43.143.139.197"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "启动所有服务" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. 修复.env文件
Write-Host "[1/6] 修复.env文件..." -ForegroundColor Blue
ssh -i $key -o StrictHostKeyChecking=no $host "cd /opt/enterprise-ai-platform && sudo rm -f .env && sudo cp env.example .env && sudo chown ubuntu:ubuntu .env && echo '✅ .env已修复'"

# 2. 启动Redis
Write-Host "[2/6] 启动Redis..." -ForegroundColor Blue
ssh -i $key -o StrictHostKeyChecking=no $host "cd /opt/enterprise-ai-platform && sudo docker compose up -d redis"
Start-Sleep -Seconds 3

# 3. 启动MCP Gateway
Write-Host "[3/6] 启动MCP Gateway..." -ForegroundColor Blue
ssh -i $key -o StrictHostKeyChecking=no $host "cd /opt/enterprise-ai-platform && sudo docker compose up -d --build mcp-gateway"
Start-Sleep -Seconds 5

# 4. 启动Auth Service和Knowledge Base
Write-Host "[4/6] 启动Auth Service和Knowledge Base..." -ForegroundColor Blue
ssh -i $key -o StrictHostKeyChecking=no $host "cd /opt/enterprise-ai-platform && sudo docker compose up -d --build auth-service knowledge-base"
Start-Sleep -Seconds 5

# 5. 启动Workflow Engine
Write-Host "[5/6] 启动Workflow Engine..." -ForegroundColor Blue
ssh -i $key -o StrictHostKeyChecking=no $host "cd /opt/enterprise-ai-platform && sudo docker compose up -d --build workflow-engine"
Start-Sleep -Seconds 5

# 6. 启动Web UI
Write-Host "[6/6] 启动Web UI..." -ForegroundColor Blue
ssh -i $key -o StrictHostKeyChecking=no $host "cd /opt/enterprise-ai-platform && sudo docker compose up -d --build web-ui"
Start-Sleep -Seconds 10

# 检查状态
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "服务状态" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$status = ssh -i $key -o StrictHostKeyChecking=no $host "cd /opt/enterprise-ai-platform && sudo docker compose ps"
$status | Write-Output

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "服务统计" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$services = @("redis", "mcp-gateway", "workflow-engine", "auth-service", "knowledge-base", "web-ui")
$running = 0
$stopped = 0

foreach ($svc in $services) {
    $svcStatus = ssh -i $key -o StrictHostKeyChecking=no $host "cd /opt/enterprise-ai-platform && sudo docker compose ps $svc 2>&1 | grep -E '(Up|Exit)' | head -1 || echo 'not_found'"
    if ($svcStatus -match "Up") {
        Write-Host "✅ $svc - 运行中" -ForegroundColor Green
        $running++
    } elseif ($svcStatus -match "Exit") {
        Write-Host "❌ $svc - 已退出" -ForegroundColor Red
        $stopped++
        Write-Host "查看日志:" -ForegroundColor Yellow
        ssh -i $key -o StrictHostKeyChecking=no $host "cd /opt/enterprise-ai-platform && sudo docker compose logs --tail=10 $svc" | Write-Output
    } else {
        Write-Host "⏳ $svc - 未启动" -ForegroundColor Yellow
        $stopped++
    }
}

Write-Host "`n运行中: $running / $($services.Count)" -ForegroundColor $(if ($running -eq $services.Count) { "Green" } else { "Yellow" })
Write-Host "未运行: $stopped / $($services.Count)" -ForegroundColor $(if ($stopped -eq 0) { "Green" } else { "Red" })

if ($running -eq $services.Count) {
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "✅ 所有服务已启动！" -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Green
    Write-Host "服务地址:" -ForegroundColor Cyan
    Write-Host "  - MCP Gateway:      http://43.143.139.197:8001" -ForegroundColor White
    Write-Host "  - Workflow Engine:   http://43.143.139.197:8002" -ForegroundColor White
    Write-Host "  - Auth Service:      http://43.143.139.197:8003" -ForegroundColor White
    Write-Host "  - Knowledge Base:    http://43.143.139.197:8004" -ForegroundColor White
    Write-Host "  - Web UI:            http://43.143.139.197:3000" -ForegroundColor White
} else {
    Write-Host "`n⚠️  部分服务未运行，请检查日志" -ForegroundColor Yellow
}


# Docker 服务连接诊断脚本 (PowerShell)

Write-Host "🔍 检查 Docker 服务连接状态..." -ForegroundColor Cyan
Write-Host ""

# 检查 API Gateway
Write-Host "1. 检查 API Gateway (http://localhost:8080)" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -Method Get -TimeoutSec 5 -ErrorAction Stop
    Write-Host "   ✅ API Gateway 可访问" -ForegroundColor Green
} catch {
    Write-Host "   ❌ API Gateway 不可访问: $_" -ForegroundColor Red
}

# 检查 agent-service
Write-Host "2. 检查 agent-service (http://localhost:8010)" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8010/api/v1/health" -Method Get -TimeoutSec 5 -ErrorAction Stop
    Write-Host "   ✅ agent-service 可访问" -ForegroundColor Green
} catch {
    Write-Host "   ❌ agent-service 不可访问: $_" -ForegroundColor Red
}

# 检查 mcp-gateway
Write-Host "3. 检查 mcp-gateway (http://localhost:8001)" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001/api/health" -Method Get -TimeoutSec 5 -ErrorAction Stop
    Write-Host "   ✅ mcp-gateway 可访问" -ForegroundColor Green
} catch {
    Write-Host "   ❌ mcp-gateway 不可访问: $_" -ForegroundColor Red
}

# 检查 knowledge-base
Write-Host "4. 检查 knowledge-base (http://localhost:8004)" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8004/health" -Method Get -TimeoutSec 5 -ErrorAction Stop
    Write-Host "   ✅ knowledge-base 可访问" -ForegroundColor Green
} catch {
    Write-Host "   ❌ knowledge-base 不可访问: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "📋 检查 Docker 容器状态..." -ForegroundColor Cyan
docker ps --filter "name=enterprise-ai" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

Write-Host ""
Write-Host "🔗 测试服务之间的连接..." -ForegroundColor Cyan
Write-Host "   从 agent-service 容器内测试连接 mcp-gateway:"
docker exec enterprise-ai-agent-service ping -c 2 mcp-gateway 2>&1 | Select-Object -First 5

Write-Host ""
Write-Host "💡 如果服务不可访问，请检查：" -ForegroundColor Yellow
Write-Host "   1. 所有服务是否都在运行: docker-compose ps"
Write-Host "   2. 服务日志是否有错误: docker-compose logs agent-service"
Write-Host "   3. Docker 网络是否正确: docker network ls"
Write-Host "   4. 环境变量配置: docker exec enterprise-ai-agent-service env | grep -E '(MCP_GATEWAY|KNOWLEDGE_BASE)'"

















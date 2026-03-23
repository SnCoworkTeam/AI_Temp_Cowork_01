# PowerShell 脚本：检查服务状态

Write-Host "=== 检查 Docker 服务状态 ===" -ForegroundColor Cyan
docker-compose ps

Write-Host "`n=== 检查 API Gateway 日志（最近20行）===" -ForegroundColor Cyan
docker-compose logs --tail=20 api-gateway

Write-Host "`n=== 检查 Agent Service 日志（最近20行）===" -ForegroundColor Cyan
docker-compose logs --tail=20 agent-service

Write-Host "`n=== 检查服务健康状态 ===" -ForegroundColor Cyan
Write-Host "API Gateway:" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -Method GET -TimeoutSec 5 -UseBasicParsing
    Write-Host "✅ API Gateway 正常: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "❌ API Gateway 无法访问: $_" -ForegroundColor Red
}

Write-Host "`nAgent Service:" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8010/health" -Method GET -TimeoutSec 5 -UseBasicParsing
    Write-Host "✅ Agent Service 正常: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "❌ Agent Service 无法访问: $_" -ForegroundColor Red
}

Write-Host "`n=== 测试聊天端点 ===" -ForegroundColor Cyan
$body = @{
    message = "你好"
    conversation_history = @()
    user_context = @{
        user_id = "test"
    }
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/api/chat/intelligent/stream" `
        -Method POST `
        -ContentType "application/json" `
        -Headers @{"Accept" = "text/event-stream"} `
        -Body $body `
        -TimeoutSec 5 `
        -UseBasicParsing
    Write-Host "✅ 聊天端点可访问" -ForegroundColor Green
} catch {
    Write-Host "❌ 聊天端点无法访问: $_" -ForegroundColor Red
}

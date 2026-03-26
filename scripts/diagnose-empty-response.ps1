# 诊断 ERR_EMPTY_RESPONSE 问题

Write-Host "`n=== 诊断 ERR_EMPTY_RESPONSE 问题 ===" -ForegroundColor Green

$SSH_KEY = "e:\enterprise-ai-platform\remote.ssh"
$SERVER = "root@43.143.139.197"

Write-Host "`n1. 检查所有关键容器状态..." -ForegroundColor Cyan
& ssh -i $SSH_KEY $SERVER "docker ps | grep -E 'web-ui|api-gateway|auth-service'"

Write-Host "`n2. 检查 API Gateway 容器状态和日志..." -ForegroundColor Cyan
& ssh -i $SSH_KEY $SERVER "docker ps -a | grep api-gateway"
& ssh -i $SSH_KEY $SERVER "docker logs --tail 30 enterprise-ai-api-gateway 2>&1"

Write-Host "`n3. 检查 web-ui 容器状态和日志..." -ForegroundColor Cyan
& ssh -i $SSH_KEY $SERVER "docker ps -a | grep web-ui"
& ssh -i $SSH_KEY $SERVER "docker logs --tail 30 enterprise-ai-web-ui 2>&1"

Write-Host "`n4. 测试 API Gateway 健康检查（从容器内）..." -ForegroundColor Cyan
& ssh -i $SSH_KEY $SERVER "docker exec enterprise-ai-api-gateway curl -f http://localhost:8080/health 2>&1 || echo 'API Gateway 无响应'"

Write-Host "`n5. 检查容器资源使用..." -ForegroundColor Cyan
& ssh -i $SSH_KEY $SERVER "docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}' | grep -E 'NAME|web-ui|api-gateway'"

Write-Host "`n6. 检查端口占用..." -ForegroundColor Cyan
& ssh -i $SSH_KEY $SERVER "netstat -tuln | grep -E '3000|8080' || ss -tuln | grep -E '3000|8080'"

Write-Host "`n=== 诊断完成 ===" -ForegroundColor Green
Write-Host "`n如果容器未运行或异常，请执行：" -ForegroundColor Yellow
Write-Host "   docker restart enterprise-ai-api-gateway enterprise-ai-web-ui" -ForegroundColor White





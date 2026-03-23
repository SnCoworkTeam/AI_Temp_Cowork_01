# 检查 web-ui 容器状态和诊断问题

Write-Host "`n=== 检查 web-ui 容器状态 ===" -ForegroundColor Green

$SSH_KEY = "e:\enterprise-ai-platform\remote.ssh"
$SERVER = "root@43.143.139.197"

Write-Host "`n1. 检查 web-ui 容器运行状态..." -ForegroundColor Cyan
& ssh -i $SSH_KEY $SERVER "docker ps | grep web-ui"

Write-Host "`n2. 检查所有 web-ui 容器（包括已停止的）..." -ForegroundColor Cyan
& ssh -i $SSH_KEY $SERVER "docker ps -a | grep web-ui"

Write-Host "`n3. 检查容器日志（最后50行）..." -ForegroundColor Cyan
& ssh -i $SSH_KEY $SERVER "docker logs --tail 50 enterprise-ai-web-ui 2>&1"

Write-Host "`n4. 检查端口 3000 是否被占用..." -ForegroundColor Cyan
& ssh -i $SSH_KEY $SERVER "netstat -tuln | grep 3000 || ss -tuln | grep 3000"

Write-Host "`n5. 测试容器内 Next.js 服务..." -ForegroundColor Cyan
& ssh -i $SSH_KEY $SERVER "docker exec enterprise-ai-web-ui curl -f http://localhost:3000/api/health 2>&1 || echo '容器内服务无响应'"

Write-Host "`n=== 诊断完成 ===" -ForegroundColor Green
Write-Host "`n如果容器未运行，请执行：" -ForegroundColor Yellow
Write-Host "   docker restart enterprise-ai-web-ui" -ForegroundColor White
Write-Host "   或" -ForegroundColor Gray
Write-Host "   cd /opt/enterprise-ai-platform && docker compose restart web-ui" -ForegroundColor White





# 修复 web-ui ERR_EMPTY_RESPONSE 问题

Write-Host "`n=== 修复 web-ui ERR_EMPTY_RESPONSE 问题 ===" -ForegroundColor Green

$SSH_KEY = "e:\enterprise-ai-platform\remote.ssh"
$SERVER = "root@43.143.139.197"

Write-Host "`n步骤1：检查容器状态..." -ForegroundColor Cyan
& ssh -i $SSH_KEY $SERVER "docker ps -a | grep web-ui"

Write-Host "`n步骤2：停止容器..." -ForegroundColor Cyan
& ssh -i $SSH_KEY $SERVER "docker stop enterprise-ai-web-ui 2>&1"

Write-Host "`n步骤3：清除 Next.js 缓存和 node_modules..." -ForegroundColor Cyan
& ssh -i $SSH_KEY $SERVER "docker exec enterprise-ai-web-ui sh -c 'rm -rf /app/.next /app/node_modules/.cache 2>/dev/null; echo Cache cleared' 2>&1 || echo 'Container not running, will clear on restart'"

Write-Host "`n步骤4：重启容器..." -ForegroundColor Cyan
& ssh -i $SSH_KEY $SERVER "docker start enterprise-ai-web-ui 2>&1 || docker restart enterprise-ai-web-ui 2>&1"

Write-Host "`n步骤5：等待20秒让 Next.js 重新编译..." -ForegroundColor Cyan
Start-Sleep -Seconds 20

Write-Host "`n步骤6：检查容器状态..." -ForegroundColor Cyan
& ssh -i $SSH_KEY $SERVER "docker ps | grep web-ui"

Write-Host "`n步骤7：检查容器日志（最后30行）..." -ForegroundColor Cyan
& ssh -i $SSH_KEY $SERVER "docker logs --tail 30 enterprise-ai-web-ui 2>&1"

Write-Host "`n步骤8：测试容器内服务..." -ForegroundColor Cyan
& ssh -i $SSH_KEY $SERVER "docker exec enterprise-ai-web-ui wget --spider -q http://localhost:3000/api/health 2>&1 && echo 'Service is responding' || echo 'Service not responding yet'"

Write-Host "`n=== 修复完成 ===" -ForegroundColor Green
Write-Host "`n如果问题仍然存在，可能需要完全重建容器：" -ForegroundColor Yellow
Write-Host "   cd /opt/enterprise-ai-platform" -ForegroundColor White
Write-Host "   docker-compose stop web-ui" -ForegroundColor White
Write-Host "   docker-compose rm -f web-ui" -ForegroundColor White
Write-Host "   docker-compose up -d web-ui" -ForegroundColor White





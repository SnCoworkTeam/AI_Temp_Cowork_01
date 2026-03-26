# 查看知识库服务日志的PowerShell脚本

$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"
$CONTAINER = "enterprise-ai-knowledge-base"

Write-Host "正在连接服务器查看知识库服务日志..." -ForegroundColor Yellow

# 先检查容器状态
Write-Host "`n1. 检查容器状态..." -ForegroundColor Cyan
ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SERVER "docker ps | grep knowledge"

# 查看最近100行日志
Write-Host "`n2. 查看最近100行日志..." -ForegroundColor Cyan
ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SERVER "docker logs $CONTAINER --tail 100"

# 查看错误日志
Write-Host "`n3. 查看错误日志..." -ForegroundColor Cyan
ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SERVER "docker logs $CONTAINER --tail 200 2>&1 | Select-String -Pattern 'error|Error|ERROR|exception|Exception|EXCEPTION|failed|Failed|FAILED' -Context 2,2"

# 查看实时日志（最后10秒）
Write-Host "`n4. 查看最近10秒的日志..." -ForegroundColor Cyan
ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SERVER "docker logs $CONTAINER --since 10s"

Write-Host "`n完成！" -ForegroundColor Green


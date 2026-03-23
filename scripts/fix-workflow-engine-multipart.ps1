# 修复 workflow-engine 缺少 python-multipart 依赖的问题

Write-Host "`n=== 修复 workflow-engine python-multipart 依赖 ===" -ForegroundColor Green

$SSH_KEY = "e:\enterprise-ai-platform\remote.ssh"
$SERVER = "root@43.143.139.197"

Write-Host "`n1. 上传更新后的 requirements.txt..." -ForegroundColor Cyan
& scp -i $SSH_KEY workflow-engine/requirements.txt ${SERVER}:/root/enterprise-ai-platform/workflow-engine/requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "上传失败，尝试继续..." -ForegroundColor Yellow
}

Write-Host "`n2. 在容器内安装 python-multipart（使用 root 用户安装到系统目录）..." -ForegroundColor Cyan
# 注意：容器运行时使用 appuser，但包需要安装到系统目录才能被所有用户访问
# 使用 root 用户安装到系统目录（不使用 --user 标志）
$installCmdRoot = "docker exec -u root enterprise-ai-workflow-engine pip install --no-cache-dir 'python-multipart>=0.0.6'"
Write-Host "执行: $installCmdRoot" -ForegroundColor Gray
& ssh -i $SSH_KEY $SERVER $installCmdRoot

Write-Host "`n验证安装（检查 Python 能否导入）..." -ForegroundColor Cyan
& ssh -i $SSH_KEY $SERVER "docker exec enterprise-ai-workflow-engine python -c 'import multipart; print(\"OK: multipart installed at\", multipart.__file__)' 2>&1"

Write-Host "`n3. 重启 workflow-engine 容器..." -ForegroundColor Cyan
# 尝试使用 docker compose（新版本），如果失败则使用 docker restart
& ssh -i $SSH_KEY $SERVER "cd /opt/enterprise-ai-platform && docker compose restart workflow-engine 2>&1 || docker restart enterprise-ai-workflow-engine"

Write-Host "`n4. 等待容器启动..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

Write-Host "`n5. 检查容器状态..." -ForegroundColor Cyan
& ssh -i $SSH_KEY $SERVER "docker ps | grep workflow-engine"

Write-Host "`n6. 检查容器日志（最后10行）..." -ForegroundColor Cyan
& ssh -i $SSH_KEY $SERVER "docker logs --tail 10 enterprise-ai-workflow-engine 2>&1"

Write-Host "`n=== 修复完成 ===" -ForegroundColor Green
Write-Host "如果容器状态为 healthy，说明修复成功！" -ForegroundColor Yellow





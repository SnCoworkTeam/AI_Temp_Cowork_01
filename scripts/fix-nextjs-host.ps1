# 修复 Next.js 监听地址问题

Write-Host "`n=== 修复 Next.js 监听地址 ===" -ForegroundColor Green

$SSH_KEY = "e:\enterprise-ai-platform\remote.ssh"
$SERVER = "root@43.143.139.197"

Write-Host "`n步骤1：上传更新后的 package.json..." -ForegroundColor Cyan
& scp -i $SSH_KEY web-ui/package.json ${SERVER}:/opt/enterprise-ai-platform/web-ui/package.json
if ($LASTEXITCODE -ne 0) {
    Write-Host "上传失败，尝试在容器内直接修改..." -ForegroundColor Yellow
    & ssh -i $SSH_KEY $SERVER "docker exec enterprise-ai-web-ui sh -c 'sed -i \"s/next dev/next dev -H 0.0.0.0/\" /app/package.json && echo \"Updated package.json\"'"
}

Write-Host "`n步骤2：验证 package.json 内容..." -ForegroundColor Cyan
& ssh -i $SSH_KEY $SERVER "docker exec enterprise-ai-web-ui cat /app/package.json | grep -A 1 scripts"

Write-Host "`n步骤3：重启容器..." -ForegroundColor Cyan
& ssh -i $SSH_KEY $SERVER "docker restart enterprise-ai-web-ui"

Write-Host "`n步骤4：等待25秒让 Next.js 重新启动..." -ForegroundColor Cyan
Start-Sleep -Seconds 25

Write-Host "`n步骤5：检查 Next.js 是否监听 0.0.0.0..." -ForegroundColor Cyan
& ssh -i $SSH_KEY $SERVER "docker logs --tail 5 enterprise-ai-web-ui 2>&1 | grep -i Local"

Write-Host "`n=== 修复完成 ===" -ForegroundColor Green
Write-Host "如果显示 'Local: http://0.0.0.0:3000'，说明修复成功！" -ForegroundColor Yellow





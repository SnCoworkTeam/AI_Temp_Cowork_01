# 检查web-ui服务状态和依赖安装情况

$serverIP = "43.143.139.197"
$serverUser = "ubuntu"
$keyFile = "enterprise_ai_platform.pem"
$remotePath = "/opt/enterprise-ai-platform"

if (-not (Test-Path $keyFile)) {
    Write-Host "错误: 找不到SSH密钥文件 $keyFile" -ForegroundColor Red
    exit 1
}

$keyPath = Resolve-Path $keyFile

Write-Host "`n=== 1. 检查web-ui服务状态 ===" -ForegroundColor Cyan
$status = ssh -i $keyPath -o StrictHostKeyChecking=no -o ConnectTimeout=10 $serverUser@$serverIP "cd $remotePath && docker compose ps web-ui 2>&1" 2>&1
Write-Host $status

Write-Host "`n=== 2. 检查web-ui容器是否运行 ===" -ForegroundColor Cyan
$running = ssh -i $keyPath -o StrictHostKeyChecking=no -o ConnectTimeout=10 $serverUser@$serverIP "docker ps | grep web-ui" 2>&1
if ($running) {
    Write-Host "✅ web-ui容器正在运行" -ForegroundColor Green
    Write-Host $running
} else {
    Write-Host "❌ web-ui容器未运行" -ForegroundColor Red
}

Write-Host "`n=== 3. 检查web-ui日志（最近20行）===" -ForegroundColor Cyan
$logs = ssh -i $keyPath -o StrictHostKeyChecking=no -o ConnectTimeout=10 $serverUser@$serverIP "cd $remotePath && docker compose logs --tail=20 web-ui 2>&1" 2>&1
Write-Host $logs

Write-Host "`n=== 4. 检查package.json中的依赖 ===" -ForegroundColor Cyan
$packageCheck = ssh -i $keyPath -o StrictHostKeyChecking=no -o ConnectTimeout=10 $serverUser@$serverIP "cd $remotePath/web-ui && grep -E '(react-force-graph|recharts|antd|@ant-design)' package.json 2>&1 | head -10" 2>&1
Write-Host $packageCheck

Write-Host "`n=== 5. 检查node_modules中的依赖 ===" -ForegroundColor Cyan
$nodeModulesCheck = ssh -i $keyPath -o StrictHostKeyChecking=no -o ConnectTimeout=10 $serverUser@$serverIP "cd $remotePath/web-ui && ls -d node_modules/react-force-graph node_modules/recharts node_modules/antd node_modules/@ant-design 2>&1" 2>&1
Write-Host $nodeModulesCheck

Write-Host "`n=== 6. 检查web-ui容器内的依赖 ===" -ForegroundColor Cyan
$containerDeps = ssh -i $keyPath -o StrictHostKeyChecking=no -o ConnectTimeout=10 $serverUser@$serverIP "cd $remotePath && docker compose exec -T web-ui ls -d /app/node_modules/react-force-graph /app/node_modules/recharts /app/node_modules/antd 2>&1" 2>&1
Write-Host $containerDeps

Write-Host "`n=== 7. 检查构建错误 ===" -ForegroundColor Cyan
$buildErrors = ssh -i $keyPath -o StrictHostKeyChecking=no -o ConnectTimeout=10 $serverUser@$serverIP "cd $remotePath && docker compose logs web-ui 2>&1 | grep -i 'error\|fail\|warn' | tail -10" 2>&1
if ($buildErrors) {
    Write-Host "发现错误/警告:" -ForegroundColor Yellow
    Write-Host $buildErrors
} else {
    Write-Host "未发现明显的错误信息" -ForegroundColor Green
}

Write-Host "`n诊断完成！" -ForegroundColor Green





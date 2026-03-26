# 安装web-ui依赖并重启服务

$serverIP = "43.143.139.197"
$serverUser = "ubuntu"
$keyFile = "enterprise_ai_platform.pem"
$remotePath = "/opt/enterprise-ai-platform"
$webUiPath = "$remotePath/web-ui"

if (-not (Test-Path $keyFile)) {
    Write-Host "错误: 找不到SSH密钥文件 $keyFile" -ForegroundColor Red
    exit 1
}

$keyPath = Resolve-Path $keyFile

Write-Host "`n=== 步骤1: 检查web-ui目录 ===" -ForegroundColor Cyan
$checkDir = ssh -i $keyPath -o StrictHostKeyChecking=no -o ConnectTimeout=10 $serverUser@$serverIP "cd $webUiPath && pwd && ls -la package.json 2>&1" 2>&1
Write-Host $checkDir

Write-Host "`n=== 步骤2: 停止web-ui服务 ===" -ForegroundColor Cyan
$stopResult = ssh -i $keyPath -o StrictHostKeyChecking=no -o ConnectTimeout=10 $serverUser@$serverIP "cd $remotePath && docker compose stop web-ui 2>&1" 2>&1
Write-Host $stopResult

Write-Host "`n=== 步骤3: 在服务器上安装依赖（这可能需要几分钟）===" -ForegroundColor Cyan
Write-Host "正在执行: cd $webUiPath && npm install --legacy-peer-deps" -ForegroundColor Yellow

# 使用nohup在后台运行，并设置超时
$installCmd = "cd $webUiPath && npm install --legacy-peer-deps 2>&1 | tee /tmp/npm-install.log"
$installResult = ssh -i $keyPath -o StrictHostKeyChecking=no -o ConnectTimeout=10 $serverUser@$serverIP $installCmd 2>&1

# 显示最后50行输出
Write-Host "`n安装输出（最后50行）:" -ForegroundColor Cyan
Write-Host $installResult

# 检查安装日志
Write-Host "`n=== 检查安装日志 ===" -ForegroundColor Cyan
$logCheck = ssh -i $keyPath -o StrictHostKeyChecking=no -o ConnectTimeout=10 $serverUser@$serverIP "tail -30 /tmp/npm-install.log 2>&1" 2>&1
Write-Host $logCheck

Write-Host "`n=== 步骤4: 验证关键依赖是否安装 ===" -ForegroundColor Cyan
$verifyDeps = ssh -i $keyPath -o StrictHostKeyChecking=no -o ConnectTimeout=10 $serverUser@$serverIP "cd $webUiPath && ls -d node_modules/react-force-graph node_modules/recharts node_modules/antd node_modules/@ant-design/icons 2>&1" 2>&1
if ($verifyDeps -match "No such file") {
    Write-Host "警告: 部分依赖可能未安装成功" -ForegroundColor Yellow
    Write-Host $verifyDeps
} else {
    Write-Host "关键依赖已安装" -ForegroundColor Green
    Write-Host $verifyDeps
}

Write-Host "`n=== 步骤5: 重启web-ui服务 ===" -ForegroundColor Cyan
$restartResult = ssh -i $keyPath -o StrictHostKeyChecking=no -o ConnectTimeout=10 $serverUser@$serverIP "cd $remotePath && docker compose up -d web-ui 2>&1" 2>&1
Write-Host $restartResult

Write-Host "`n等待服务启动（5秒）..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "`n=== 步骤6: 检查服务状态 ===" -ForegroundColor Cyan
$status = ssh -i $keyPath -o StrictHostKeyChecking=no -o ConnectTimeout=10 $serverUser@$serverIP "cd $remotePath && docker compose ps web-ui 2>&1" 2>&1
Write-Host $status

Write-Host "`n=== 步骤7: 查看服务日志（最后20行）===" -ForegroundColor Cyan
$logs = ssh -i $keyPath -o StrictHostKeyChecking=no -o ConnectTimeout=10 $serverUser@$serverIP "cd $remotePath && docker compose logs --tail=20 web-ui 2>&1" 2>&1
Write-Host $logs

Write-Host "`n操作完成！" -ForegroundColor Green


# 快速检查服务状态
param(
    [string]$KeyPath = "E:\enterprise-ai-platform\enterprise_ai_platform.pem",
    [string]$ServerIP = "43.143.139.197",
    [string]$ServerUser = "ubuntu"
)

$sshCmd = "ssh -i `"$KeyPath`" -o StrictHostKeyChecking=no $ServerUser@${ServerIP}"

Write-Host "=== 服务状态检查 ===" -ForegroundColor Cyan
$status = & $sshCmd "cd /opt/enterprise-ai-platform && sudo docker compose ps 2>&1"
$status | Write-Output

Write-Host "`n=== 错误日志检查 ===" -ForegroundColor Yellow
$errors = & $sshCmd "cd /opt/enterprise-ai-platform && sudo docker compose logs --tail=50 2>&1 | grep -iE '(error|failed|exception|traceback)' | head -20"
if ($errors) {
    $errors | Write-Output
} else {
    Write-Host "✅ 未发现错误" -ForegroundColor Green
}

Write-Host "`n=== 各服务状态 ===" -ForegroundColor Cyan
$services = @('mcp-gateway', 'workflow-engine', 'auth-service', 'knowledge-base', 'web-ui')
foreach ($svc in $services) {
    $svcStatus = & $sshCmd "cd /opt/enterprise-ai-platform && sudo docker compose ps $svc 2>&1 | grep -E '(Up|running|Exit)' || echo 'not_found'"
    if ($svcStatus -match 'Up|running') {
        Write-Host "✅ $svc - 运行中" -ForegroundColor Green
    } elseif ($svcStatus -match 'Exit') {
        Write-Host "❌ $svc - 已退出" -ForegroundColor Red
        $logs = & $sshCmd "cd /opt/enterprise-ai-platform && sudo docker compose logs --tail=20 $svc 2>&1"
        Write-Host "日志: $logs" -ForegroundColor Yellow
    } else {
        Write-Host "⏳ $svc - 未启动" -ForegroundColor Yellow
    }
}


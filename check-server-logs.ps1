# 检查服务器日志脚本
# 查看 agent-service, metadata-service, api-gateway 的最近错误日志

$serverIP = "43.143.139.197"
$sshKey = "enterprise_ai_platform.pem"
$services = @(
    "enterprise-ai-agent-service",
    "enterprise-ai-metadata-service", 
    "enterprise-ai-api-gateway"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "检查服务器服务日志" -ForegroundColor Cyan
Write-Host "服务器: $serverIP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

foreach ($service in $services) {
    Write-Host "----------------------------------------" -ForegroundColor Yellow
    Write-Host "检查服务: $service" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Yellow
    
    # 检查容器是否存在
    Write-Host "`n1. 检查容器状态..." -ForegroundColor Green
    $statusCmd = "docker ps --format '{{.Names}}\t{{.Status}}' | grep '$service'"
    $status = ssh -i $sshKey -o StrictHostKeyChecking=no ubuntu@$serverIP $statusCmd 2>&1
    if ($status) {
        Write-Host "容器状态: $status" -ForegroundColor Green
    } else {
        Write-Host "警告: 容器未运行或不存在" -ForegroundColor Red
        Write-Host ""
        continue
    }
    
    # 查看最近的错误日志
    Write-Host "`n2. 查看最近50行包含错误的日志..." -ForegroundColor Green
    $errorCmd = "docker logs $service --tail 200 2>&1 | grep -i 'error\|exception\|failed\|traceback\|critical' | tail -50"
    $errors = ssh -i $sshKey -o StrictHostKeyChecking=no ubuntu@$serverIP $errorCmd 2>&1
    if ($errors -and $errors -notmatch "grep:") {
        Write-Host $errors -ForegroundColor Red
    } else {
        Write-Host "未发现错误日志" -ForegroundColor Green
    }
    
    # 查看最近的警告日志
    Write-Host "`n3. 查看最近20行警告日志..." -ForegroundColor Green
    $warnCmd = "docker logs $service --tail 200 2>&1 | grep -i 'warn\|warning' | tail -20"
    $warnings = ssh -i $sshKey -o StrictHostKeyChecking=no ubuntu@$serverIP $warnCmd 2>&1
    if ($warnings -and $warnings -notmatch "grep:") {
        Write-Host $warnings -ForegroundColor Yellow
    } else {
        Write-Host "未发现警告日志" -ForegroundColor Green
    }
    
    # 查看最近的执行日志（针对agent-service）
    if ($service -eq "enterprise-ai-agent-service") {
        Write-Host "`n4. 查看最近的组织架构查询相关日志..." -ForegroundColor Green
        $orgCmd = "docker logs $service --tail 300 2>&1 | grep -i '组织架构\|organization\|data_query\|data_query_agent' | tail -30"
        $orgLogs = ssh -i $sshKey -o StrictHostKeyChecking=no ubuntu@$serverIP $orgCmd 2>&1
        if ($orgLogs -and $orgLogs -notmatch "grep:") {
            Write-Host $orgLogs -ForegroundColor Cyan
        } else {
            Write-Host "未发现相关日志" -ForegroundColor Gray
        }
    }
    
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "日志检查完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan


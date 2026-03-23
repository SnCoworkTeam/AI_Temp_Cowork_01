# PowerShell 脚本：监控服务状态，发现错误自动修复
# 使用方法: .\scripts\deployment\monitor-and-fix.ps1

param(
    [string]$ServerIP = "43.143.139.197",
    [string]$ServerUser = "ubuntu",
    [string]$KeyPath = "E:\enterprise-ai-platform\enterprise_ai_platform.pem",
    [string]$RemotePath = "/opt/enterprise-ai-platform",
    [int]$MaxIterations = 10
)

$sshCmd = "ssh -i `"$KeyPath`" -o StrictHostKeyChecking=no $ServerUser@${ServerIP}"

function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Cyan "=========================================="
Write-ColorOutput Cyan "服务监控和自动修复脚本"
Write-ColorOutput Cyan "=========================================="
Write-Output ""

$iteration = 0
$allServicesRunning = $false

while (-not $allServicesRunning -and $iteration -lt $MaxIterations) {
    $iteration++
    Write-ColorOutput Blue "=== 第 $iteration 次检查 ==="
    
    # 检查服务状态
    Write-Output "检查服务状态..."
    $psOutput = & $sshCmd "cd $RemotePath && sudo docker compose ps 2>&1"
    $psOutput | Write-Output
    
    # 检查哪些服务应该运行
    $expectedServices = @("redis", "mcp-gateway", "workflow-engine", "auth-service", "knowledge-base", "web-ui")
    $runningServices = @()
    $failedServices = @()
    
    foreach ($service in $expectedServices) {
        $serviceStatus = & $sshCmd "cd $RemotePath && sudo docker compose ps --format json 2>&1 | grep -i $service || echo 'not_found'"
        if ($serviceStatus -match "running" -or $serviceStatus -match "Up") {
            $runningServices += $service
            Write-ColorOutput Green "✅ $service - 运行中"
        } else {
            $failedServices += $service
            Write-ColorOutput Red "❌ $service - 未运行"
        }
    }
    
    # 检查错误日志
    Write-Output ""
    Write-ColorOutput Yellow "检查错误日志..."
    $errorLogs = & $sshCmd "cd $RemotePath && sudo docker compose logs --tail=50 2>&1 | grep -iE '(error|failed|exception|traceback)' | head -20"
    if ($errorLogs) {
        Write-ColorOutput Red "发现错误:"
        $errorLogs | Write-Output
    } else {
        Write-ColorOutput Green "未发现明显错误"
    }
    
    # 如果所有服务都运行，退出循环
    if ($failedServices.Count -eq 0) {
        Write-ColorOutput Green "✅ 所有服务运行正常！"
        $allServicesRunning = $true
        break
    }
    
    # 尝试启动失败的服务
    Write-Output ""
    Write-ColorOutput Blue "尝试启动失败的服务..."
    foreach ($service in $failedServices) {
        Write-Output "启动 $service..."
        $startOutput = & $sshCmd "cd $RemotePath && sudo docker compose up -d $service 2>&1"
        $startOutput | Write-Output
        Start-Sleep -Seconds 5
    }
    
    # 等待服务启动
    Write-Output "等待服务启动..."
    Start-Sleep -Seconds 10
    
    Write-Output ""
}

# 最终状态检查
Write-Output ""
Write-ColorOutput Cyan "=== 最终状态检查 ==="
$finalStatus = & $sshCmd "cd $RemotePath && sudo docker compose ps"
$finalStatus | Write-Output

# 健康检查
Write-Output ""
Write-ColorOutput Cyan "=== 健康检查 ==="
$healthChecks = @(
    @{Port=8001; Name="MCP Gateway"; Path="/api/health"},
    @{Port=8002; Name="Workflow Engine"; Path="/api/health"},
    @{Port=8003; Name="Auth Service"; Path="/health"},
    @{Port=8004; Name="Knowledge Base"; Path="/api/health"},
    @{Port=3000; Name="Web UI"; Path="/api/health"}
)

foreach ($check in $healthChecks) {
    $health = & $sshCmd "curl -s -o /dev/null -w '%{http_code}' http://localhost:$($check.Port)$($check.Path) 2>&1 || echo '000'"
    if ($health -eq "200") {
        Write-ColorOutput Green "✅ $($check.Name) - 健康 (HTTP $health)"
    } else {
        Write-ColorOutput Red "❌ $($check.Name) - 未响应 (HTTP $health)"
    }
}

Write-Output ""
if ($allServicesRunning) {
    Write-ColorOutput Green "=========================================="
    Write-ColorOutput Green "✅ 所有服务已启动并运行正常！"
    Write-ColorOutput Green "=========================================="
} else {
    Write-ColorOutput Yellow "⚠️  部分服务可能未正常运行，请检查日志"
}


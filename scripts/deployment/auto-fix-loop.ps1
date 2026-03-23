# PowerShell 脚本：自动监控、修复、部署循环
# 使用方法: .\scripts\deployment\auto-fix-loop.ps1

param(
    [string]$ServerIP = "43.143.139.197",
    [string]$ServerUser = "ubuntu",
    [string]$KeyPath = "E:\enterprise-ai-platform\enterprise_ai_platform.pem",
    [string]$RemotePath = "/opt/enterprise-ai-platform",
    [int]$MaxIterations = 20
)

$ErrorActionPreference = "Continue"
$sshCmd = "ssh -i `"$KeyPath`" -o StrictHostKeyChecking=no $ServerUser@${ServerIP}"
$ProjectRoot = "E:\enterprise-ai-platform"

function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function CheckServices {
    Write-ColorOutput Blue "=== 检查服务状态 ==="
    $psOutput = & $sshCmd "cd $RemotePath && sudo docker compose ps 2>&1"
    $psOutput | Write-Output
    
    $expectedServices = @("redis", "mcp-gateway", "workflow-engine", "auth-service", "knowledge-base", "web-ui")
    $running = @()
    $failed = @()
    
    foreach ($svc in $expectedServices) {
        $status = & $sshCmd "cd $RemotePath && sudo docker compose ps $svc 2>&1 | grep -E '(Up|running)' || echo 'down'"
        if ($status -match "Up|running") {
            $running += $svc
            Write-ColorOutput Green "✅ $svc"
        } else {
            $failed += $svc
            Write-ColorOutput Red "❌ $svc"
        }
    }
    
    return @{Running=$running; Failed=$failed}
}

function GetErrorLogs {
    Write-ColorOutput Yellow "=== 检查错误日志 ==="
    $logs = & $sshCmd "cd $RemotePath && sudo docker compose logs --tail=100 2>&1 | grep -iE '(error|failed|exception|traceback|fatal)' | head -30"
    return $logs
}

function PullAndDeploy {
    Write-ColorOutput Blue "=== 拉取代码并重新部署 ==="
    & $sshCmd "cd $RemotePath && git pull origin main 2>&1"
    & $sshCmd "cd $RemotePath && sudo docker compose down 2>&1"
    & $sshCmd "cd $RemotePath && sudo docker compose up -d --build 2>&1 | tail -20"
    Start-Sleep -Seconds 15
}

function HealthCheck {
    Write-ColorOutput Cyan "=== 健康检查 ==="
    $checks = @(
        @{Port=8001; Name="MCP Gateway"},
        @{Port=8002; Name="Workflow Engine"},
        @{Port=8003; Name="Auth Service"},
        @{Port=8004; Name="Knowledge Base"},
        @{Port=3000; Name="Web UI"}
    )
    
    $allHealthy = $true
    foreach ($check in $checks) {
        $health = & $sshCmd "curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://localhost:$($check.Port)/api/health 2>&1 || curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://localhost:$($check.Port)/health 2>&1 || echo '000'"
        if ($health -eq "200") {
            Write-ColorOutput Green "✅ $($check.Name) - 健康"
        } else {
            Write-ColorOutput Red "❌ $($check.Name) - 未响应 (HTTP $health)"
            $allHealthy = $false
        }
    }
    return $allHealthy
}

Write-ColorOutput Cyan "=========================================="
Write-ColorOutput Cyan "自动监控和修复循环"
Write-ColorOutput Cyan "=========================================="
Write-Output ""

$iteration = 0
$allHealthy = $false

while (-not $allHealthy -and $iteration -lt $MaxIterations) {
    $iteration++
    Write-ColorOutput Magenta "`n=== 迭代 $iteration/$MaxIterations ==="
    
    # 检查服务状态
    $status = CheckServices
    
    if ($status.Failed.Count -eq 0) {
        Write-ColorOutput Green "所有服务容器都在运行"
    } else {
        Write-ColorOutput Red "以下服务未运行: $($status.Failed -join ', ')"
    }
    
    # 检查错误日志
    $errors = GetErrorLogs
    if ($errors) {
        Write-ColorOutput Red "发现错误日志:"
        $errors | Write-Output
    }
    
    # 健康检查
    $allHealthy = HealthCheck
    
    if ($allHealthy) {
        Write-ColorOutput Green "`n✅ 所有服务健康检查通过！"
        break
    }
    
    # 如果有错误，拉取最新代码并重新部署
    if ($errors -or $status.Failed.Count -gt 0) {
        Write-ColorOutput Yellow "`n发现问题，重新部署..."
        PullAndDeploy
    } else {
        Write-ColorOutput Yellow "等待服务启动..."
        Start-Sleep -Seconds 10
    }
    
    Write-Output ""
}

# 最终报告
Write-Output ""
Write-ColorOutput Cyan "=========================================="
Write-ColorOutput Cyan "最终状态报告"
Write-ColorOutput Cyan "=========================================="

$finalStatus = CheckServices
$finalHealth = HealthCheck

Write-Output ""
if ($finalHealth) {
    Write-ColorOutput Green "✅ 所有服务已启动并运行正常！"
    Write-Output ""
    Write-Output "服务地址:"
    Write-Output "  - MCP Gateway:      http://$ServerIP:8001"
    Write-Output "  - Workflow Engine:   http://$ServerIP:8002"
    Write-Output "  - Auth Service:      http://$ServerIP:8003"
    Write-Output "  - Knowledge Base:    http://$ServerIP:8004"
    Write-Output "  - Web UI:            http://$ServerIP:3000"
} else {
    Write-ColorOutput Red "❌ 部分服务未正常运行"
    Write-Output ""
    Write-Output "请手动检查:"
    Write-Output "  ssh -i `"$KeyPath`" $ServerUser@${ServerIP}"
    Write-Output "  cd $RemotePath"
    Write-Output "  sudo docker compose logs -f"
}


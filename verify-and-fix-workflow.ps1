# 验证并修复工作流配置

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "验证工作流配置" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查本地工作流文件
Write-Host "检查本地工作流文件..." -ForegroundColor Yellow
$workflowFile = ".github/workflows/deploy.yml"

if (-not (Test-Path $workflowFile)) {
    Write-Host "❌ 工作流文件不存在: $workflowFile" -ForegroundColor Red
    exit 1
}

# 统计服务数量
$content = Get-Content $workflowFile -Raw
$serviceCount = ([regex]::Matches($content, 'service:\s+[\w-]+')).Count

Write-Host "本地工作流文件中的服务数量: $serviceCount" -ForegroundColor $(if ($serviceCount -ge 19) { "Green" } else { "Red" })

if ($serviceCount -lt 19) {
    Write-Host ""
    Write-Host "⚠️ 警告: 服务数量不足，应该是19个" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "检查服务列表..." -ForegroundColor Yellow
    
    # 提取所有服务名
    $services = [regex]::Matches($content, 'service:\s+([\w-]+)') | ForEach-Object { $_.Groups[1].Value }
    Write-Host "当前服务列表:" -ForegroundColor Cyan
    $services | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
    
    Write-Host ""
    Write-Host "需要添加的服务:" -ForegroundColor Yellow
    $requiredServices = @(
        "api-gateway", "auth-service", "knowledge-base", "metadata-service", 
        "workflow-engine", "web-ui", "registry-service", "config-center",
        "sap-mcp-server", "mcp-gateway", "chat-service", "dag-orchestrator",
        "agent-service", "agent-orchestrator", "agent-registry", 
        "joyagent-adapter", "memory-service", "sap-metadata-agent",
        "vector-coordinator-service"
    )
    
    $missingServices = $requiredServices | Where-Object { $services -notcontains $_ }
    if ($missingServices) {
        $missingServices | ForEach-Object { Write-Host "  ❌ $_" -ForegroundColor Red }
    } else {
        Write-Host "  ✅ 所有服务都已包含" -ForegroundColor Green
    }
} else {
    Write-Host "✅ 本地工作流文件包含所有19个服务" -ForegroundColor Green
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "检查Git状态" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查工作流文件是否已提交
$gitStatus = git status --short .github/workflows/deploy.yml 2>&1
if ($gitStatus) {
    Write-Host "⚠️ 工作流文件有未提交的更改:" -ForegroundColor Yellow
    Write-Host $gitStatus -ForegroundColor Gray
    Write-Host ""
    Write-Host "需要提交更改:" -ForegroundColor Yellow
    Write-Host "  git add .github/workflows/deploy.yml" -ForegroundColor White
    Write-Host "  git commit -m 'feat: 更新工作流以包含所有19个服务'" -ForegroundColor White
    Write-Host "  git push origin main" -ForegroundColor White
} else {
    Write-Host "✅ 工作流文件已提交" -ForegroundColor Green
    
    # 检查远程是否有更新
    Write-Host ""
    Write-Host "检查远程仓库..." -ForegroundColor Yellow
    $remoteStatus = git log origin/main..HEAD --oneline -- .github/workflows/deploy.yml 2>&1
    
    if ($remoteStatus) {
        Write-Host "⚠️ 本地有未推送的提交:" -ForegroundColor Yellow
        Write-Host $remoteStatus -ForegroundColor Gray
        Write-Host ""
        Write-Host "需要推送到远程:" -ForegroundColor Yellow
        Write-Host "  git push origin main" -ForegroundColor White
    } else {
        Write-Host "✅ 工作流文件已同步到远程" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "查看最新工作流运行" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$runs = gh run list --workflow="deploy.yml" --limit 1 --json databaseId,status,conclusion,displayTitle,createdAt,url,headSha 2>&1 | ConvertFrom-Json

if ($runs) {
    $run = $runs[0]
    Write-Host "最新运行ID: $($run.databaseId)" -ForegroundColor Green
    Write-Host "状态: $($run.status)" -ForegroundColor $(if ($run.status -eq "completed") { "Green" } elseif ($run.status -eq "in_progress") { "Yellow" } else { "Cyan" })
    Write-Host "提交SHA: $($run.headSha)" -ForegroundColor Gray
    
    # 检查当前HEAD
    $currentSha = git rev-parse HEAD
    if ($run.headSha -ne $currentSha) {
        Write-Host ""
        Write-Host "⚠️ 工作流运行的是旧提交" -ForegroundColor Yellow
        Write-Host "当前HEAD: $currentSha" -ForegroundColor Gray
        Write-Host "运行SHA: $($run.headSha)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "需要重新触发工作流以使用最新代码" -ForegroundColor Yellow
    } else {
        Write-Host "✅ 工作流使用的是最新提交" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "查看运行: $($run.url)" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "建议操作" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

if ($serviceCount -lt 19 -or $gitStatus -or $remoteStatus) {
    Write-Host "1. 确保工作流文件包含所有19个服务" -ForegroundColor Yellow
    Write-Host "2. 提交并推送更改:" -ForegroundColor Yellow
    Write-Host "   git add .github/workflows/deploy.yml" -ForegroundColor White
    Write-Host "   git commit -m 'feat: 更新工作流以包含所有19个服务'" -ForegroundColor White
    Write-Host "   git push origin main" -ForegroundColor White
    Write-Host ""
    Write-Host "3. 重新触发工作流:" -ForegroundColor Yellow
    Write-Host "   gh workflow run deploy.yml --field environment=staging" -ForegroundColor White
} else {
    Write-Host "✅ 配置正确，可以查看测试结果:" -ForegroundColor Green
    Write-Host "   gh run view <运行ID> --log" -ForegroundColor White
    Write-Host "   或访问: https://github.com/PMLiuyubin/enterprise-ai-platform/actions" -ForegroundColor White
}






# 检查工作流运行状态

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "检查工作流运行状态" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 获取最新运行
Write-Host "获取最新运行..." -ForegroundColor Yellow
$runs = gh run list --workflow="deploy.yml" --limit 5 --json databaseId,status,conclusion,displayTitle,createdAt,url,headSha 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 无法获取运行列表" -ForegroundColor Red
    Write-Host $runs -ForegroundColor Red
    Write-Host ""
    Write-Host "请检查:" -ForegroundColor Yellow
    Write-Host "1. GitHub CLI是否已登录: gh auth status" -ForegroundColor White
    Write-Host "2. 工作流是否存在: gh workflow list" -ForegroundColor White
    exit 1
}

$runsJson = $runs | ConvertFrom-Json

if (-not $runsJson -or $runsJson.Count -eq 0) {
    Write-Host "⚠️ 没有找到运行记录" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "触发新的工作流:" -ForegroundColor Yellow
    Write-Host "  gh workflow run deploy.yml --field environment=staging" -ForegroundColor White
    exit 0
}

Write-Host "找到 $($runsJson.Count) 个运行记录" -ForegroundColor Green
Write-Host ""

# 显示最新运行
$latestRun = $runsJson[0]
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "最新运行" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "运行ID: $($latestRun.databaseId)" -ForegroundColor Green
Write-Host "标题: $($latestRun.displayTitle)" -ForegroundColor Gray
Write-Host "状态: $($latestRun.status)" -ForegroundColor $(if ($latestRun.status -eq "completed") { "Green" } elseif ($latestRun.status -eq "in_progress") { "Yellow" } else { "Cyan" })

if ($latestRun.conclusion) {
    $conclusionColor = switch ($latestRun.conclusion) {
        "success" { "Green" }
        "failure" { "Red" }
        "cancelled" { "Yellow" }
        default { "White" }
    }
    Write-Host "结果: $($latestRun.conclusion)" -ForegroundColor $conclusionColor
}

Write-Host "创建时间: $($latestRun.createdAt)" -ForegroundColor Gray
Write-Host "提交SHA: $($latestRun.headSha.Substring(0, 7))" -ForegroundColor Gray
Write-Host ""
Write-Host "在浏览器中查看:" -ForegroundColor Cyan
Write-Host $latestRun.url -ForegroundColor Yellow
Write-Host ""

# 获取作业详情
Write-Host "获取作业详情..." -ForegroundColor Yellow
$jobs = gh run view $latestRun.databaseId --json jobs --jq '.jobs[] | {name: .name, status: .status, conclusion: .conclusion}' 2>&1 | ConvertFrom-Json

if ($jobs) {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "作业状态" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    
    foreach ($job in $jobs) {
        $statusIcon = switch ($job.status) {
            "completed" { if ($job.conclusion -eq "success") { "✅" } else { "❌" } }
            "in_progress" { "🔄" }
            "queued" { "⏳" }
            default { "⚪" }
        }
        
        $statusColor = switch ($job.status) {
            "completed" { if ($job.conclusion -eq "success") { "Green" } else { "Red" } }
            "in_progress" { "Yellow" }
            "queued" { "Cyan" }
            default { "White" }
        }
        
        Write-Host "$statusIcon $($job.name): $($job.status)" -ForegroundColor $statusColor
        if ($job.conclusion) {
            Write-Host "   结果: $($job.conclusion)" -ForegroundColor Gray
        }
    }
    
    # 检查build-images作业中的服务数量
    Write-Host ""
    Write-Host "检查build-images作业..." -ForegroundColor Yellow
    $buildLog = gh run view $latestRun.databaseId --log --job=build-images 2>&1
    
    if ($buildLog) {
        $serviceMatches = [regex]::Matches($buildLog, 'Build Docker image for ([\w-]+)')
        if ($serviceMatches.Count -gt 0) {
            Write-Host ""
            Write-Host "找到 $($serviceMatches.Count) 个服务的构建任务:" -ForegroundColor $(if ($serviceMatches.Count -ge 19) { "Green" } else { "Yellow" })
            $serviceMatches | ForEach-Object { 
                Write-Host "  - $($_.Groups[1].Value)" -ForegroundColor Gray 
            }
            
            if ($serviceMatches.Count -lt 19) {
                Write-Host ""
                Write-Host "⚠️ 警告: 只有 $($serviceMatches.Count) 个服务，应该是19个" -ForegroundColor Yellow
                Write-Host "可能原因:" -ForegroundColor Yellow
                Write-Host "  1. 工作流文件未正确提交" -ForegroundColor Gray
                Write-Host "  2. 工作流从旧提交触发" -ForegroundColor Gray
                Write-Host ""
                Write-Host "解决方案:" -ForegroundColor Yellow
                Write-Host "  1. 检查工作流文件: git status .github/workflows/deploy.yml" -ForegroundColor White
                Write-Host "  2. 提交并推送: git add .github/workflows/deploy.yml && git commit -m 'fix' && git push" -ForegroundColor White
                Write-Host "  3. 重新触发: gh workflow run deploy.yml --field environment=staging" -ForegroundColor White
            }
        }
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "常用命令" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "查看运行详情:" -ForegroundColor Gray
Write-Host "  gh run view $($latestRun.databaseId)" -ForegroundColor White
Write-Host ""
Write-Host "实时查看日志:" -ForegroundColor Gray
Write-Host "  gh run watch $($latestRun.databaseId)" -ForegroundColor White
Write-Host ""
Write-Host "查看特定作业日志:" -ForegroundColor Gray
Write-Host "  gh run view $($latestRun.databaseId) --log --job=<作业名>" -ForegroundColor White
Write-Host ""
Write-Host "查看失败作业:" -ForegroundColor Gray
Write-Host "  gh run view $($latestRun.databaseId) --json jobs --jq '.jobs[] | select(.conclusion == \"failure\") | .name'" -ForegroundColor White
Write-Host ""






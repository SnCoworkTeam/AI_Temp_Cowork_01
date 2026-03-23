# 诊断工作流失败

param(
    [string]$RunId = ""
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "诊断工作流失败" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 如果没有提供运行ID，获取最新的
if (-not $RunId) {
    Write-Host "获取最新运行..." -ForegroundColor Yellow
    $runs = gh run list --workflow="deploy.yml" --limit 1 --json databaseId,status,conclusion 2>&1 | ConvertFrom-Json
    
    if (-not $runs -or $runs.Count -eq 0) {
        Write-Host "❌ 没有找到运行记录" -ForegroundColor Red
        exit 1
    }
    
    $RunId = $runs[0].databaseId
    Write-Host "使用最新运行ID: $RunId" -ForegroundColor Green
    Write-Host "状态: $($runs[0].status)" -ForegroundColor $(if ($runs[0].status -eq "completed") { "Green" } else { "Yellow" })
    if ($runs[0].conclusion) {
        Write-Host "结果: $($runs[0].conclusion)" -ForegroundColor $(if ($runs[0].conclusion -eq "success") { "Green" } else { "Red" })
    }
} else {
    Write-Host "使用指定的运行ID: $RunId" -ForegroundColor Green
}

Write-Host ""

# 获取所有作业
Write-Host "获取作业信息..." -ForegroundColor Yellow
$jobs = gh run view $RunId --json jobs --jq '.jobs[] | {name: .name, status: .status, conclusion: .conclusion}' 2>&1 | ConvertFrom-Json

if (-not $jobs) {
    Write-Host "❌ 无法获取作业信息" -ForegroundColor Red
    exit 1
}

# 筛选失败的作业
$failedJobs = $jobs | Where-Object { $_.conclusion -eq "failure" }

if ($failedJobs) {
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "失败的作业 ($($failedJobs.Count))" -ForegroundColor Red
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($job in $failedJobs) {
        Write-Host "作业: $($job.name)" -ForegroundColor Yellow
        Write-Host "状态: $($job.status)" -ForegroundColor Red
        Write-Host "结果: $($job.conclusion)" -ForegroundColor Red
        Write-Host ""
        
        Write-Host "获取错误信息..." -ForegroundColor Gray
        $log = gh run view $RunId --log --job=$($job.name) 2>&1
        
        if ($log) {
            # 提取错误行
            $errors = $log | Select-String -Pattern "error|Error|ERROR|failed|Failed|FAILED|Exception|AssertionError" -Context 2
            
            if ($errors) {
                Write-Host "错误摘要 (前10条):" -ForegroundColor Yellow
                $errors | Select-Object -First 10 | ForEach-Object { 
                    Write-Host "  $($_.Line.Trim())" -ForegroundColor Red 
                    if ($_.Context.PreContext) {
                        $_.Context.PreContext | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
                    }
                    if ($_.Context.PostContext) {
                        $_.Context.PostContext | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
                    }
                }
            } else {
                Write-Host "  未找到明显的错误模式" -ForegroundColor Gray
            }
        }
        
        Write-Host ""
        Write-Host "查看完整日志:" -ForegroundColor Cyan
        Write-Host "  gh run view $RunId --log --job=$($job.name)" -ForegroundColor White
        Write-Host ""
        Write-Host "在浏览器中查看:" -ForegroundColor Cyan
        Write-Host "  https://github.com/PMLiuyubin/enterprise-ai-platform/actions/runs/$RunId" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "----------------------------------------" -ForegroundColor Gray
        Write-Host ""
    }
    
    # 提供修复建议
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "修复建议" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    
    if ($failedJobs | Where-Object { $_.name -eq "test" }) {
        Write-Host "测试失败:" -ForegroundColor Yellow
        Write-Host "  1. 本地运行失败的测试: pytest tests/<测试文件> -v" -ForegroundColor White
        Write-Host "  2. 查看详细错误: pytest tests/<测试文件> -v --tb=short" -ForegroundColor White
        Write-Host "  3. 修复代码或测试后重新提交" -ForegroundColor White
        Write-Host ""
    }
    
    if ($failedJobs | Where-Object { $_.name -eq "frontend-test" }) {
        Write-Host "前端测试失败:" -ForegroundColor Yellow
        Write-Host "  1. 进入前端目录: cd web-ui" -ForegroundColor White
        Write-Host "  2. 运行Lint: npm run lint" -ForegroundColor White
        Write-Host "  3. 运行类型检查: npx tsc --noEmit" -ForegroundColor White
        Write-Host "  4. 尝试构建: npm run build" -ForegroundColor White
        Write-Host "  5. 修复问题后重新提交" -ForegroundColor White
        Write-Host ""
    }
    
    if ($failedJobs | Where-Object { $_.name -eq "build-images" }) {
        Write-Host "构建失败:" -ForegroundColor Yellow
        Write-Host "  1. 查看具体哪个服务构建失败" -ForegroundColor White
        Write-Host "  2. 本地测试构建: docker build -f <服务>/Dockerfile.dev -t test-<服务> ./<服务>" -ForegroundColor White
        Write-Host "  3. 检查Dockerfile路径和依赖" -ForegroundColor White
        Write-Host "  4. 修复后重新提交" -ForegroundColor White
        Write-Host ""
    }
    
    if ($failedJobs | Where-Object { $_.name -eq "deploy" }) {
        Write-Host "部署失败:" -ForegroundColor Yellow
        Write-Host "  1. 检查SSH连接: ssh ubuntu@43.143.139.197" -ForegroundColor White
        Write-Host "  2. 检查服务器资源: df -h && free -h" -ForegroundColor White
        Write-Host "  3. 检查服务状态: docker-compose ps" -ForegroundColor White
        Write-Host "  4. 查看服务器日志: docker-compose logs" -ForegroundColor White
        Write-Host ""
    }
    
} else {
    Write-Host "✅ 没有失败的作业" -ForegroundColor Green
    Write-Host ""
    Write-Host "所有作业状态:" -ForegroundColor Cyan
    foreach ($job in $jobs) {
        $statusColor = switch ($job.status) {
            "completed" { if ($job.conclusion -eq "success") { "Green" } else { "Red" } }
            "in_progress" { "Yellow" }
            default { "White" }
        }
        $icon = switch ($job.status) {
            "completed" { if ($job.conclusion -eq "success") { "✅" } else { "❌" } }
            "in_progress" { "🔄" }
            default { "⚪" }
        }
        Write-Host "$icon $($job.name): $($job.status)" -ForegroundColor $statusColor
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "常用命令" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "实时查看日志:" -ForegroundColor Gray
Write-Host "  gh run watch $RunId" -ForegroundColor White
Write-Host ""
Write-Host "查看运行详情:" -ForegroundColor Gray
Write-Host "  gh run view $RunId" -ForegroundColor White
Write-Host ""
Write-Host "在浏览器中查看:" -ForegroundColor Gray
Write-Host "  https://github.com/PMLiuyubin/enterprise-ai-platform/actions/runs/$RunId" -ForegroundColor Yellow
Write-Host ""






# 触发完整CI/CD测试和部署

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "触发完整CI/CD测试和部署" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查GitHub CLI是否已登录
Write-Host "检查GitHub CLI状态..." -ForegroundColor Yellow
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ GitHub CLI未登录，请先运行: gh auth login" -ForegroundColor Red
    exit 1
}
Write-Host "✅ GitHub CLI已登录" -ForegroundColor Green
Write-Host ""

# 触发部署工作流
Write-Host "触发完整测试和部署工作流..." -ForegroundColor Yellow
Write-Host "环境: staging" -ForegroundColor Gray
Write-Host ""

$result = gh workflow run deploy.yml --field environment=staging 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 工作流已触发！" -ForegroundColor Green
    Write-Host ""
    
    # 等待几秒后获取运行ID
    Start-Sleep -Seconds 3
    
    Write-Host "获取最新运行信息..." -ForegroundColor Yellow
    $runs = gh run list --workflow="deploy.yml" --limit 1 --json databaseId,status,displayTitle,createdAt,url 2>&1 | ConvertFrom-Json
    
    if ($runs) {
        $run = $runs[0]
        Write-Host ""
        Write-Host "==========================================" -ForegroundColor Cyan
        Write-Host "工作流运行信息" -ForegroundColor Cyan
        Write-Host "==========================================" -ForegroundColor Cyan
        Write-Host "运行ID: $($run.databaseId)" -ForegroundColor Green
        Write-Host "状态: $($run.status)" -ForegroundColor $(if ($run.status -eq "completed") { "Green" } elseif ($run.status -eq "in_progress") { "Yellow" } else { "Cyan" })
        Write-Host "标题: $($run.displayTitle)" -ForegroundColor Gray
        Write-Host "创建时间: $($run.createdAt)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "在浏览器中查看:" -ForegroundColor Cyan
        Write-Host $run.url -ForegroundColor Yellow
        Write-Host ""
        Write-Host "==========================================" -ForegroundColor Cyan
        Write-Host "监控命令" -ForegroundColor Cyan
        Write-Host "==========================================" -ForegroundColor Cyan
        Write-Host "查看运行状态:" -ForegroundColor Gray
        Write-Host "  gh run view $($run.databaseId)" -ForegroundColor White
        Write-Host ""
        Write-Host "实时查看日志:" -ForegroundColor Gray
        Write-Host "  gh run watch $($run.databaseId)" -ForegroundColor White
        Write-Host ""
        Write-Host "查看最新运行:" -ForegroundColor Gray
        Write-Host "  gh run list --workflow=deploy.yml --limit 1" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host "⚠️ 无法获取运行信息，请稍后手动查看" -ForegroundColor Yellow
        Write-Host "查看最新运行: gh run list --workflow=deploy.yml --limit 1" -ForegroundColor Gray
    }
} else {
    Write-Host "❌ 触发工作流失败" -ForegroundColor Red
    Write-Host $result -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "工作流执行阶段" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "1. test - 后端测试 (10-15分钟)" -ForegroundColor Gray
Write-Host "   - 单元测试" -ForegroundColor DarkGray
Write-Host "   - 集成测试" -ForegroundColor DarkGray
Write-Host "   - 前端API集成测试" -ForegroundColor DarkGray
Write-Host "   - E2E测试" -ForegroundColor DarkGray
Write-Host ""
Write-Host "2. frontend-test - 前端测试 (5-10分钟)" -ForegroundColor Gray
Write-Host "   - Lint检查" -ForegroundColor DarkGray
Write-Host "   - 类型检查" -ForegroundColor DarkGray
Write-Host "   - 构建测试" -ForegroundColor DarkGray
Write-Host ""
Write-Host "3. build-images - 构建镜像 (10-15分钟)" -ForegroundColor Gray
Write-Host "   - 所有服务镜像" -ForegroundColor DarkGray
Write-Host ""
Write-Host "4. deploy - 部署到服务器 (5-10分钟)" -ForegroundColor Gray
Write-Host "   - 蓝绿部署" -ForegroundColor DarkGray
Write-Host "   - 健康检查" -ForegroundColor DarkGray
Write-Host ""
Write-Host "预计总时间: 30-50分钟" -ForegroundColor Yellow
Write-Host ""






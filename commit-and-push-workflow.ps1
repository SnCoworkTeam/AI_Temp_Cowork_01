# 提交并推送工作流文件

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "提交并推送工作流文件" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查工作流文件状态
Write-Host "检查工作流文件状态..." -ForegroundColor Yellow
$workflowFile = ".github/workflows/deploy.yml"

if (-not (Test-Path $workflowFile)) {
    Write-Host "❌ 工作流文件不存在: $workflowFile" -ForegroundColor Red
    exit 1
}

# 检查git状态
Write-Host "检查git状态..." -ForegroundColor Yellow
$gitStatus = git status --short $workflowFile 2>&1

if ($gitStatus) {
    Write-Host "发现未提交的更改:" -ForegroundColor Yellow
    Write-Host $gitStatus -ForegroundColor Gray
    Write-Host ""
    
    # 显示更改内容摘要
    Write-Host "检查更改内容..." -ForegroundColor Yellow
    $diff = git diff $workflowFile 2>&1
    if ($diff) {
        $serviceCount = ([regex]::Matches($diff, 'service:\s+[\w-]+')).Count
        Write-Host "检测到 $serviceCount 个服务配置" -ForegroundColor $(if ($serviceCount -ge 19) { "Green" } else { "Yellow" })
    }
    
    Write-Host ""
    Write-Host "准备提交更改..." -ForegroundColor Yellow
    
    # 添加文件
    Write-Host "添加文件到暂存区..." -ForegroundColor Yellow
    git add $workflowFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 文件已添加到暂存区" -ForegroundColor Green
        
        # 提交
        Write-Host "提交更改..." -ForegroundColor Yellow
        $commitMessage = "feat: 更新工作流以包含所有19个服务"
        git commit -m $commitMessage
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 更改已提交" -ForegroundColor Green
            Write-Host "提交信息: $commitMessage" -ForegroundColor Gray
            Write-Host ""
            
            # 推送
            Write-Host "推送到远程仓库..." -ForegroundColor Yellow
            git push origin main
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ 更改已推送到远程仓库" -ForegroundColor Green
                Write-Host ""
                Write-Host "==========================================" -ForegroundColor Cyan
                Write-Host "下一步" -ForegroundColor Cyan
                Write-Host "==========================================" -ForegroundColor Cyan
                Write-Host "等待几秒后重新触发工作流..." -ForegroundColor Yellow
                Start-Sleep -Seconds 3
                
                Write-Host "触发新的工作流..." -ForegroundColor Yellow
                gh workflow run deploy.yml --field environment=staging
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "✅ 工作流已触发" -ForegroundColor Green
                    Write-Host ""
                    Write-Host "查看运行状态:" -ForegroundColor Cyan
                    Write-Host "  gh run list --workflow=deploy.yml --limit 1" -ForegroundColor White
                    Write-Host ""
                    Write-Host "实时查看日志:" -ForegroundColor Cyan
                    Write-Host "  gh run watch" -ForegroundColor White
                } else {
                    Write-Host "⚠️ 触发工作流失败，请手动执行:" -ForegroundColor Yellow
                    Write-Host "  gh workflow run deploy.yml --field environment=staging" -ForegroundColor White
                }
            } else {
                Write-Host "❌ 推送失败" -ForegroundColor Red
                Write-Host "请检查:" -ForegroundColor Yellow
                Write-Host "  1. 是否有推送权限" -ForegroundColor White
                Write-Host "  2. 远程仓库是否正确" -ForegroundColor White
                Write-Host "  3. 网络连接是否正常" -ForegroundColor White
            }
        } else {
            Write-Host "❌ 提交失败" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ 添加文件失败" -ForegroundColor Red
    }
} else {
    Write-Host "检查是否有未推送的提交..." -ForegroundColor Yellow
    $unpushed = git log origin/main..HEAD --oneline -- $workflowFile 2>&1
    
    if ($unpushed) {
        Write-Host "发现未推送的提交:" -ForegroundColor Yellow
        Write-Host $unpushed -ForegroundColor Gray
        Write-Host ""
        Write-Host "推送到远程仓库..." -ForegroundColor Yellow
        git push origin main
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 提交已推送" -ForegroundColor Green
            Write-Host ""
            Write-Host "重新触发工作流..." -ForegroundColor Yellow
            Start-Sleep -Seconds 3
            gh workflow run deploy.yml --field environment=staging
        }
    } else {
        Write-Host "✅ 工作流文件已是最新状态" -ForegroundColor Green
        Write-Host ""
        Write-Host "检查远程文件..." -ForegroundColor Yellow
        
        # 检查远程是否有更新
        git fetch origin main 2>&1 | Out-Null
        $localSha = git rev-parse HEAD
        $remoteSha = git rev-parse origin/main
        
        if ($localSha -ne $remoteSha) {
            Write-Host "⚠️ 本地和远程不同步" -ForegroundColor Yellow
            Write-Host "本地: $localSha" -ForegroundColor Gray
            Write-Host "远程: $remoteSha" -ForegroundColor Gray
            Write-Host ""
            Write-Host "建议拉取最新代码:" -ForegroundColor Yellow
            Write-Host "  git pull origin main" -ForegroundColor White
        } else {
            Write-Host "✅ 本地和远程已同步" -ForegroundColor Green
            Write-Host ""
            Write-Host "如果工作流还是只有5个服务，可能需要:" -ForegroundColor Yellow
            Write-Host "  1. 检查GitHub上的实际文件内容" -ForegroundColor White
            Write-Host "  2. 重新触发工作流" -ForegroundColor White
            Write-Host "  3. 确认工作流使用的是最新提交" -ForegroundColor White
        }
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "验证" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "在浏览器中查看工作流文件:" -ForegroundColor Cyan
Write-Host "https://github.com/PMLiuyubin/enterprise-ai-platform/blob/main/.github/workflows/deploy.yml" -ForegroundColor Yellow
Write-Host ""
Write-Host "应该看到19个服务在matrix.include中" -ForegroundColor Gray






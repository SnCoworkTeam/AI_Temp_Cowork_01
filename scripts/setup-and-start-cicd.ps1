#!/usr/bin/env pwsh
# 完整的CI/CD设置和启动脚本

$ErrorActionPreference = "Continue"

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "🚀 CI/CD 完整设置和启动" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查GitHub CLI
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "❌ GitHub CLI未安装" -ForegroundColor Red
    Write-Host "请先安装: winget install GitHub.cli" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ GitHub CLI已安装" -ForegroundColor Green
gh --version
Write-Host ""

# 检查登录状态
Write-Host "检查GitHub登录状态..." -ForegroundColor Yellow
gh auth status 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  未登录，开始登录流程..." -ForegroundColor Yellow
    Write-Host "`n请按照提示完成登录:" -ForegroundColor Cyan
    Write-Host "  1. 选择 GitHub.com" -ForegroundColor White
    Write-Host "  2. 选择 HTTPS" -ForegroundColor White
    Write-Host "  3. 选择浏览器登录或使用token" -ForegroundColor White
    Write-Host ""
    gh auth login
} else {
    Write-Host "✅ 已登录GitHub" -ForegroundColor Green
    gh auth status
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "配置GitHub Secrets" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查密钥文件
if (-not (Test-Path "enterprise_ai_platform.pem")) {
    Write-Host "❌ 未找到密钥文件: enterprise_ai_platform.pem" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 找到密钥文件" -ForegroundColor Green
Write-Host ""

# 配置Secrets
$secrets = @{
    "SSH_PRIVATE_KEY" = (Get-Content "enterprise_ai_platform.pem" -Raw)
    "SERVER_HOST" = "43.143.139.197"
    "SERVER_USER" = "ubuntu"
    "SERVER_URL" = "http://43.143.139.197:8080"
}

$successCount = 0
$failCount = 0

foreach ($secretName in $secrets.Keys) {
    Write-Host "配置 $secretName..." -ForegroundColor Yellow
    
    if ($secretName -eq "SSH_PRIVATE_KEY") {
        $secrets[$secretName] | gh secret set $secretName 2>&1 | Out-Null
    } else {
        gh secret set $secretName --body $secrets[$secretName] 2>&1 | Out-Null
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ $secretName 配置成功" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host "  ⚠️  $secretName 配置失败" -ForegroundColor Yellow
        $failCount++
    }
}

Write-Host ""
Write-Host "配置结果: 成功 $successCount, 失败 $failCount" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Yellow" })

# 验证配置
Write-Host ""
Write-Host "验证配置..." -ForegroundColor Cyan
$secretList = gh secret list 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "已配置的Secrets:" -ForegroundColor Green
    $secretList | ForEach-Object {
        if ($_ -match "SSH_PRIVATE_KEY|SERVER_") {
            Write-Host "  ✅ $_" -ForegroundColor Green
        }
    }
} else {
    Write-Host "⚠️  无法列出Secrets" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "启动CI/CD工作流" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 列出可用工作流
Write-Host "可用工作流:" -ForegroundColor Cyan
gh workflow list 2>&1
Write-Host ""

# 触发部署工作流
Write-Host "触发部署工作流 (staging环境)..." -ForegroundColor Yellow
gh workflow run "Deploy to Server.yml" --field environment=staging 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ 工作流已成功触发！" -ForegroundColor Green
    Write-Host ""
    Write-Host "等待3秒后查看运行状态..." -ForegroundColor Cyan
    Start-Sleep -Seconds 3
    
    Write-Host ""
    Write-Host "最近的运行:" -ForegroundColor Cyan
    gh run list --workflow="Deploy to Server.yml" --limit 5 2>&1
    
    Write-Host ""
    Write-Host "💡 提示:" -ForegroundColor Yellow
    Write-Host "  - 实时查看: gh run watch" -ForegroundColor White
    Write-Host "  - 查看日志: gh run view <run-id> --log" -ForegroundColor White
    Write-Host "  - GitHub Actions: https://github.com/YOUR_REPO/actions" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "⚠️  触发失败" -ForegroundColor Yellow
    Write-Host "请检查:" -ForegroundColor Yellow
    Write-Host "  1. 工作流文件是否存在" -ForegroundColor White
    Write-Host "  2. 是否有权限触发工作流" -ForegroundColor White
    Write-Host "  3. 手动在GitHub Web界面触发" -ForegroundColor White
}

Write-Host ""
Write-Host "✅ 完成！" -ForegroundColor Green


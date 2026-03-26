#!/usr/bin/env pwsh
# GitHub Secrets 自动配置脚本

param(
    [string]$Repo = "",
    [string]$KeyFile = "enterprise_ai_platform.pem"
)

$ErrorActionPreference = "Stop"

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "🔐 GitHub Secrets 配置工具" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查GitHub CLI
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "❌ GitHub CLI未安装" -ForegroundColor Red
    Write-Host "`n请先安装GitHub CLI:" -ForegroundColor Yellow
    Write-Host "  Windows: winget install GitHub.cli" -ForegroundColor White
    Write-Host "  或访问: https://cli.github.com/" -ForegroundColor White
    exit 1
}

# 检查是否已登录
Write-Host "检查GitHub CLI登录状态..." -ForegroundColor Yellow
gh auth status 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n⚠️  未登录GitHub CLI" -ForegroundColor Yellow
    Write-Host "请运行: gh auth login" -ForegroundColor White
    exit 1
}

# 获取仓库信息
if ([string]::IsNullOrEmpty($Repo)) {
    Write-Host "`n获取当前仓库信息..." -ForegroundColor Yellow
    $repoInfo = gh repo view --json nameWithOwner 2>&1
    if ($LASTEXITCODE -eq 0) {
        $Repo = ($repoInfo | ConvertFrom-Json).nameWithOwner
        Write-Host "✅ 检测到仓库: $Repo" -ForegroundColor Green
    } else {
        Write-Host "`n请输入仓库名称 (格式: owner/repo):" -ForegroundColor Yellow
        $Repo = Read-Host
        if ([string]::IsNullOrEmpty($Repo)) {
            Write-Host "❌ 仓库名称不能为空" -ForegroundColor Red
            exit 1
        }
    }
}

# 检查密钥文件
if (-not (Test-Path $KeyFile)) {
    Write-Host "`n❌ 未找到密钥文件: $KeyFile" -ForegroundColor Red
    Write-Host "请确保密钥文件在当前目录" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n✅ 找到密钥文件: $KeyFile" -ForegroundColor Green
$keyContent = Get-Content $KeyFile -Raw

# 验证密钥格式
if ($keyContent -notmatch "BEGIN.*PRIVATE KEY") {
    Write-Host "`n⚠️  警告: 密钥文件格式可能不正确" -ForegroundColor Yellow
    $confirm = Read-Host "是否继续? (y/n)"
    if ($confirm -ne "y") {
        exit 0
    }
}

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "配置GitHub Secrets" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "仓库: $Repo" -ForegroundColor Yellow
Write-Host ""

# 配置Secrets
$secrets = @{
    "SSH_PRIVATE_KEY" = $keyContent
    "SERVER_HOST" = "43.143.139.197"
    "SERVER_USER" = "ubuntu"
    "SERVER_URL" = "http://43.143.139.197:8080"
}

$successCount = 0
$failCount = 0

foreach ($secretName in $secrets.Keys) {
    Write-Host "设置 $secretName..." -ForegroundColor Yellow
    
    if ($secretName -eq "SSH_PRIVATE_KEY") {
        # SSH密钥需要从文件读取
        $secrets[$secretName] | gh secret set $secretName --repo $Repo 2>&1 | Out-Null
    } else {
        gh secret set $secretName --body $secrets[$secretName] --repo $Repo 2>&1 | Out-Null
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ $secretName 配置成功" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host "  ❌ $secretName 配置失败" -ForegroundColor Red
        $failCount++
    }
}

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "配置完成" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "成功: $successCount" -ForegroundColor Green
Write-Host "失败: $failCount" -ForegroundColor $(if ($failCount -gt 0) { "Red" } else { "Green" })
Write-Host ""

# 验证配置
Write-Host "验证配置..." -ForegroundColor Yellow
$secretList = gh secret list --repo $Repo 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "`n已配置的Secrets:" -ForegroundColor Cyan
    $secretList | ForEach-Object {
        if ($_ -match "SSH_PRIVATE_KEY|SERVER_") {
            Write-Host "  ✅ $_" -ForegroundColor Green
        }
    }
} else {
    Write-Host "⚠️  无法验证配置，请手动检查" -ForegroundColor Yellow
}

Write-Host "`n✅ 配置完成！" -ForegroundColor Green
Write-Host "`n📝 下一步:" -ForegroundColor Yellow
Write-Host "  1. 进入GitHub仓库验证Secrets" -ForegroundColor White
Write-Host "  2. 测试工作流运行" -ForegroundColor White
Write-Host "  3. 查看 Actions 标签页确认工作流正常" -ForegroundColor White


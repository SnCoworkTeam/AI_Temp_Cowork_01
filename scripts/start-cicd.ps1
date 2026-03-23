#!/usr/bin/env pwsh
# CI/CD 启动脚本

param(
    [string]$Workflow = "Deploy to Server.yml",
    [string]$Environment = "staging",
    [switch]$VerifySecrets = $true
)

$ErrorActionPreference = "Stop"

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "🚀 启动CI/CD工作流" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查GitHub CLI
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "❌ GitHub CLI未安装" -ForegroundColor Red
    Write-Host "请安装: winget install GitHub.cli" -ForegroundColor Yellow
    exit 1
}

# 检查登录状态
Write-Host "检查GitHub CLI登录状态..." -ForegroundColor Yellow
gh auth status 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 未登录GitHub CLI" -ForegroundColor Red
    Write-Host "请运行: gh auth login" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ 已登录" -ForegroundColor Green

# 验证Secrets
if ($VerifySecrets) {
    Write-Host "`n验证GitHub Secrets..." -ForegroundColor Yellow
    $requiredSecrets = @("SSH_PRIVATE_KEY", "SERVER_HOST", "SERVER_USER", "SERVER_URL")
    $secrets = gh secret list 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $missingSecrets = @()
        foreach ($secret in $requiredSecrets) {
            if ($secrets -match $secret) {
                Write-Host "  ✅ $secret" -ForegroundColor Green
            } else {
                Write-Host "  ❌ $secret (缺失)" -ForegroundColor Red
                $missingSecrets += $secret
            }
        }
        
        if ($missingSecrets.Count -gt 0) {
            Write-Host "`n⚠️  缺少以下Secrets:" -ForegroundColor Yellow
            $missingSecrets | ForEach-Object { Write-Host "  - $_" -ForegroundColor White }
            Write-Host "`n请先运行: pwsh scripts/setup-github-secrets.ps1" -ForegroundColor Yellow
            exit 1
        }
    } else {
        Write-Host "⚠️  无法验证Secrets，继续执行..." -ForegroundColor Yellow
    }
}

# 列出可用工作流
Write-Host "`n可用工作流:" -ForegroundColor Cyan
$workflows = gh workflow list 2>&1
if ($LASTEXITCODE -eq 0) {
    $workflows | ForEach-Object { Write-Host "  - $_" -ForegroundColor White }
} else {
    Write-Host "  ⚠️  无法列出工作流" -ForegroundColor Yellow
}

# 触发工作流
Write-Host "`n触发工作流: $Workflow" -ForegroundColor Yellow
Write-Host "环境: $Environment" -ForegroundColor Yellow
Write-Host ""

$workflowFile = $Workflow
if (-not $Workflow.EndsWith(".yml")) {
    $workflowFile = "$Workflow.yml"
}

# 根据工作流类型触发
switch ($Workflow) {
    "Deploy to Server.yml" {
        Write-Host "触发部署工作流..." -ForegroundColor Yellow
        gh workflow run $workflowFile --field environment=$Environment 2>&1 | Out-Null
    }
    "PR Checks" {
        Write-Host "PR检查工作流需要Pull Request触发" -ForegroundColor Yellow
        Write-Host "请创建Pull Request来自动触发" -ForegroundColor White
        exit 0
    }
    "Test Suite" {
        Write-Host "触发测试套件..." -ForegroundColor Yellow
        gh workflow run $workflowFile 2>&1 | Out-Null
    }
    default {
        Write-Host "触发工作流: $workflowFile" -ForegroundColor Yellow
        gh workflow run $workflowFile 2>&1 | Out-Null
    }
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 工作流已触发" -ForegroundColor Green
    
    Write-Host "`n查看运行状态:" -ForegroundColor Cyan
    Write-Host "  gh run list --workflow='$workflowFile' --limit 5" -ForegroundColor White
    Write-Host "`n实时查看日志:" -ForegroundColor Cyan
    Write-Host "  gh run watch" -ForegroundColor White
    
    # 等待一下然后显示运行列表
    Start-Sleep -Seconds 2
    Write-Host "`n最近的运行:" -ForegroundColor Cyan
    gh run list --workflow=$workflowFile --limit 3
} else {
    Write-Host "❌ 触发失败" -ForegroundColor Red
    Write-Host "`n请检查:" -ForegroundColor Yellow
    Write-Host "  1. 工作流文件是否存在" -ForegroundColor White
    Write-Host "  2. 是否有权限触发工作流" -ForegroundColor White
    Write-Host "  3. 手动在GitHub Web界面触发" -ForegroundColor White
    exit 1
}

Write-Host "`n✅ CI/CD已启动！" -ForegroundColor Green
Write-Host "`n💡 提示:" -ForegroundColor Yellow
Write-Host "  - 在GitHub Actions页面查看详细日志" -ForegroundColor White
Write-Host "  - 使用 'gh run watch' 实时查看运行状态" -ForegroundColor White


# GitHub Secrets 快速配置脚本（PowerShell）
# 使用方法: .\configure-github-secrets.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GitHub Secrets 配置脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 GitHub CLI 是否安装
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "❌ GitHub CLI 未安装" -ForegroundColor Red
    Write-Host "请先安装 GitHub CLI:" -ForegroundColor Yellow
    Write-Host "  Windows: winget install GitHub.cli" -ForegroundColor Yellow
    Write-Host "  或访问: https://cli.github.com/" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ GitHub CLI 已安装" -ForegroundColor Green
Write-Host ""

# 检查是否已登录
Write-Host "检查 GitHub 登录状态..." -ForegroundColor Cyan
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  未登录 GitHub，正在引导登录..." -ForegroundColor Yellow
    gh auth login
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 登录失败" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ 已登录 GitHub" -ForegroundColor Green
}
Write-Host ""

# 查找密钥文件
$keyFile = "enterprise_ai_platform.pem"
if (-not (Test-Path $keyFile)) {
    $keyFile = "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem"
    if (-not (Test-Path $keyFile)) {
        Write-Host "❌ 未找到密钥文件" -ForegroundColor Red
        Write-Host "请确保密钥文件在以下位置之一:" -ForegroundColor Yellow
        Write-Host "  - .\enterprise_ai_platform.pem" -ForegroundColor Yellow
        Write-Host "  - $env:USERPROFILE\.ssh\enterprise_ai_platform.pem" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "✅ 找到密钥文件: $keyFile" -ForegroundColor Green
Write-Host ""

# 配置 Secrets
Write-Host "开始配置 GitHub Secrets..." -ForegroundColor Cyan
Write-Host ""

# 1. 配置 SSH_PRIVATE_KEY
Write-Host "[1/3] 配置 SSH_PRIVATE_KEY..." -ForegroundColor Yellow
try {
    # PowerShell 正确语法：使用 Get-Content 和管道
    Get-Content $keyFile -Raw | gh secret set SSH_PRIVATE_KEY 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ SSH_PRIVATE_KEY 配置成功" -ForegroundColor Green
    } else {
        Write-Host "  ❌ SSH_PRIVATE_KEY 配置失败" -ForegroundColor Red
    }
} catch {
    Write-Host "  ❌ 错误: $_" -ForegroundColor Red
}

# 2. 配置 SERVER_HOST
Write-Host "[2/3] 配置 SERVER_HOST..." -ForegroundColor Yellow
try {
    gh secret set SERVER_HOST --body "43.143.139.197" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ SERVER_HOST 配置成功" -ForegroundColor Green
    } else {
        Write-Host "  ❌ SERVER_HOST 配置失败" -ForegroundColor Red
    }
} catch {
    Write-Host "  ❌ 错误: $_" -ForegroundColor Red
}

# 3. 配置 SERVER_USER
Write-Host "[3/3] 配置 SERVER_USER..." -ForegroundColor Yellow
try {
    gh secret set SERVER_USER --body "ubuntu" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ SERVER_USER 配置成功" -ForegroundColor Green
    } else {
        Write-Host "  ❌ SERVER_USER 配置失败" -ForegroundColor Red
    }
} catch {
    Write-Host "  ❌ 错误: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "配置完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 验证配置
Write-Host "验证配置..." -ForegroundColor Cyan
$secrets = gh secret list 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "当前配置的 Secrets:" -ForegroundColor Green
    $secrets | Select-String -Pattern "SSH_PRIVATE_KEY|SERVER_HOST|SERVER_USER" | ForEach-Object {
        Write-Host "  ✅ $_" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️  无法验证配置，请手动检查" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "下一步:" -ForegroundColor Cyan
Write-Host "  1. 在 GitHub Actions 页面测试部署" -ForegroundColor Yellow
Write-Host "  2. 推送代码到 main 分支触发自动部署" -ForegroundColor Yellow
Write-Host ""


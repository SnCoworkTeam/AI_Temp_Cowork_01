# 本地运行自动修复系统（Windows）

param(
    [switch]$UseDocker,
    [switch]$UseVenv
)

$ErrorActionPreference = "Stop"

$PROJECT_DIR = $PSScriptRoot + "\..\.."
Set-Location $PROJECT_DIR

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "本地自动修复系统" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查GitHub CLI
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "❌ GitHub CLI (gh) 未安装" -ForegroundColor Red
    Write-Host "安装: https://cli.github.com/" -ForegroundColor Yellow
    exit 1
}

# 检查是否已登录
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ GitHub CLI 未登录" -ForegroundColor Red
    Write-Host "请运行: gh auth login" -ForegroundColor Yellow
    exit 1
}

if ($UseDocker) {
    Write-Host "使用Docker运行..." -ForegroundColor Yellow
    
    # 检查docker-compose
    if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
        Write-Host "❌ docker-compose 未安装" -ForegroundColor Red
        exit 1
    }
    
    docker-compose run --rm -v "${PWD}:/app" -w /app api-gateway bash scripts/cicd/docker-auto-fix.sh
    exit $LASTEXITCODE
}

if ($UseVenv) {
    Write-Host "使用Python venv运行..." -ForegroundColor Yellow
    
    # 创建venv（如果不存在）
    if (-not (Test-Path "venv")) {
        Write-Host "创建venv..." -ForegroundColor Gray
        python -m venv venv
    }
    
    # 激活venv
    & "venv\Scripts\Activate.ps1"
    
    # 安装依赖
    Write-Host "安装依赖..." -ForegroundColor Gray
    pip install -q requests pyyaml
    
    # 运行Python脚本
    python scripts\cicd\local-auto-fix.py
    exit $LASTEXITCODE
}

# 默认使用PowerShell脚本
Write-Host "使用PowerShell脚本运行..." -ForegroundColor Yellow
$scriptPath = Join-Path $PSScriptRoot "local-auto-fix.ps1"
& $scriptPath


# Windows Docker构建脚本
# 用于在Windows环境下拉取镜像并构建项目

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "企业AI平台 - Docker构建脚本 (Windows)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Docker是否安装
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "错误: Docker未安装或未添加到PATH" -ForegroundColor Red
    Write-Host "请先安装Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# 检查Docker Desktop是否运行
Write-Host "[1/4] 检查Docker Desktop状态..." -ForegroundColor Blue
$dockerRunning = $false
$dockerInfo = docker info 2>&1
if ($LASTEXITCODE -eq 0) {
    $dockerRunning = $true
}

if (-not $dockerRunning) {
    Write-Host "警告: Docker Desktop未运行，正在尝试启动..." -ForegroundColor Yellow
    
    # 尝试启动Docker Desktop
    $dockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerPath) {
        Write-Host "正在启动Docker Desktop..." -ForegroundColor Yellow
        Start-Process -FilePath $dockerPath
        
        # 等待Docker启动（最多等待2分钟）
        Write-Host "等待Docker Desktop启动..." -ForegroundColor Yellow
        $maxWait = 120
        $waited = 0
        while ($waited -lt $maxWait) {
            Start-Sleep -Seconds 2
            $waited += 2
            $dockerInfo = docker info 2>&1
            if ($LASTEXITCODE -eq 0) {
                $dockerRunning = $true
                Write-Host "Docker Desktop已启动" -ForegroundColor Green
                break
            } else {
                Write-Host "." -NoNewline -ForegroundColor Gray
            }
        }
        
        if (-not $dockerRunning) {
            Write-Host ""
            Write-Host "错误: Docker Desktop启动超时" -ForegroundColor Red
            Write-Host "请手动启动Docker Desktop，然后重新运行此脚本" -ForegroundColor Yellow
            exit 1
        }
    } else {
        Write-Host "错误: 找不到Docker Desktop" -ForegroundColor Red
        Write-Host "请手动启动Docker Desktop，然后重新运行此脚本" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "Docker Desktop正在运行" -ForegroundColor Green
}

Write-Host ""

# 检查.env文件
Write-Host "[2/4] 检查环境配置..." -ForegroundColor Blue
if (-not (Test-Path ".env")) {
    if (Test-Path "env.example") {
        Write-Host "警告: .env文件不存在，从env.example创建..." -ForegroundColor Yellow
        Copy-Item "env.example" ".env"
        Write-Host "已创建.env文件，请根据需要修改配置" -ForegroundColor Green
    } else {
        Write-Host "警告: .env文件不存在" -ForegroundColor Yellow
    }
} else {
    Write-Host ".env文件存在" -ForegroundColor Green
}

Write-Host ""

# 拉取基础镜像
Write-Host "[3/4] 拉取必要的Docker镜像..." -ForegroundColor Blue
Write-Host "正在拉取基础镜像..." -ForegroundColor Gray

# 拉取Redis镜像
Write-Host "  - 拉取 redis:7-alpine..." -ForegroundColor Gray
docker pull redis:7-alpine
if ($LASTEXITCODE -ne 0) {
    Write-Host "警告: Redis镜像拉取失败，将使用本地镜像或重新构建" -ForegroundColor Yellow
}

# 拉取Python基础镜像
Write-Host "  - 拉取 python:3.11-slim..." -ForegroundColor Gray
docker pull python:3.11-slim
if ($LASTEXITCODE -ne 0) {
    Write-Host "警告: Python镜像拉取失败，将使用本地镜像或重新构建" -ForegroundColor Yellow
}

# 拉取Node.js基础镜像
Write-Host "  - 拉取 node:20-alpine..." -ForegroundColor Gray
docker pull node:20-alpine
if ($LASTEXITCODE -ne 0) {
    Write-Host "警告: Node.js镜像拉取失败，将使用本地镜像或重新构建" -ForegroundColor Yellow
}

Write-Host "基础镜像拉取完成" -ForegroundColor Green
Write-Host ""

# 构建项目镜像
Write-Host "[4/4] 构建项目Docker镜像..." -ForegroundColor Blue
Write-Host "这可能需要几分钟时间，请耐心等待..." -ForegroundColor Gray
Write-Host ""

# 使用docker-compose构建所有服务
Write-Host "正在构建所有服务镜像..." -ForegroundColor Gray
docker-compose build

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "镜像构建失败" -ForegroundColor Red
    Write-Host ""
    Write-Host "可能的原因:" -ForegroundColor Yellow
    Write-Host "  1. 网络连接问题 - 检查网络连接或配置镜像加速器" -ForegroundColor Yellow
    Write-Host "  2. Dockerfile配置错误 - 检查Dockerfile语法" -ForegroundColor Yellow
    Write-Host "  3. 依赖安装失败 - 检查requirements.txt和package.json" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "查看详细错误信息:" -ForegroundColor Yellow
    Write-Host "  docker-compose build --no-cache" -ForegroundColor Cyan
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "构建完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "查看已构建的镜像:" -ForegroundColor Yellow
Write-Host "  docker images" -ForegroundColor Cyan
Write-Host ""
Write-Host "启动所有服务:" -ForegroundColor Yellow
Write-Host "  docker-compose up -d" -ForegroundColor Cyan
Write-Host ""
Write-Host "查看服务状态:" -ForegroundColor Yellow
Write-Host "  docker-compose ps" -ForegroundColor Cyan
Write-Host ""

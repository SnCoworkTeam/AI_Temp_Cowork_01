# PowerShell脚本：同步本地Docker镜像到服务器测试环境
# 使用方法: .\scripts\sync-to-server.ps1 [service1] [service2] ...

param(
    [string[]]$Services = @()
)

$ErrorActionPreference = "Stop"

$SERVER_HOST = "43.143.139.197"
$SERVER_USER = "ubuntu"
$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER_DOCKER_DIR = "/home/ubuntu/enterprise-ai-platform"

Write-Host "🚀 开始同步Docker镜像到服务器..." -ForegroundColor Green

# 检查SSH密钥
if (-not (Test-Path $SSH_KEY)) {
    Write-Host "❌ SSH密钥文件不存在: $SSH_KEY" -ForegroundColor Red
    exit 1
}

# 获取要同步的服务列表
if ($Services.Count -eq 0) {
    $Services = @(
        "api-gateway",
        "agent-service",
        "chat-service",
        "config-center",
        "knowledge-base",
        "mcp-gateway",
        "workflow-engine",
        "dag-orchestrator",
        "sap-mcp-server"
    )
}

# 创建临时目录
$TEMP_DIR = New-TemporaryFile | ForEach-Object { Remove-Item $_; New-Item -ItemType Directory -Path $_.FullName }
Write-Host "📦 临时目录: $TEMP_DIR" -ForegroundColor Yellow

# 导出并同步每个服务的镜像
foreach ($SERVICE in $Services) {
    $IMAGE_NAME = "enterprise-ai-${SERVICE}"
    $IMAGE_FILE = Join-Path $TEMP_DIR "${SERVICE}.tar"
    
    Write-Host "📦 导出镜像: $IMAGE_NAME" -ForegroundColor Yellow
    
    # 检查镜像是否存在
    $imageExists = docker images --format "{{.Repository}}:{{.Tag}}" | Select-String -Pattern "^${IMAGE_NAME}:latest$"
    if (-not $imageExists) {
        Write-Host "⚠️  镜像 $IMAGE_NAME 不存在，跳过..." -ForegroundColor Yellow
        continue
    }
    
    # 导出镜像
    docker save "${IMAGE_NAME}:latest" -o $IMAGE_FILE
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 镜像导出成功: $IMAGE_FILE" -ForegroundColor Green
        
        # 压缩镜像文件
        Write-Host "🗜️  压缩镜像文件..." -ForegroundColor Yellow
        $compressedFile = "${IMAGE_FILE}.gz"
        # 使用7zip或gzip压缩（需要安装）
        if (Get-Command gzip -ErrorAction SilentlyContinue) {
            gzip -f $IMAGE_FILE
        } else {
            Write-Host "⚠️  gzip未安装，跳过压缩" -ForegroundColor Yellow
            $compressedFile = $IMAGE_FILE
        }
        
        # 上传到服务器
        Write-Host "📤 上传镜像到服务器..." -ForegroundColor Yellow
        scp -i $SSH_KEY $compressedFile "${SERVER_USER}@${SERVER_HOST}:${SERVER_DOCKER_DIR}/images/"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 镜像上传成功: $SERVICE" -ForegroundColor Green
            
            # 在服务器上加载镜像
            Write-Host "📥 在服务器上加载镜像..." -ForegroundColor Yellow
            $loadCommand = @"
cd ${SERVER_DOCKER_DIR} && \
gunzip -c images/${SERVICE}.tar.gz | docker load && \
rm -f images/${SERVICE}.tar.gz
"@
            ssh -i $SSH_KEY "${SERVER_USER}@${SERVER_HOST}" $loadCommand
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ 镜像加载成功: $SERVICE" -ForegroundColor Green
            } else {
                Write-Host "❌ 镜像加载失败: $SERVICE" -ForegroundColor Red
            }
        } else {
            Write-Host "❌ 镜像上传失败: $SERVICE" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ 镜像导出失败: $SERVICE" -ForegroundColor Red
    }
}

# 清理临时文件
Remove-Item -Recurse -Force $TEMP_DIR
Write-Host "🧹 临时文件已清理" -ForegroundColor Green

# 同步docker-compose.yml和配置文件
Write-Host "📤 同步配置文件..." -ForegroundColor Yellow
scp -i $SSH_KEY docker-compose.yml "${SERVER_USER}@${SERVER_HOST}:${SERVER_DOCKER_DIR}/"
if (Test-Path "docker-compose.test.yml") {
    scp -i $SSH_KEY docker-compose.test.yml "${SERVER_USER}@${SERVER_HOST}:${SERVER_DOCKER_DIR}/"
}

# 重启服务（可选）
$restart = Read-Host "是否重启服务器上的服务? (y/n)"
if ($restart -eq "y" -or $restart -eq "Y") {
    Write-Host "🔄 重启服务器上的服务..." -ForegroundColor Yellow
    $restartCommand = @"
cd ${SERVER_DOCKER_DIR} && \
docker-compose -f docker-compose.test.yml down && \
docker-compose -f docker-compose.test.yml up -d
"@
    ssh -i $SSH_KEY "${SERVER_USER}@${SERVER_HOST}" $restartCommand
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 服务重启成功" -ForegroundColor Green
    } else {
        Write-Host "❌ 服务重启失败" -ForegroundColor Red
    }
}

Write-Host "🎉 同步完成！" -ForegroundColor Green


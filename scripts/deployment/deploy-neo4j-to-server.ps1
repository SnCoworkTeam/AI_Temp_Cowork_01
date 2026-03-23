#!/usr/bin/env pwsh
# Neo4j图数据库部署脚本 - 部署到服务器43.143.90.179
# 使用方法: .\scripts\deployment\deploy-neo4j-to-server.ps1

param(
    [string]$ServerIP = "43.143.90.179",
    [string]$ServerUser = "root",
    [string]$KeyPath = "",
    [string]$RemotePath = "/opt/enterprise-ai-platform",
    [string]$Neo4jPassword = "Neo4j"
)

$ErrorActionPreference = "Stop"

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "🚀 Neo4j图数据库部署到服务器" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "服务器: $ServerUser@$ServerIP" -ForegroundColor Yellow
Write-Host "远程路径: $RemotePath" -ForegroundColor Yellow
Write-Host "Neo4j密码: $Neo4jPassword" -ForegroundColor Yellow
Write-Host ""

# 检查密钥文件
$ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if ([string]::IsNullOrEmpty($KeyPath)) {
    $KeyPath = Join-Path $ProjectRoot "enterprise_ai_platform.pem"
    if (-not (Test-Path $KeyPath)) {
        $KeyPath = Join-Path $env:USERPROFILE ".ssh\enterprise_ai_platform.pem"
    }
}

if (-not (Test-Path $KeyPath)) {
    Write-Host "❌ 未找到SSH密钥文件: $KeyPath" -ForegroundColor Red
    Write-Host "请提供SSH密钥文件路径，或将其放置在以下位置之一：" -ForegroundColor Yellow
    Write-Host "  1. $ProjectRoot\enterprise_ai_platform.pem" -ForegroundColor Gray
    Write-Host "  2. $env:USERPROFILE\.ssh\enterprise_ai_platform.pem" -ForegroundColor Gray
    Write-Host ""
    $KeyPath = Read-Host "请输入SSH密钥文件路径（或按Enter跳过，使用密码登录）"
    if ([string]::IsNullOrEmpty($KeyPath)) {
        $UsePassword = $true
    }
}

# 构建SSH命令
if ($UsePassword) {
    $sshCmd = "ssh -o StrictHostKeyChecking=no $ServerUser@${ServerIP}"
    $scpCmd = "scp -o StrictHostKeyChecking=no"
} else {
    $sshCmd = "ssh -i `"$KeyPath`" -o StrictHostKeyChecking=no $ServerUser@${ServerIP}"
    $scpCmd = "scp -i `"$KeyPath`" -o StrictHostKeyChecking=no"
}

# 检查服务器连接
Write-Host "[1/6] 检查服务器连接..." -ForegroundColor Cyan
if ($UsePassword) {
    Write-Host "⚠️  使用密码登录，请准备好服务器密码" -ForegroundColor Yellow
    Write-Host "提示: 如果连接失败，请确保已配置SSH密钥或使用sshpass工具" -ForegroundColor Gray
}

try {
    # 对于密码登录，使用sshpass（如果可用）或提示用户
    if ($UsePassword) {
        # 尝试使用sshpass
        $sshpassCmd = Get-Command sshpass -ErrorAction SilentlyContinue
        if ($sshpassCmd) {
            Write-Host "检测到sshpass，将使用密码登录" -ForegroundColor Gray
            $sshCmd = "sshpass -p `"$Neo4jPassword`" ssh -o StrictHostKeyChecking=no $ServerUser@${ServerIP}"
        } else {
            Write-Host "未找到sshpass，将尝试交互式密码登录" -ForegroundColor Yellow
            Write-Host "如果失败，请安装sshpass或配置SSH密钥" -ForegroundColor Gray
        }
    }
    
    $testResult = Invoke-Expression "$sshCmd 'echo Connection test successful'" 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "SSH连接失败: $testResult"
    }
    Write-Host "✅ 服务器连接成功" -ForegroundColor Green
} catch {
    Write-Host "❌ 服务器连接失败: $_" -ForegroundColor Red
    Write-Host "`n解决方案:" -ForegroundColor Yellow
    Write-Host "1. 配置SSH密钥文件（推荐）" -ForegroundColor White
    Write-Host "2. 安装sshpass工具: choco install sshpass 或 brew install sshpass" -ForegroundColor White
    Write-Host "3. 手动SSH连接测试: ssh $ServerUser@$ServerIP" -ForegroundColor White
    exit 1
}

# 检查Docker和Docker Compose
Write-Host "`n[2/6] 检查服务器Docker环境..." -ForegroundColor Cyan
$dockerCheck = Invoke-Expression "$sshCmd 'docker --version && docker-compose --version'" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Docker未安装，尝试安装..." -ForegroundColor Yellow
    $installDocker = @"
# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
# 安装Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
"@
    Invoke-Expression "$sshCmd `"$installDocker`"" | Out-Null
    Write-Host "✅ Docker安装完成" -ForegroundColor Green
} else {
    Write-Host "✅ Docker环境正常" -ForegroundColor Green
}

# 创建远程目录
Write-Host "`n[3/6] 创建远程目录..." -ForegroundColor Cyan
$createDir = "mkdir -p $RemotePath/neo4j && mkdir -p $RemotePath/neo4j/data && mkdir -p $RemotePath/neo4j/logs && mkdir -p $RemotePath/neo4j/import && mkdir -p $RemotePath/neo4j/plugins"
Invoke-Expression "$sshCmd `"$createDir`"" | Out-Null
Write-Host "✅ 远程目录创建完成" -ForegroundColor Green

# 创建docker-compose文件
Write-Host "`n[4/6] 创建docker-compose配置文件..." -ForegroundColor Cyan
$dockerComposeContent = @"
version: '3.8'

services:
  # Neo4j - 图数据库（服务器部署）
  neo4j:
    image: neo4j:5-community
    container_name: enterprise-ai-neo4j
    environment:
      NEO4J_AUTH: neo4j/$Neo4jPassword
      # 插件配置
      NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
      
      # 内存配置（根据服务器配置调整）
      NEO4J_dbms_memory_heap_initial__size: 1G
      NEO4J_dbms_memory_heap_max__size: 2G
      NEO4J_dbms_memory_pagecache_size: 1G
      NEO4J_dbms_memory_transaction_total_max: 512M
      
      # 性能优化配置
      NEO4J_dbms_transaction_timeout: 60s
      NEO4J_dbms_lock_acquisition_timeout: 10s
      
      # 连接池配置
      NEO4J_dbms_connector_bolt_thread__pool__max__size: 100
      NEO4J_dbms_connector_http_thread__pool__max__size: 50
      
      # 允许远程访问
      NEO4J_dbms_connector_bolt_listen__address: 0.0.0.0:7687
      NEO4J_dbms_connector_http_listen__address: 0.0.0.0:7474
      NEO4J_dbms_connector_https_listen__address: 0.0.0.0:7473
      
    volumes:
      - $RemotePath/neo4j/data:/data
      - $RemotePath/neo4j/logs:/logs
      - $RemotePath/neo4j/import:/var/lib/neo4j/import
      - $RemotePath/neo4j/plugins:/plugins
    ports:
      - "7474:7474"   # HTTP Web界面
      - "7687:7687"   # Bolt协议（应用连接）
      - "7473:7473"   # HTTPS（可选）
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "$Neo4jPassword", "RETURN 1"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
        reservations:
          memory: 2G
          cpus: '1'

networks:
  default:
    name: neo4j-network
"@

# 将docker-compose内容写入临时文件
$tempComposeFile = "$env:TEMP\neo4j-docker-compose-$(Get-Date -Format 'yyyyMMdd-HHmmss').yml"
$dockerComposeContent | Out-File -FilePath $tempComposeFile -Encoding utf8

# 上传docker-compose文件
Write-Host "正在上传docker-compose文件..." -ForegroundColor Yellow
Invoke-Expression "$scpCmd `"$tempComposeFile`" $ServerUser@${ServerIP}:$RemotePath/neo4j/docker-compose.yml" | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ docker-compose文件上传成功" -ForegroundColor Green
} else {
    Write-Host "❌ docker-compose文件上传失败" -ForegroundColor Red
    exit 1
}

# 删除临时文件
Remove-Item $tempComposeFile -Force -ErrorAction SilentlyContinue

# 启动Neo4j容器
Write-Host "`n[5/6] 启动Neo4j容器..." -ForegroundColor Cyan
$startNeo4j = "cd $RemotePath/neo4j && docker-compose down && docker-compose up -d"
Invoke-Expression "$sshCmd `"$startNeo4j`"" | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Neo4j容器启动成功" -ForegroundColor Green
} else {
    Write-Host "❌ Neo4j容器启动失败" -ForegroundColor Red
    exit 1
}

# 等待Neo4j启动并检查状态
Write-Host "`n[6/6] 等待Neo4j启动并检查状态..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

$checkStatus = "docker ps | grep neo4j"
$statusResult = Invoke-Expression "$sshCmd `"$checkStatus`"" 2>&1
if ($statusResult -match "neo4j") {
    Write-Host "✅ Neo4j容器运行正常" -ForegroundColor Green
} else {
    Write-Host "⚠️  无法确认Neo4j状态，请手动检查" -ForegroundColor Yellow
}

# 检查健康状态
Write-Host "`n检查Neo4j健康状态..." -ForegroundColor Cyan
Start-Sleep -Seconds 20
$healthCheck = "docker exec enterprise-ai-neo4j cypher-shell -u neo4j -p $Neo4jPassword 'RETURN 1 AS test'"
$healthResult = Invoke-Expression "$sshCmd `"$healthCheck`"" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Neo4j健康检查通过" -ForegroundColor Green
} else {
    Write-Host "⚠️  Neo4j健康检查失败，可能需要更多时间启动" -ForegroundColor Yellow
}

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "🎉 Neo4j部署完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "访问地址:" -ForegroundColor Yellow
Write-Host "  HTTP界面: http://$ServerIP:7474" -ForegroundColor White
Write-Host "  Bolt连接: bolt://$ServerIP:7687" -ForegroundColor White
Write-Host "  用户名: neo4j" -ForegroundColor White
Write-Host "  密码: $Neo4jPassword" -ForegroundColor White
Write-Host ""


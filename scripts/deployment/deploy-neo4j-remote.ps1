#!/usr/bin/env pwsh
# Neo4j图数据库远程部署脚本
# 使用Neo4j.pem密钥连接到43.143.90.179服务器
# 使用方法: .\scripts\deployment\deploy-neo4j-remote.ps1

param(
    [string]$ServerIP = "43.143.90.179",
    [string]$ServerUser = "root",
    [string]$KeyPath = "",
    [string]$RemotePath = "/opt/enterprise-ai-platform",
    [string]$Neo4jPassword = "Neo4j@2024"
)

$ErrorActionPreference = "Stop"

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "🚀 Neo4j图数据库远程部署脚本" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "服务器: $ServerUser@$ServerIP" -ForegroundColor Yellow
Write-Host "远程路径: $RemotePath" -ForegroundColor Yellow
Write-Host "Neo4j密码: $Neo4jPassword" -ForegroundColor Yellow
Write-Host ""

# 检查密钥文件
$ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if ([string]::IsNullOrEmpty($KeyPath)) {
    # 优先查找Neo4j.pem
    $KeyPath = Join-Path $ProjectRoot "Neo4j.pem"
    if (-not (Test-Path $KeyPath)) {
        $KeyPath = Join-Path $ProjectRoot "enterprise_ai_platform.pem"
        if (-not (Test-Path $KeyPath)) {
            $KeyPath = Join-Path $env:USERPROFILE ".ssh\enterprise_ai_platform.pem"
        }
    }
}

if (-not (Test-Path $KeyPath)) {
    Write-Host "❌ 未找到SSH密钥文件" -ForegroundColor Red
    Write-Host "请将Neo4j.pem放置在以下位置之一：" -ForegroundColor Yellow
    Write-Host "  1. $ProjectRoot\Neo4j.pem" -ForegroundColor Gray
    Write-Host "  2. $ProjectRoot\enterprise_ai_platform.pem" -ForegroundColor Gray
    Write-Host "  3. $env:USERPROFILE\.ssh\enterprise_ai_platform.pem" -ForegroundColor Gray
    exit 1
}

Write-Host "✅ 找到密钥文件: $KeyPath" -ForegroundColor Green

# 设置密钥文件权限（Windows）
try {
    icacls $KeyPath /inheritance:r /grant:r "${env:USERNAME}:R" 2>&1 | Out-Null
} catch {
    Write-Host "⚠️  无法设置密钥文件权限（可能已正确设置）" -ForegroundColor Yellow
}

# 构建SSH命令
$sshCmd = "ssh -i `"$KeyPath`" -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL $ServerUser@${ServerIP}"
$scpCmd = "scp -i `"$KeyPath`" -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL"

# 检查服务器连接
Write-Host "`n[1/7] 检查服务器连接..." -ForegroundColor Cyan
try {
    $testResult = Invoke-Expression "$sshCmd 'echo Connection test successful'" 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "SSH连接失败: $testResult"
    }
    Write-Host "✅ 服务器连接成功" -ForegroundColor Green
} catch {
    Write-Host "❌ 服务器连接失败: $_" -ForegroundColor Red
    Write-Host "`n解决方案:" -ForegroundColor Yellow
    Write-Host "1. 检查密钥文件路径和权限" -ForegroundColor White
    Write-Host "2. 检查服务器IP和用户名是否正确" -ForegroundColor White
    Write-Host "3. 检查服务器安全组是否开放22端口" -ForegroundColor White
    exit 1
}

# 检查Docker环境
Write-Host "`n[2/7] 检查服务器Docker环境..." -ForegroundColor Cyan
$dockerCheck = Invoke-Expression "$sshCmd 'command -v docker && command -v docker-compose'" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Docker未安装，开始安装..." -ForegroundColor Yellow
    $installDocker = @"
# 安装Docker
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
fi
# 安装Docker Compose
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi
"@
    Invoke-Expression "$sshCmd `"$installDocker`"" | Out-Null
    Write-Host "✅ Docker安装完成" -ForegroundColor Green
} else {
    Write-Host "✅ Docker环境正常" -ForegroundColor Green
}

# 创建远程目录
Write-Host "`n[3/7] 创建远程目录..." -ForegroundColor Cyan
$createDir = "mkdir -p $RemotePath/neo4j/{data,logs,import,plugins,conf}"
Invoke-Expression "$sshCmd `"$createDir`"" | Out-Null
Write-Host "✅ 远程目录创建完成" -ForegroundColor Green

# 创建docker-compose文件
Write-Host "`n[4/7] 创建docker-compose配置文件..." -ForegroundColor Cyan
$dockerComposeContent = @"
version: '3.8'

services:
  # Neo4j - 图数据库（远程服务器部署）
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
      
      # 安全配置
      NEO4J_dbms_security_procedures_unrestricted: apoc.*,gds.*
      
    volumes:
      - $RemotePath/neo4j/data:/data
      - $RemotePath/neo4j/logs:/logs
      - $RemotePath/neo4j/import:/var/lib/neo4j/import
      - $RemotePath/neo4j/plugins:/plugins
      - $RemotePath/neo4j/conf:/var/lib/neo4j/conf
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
    driver: bridge
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
Write-Host "`n[5/7] 启动Neo4j容器..." -ForegroundColor Cyan
$startNeo4j = "cd $RemotePath/neo4j && docker-compose down 2>/dev/null; docker-compose up -d"
Invoke-Expression "$sshCmd `"$startNeo4j`"" | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Neo4j容器启动成功" -ForegroundColor Green
} else {
    Write-Host "❌ Neo4j容器启动失败" -ForegroundColor Red
    exit 1
}

# 等待Neo4j启动
Write-Host "`n[6/7] 等待Neo4j启动（30秒）..." -ForegroundColor Cyan
Start-Sleep -Seconds 30

# 检查容器状态
Write-Host "检查Neo4j容器状态..." -ForegroundColor Cyan
$checkStatus = "docker ps --filter name=enterprise-ai-neo4j --format '{{.Status}}'"
$statusResult = Invoke-Expression "$sshCmd `"$checkStatus`"" 2>&1
if ($statusResult -match "Up") {
    Write-Host "✅ Neo4j容器运行正常" -ForegroundColor Green
} else {
    Write-Host "⚠️  无法确认Neo4j状态，请手动检查" -ForegroundColor Yellow
    Write-Host "查看日志: ssh $ServerUser@$ServerIP 'docker logs enterprise-ai-neo4j'" -ForegroundColor Gray
}

# 健康检查
Write-Host "`n[7/7] 执行Neo4j健康检查..." -ForegroundColor Cyan
Start-Sleep -Seconds 10
$healthCheck = "docker exec enterprise-ai-neo4j cypher-shell -u neo4j -p $Neo4jPassword 'RETURN 1 AS test' 2>&1"
$healthResult = Invoke-Expression "$sshCmd `"$healthCheck`"" 2>&1
if ($LASTEXITCODE -eq 0 -or $healthResult -match "1") {
    Write-Host "✅ Neo4j健康检查通过" -ForegroundColor Green
} else {
    Write-Host "⚠️  Neo4j健康检查失败，可能需要更多时间启动" -ForegroundColor Yellow
    Write-Host "提示: Neo4j首次启动需要1-2分钟，请稍后访问Web界面确认" -ForegroundColor Gray
}

# 显示连接信息
Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "🎉 Neo4j部署完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "访问地址:" -ForegroundColor Yellow
Write-Host "  HTTP界面: http://$ServerIP:7474" -ForegroundColor White
Write-Host "  Bolt连接: bolt://$ServerIP:7687" -ForegroundColor White
Write-Host "  用户名: neo4j" -ForegroundColor White
Write-Host "  密码: $Neo4jPassword" -ForegroundColor White
Write-Host ""
Write-Host "下一步操作:" -ForegroundColor Yellow
Write-Host "  1. 运行数据导入脚本: python scripts/import_data_to_neo4j_remote.py" -ForegroundColor White
Write-Host "  2. 更新应用配置连接到远程Neo4j" -ForegroundColor White
Write-Host "  3. 验证数据导入结果" -ForegroundColor White
Write-Host ""




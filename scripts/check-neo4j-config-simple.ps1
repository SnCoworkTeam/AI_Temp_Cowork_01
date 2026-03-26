#!/usr/bin/env pwsh
# 简单检查Neo4j连接配置

param(
    [string]$AppServerIP = "43.143.139.197",
    [string]$AppServerUser = "root",
    [string]$Neo4jServerIP = "43.143.90.179",
    [string]$Neo4jPort = "7687"
)

Write-Host "`n检查Neo4j连接配置..." -ForegroundColor Cyan
Write-Host "应用服务器: ${AppServerUser}@${AppServerIP}" -ForegroundColor Yellow
Write-Host "Neo4j服务器: ${Neo4jServerIP}:${Neo4jPort}" -ForegroundColor Yellow
Write-Host ""

# 检查密钥文件
$ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$KeyPath = Join-Path $ProjectRoot "Neo4j.pem"
if (-not (Test-Path $KeyPath)) {
    $KeyPath = Join-Path $ProjectRoot "enterprise_ai_platform.pem"
}

if (Test-Path $KeyPath) {
    $sshCmd = "ssh -i `"$KeyPath`" -o StrictHostKeyChecking=no ${AppServerUser}@${AppServerIP}"
} else {
    $sshCmd = "ssh -o StrictHostKeyChecking=no ${AppServerUser}@${AppServerIP}"
    Write-Host "⚠️  使用密码连接" -ForegroundColor Yellow
}

# 检查环境变量
Write-Host "`n[1] 检查环境变量..." -ForegroundColor Cyan
$envCmd = "grep -i neo4j /opt/enterprise-ai-platform/.env 2>/dev/null || echo '未找到Neo4j配置'"
$envResult = Invoke-Expression "${sshCmd} `"${envCmd}`"" 2>&1
Write-Host $envResult

# 检查网络连接
Write-Host "`n[2] 测试网络连接..." -ForegroundColor Cyan
$netCmd = "timeout 5 bash -c 'cat < /dev/null > /dev/tcp/${Neo4jServerIP}/${Neo4jPort}' 2>&1 && echo '✅ 网络连接成功' || echo '❌ 网络连接失败'"
$netResult = Invoke-Expression "${sshCmd} `"${netCmd}`"" 2>&1
Write-Host $netResult

# 显示建议配置
Write-Host "`n建议配置:" -ForegroundColor Yellow
Write-Host "NEO4J_URI=bolt://${Neo4jServerIP}:${Neo4jPort}" -ForegroundColor Gray
Write-Host "NEO4J_USER=neo4j" -ForegroundColor Gray
Write-Host "NEO4J_PASSWORD=Neo4j@2024" -ForegroundColor Gray
Write-Host "NEO4J_DATABASE=neo4j" -ForegroundColor Gray




#!/usr/bin/env pwsh
# 更新应用服务器上的Neo4j配置
# 使用方法: .\scripts\update-neo4j-config-on-app-server.ps1

param(
    [string]$AppServerIP = "43.143.139.197",
    [string]$AppServerUser = "root",
    [string]$Neo4jServerIP = "43.143.90.179",
    [string]$Neo4jPort = "7687",
    [string]$Neo4jUser = "neo4j",
    [string]$Neo4jPassword = "Neo4j@2024",
    [string]$KeyPath = "enterprise_ai_platform.pem"
)

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "更新应用服务器Neo4j配置" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "应用服务器: ${AppServerUser}@${AppServerIP}" -ForegroundColor Yellow
Write-Host "Neo4j服务器: ${Neo4jServerIP}:${Neo4jPort}" -ForegroundColor Yellow
Write-Host ""

# 检查密钥文件
if (-not (Test-Path $KeyPath)) {
    Write-Host "❌ 未找到密钥文件: $KeyPath" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 找到密钥文件: $KeyPath" -ForegroundColor Green

# 构建SSH命令
$sshCmd = "ssh -i `"$KeyPath`" -o StrictHostKeyChecking=no ${AppServerUser}@${AppServerIP}"
$scpCmd = "scp -i `"$KeyPath`" -o StrictHostKeyChecking=no"

# 创建配置内容
$neo4jConfig = @"
# Neo4j图数据库配置
NEO4J_URI=bolt://${Neo4jServerIP}:${Neo4jPort}
NEO4J_USER=${Neo4jUser}
NEO4J_PASSWORD=${Neo4jPassword}
NEO4J_DATABASE=neo4j
NEO4J_MAX_CONNECTION_POOL_SIZE=50
NEO4J_CONNECTION_ACQUISITION_TIMEOUT=60
NEO4J_CONNECTION_TIMEOUT=30
"@

# 将配置写入临时文件
$tempConfigFile = "$env:TEMP\neo4j-config-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
$neo4jConfig | Out-File -FilePath $tempConfigFile -Encoding utf8

Write-Host "`n配置内容:" -ForegroundColor Cyan
Write-Host $neo4jConfig -ForegroundColor Gray
Write-Host ""

# 检查现有配置
Write-Host "[1/3] 检查现有配置..." -ForegroundColor Cyan
$checkCmd = @"
if [ -f /opt/enterprise-ai-platform/.env ]; then
    echo "=== 现有Neo4j配置 ==="
    grep -i neo4j /opt/enterprise-ai-platform/.env 2>/dev/null || echo "未找到Neo4j配置"
    echo ""
    echo "=== 是否已配置 ==="
    if grep -q "NEO4J_URI" /opt/enterprise-ai-platform/.env 2>/dev/null; then
        echo "✅ 已配置Neo4j"
    else
        echo "❌ 未配置Neo4j"
    fi
else
    echo ".env文件不存在"
fi
"@

try {
    $checkResult = Invoke-Expression "${sshCmd} `"${checkCmd}`"" 2>&1
    Write-Host $checkResult
} catch {
    Write-Host "⚠️  无法检查现有配置，可能需要手动检查" -ForegroundColor Yellow
}

# 更新配置
Write-Host "`n[2/3] 更新配置..." -ForegroundColor Cyan
$updateCmd = @"
cd /opt/enterprise-ai-platform 2>/dev/null || cd /root/enterprise-ai-platform 2>/dev/null || (echo '项目目录未找到' && exit 1)

# 备份现有.env文件
if [ -f .env ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ 已备份.env文件"
fi

# 移除旧的Neo4j配置
if [ -f .env ]; then
    sed -i '/^NEO4J_/d' .env
    echo "✅ 已移除旧Neo4j配置"
fi

# 添加新的Neo4j配置
cat >> .env << 'NEO4J_CONFIG_EOF'
# Neo4j图数据库配置
NEO4J_URI=bolt://${Neo4jServerIP}:${Neo4jPort}
NEO4J_USER=${Neo4jUser}
NEO4J_PASSWORD=${Neo4jPassword}
NEO4J_DATABASE=neo4j
NEO4J_MAX_CONNECTION_POOL_SIZE=50
NEO4J_CONNECTION_ACQUISITION_TIMEOUT=60
NEO4J_CONNECTION_TIMEOUT=30
NEO4J_CONFIG_EOF

echo "✅ 已添加Neo4j配置"
echo ""
echo "=== 更新后的Neo4j配置 ==="
grep -i neo4j .env
"@

try {
    $updateResult = Invoke-Expression "${sshCmd} `"${updateCmd}`"" 2>&1
    Write-Host $updateResult
} catch {
    Write-Host "❌ 更新配置失败: $_" -ForegroundColor Red
    Write-Host "`n请手动执行以下命令更新配置:" -ForegroundColor Yellow
    Write-Host $updateCmd -ForegroundColor Gray
    exit 1
}

# 测试连接
Write-Host "`n[3/3] 测试Neo4j连接..." -ForegroundColor Cyan
$testCmd = "timeout 5 bash -c 'cat < /dev/null > /dev/tcp/${Neo4jServerIP}/${Neo4jPort}' 2>&1; if [ `$? -eq 0 ]; then echo '✅ 网络连接成功'; else echo '❌ 网络连接失败，请检查防火墙和安全组设置'; fi"

$testResult = Invoke-Expression "${sshCmd} `"${testCmd}`"" 2>&1
Write-Host $testResult

# 清理临时文件
Remove-Item $tempConfigFile -Force -ErrorAction SilentlyContinue

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "配置更新完成" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步操作:" -ForegroundColor Yellow
Write-Host "1. 重启相关服务以应用新配置" -ForegroundColor White
Write-Host "2. 验证Neo4j连接是否正常" -ForegroundColor White
Write-Host ""


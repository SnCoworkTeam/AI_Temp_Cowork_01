#!/usr/bin/env pwsh
# 检查应用服务器到Neo4j服务器的连接配置
# 使用方法: .\scripts\check-neo4j-connection-config.ps1

param(
    [string]$AppServerIP = "43.143.139.197",
    [string]$AppServerUser = "root",
    [string]$Neo4jServerIP = "43.143.90.179",
    [string]$Neo4jPort = "7687",
    [string]$KeyPath = ""
)

$ErrorActionPreference = "Stop"

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "检查Neo4j连接配置" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "应用服务器: $AppServerUser@${AppServerIP}" -ForegroundColor Yellow
Write-Host "Neo4j服务器: ${Neo4jServerIP}:${Neo4jPort}" -ForegroundColor Yellow
Write-Host ""

# 检查密钥文件
$ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if ([string]::IsNullOrEmpty($KeyPath)) {
    $KeyPath = Join-Path $ProjectRoot "Neo4j.pem"
    if (-not (Test-Path $KeyPath)) {
        $KeyPath = Join-Path $ProjectRoot "enterprise_ai_platform.pem"
    }
}

if (-not (Test-Path $KeyPath)) {
    Write-Host "⚠️  未找到SSH密钥文件，将尝试使用密码连接" -ForegroundColor Yellow
    $UsePassword = $true
} else {
    Write-Host "✅ 找到密钥文件: $KeyPath" -ForegroundColor Green
    $UsePassword = $false
}

# 构建SSH命令
if ($UsePassword) {
    $sshCmd = "ssh -o StrictHostKeyChecking=no $AppServerUser@${AppServerIP}"
} else {
    $sshCmd = "ssh -i `"$KeyPath`" -o StrictHostKeyChecking=no $AppServerUser@${AppServerIP}"
}

# 检查1: 测试应用服务器连接
Write-Host "`n[1/5] 测试应用服务器连接..." -ForegroundColor Cyan
try {
    $testResult = Invoke-Expression "$sshCmd 'echo Connection OK'" 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "连接失败"
    }
    Write-Host "✅ 应用服务器连接成功" -ForegroundColor Green
} catch {
    Write-Host "❌ 应用服务器连接失败: $_" -ForegroundColor Red
    Write-Host "提示: 请检查服务器IP、用户名和密钥文件" -ForegroundColor Yellow
    exit 1
}

# 检查2: 检查环境变量配置
Write-Host "`n[2/5] 检查环境变量配置..." -ForegroundColor Cyan
$envCheck = @"
if [ -f /opt/enterprise-ai-platform/.env ]; then
    echo "=== .env文件内容（Neo4j相关）==="
    grep -i neo4j /opt/enterprise-ai-platform/.env 2>/dev/null || echo "未找到Neo4j配置"
else
    echo ".env文件不存在"
fi
"@

$envResult = Invoke-Expression "$sshCmd `"$envCheck`"" 2>&1
Write-Host $envResult

if ($envResult -match "NEO4J_URI|NEO4J_USER|NEO4J_PASSWORD") {
    Write-Host "✅ 找到Neo4j环境变量配置" -ForegroundColor Green
} else {
    Write-Host "⚠️  未找到Neo4j环境变量配置" -ForegroundColor Yellow
}

# 检查3: 检查Docker Compose配置
Write-Host "`n[3/5] 检查Docker Compose配置..." -ForegroundColor Cyan
$composeCheck = @"
cd /opt/enterprise-ai-platform 2>/dev/null || cd /root/enterprise-ai-platform 2>/dev/null || echo "项目目录未找到"
if [ -f docker-compose.yml ]; then
    echo "=== Docker Compose中的Neo4j配置 ==="
    grep -A 20 -i "neo4j:" docker-compose.yml 2>/dev/null || echo "未找到Neo4j服务配置"
else
    echo "docker-compose.yml文件不存在"
fi
"@

$composeResult = Invoke-Expression "$sshCmd `"$composeCheck`"" 2>&1
Write-Host $composeResult

# 检查4: 测试网络连接
Write-Host "`n[4/5] 测试到Neo4j服务器的网络连接..." -ForegroundColor Cyan
$networkTest = "timeout 5 bash -c 'cat < /dev/null > /dev/tcp/${Neo4jServerIP}/${Neo4jPort}' 2>&1 && echo '连接成功' || echo '连接失败'"
$networkResult = Invoke-Expression "$sshCmd `"$networkTest`"" 2>&1
Write-Host "网络连接测试: $networkResult" -ForegroundColor $(if ($networkResult -match "成功") { "Green" } else { "Yellow" })

# 检查5: 测试Neo4j连接（如果安装了neo4j客户端）
Write-Host "`n[5/5] 测试Neo4j数据库连接..." -ForegroundColor Cyan
$neo4jTest = @"
if command -v cypher-shell &> /dev/null; then
    echo "使用cypher-shell测试连接..."
    timeout 10 cypher-shell -a bolt://${Neo4jServerIP}:${Neo4jPort} -u neo4j -p 'Neo4j@2024' 'RETURN 1 AS test' 2>&1 | head -5
elif command -v python3 &> /dev/null; then
    echo "使用Python测试连接..."
    python3 -c "
import sys
try:
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver('bolt://${Neo4jServerIP}:${Neo4jPort}', auth=('neo4j', 'Neo4j@2024'))
    with driver.session() as session:
        result = session.run('RETURN 1 AS test')
        print('✅ Neo4j连接成功')
    driver.close()
except Exception as e:
    print(f'❌ Neo4j连接失败: {e}')
    sys.exit(1)
" 2>&1
else
    echo "未找到Neo4j客户端工具，跳过连接测试"
fi
"@

$neo4jResult = Invoke-Expression "$sshCmd `"$neo4jTest`"" 2>&1
Write-Host $neo4jResult

# 总结
Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "检查完成" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "建议配置（如果未配置）:" -ForegroundColor Yellow
Write-Host "在应用服务器的.env文件中添加:" -ForegroundColor White
Write-Host "  NEO4J_URI=bolt://${Neo4jServerIP}:${Neo4jPort}" -ForegroundColor Gray
Write-Host "  NEO4J_USER=neo4j" -ForegroundColor Gray
Write-Host "  NEO4J_PASSWORD=Neo4j@2024" -ForegroundColor Gray
Write-Host "  NEO4J_DATABASE=neo4j" -ForegroundColor Gray
Write-Host ""


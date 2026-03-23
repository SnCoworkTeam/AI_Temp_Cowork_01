# 检查应用服务器Neo4j配置
$ServerIP = "43.143.139.197"
$ServerUser = "ubuntu"
$Password = "Liu@bner1983"
$Neo4jServerIP = "43.143.90.179"
$Neo4jPort = "7687"

Write-Host "检查应用服务器Neo4j配置..." -ForegroundColor Cyan
Write-Host "服务器: ${ServerUser}@${ServerIP}" -ForegroundColor Yellow
Write-Host "Neo4j服务器: ${Neo4jServerIP}:${Neo4jPort}" -ForegroundColor Yellow
Write-Host ""

# 创建检查脚本
$checkScript = @"
#!/bin/bash
echo "=== [1] 检查.env文件中的Neo4j配置 ==="
cd /opt/enterprise-ai-platform 2>/dev/null || cd /root/enterprise-ai-platform 2>/dev/null || cd ~/enterprise-ai-platform 2>/dev/null || { echo "项目目录未找到"; exit 1; }

if [ -f .env ]; then
    echo "找到.env文件"
    if grep -q "NEO4J_URI" .env; then
        echo "已配置NEO4J_URI:"
        grep "NEO4J_URI" .env
    else
        echo "未配置NEO4J_URI"
    fi
    
    if grep -q "NEO4J_USER" .env; then
        echo "已配置NEO4J_USER:"
        grep "NEO4J_USER" .env
    else
        echo "未配置NEO4J_USER"
    fi
    
    if grep -q "NEO4J_PASSWORD" .env; then
        echo "已配置NEO4J_PASSWORD:"
        grep "NEO4J_PASSWORD" .env | sed 's/PASSWORD=.*/PASSWORD=***/'
    else
        echo "未配置NEO4J_PASSWORD"
    fi
else
    echo ".env文件不存在"
fi

echo ""
echo "=== [2] 测试到Neo4j服务器的网络连接 ==="
if timeout 5 bash -c "cat < /dev/null > /dev/tcp/${Neo4jServerIP}/${Neo4jPort}" 2>/dev/null; then
    echo "网络连接成功: ${Neo4jServerIP}:${Neo4jPort}"
else
    echo "网络连接失败: ${Neo4jServerIP}:${Neo4jPort}"
fi

echo ""
echo "=== [3] 检查Docker Compose配置 ==="
if [ -f docker-compose.yml ]; then
    docker-compose config 2>/dev/null | grep -i NEO4J | head -10 || echo "未找到Neo4j配置"
else
    echo "docker-compose.yml文件不存在"
fi
"@

$tempFile = "$env:TEMP\check-neo4j-$(Get-Date -Format 'yyyyMMdd-HHmmss').sh"
$checkScript | Out-File -FilePath $tempFile -Encoding utf8

Write-Host "执行检查..." -ForegroundColor Cyan

# 使用WSL的sshpass（如果可用）
$wslSshpass = wsl which sshpass 2>$null
if ($wslSshpass) {
    Write-Host "使用WSL sshpass执行..." -ForegroundColor Gray
    wsl bash -c "sshpass -p '${Password}' ssh -o StrictHostKeyChecking=no ${ServerUser}@${ServerIP} 'bash -s' < $tempFile"
} else {
    Write-Host "请手动执行以下命令:" -ForegroundColor Yellow
    Write-Host "ssh ${ServerUser}@${ServerIP}" -ForegroundColor White
    Write-Host "然后执行:" -ForegroundColor White
    Get-Content $tempFile | Write-Host -ForegroundColor Gray
}

Remove-Item $tempFile -Force -ErrorAction SilentlyContinue




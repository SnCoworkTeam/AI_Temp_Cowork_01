#!/usr/bin/env pwsh
# 使用密码检查Neo4j配置

param(
    [string]$ServerIP = "43.143.139.197",
    [string]$ServerUser = "ubuntu",
    [string]$Password = "Liu@bner1983",
    [string]$Neo4jServerIP = "43.143.90.179",
    [string]$Neo4jPort = "7687"
)

$ErrorActionPreference = "Stop"

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "检查应用服务器Neo4j配置" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "应用服务器: ${ServerUser}@${ServerIP}" -ForegroundColor Yellow
Write-Host "Neo4j服务器: ${Neo4jServerIP}:${Neo4jPort}" -ForegroundColor Yellow
Write-Host ""

# 创建临时脚本文件
$tempScript = "$env:TEMP\check-neo4j-$(Get-Date -Format 'yyyyMMdd-HHmmss').sh"
$scriptContent = @"
#!/bin/bash
echo "=========================================="
echo "Neo4j配置检查"
echo "=========================================="

# 检查1: 环境变量
echo ""
echo "[1] 检查.env文件中的Neo4j配置"
cd /opt/enterprise-ai-platform 2>/dev/null || cd /root/enterprise-ai-platform 2>/dev/null || cd ~/enterprise-ai-platform 2>/dev/null || { echo "项目目录未找到"; exit 1; }

if [ -f .env ]; then
    echo "找到.env文件"
    echo "=== Neo4j配置 ==="
    if grep -q "NEO4J_URI" .env; then
        echo "✅ 已配置NEO4J_URI:"
        grep "NEO4J_URI" .env
    else
        echo "❌ 未配置NEO4J_URI"
    fi
    
    if grep -q "NEO4J_USER" .env; then
        echo "✅ 已配置NEO4J_USER:"
        grep "NEO4J_USER" .env
    else
        echo "❌ 未配置NEO4J_USER"
    fi
    
    if grep -q "NEO4J_PASSWORD" .env; then
        echo "✅ 已配置NEO4J_PASSWORD:"
        grep "NEO4J_PASSWORD" .env | sed 's/PASSWORD=.*/PASSWORD=***/'
    else
        echo "❌ 未配置NEO4J_PASSWORD"
    fi
else
    echo "❌ .env文件不存在"
fi

# 检查2: 网络连接
echo ""
echo "[2] 测试到Neo4j服务器的网络连接"
if timeout 5 bash -c "cat < /dev/null > /dev/tcp/${Neo4jServerIP}/${Neo4jPort}" 2>/dev/null; then
    echo "✅ 网络连接成功: ${Neo4jServerIP}:${Neo4jPort}"
else
    echo "❌ 网络连接失败: ${Neo4jServerIP}:${Neo4jPort}"
    echo "   请检查防火墙和安全组设置"
fi

# 检查3: Docker Compose配置
echo ""
echo "[3] 检查Docker Compose配置"
if [ -f docker-compose.yml ]; then
    echo "找到docker-compose.yml文件"
    docker-compose config 2>/dev/null | grep -i NEO4J | head -10 || echo "未找到Neo4j配置"
else
    echo "docker-compose.yml文件不存在"
fi

# 检查4: 运行中的容器
echo ""
echo "[4] 检查运行中容器的环境变量"
for container in `$(docker ps --format "{{.Names}}" 2>/dev/null); do
    if docker exec `$container env 2>/dev/null | grep -q NEO4J; then
        echo "容器 `$container 包含Neo4j配置:"
        docker exec `$container env | grep NEO4J
    fi
done

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="
"@

$scriptContent | Out-File -FilePath $tempScript -Encoding utf8

# 使用Plink或SSH执行脚本
Write-Host "[1/2] 上传并执行检查脚本..." -ForegroundColor Cyan

# 检查是否有plink
$plinkPath = Get-Command plink -ErrorAction SilentlyContinue
if ($plinkPath) {
    Write-Host "使用Plink执行..." -ForegroundColor Gray
    # 使用plink执行
    $plinkCmd = "plink -ssh ${ServerUser}@${ServerIP} -pw ${Password} -batch `"bash -s`" < `"$tempScript`""
    Invoke-Expression $plinkCmd
} else {
    # 使用SSH，需要手动输入密码或使用expect
    Write-Host "使用SSH执行（需要手动输入密码）..." -ForegroundColor Yellow
    Write-Host "提示: 如果连接失败，请安装Plink (PuTTY) 或使用WSL" -ForegroundColor Gray
    
    # 尝试使用WSL的sshpass（如果可用）
    $wslSshpass = wsl which sshpass 2>$null
    if ($wslSshpass) {
        Write-Host "使用WSL sshpass执行..." -ForegroundColor Gray
        $wslCmd = "wsl sshpass -p '${Password}' ssh -o StrictHostKeyChecking=no ${ServerUser}@${ServerIP} 'bash -s' < `"$tempScript`""
        Invoke-Expression $wslCmd
    } else {
        # 使用expect脚本
        Write-Host "创建expect脚本..." -ForegroundColor Gray
        $expectScript = "$env:TEMP\ssh-expect-$(Get-Date -Format 'yyyyMMdd-HHmmss').exp"
        $expectContent = @"
#!/usr/bin/expect
set timeout 30
spawn ssh -o StrictHostKeyChecking=no ${ServerUser}@${ServerIP} "bash -s" < "$tempScript"
expect {
    "password:" {
        send "${Password}\r"
        exp_continue
    }
    "Password:" {
        send "${Password}\r"
        exp_continue
    }
    eof
}
"@
        $expectContent | Out-File -FilePath $expectScript -Encoding utf8
        
        $expectCmd = Get-Command expect -ErrorAction SilentlyContinue
        if ($expectCmd) {
            & expect $expectScript
        } else {
            Write-Host "`n无法自动执行，请手动执行以下命令:" -ForegroundColor Yellow
            Write-Host "ssh ${ServerUser}@${ServerIP}" -ForegroundColor White
            Write-Host "然后执行:" -ForegroundColor White
            Write-Host "bash < $tempScript" -ForegroundColor White
        }
    }
}

# 清理临时文件
Remove-Item $tempScript -Force -ErrorAction SilentlyContinue

Write-Host "`n检查完成" -ForegroundColor Green




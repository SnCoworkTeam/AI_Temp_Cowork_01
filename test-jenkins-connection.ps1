# 测试Jenkins服务器连接
param(
    [string]$Server = "1.117.62.202",
    [string]$KeyFile = ".\Jenkins.pem"
)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Jenkins服务器连接测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查密钥文件
if (-not (Test-Path $KeyFile)) {
    Write-Host "❌ 密钥文件不存在: $KeyFile" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 密钥文件存在: $KeyFile" -ForegroundColor Green

# 修复密钥权限
Write-Host "`n修复密钥文件权限..." -ForegroundColor Yellow
icacls $KeyFile /inheritance:r /grant:r "$env:USERNAME`:R" 2>&1 | Out-Null
Write-Host "✅ 权限已修复" -ForegroundColor Green

# 测试不同的用户名
$users = @("ubuntu", "root", "admin", "jenkins")

foreach ($user in $users) {
    Write-Host "`n测试用户: $user@$Server" -ForegroundColor Yellow
    $result = ssh -i $KeyFile -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o BatchMode=yes "$user@$Server" "echo '连接成功' && whoami && uname -a" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ 连接成功！" -ForegroundColor Green
        Write-Host "  用户信息:" -ForegroundColor Cyan
        Write-Host $result -ForegroundColor White
        
        # 如果连接成功，检查系统信息
        Write-Host "`n检查系统信息..." -ForegroundColor Yellow
        $sysInfo = ssh -i $KeyFile -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$user@$Server" @"
echo '=== 系统信息 ==='
uname -a
echo ''
echo '=== 操作系统 ==='
cat /etc/os-release | head -5
echo ''
echo '=== 内存和CPU ==='
free -h
echo "CPU核心: \$(nproc)"
echo ''
echo '=== 磁盘空间 ==='
df -h | head -6
echo ''
echo '=== Docker检查 ==='
/usr/bin/docker --version 2>&1 || echo 'Docker未安装'
docker ps 2>&1 | head -5
echo ''
echo '=== 已安装的应用 ==='
ls -lah /usr/bin/docker* 2>&1
echo ''
echo '=== 运行中的服务 ==='
systemctl list-units --type=service --state=running | grep -E 'docker|jenkins|nginx|apache' | head -10
"@ 2>&1
        
        Write-Host $sysInfo -ForegroundColor Green
        
        Write-Host "`n✅ 找到正确的用户: $user" -ForegroundColor Green
        Write-Host "可以使用以下命令连接:" -ForegroundColor Cyan
        Write-Host "  ssh -i $KeyFile $user@$Server" -ForegroundColor White
        break
    } else {
        Write-Host "  ❌ 连接失败" -ForegroundColor Red
        if ($result -match "Permission denied") {
            Write-Host "  原因: 权限被拒绝（用户名或密钥不正确）" -ForegroundColor Yellow
        } elseif ($result -match "Connection refused") {
            Write-Host "  原因: 连接被拒绝（SSH服务未运行或端口不对）" -ForegroundColor Yellow
        } elseif ($result -match "Connection timed out") {
            Write-Host "  原因: 连接超时（服务器不可达或防火墙阻止）" -ForegroundColor Yellow
        } else {
            Write-Host "  错误: $result" -ForegroundColor Gray
        }
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""


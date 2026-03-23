# Docker Hub部署方案配置脚本
# 帮助用户配置GitHub Actions + Docker Hub自动化部署

param(
    [string]$DockerHubUsername = "",
    [string]$DockerHubToken = "",
    [string]$ServerHost = "43.143.139.197",
    [string]$ServerUser = "root",
    [string]$SshKeyPath = "E:\enterprise-ai-platform\enterprise_ai_platform.pem"
)

Write-Host "=========================================="
Write-Host "Docker Hub自动化部署配置向导"
Write-Host "=========================================="
Write-Host ""

# 步骤1: 检查Docker Hub配置
Write-Host "[1/5] 检查Docker Hub配置..." -ForegroundColor Cyan

if (-not $DockerHubUsername) {
    $DockerHubUsername = Read-Host "请输入Docker Hub用户名"
}

if (-not $DockerHubToken) {
    Write-Host "请输入Docker Hub Access Token（创建方法：Docker Hub → Account Settings → Security → New Access Token）" -ForegroundColor Yellow
    $DockerHubToken = Read-Host "Docker Hub Token" -AsSecureString
    $DockerHubToken = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($DockerHubToken)
    )
}

Write-Host "✅ Docker Hub配置已收集" -ForegroundColor Green
Write-Host ""

# 步骤2: 检查SSH密钥
Write-Host "[2/5] 检查SSH密钥..." -ForegroundColor Cyan

if (-not (Test-Path $SshKeyPath)) {
    Write-Host "❌ SSH密钥文件不存在: $SshKeyPath" -ForegroundColor Red
    Write-Host "请提供正确的SSH密钥路径" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ SSH密钥文件存在: $SshKeyPath" -ForegroundColor Green
Write-Host ""

# 步骤3: 测试SSH连接
Write-Host "[3/5] 测试SSH连接..." -ForegroundColor Cyan

$sshCmd = "ssh -i `"$SshKeyPath`" -o StrictHostKeyChecking=no -o ConnectTimeout=5 ${ServerUser}@${ServerHost} 'echo SSH连接成功'"
try {
    $sshResult = Invoke-Expression $sshCmd 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ SSH连接成功" -ForegroundColor Green
    } else {
        Write-Host "❌ SSH连接失败: $sshResult" -ForegroundColor Red
        Write-Host "请检查：" -ForegroundColor Yellow
        Write-Host "  1. 服务器IP是否正确: $ServerHost" -ForegroundColor White
        Write-Host "  2. SSH密钥是否正确" -ForegroundColor White
        Write-Host "  3. 服务器是否可访问" -ForegroundColor White
        exit 1
    }
} catch {
    Write-Host "❌ SSH连接失败: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 步骤4: 生成GitHub Secrets配置说明
Write-Host "[4/5] 生成GitHub Secrets配置说明..." -ForegroundColor Cyan

$secretsGuide = @"
# GitHub Secrets配置清单

请在GitHub仓库中配置以下Secrets：

## 配置步骤

1. 进入GitHub仓库
2. 点击 Settings → Secrets and variables → Actions
3. 点击 New repository secret
4. 添加以下Secrets：

## Secrets列表

### DOCKER_HUB_USERNAME
- 值: $DockerHubUsername
- 说明: Docker Hub用户名

### DOCKER_HUB_TOKEN
- 值: [已隐藏，请手动输入]
- 说明: Docker Hub Access Token（Read & Write权限）
- 创建方法: Docker Hub → Account Settings → Security → New Access Token

### SSH_PRIVATE_KEY
- 值: [从文件读取]
- 说明: SSH私钥完整内容
- 文件路径: $SshKeyPath

### SERVER_HOST
- 值: $ServerHost
- 说明: 服务器IP地址

### SERVER_USER
- 值: $ServerUser
- 说明: 服务器用户名

## 如何获取SSH_PRIVATE_KEY

在PowerShell中执行：
```powershell
Get-Content "$SshKeyPath" | Out-String
```

复制完整输出（包括 -----BEGIN 和 -----END 行）
"@

$secretsGuidePath = "docs/deployment/github-secrets-config.md"
$secretsGuide | Out-File -FilePath $secretsGuidePath -Encoding UTF8
Write-Host "✅ 配置说明已生成: $secretsGuidePath" -ForegroundColor Green
Write-Host ""

# 步骤5: 生成服务器初始化脚本
Write-Host "[5/5] 生成服务器初始化脚本..." -ForegroundColor Cyan

$serverInitScript = @"
#!/bin/bash
# 服务器端初始化脚本
# 在服务器上执行此脚本完成初始化

set -e

echo "=========================================="
echo "服务器端初始化"
echo "=========================================="

# 创建项目目录
echo "[1/6] 创建项目目录..."
mkdir -p /opt/enterprise-ai-platform
cd /opt/enterprise-ai-platform
echo "✅ 目录已创建"

# 初始化Git仓库（可选）
echo ""
echo "[2/6] 初始化Git仓库..."
if [ ! -d .git ]; then
    git init
    git remote add origin https://github.com/PMLiuyubin/enterprise-ai-platform.git
    git pull origin main
    echo "✅ Git仓库已初始化"
else
    echo "⚠️ Git仓库已存在，跳过"
fi

# 登录Docker Hub
echo ""
echo "[3/6] 配置Docker Hub登录..."
echo "请手动执行: docker login"
echo "输入Docker Hub用户名和密码/Token"
echo "⚠️ 需要手动完成"

# 创建生产环境变量文件
echo ""
echo "[4/6] 创建生产环境变量文件..."
if [ ! -f .env.prod ]; then
    cp .env.example .env.prod 2>/dev/null || echo "# 生产环境变量" > .env.prod
    echo "✅ .env.prod已创建"
    echo "⚠️ 请编辑 .env.prod 配置生产环境变量"
else
    echo "⚠️ .env.prod已存在"
fi

# 创建docker-compose.prod.yml（如果不存在）
echo ""
echo "[5/6] 检查docker-compose.prod.yml..."
if [ ! -f docker-compose.prod.yml ]; then
    echo "⚠️ docker-compose.prod.yml不存在，需要从GitHub获取"
else
    echo "✅ docker-compose.prod.yml已存在"
fi

# 设置环境变量
echo ""
echo "[6/6] 设置环境变量..."
export DOCKER_HUB_USERNAME="$DockerHubUsername"
export IMAGE_TAG="latest"

echo ""
echo "=========================================="
echo "✅ 服务器初始化完成"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 编辑 .env.prod 配置生产环境变量"
echo "2. 确保 docker-compose.prod.yml 已上传"
echo "3. 在GitHub Actions中触发部署"
echo "=========================================="
"@

$serverInitScriptPath = "scripts/server-init-dockerhub.sh"
$serverInitScript | Out-File -FilePath $serverInitScriptPath -Encoding UTF8
Write-Host "✅ 服务器初始化脚本已生成: $serverInitScriptPath" -ForegroundColor Green
Write-Host ""

# 总结
Write-Host "=========================================="
Write-Host "配置完成！"
Write-Host "=========================================="
Write-Host ""
Write-Host "下一步操作：" -ForegroundColor Cyan
Write-Host "1. 在GitHub仓库中配置Secrets（参考: $secretsGuidePath）" -ForegroundColor White
Write-Host "2. 将server-init-dockerhub.sh上传到服务器并执行" -ForegroundColor White
Write-Host "3. 在GitHub Actions中触发首次部署" -ForegroundColor White
Write-Host ""
Write-Host "GitHub Secrets配置：" -ForegroundColor Yellow
Write-Host "  DOCKER_HUB_USERNAME: $DockerHubUsername" -ForegroundColor White
Write-Host "  DOCKER_HUB_TOKEN: [请手动输入]" -ForegroundColor White
Write-Host "  SSH_PRIVATE_KEY: [从 $SshKeyPath 读取]" -ForegroundColor White
Write-Host "  SERVER_HOST: $ServerHost" -ForegroundColor White
Write-Host "  SERVER_USER: $ServerUser" -ForegroundColor White
Write-Host ""





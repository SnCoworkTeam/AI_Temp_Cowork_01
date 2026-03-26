# PowerShell 脚本：自动上传代码、部署并启动调试
# 使用方法: .\scripts\deployment\auto-deploy-and-debug.ps1

param(
    [string]$ServerIP = "43.143.139.197",
    [string]$ServerUser = "ubuntu",
    [string]$KeyPath = "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem",
    [string]$RemotePath = "/opt/enterprise-ai-platform",
    [string]$Environment = "production",
    [switch]$SkipUpload = $false
)

# 颜色输出函数
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Cyan "=========================================="
Write-ColorOutput Cyan "企业AI平台 - 自动部署和调试脚本"
Write-ColorOutput Cyan "=========================================="
Write-Output "服务器: $ServerUser@$ServerIP"
Write-Output "远程路径: $RemotePath"
Write-Output ""

# 检查密钥文件
$ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$ProjectKeyPath = Join-Path $ProjectRoot "enterprise_ai_platform.pem"

if (-not (Test-Path $KeyPath)) {
    if (Test-Path $ProjectKeyPath) {
        Write-ColorOutput Green "✅ 在项目根目录找到密钥文件"
        $KeyPath = $ProjectKeyPath
    } else {
        Write-ColorOutput Red "❌ 未找到密钥文件: $KeyPath"
        Write-Output "请将 enterprise_ai_platform.pem 放置在以下位置之一："
        Write-Output "  1. $env:USERPROFILE\.ssh\enterprise_ai_platform.pem"
        Write-Output "  2. $ProjectKeyPath"
        exit 1
    }
}

# 构建 SSH 和 SCP 命令
$sshBase = "ssh -i `"$KeyPath`" -o StrictHostKeyChecking=no -o ConnectTimeout=10"
$scpBase = "scp -i `"$KeyPath`" -o StrictHostKeyChecking=no -o ConnectTimeout=10"
$sshCmd = "$sshBase $ServerUser@${ServerIP}"

# 步骤1: 上传代码
if (-not $SkipUpload) {
    Write-ColorOutput Blue "[1/5] 上传代码到服务器..."
    & "$PSScriptRoot\upload-to-server.ps1" -ServerIP $ServerIP -ServerUser $ServerUser -KeyPath $KeyPath -RemotePath $RemotePath
    
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput Red "❌ 代码上传失败"
        exit 1
    }
    Write-ColorOutput Green "✅ 代码上传完成"
} else {
    Write-ColorOutput Yellow "[1/5] 跳过代码上传"
}

# 步骤2: 检查并初始化服务器环境
Write-ColorOutput Blue "[2/5] 检查服务器环境..."
$dockerCheck = & $sshCmd "command -v docker > /dev/null 2>&1 && echo 'installed' || echo 'not_installed'"
if ($dockerCheck -eq "not_installed") {
    Write-ColorOutput Yellow "⚠️  Docker 未安装，开始初始化..."
    $setupScript = Join-Path $PSScriptRoot "setup-server.sh"
    if (Test-Path $setupScript) {
        & $scpBase $setupScript "$ServerUser@${ServerIP}:/tmp/setup-server.sh"
        & $sshCmd "chmod +x /tmp/setup-server.sh && sudo bash /tmp/setup-server.sh --git-url https://github.com/PMLiuyubin/enterprise-ai-platform.git"
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput Red "❌ 服务器初始化失败"
            exit 1
        }
    }
} else {
    Write-ColorOutput Green "✅ Docker 已安装"
}

# 步骤3: 检查并创建环境变量文件
Write-ColorOutput Blue "[3/5] 检查环境变量配置..."
$envFile = ".env.$Environment"
$envCheck = & $sshCmd "test -f $RemotePath/$envFile && echo 'exists' || echo 'not_exists'"
if ($envCheck -eq "not_exists") {
    Write-ColorOutput Yellow "⚠️  环境变量文件不存在，创建默认配置..."
    & $sshCmd "cd $RemotePath && if [ -f env.example ]; then cp env.example $envFile; fi"
    Write-ColorOutput Yellow "⚠️  请确保 .env.$Environment 文件已正确配置"
    Write-Output "  可以在 VS Code 中连接到服务器后编辑: $RemotePath/$envFile"
} else {
    Write-ColorOutput Green "✅ 环境变量文件已存在"
}

# 步骤4: 停止现有服务并启动
Write-ColorOutput Blue "[4/5] 停止现有服务并重新部署..."
$stopCmd = "cd $RemotePath; docker compose down 2>&1 || docker-compose down 2>&1 || true"
& $sshCmd $stopCmd | Out-Null

Write-Output "启动数据库服务..."
$dbCmd = "cd $RemotePath; if [ -f docker-compose.db.yml ]; then docker compose -f docker-compose.db.yml up -d 2>&1 || docker-compose -f docker-compose.db.yml up -d 2>&1; fi"
& $sshCmd $dbCmd

Write-Output "等待数据库就绪..."
Start-Sleep -Seconds 5

Write-Output "构建并启动所有服务..."
$startCmd = "cd $RemotePath; docker compose up -d --build 2>&1 || docker-compose up -d --build 2>&1"
$startOutput = & $sshCmd $startCmd
$startOutput | Write-Output

if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "❌ 服务启动失败"
    Write-Output "查看详细错误信息..."
    & $sshCmd "cd $RemotePath; docker compose logs --tail=50 2>&1 || docker-compose logs --tail=50 2>&1" | Write-Output
    exit 1
}

# 步骤5: 检查服务状态并调试
Write-ColorOutput Blue "[5/5] 检查服务状态并调试..."
Start-Sleep -Seconds 10

Write-Output ""
Write-ColorOutput Cyan "=========================================="
Write-ColorOutput Cyan "服务状态检查"
Write-ColorOutput Cyan "=========================================="

# 检查容器状态
$psCmd = "cd $RemotePath; docker compose ps 2>&1 || docker-compose ps 2>&1"
$psOutput = & $sshCmd $psCmd
$psOutput | Write-Output

# 检查每个服务的健康状态
Write-Output ""
Write-ColorOutput Cyan "健康检查..."
$services = @(
    @{Port=8001; Name="MCP Gateway"; Path="/api/health"},
    @{Port=8002; Name="Workflow Engine"; Path="/api/health"},
    @{Port=8003; Name="Auth Service"; Path="/health"},
    @{Port=8004; Name="Knowledge Base"; Path="/api/health"},
    @{Port=3000; Name="Web UI"; Path="/api/health"}
)

foreach ($service in $services) {
    $healthCheck = & $sshCmd "curl -s -o /dev/null -w '%{http_code}' http://localhost:$($service.Port)$($service.Path) 2>&1 || echo '000'"
    if ($healthCheck -eq "200") {
        Write-ColorOutput Green "✅ $($service.Name) (端口 $($service.Port)) - 健康"
    } else {
        Write-ColorOutput Red "❌ $($service.Name) (端口 $($service.Port)) - 未响应 (HTTP $healthCheck)"
    }
}

# 检查错误日志
Write-Output ""
Write-ColorOutput Cyan "检查错误日志..."
$errorLogs = & $sshCmd "cd $RemotePath; docker compose logs --tail=20 2>&1 | grep -i error || docker-compose logs --tail=20 2>&1 | grep -i error || echo '未发现错误'"
if ($errorLogs -and $errorLogs -ne "未发现错误") {
    Write-ColorOutput Red "发现错误日志:"
    $errorLogs | Write-Output
} else {
    Write-ColorOutput Green "✅ 未发现明显错误"
}

# 显示各服务日志（最后10行）
Write-Output ""
Write-ColorOutput Cyan "各服务最新日志:"
$servicesList = @("redis", "mcp-gateway", "workflow-engine", "auth-service", "knowledge-base", "web-ui")
foreach ($svc in $servicesList) {
    Write-Output ""
    Write-ColorOutput Yellow "--- $svc ---"
    $svcLogs = & $sshCmd "cd $RemotePath; docker compose logs --tail=5 $svc 2>&1 || docker-compose logs --tail=5 $svc 2>&1 || echo '无法获取日志'"
    $svcLogs | Write-Output
}

# 显示部署信息
Write-Output ""
Write-ColorOutput Green "=========================================="
Write-ColorOutput Green "✅ 部署完成！"
Write-ColorOutput Green "=========================================="
Write-Output ""
Write-Output "服务地址:"
Write-Output "  - MCP Gateway:      http://$ServerIP:8001"
Write-Output "  - Workflow Engine:   http://$ServerIP:8002"
Write-Output "  - Auth Service:      http://$ServerIP:8003"
Write-Output "  - Knowledge Base:    http://$ServerIP:8004"
Write-Output "  - Web UI:            http://$ServerIP:3000"
Write-Output ""
Write-Output "常用调试命令:"
Write-Output "  查看所有日志: ssh -i `"$KeyPath`" $ServerUser@${ServerIP} 'cd $RemotePath; docker compose logs -f'"
Write-Output "  查看特定服务: ssh -i `"$KeyPath`" $ServerUser@${ServerIP} 'cd $RemotePath; docker compose logs -f <service-name>'"
Write-Output "  重启服务:     ssh -i `"$KeyPath`" $ServerUser@${ServerIP} 'cd $RemotePath; docker compose restart'"
Write-Output "  停止服务:     ssh -i `"$KeyPath`" $ServerUser@${ServerIP} 'cd $RemotePath; docker compose down'"
Write-Output ""


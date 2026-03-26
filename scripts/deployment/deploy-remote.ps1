# PowerShell 脚本：一键部署到远程服务器
# 使用方法: .\scripts\deployment\deploy-remote.ps1

param(
    [string]$ServerIP = "43.143.139.197",
    [string]$ServerUser = "ubuntu",
    [string]$KeyPath = "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem",
    [string]$RemotePath = "/opt/enterprise-ai-platform",
    [string]$Environment = "production",
    [switch]$SkipUpload = $false,
    [switch]$SkipSetup = $false
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
Write-ColorOutput Cyan "企业AI平台 - 远程一键部署脚本"
Write-ColorOutput Cyan "=========================================="
Write-Output "服务器: $ServerUser@$ServerIP"
Write-Output "远程路径: $RemotePath"
Write-Output "环境: $Environment"
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

# 构建 SSH 命令前缀
$sshCmd = "ssh -i `"$KeyPath`" -o StrictHostKeyChecking=no $ServerUser@${ServerIP}"

# 步骤1: 上传代码
if (-not $SkipUpload) {
    Write-ColorOutput Blue "[1/4] 上传代码到服务器..."
    & "$PSScriptRoot\upload-to-server.ps1" -ServerIP $ServerIP -ServerUser $ServerUser -KeyPath $KeyPath -RemotePath $RemotePath
    
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput Red "❌ 代码上传失败"
        exit 1
    }
} else {
    Write-ColorOutput Yellow "[1/4] 跳过代码上传（--SkipUpload）"
}

# 步骤2: 初始化服务器（如果需要）
if (-not $SkipSetup) {
    Write-ColorOutput Blue "[2/4] 检查服务器环境..."
    
    # 检查 Docker
    $dockerCheckResult = & $sshCmd "command -v docker" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput Yellow "⚠️  Docker 未安装，开始初始化服务器..."
        
        # 上传 setup-server.sh 并执行
        Write-Output "上传初始化脚本..."
        $setupScript = Join-Path $PSScriptRoot "setup-server.sh"
        if (Test-Path $setupScript) {
            & scp -i "`"$KeyPath`" -o StrictHostKeyChecking=no $setupScript "$ServerUser@${ServerIP}:/tmp/setup-server.sh"
            if ($LASTEXITCODE -eq 0) {
                & $sshCmd "chmod +x /tmp/setup-server.sh"
                if ($LASTEXITCODE -eq 0) {
                    & $sshCmd "sudo bash /tmp/setup-server.sh --git-url https://github.com/PMLiuyubin/enterprise-ai-platform.git"
                    if ($LASTEXITCODE -eq 0) {
                        Write-ColorOutput Green "✅ 服务器初始化完成"
                    } else {
                        Write-ColorOutput Red "❌ 服务器初始化失败"
                        exit 1
                    }
                } else {
                    Write-ColorOutput Red "❌ 无法设置脚本执行权限"
                    exit 1
                }
            } else {
                Write-ColorOutput Red "❌ 无法上传初始化脚本"
                exit 1
            }
        } else {
            Write-ColorOutput Red "❌ 未找到 setup-server.sh"
            exit 1
        }
    } else {
        Write-ColorOutput Green "✅ Docker 已安装"
    }
} else {
    Write-ColorOutput Yellow "[2/4] 跳过服务器初始化（--SkipSetup）"
}

# 步骤3: 配置环境变量（如果需要）
Write-ColorOutput Blue "[3/4] 检查环境变量配置..."
$envCheckCmd = "test -f $RemotePath/.env.$Environment"
$envCheckResult = & $sshCmd $envCheckCmd 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Yellow "⚠️  环境变量文件不存在，创建默认配置..."
    $createEnvCmd = 'cd ' + $RemotePath + '; test -f env.example && cp env.example .env.' + $Environment + ' || echo "env.example not found"'
    & $sshCmd $createEnvCmd
    Write-ColorOutput Yellow "⚠️  请手动编辑 .env.$Environment 文件并配置必要的环境变量"
    Write-Output "  在 VS Code 中连接到服务器后编辑: $RemotePath/.env.$Environment"
    Write-Output ""
    $continue = Read-Host "是否继续部署？(Y/n)"
    if ($continue -eq "n" -or $continue -eq "N") {
        Write-ColorOutput Yellow "部署已取消"
        exit 0
    }
} else {
    Write-ColorOutput Green "✅ 环境变量文件已存在"
}

# 步骤4: 执行部署
Write-ColorOutput Blue "[4/4] 执行部署脚本..."
$deployCmd = "cd $RemotePath; bash scripts/deployment/deploy-server.sh --env $Environment"
& $sshCmd $deployCmd

if ($LASTEXITCODE -eq 0) {
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
    Write-Output "查看日志:"
    $logCmd = "ssh -i `"$KeyPath`" $ServerUser@${ServerIP} 'cd $RemotePath; docker compose logs -f'"
    Write-Output "  $logCmd"
    Write-Output ""
} else {
    Write-ColorOutput Red "❌ 部署失败，请检查错误信息"
    exit 1
}


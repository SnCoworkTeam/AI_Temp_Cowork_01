# 检查服务器代码状态脚本
# 检查代码是否已上传到服务器 43.143.139.197

$ErrorActionPreference = "Stop"

Write-Host "=========================================="
Write-Host "检查服务器代码状态"
Write-Host "=========================================="
Write-Host ""

$SERVER_HOST = "43.143.139.197"
$SERVER_USER = "ubuntu"
$PROJECT_DIR = "/opt/enterprise-ai-platform"
$SSH_KEY = "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem"

# 检查SSH密钥文件
if (-not (Test-Path $SSH_KEY)) {
    Write-Host "警告: SSH密钥文件不存在: $SSH_KEY" -ForegroundColor Yellow
    Write-Host "尝试使用密码连接..." -ForegroundColor Yellow
    $USE_PASSWORD = $true
} else {
    $USE_PASSWORD = $false
    Write-Host "找到SSH密钥文件: $SSH_KEY" -ForegroundColor Green
}

Write-Host ""
Write-Host "连接到服务器: $SERVER_USER@$SERVER_HOST" -ForegroundColor Cyan
Write-Host "项目目录: $PROJECT_DIR" -ForegroundColor Cyan
Write-Host ""

# 检查本地Git状态
Write-Host "--- 本地Git状态 ---" -ForegroundColor Yellow
$localCommit = git log -1 --oneline
Write-Host "最新提交: $localCommit" -ForegroundColor Green

$localBranch = git branch --show-current
Write-Host "当前分支: $localBranch" -ForegroundColor Green

$remoteStatus = git status -sb
Write-Host "远程状态: $remoteStatus" -ForegroundColor Green

Write-Host ""

# 检查服务器代码状态
Write-Host "--- 服务器代码状态 ---" -ForegroundColor Yellow

try {
    if ($USE_PASSWORD) {
        # 使用密码连接（需要手动输入密码）
        $password = "Liu@bner1983"
        $commands = @"
cd $PROJECT_DIR 2>/dev/null || { echo 'ERROR: 项目目录不存在'; exit 1; }
echo '=== Git状态 ==='
git status -sb 2>/dev/null || echo 'Git未初始化'
echo ''
echo '=== 最新提交 ==='
git log -1 --oneline 2>/dev/null || echo '无提交记录'
echo ''
echo '=== 当前分支 ==='
git branch --show-current 2>/dev/null || echo '无分支信息'
echo ''
echo '=== 远程仓库 ==='
git remote -v 2>/dev/null || echo '无远程仓库'
echo ''
echo '=== 文件修改时间 ==='
ls -la | head -5
"@
        
        # 使用sshpass或直接ssh（Windows需要特殊处理）
        Write-Host "尝试使用SSH连接..." -ForegroundColor Cyan
        ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$SERVER_USER@$SERVER_HOST" $commands
    } else {
        # 使用密钥文件连接
        $commands = @"
cd $PROJECT_DIR 2>/dev/null || { echo 'ERROR: 项目目录不存在'; exit 1; }
echo '=== Git状态 ==='
git status -sb 2>/dev/null || echo 'Git未初始化'
echo ''
echo '=== 最新提交 ==='
git log -1 --oneline 2>/dev/null || echo '无提交记录'
echo ''
echo '=== 当前分支 ==='
git branch --show-current 2>/dev/null || echo '无分支信息'
echo ''
echo '=== 远程仓库 ==='
git remote -v 2>/dev/null || echo '无远程仓库'
echo ''
echo '=== 文件修改时间 ==='
ls -la | head -5
"@
        
        ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$SERVER_USER@$SERVER_HOST" $commands
    }
    
    Write-Host ""
    Write-Host "=========================================="
    Write-Host "检查完成" -ForegroundColor Green
    Write-Host "=========================================="
    
} catch {
    Write-Host ""
    Write-Host "错误: 无法连接到服务器" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "请检查:" -ForegroundColor Yellow
    Write-Host "1. 服务器是否可访问 (ping $SERVER_HOST)" -ForegroundColor Yellow
    Write-Host "2. SSH密钥文件是否正确" -ForegroundColor Yellow
    Write-Host "3. 服务器用户名是否正确" -ForegroundColor Yellow
    exit 1
}

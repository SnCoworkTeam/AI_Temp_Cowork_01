# 简单检查服务器代码状态
$SERVER = "ubuntu@43.143.139.197"
$PROJECT_DIR = "/opt/enterprise-ai-platform"
$SSH_KEY = "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "检查服务器代码状态" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查本地状态
Write-Host "[本地] 最新提交:" -ForegroundColor Yellow
git log -1 --oneline
Write-Host ""

# 检查SSH密钥
if (Test-Path $SSH_KEY) {
    Write-Host "[服务器] 连接中..." -ForegroundColor Yellow
    
    $checkCmd = "cd $PROJECT_DIR && echo '=== Git状态 ===' && git log -1 --oneline 2>&1 && echo '' && git status -sb 2>&1 && echo '' && echo '=== 检查文件 ===' && ls -la docs/testing/test-nameerror-batch-fix-complete.md scripts/fix-all-nameerrors.py 2>&1"
    
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SERVER $checkCmd
} else {
    Write-Host "[警告] SSH密钥文件不存在: $SSH_KEY" -ForegroundColor Red
    Write-Host ""
    Write-Host "请手动执行以下命令检查:" -ForegroundColor Yellow
    Write-Host "  ssh -i $SSH_KEY $SERVER" -ForegroundColor Cyan
    Write-Host "  cd $PROJECT_DIR" -ForegroundColor Cyan
    Write-Host "  git log -1 --oneline" -ForegroundColor Cyan
    Write-Host "  git status" -ForegroundColor Cyan
}





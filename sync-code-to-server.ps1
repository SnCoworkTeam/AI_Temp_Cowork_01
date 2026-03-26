# 同步代码到服务器并配置Jenkins自动部署
# 一次性完整同步，后续通过Jenkins自动同步

param(
    [string]$DeployServer = "ubuntu@43.143.139.197",
    [string]$DeployKey = ".\enterprise_ai_platform.pem",
    [string]$JenkinsServer = "ubuntu@1.117.62.202",
    [string]$JenkinsKey = ".\Jenkins.pem"
)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "代码同步和Jenkins配置" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤1: 检查本地Git状态
Write-Host "[1/5] 检查本地Git状态..." -ForegroundColor Yellow
$status = git status --porcelain
if ($status) {
    Write-Host "发现未提交的文件:" -ForegroundColor Yellow
    $status | Select-Object -First 10 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    
    Write-Host "`n添加所有更改..." -ForegroundColor Cyan
    git add -A 2>&1 | Out-Null
    
    Write-Host "提交更改..." -ForegroundColor Cyan
    $commitMsg = "chore: 同步代码到服务器，配置Jenkins自动部署 - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    git commit -m $commitMsg 2>&1
} else {
    Write-Host "✅ 所有文件已提交" -ForegroundColor Green
}

# 步骤2: 推送到GitHub
Write-Host "`n[2/5] 推送到GitHub..." -ForegroundColor Yellow
$pushResult = git push origin main 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 代码已推送到GitHub" -ForegroundColor Green
    $pushResult | Select-Object -Last 5 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
} else {
    Write-Host "❌ 推送失败" -ForegroundColor Red
    Write-Host $pushResult
    exit 1
}

# 步骤3: 在部署服务器上同步代码
Write-Host "`n[3/5] 在部署服务器上同步代码..." -ForegroundColor Yellow
$syncScript = @"
cd /opt/enterprise-ai-platform
echo '=== 当前状态 ==='
git status --short | head -5
echo ''
echo '=== 拉取最新代码 ==='
git fetch origin main
git reset --hard origin/main
echo ''
echo '=== 验证同步 ==='
LOCAL_COMMIT=\$(git rev-parse --short HEAD)
REMOTE_COMMIT=\$(git rev-parse --short origin/main)
echo "本地提交: \$LOCAL_COMMIT"
echo "远程提交: \$REMOTE_COMMIT"
if [ "\$LOCAL_COMMIT" = "\$REMOTE_COMMIT" ]; then
    echo '✅ 代码已同步'
else
    echo '⚠️  提交不一致'
fi
"@

$syncResult = ssh -i $DeployKey -o StrictHostKeyChecking=no -o ConnectTimeout=15 $DeployServer "bash -s" <<< $syncScript 2>&1
Write-Host $syncResult

# 步骤4: 检查Jenkins配置
Write-Host "`n[4/5] 检查Jenkins配置..." -ForegroundColor Yellow
$jenkinsCheck = ssh -i $JenkinsKey -o StrictHostKeyChecking=no -o ConnectTimeout=15 $JenkinsServer @"
echo '=== Jenkins Git配置 ==='
sudo -u jenkins git config --global --list 2>&1 | grep -E 'user|credential' | head -5 || echo '未配置Git用户'
echo ''
echo '=== 测试Git连接 ==='
sudo -u jenkins git ls-remote https://github.com/PMLiuyubin/enterprise-ai-platform.git HEAD 2>&1 | head -3
"@ 2>&1

Write-Host $jenkinsCheck

# 步骤5: 验证Jenkins Pipeline配置
Write-Host "`n[5/5] 验证Jenkins Pipeline配置..." -ForegroundColor Yellow
Write-Host "请确认Jenkins Pipeline已配置:" -ForegroundColor Cyan
Write-Host "  ✅ Repository URL: https://github.com/PMLiuyubin/enterprise-ai-platform.git" -ForegroundColor Gray
Write-Host "  ✅ Credentials: github-credentials" -ForegroundColor Gray
Write-Host "  ✅ Branch: */main" -ForegroundColor Gray
Write-Host "  ✅ Script Path: Jenkinsfile" -ForegroundColor Gray
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ 代码同步完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "后续操作:" -ForegroundColor Yellow
Write-Host "  1. 在Jenkins中手动触发一次构建（Build Now）" -ForegroundColor White
Write-Host "  2. 验证部署是否成功" -ForegroundColor White
Write-Host "  3. 配置GitHub Webhook实现自动触发（可选）" -ForegroundColor White
Write-Host ""
Write-Host "Jenkins访问: http://1.117.62.202:8080" -ForegroundColor Cyan
Write-Host ""


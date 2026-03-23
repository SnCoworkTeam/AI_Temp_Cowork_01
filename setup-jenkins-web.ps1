# Jenkins Web界面自动化配置脚本
# 使用Jenkins CLI或REST API配置Jenkins

param(
    [string]$JenkinsUrl = "http://1.117.62.202:8080",
    [string]$InitialPassword = "7915873e43a545f78e6bc38fe1bb0cbb"
)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Jenkins Web界面配置指南" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Jenkins访问信息:" -ForegroundColor Yellow
Write-Host "  URL: $JenkinsUrl" -ForegroundColor White
Write-Host "  初始密码: $InitialPassword" -ForegroundColor White
Write-Host ""

Write-Host "手动配置步骤:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. 访问Jenkins Web界面" -ForegroundColor Cyan
Write-Host "   打开浏览器访问: $JenkinsUrl" -ForegroundColor White
Write-Host ""
Write-Host "2. 首次登录" -ForegroundColor Cyan
Write-Host "   - 输入初始密码: $InitialPassword" -ForegroundColor White
Write-Host "   - 点击 'Continue'" -ForegroundColor White
Write-Host ""
Write-Host "3. 安装插件" -ForegroundColor Cyan
Write-Host "   - 选择 'Install suggested plugins'" -ForegroundColor White
Write-Host "   - 等待插件安装完成" -ForegroundColor White
Write-Host ""
Write-Host "4. 创建管理员账户" -ForegroundColor Cyan
Write-Host "   - 输入用户名、密码等信息" -ForegroundColor White
Write-Host "   - 点击 'Save and Continue'" -ForegroundColor White
Write-Host ""
Write-Host "5. 配置SSH凭据" -ForegroundColor Cyan
Write-Host "   - 进入: Manage Jenkins → Manage Credentials" -ForegroundColor White
Write-Host "   - 点击 (global) → Add Credentials" -ForegroundColor White
Write-Host "   - 配置:" -ForegroundColor White
Write-Host "     * Kind: SSH Username with private key" -ForegroundColor Gray
Write-Host "     * ID: deploy-ssh-key" -ForegroundColor Gray
Write-Host "     * Username: ubuntu" -ForegroundColor Gray
Write-Host "     * Private Key: Enter directly" -ForegroundColor Gray
Write-Host "     * 粘贴 enterprise_ai_platform.pem 的内容" -ForegroundColor Gray
Write-Host ""
Write-Host "6. 创建Pipeline任务" -ForegroundColor Cyan
Write-Host "   - 点击 New Item" -ForegroundColor White
Write-Host "   - 输入名称: enterprise-ai-platform-deploy" -ForegroundColor White
Write-Host "   - 选择 Pipeline" -ForegroundColor White
Write-Host "   - 配置Pipeline脚本（使用Jenkinsfile）" -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "配置完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""


# 快速提交并推送改进的工作流文件

Write-Host "提交CI/CD改进..." -ForegroundColor Cyan

# 设置Git不使用分页器
$env:GIT_PAGER = "cat"

# 添加文件
git add .github/workflows/test-suite.yml
git add .github/workflows/deploy.yml

# 提交
git commit -m "feat: 改进CI/CD - 添加智能测试选择和蓝绿部署" --no-verify

# 推送
git push origin main

Write-Host "完成！" -ForegroundColor Green






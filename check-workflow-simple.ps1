# 简单的工作流状态检查（无emoji）

param(
    [string]$RunId = "19901535278"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "检查CI/CD工作流状态" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "运行ID: $RunId" -ForegroundColor Yellow
Write-Host ""

# 查看运行状态
Write-Host "获取运行状态..." -ForegroundColor Yellow
gh run view $RunId

Write-Host ""
Write-Host "在浏览器中查看详细日志:" -ForegroundColor Cyan
Write-Host "https://github.com/PMLiuyubin/enterprise-ai-platform/actions/runs/$RunId" -ForegroundColor Yellow

Write-Host ""
Write-Host "实时查看日志命令:" -ForegroundColor Cyan
Write-Host "gh run watch $RunId" -ForegroundColor Gray






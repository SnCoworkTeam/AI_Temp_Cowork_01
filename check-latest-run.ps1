# 查看最新工作流运行的详细信息

Write-Host "获取最新运行详情..." -ForegroundColor Yellow

# 获取最新的运行ID
$runId = gh run list --workflow="deploy.yml" --limit 1 --json databaseId --jq '.[0].databaseId'

if ($runId) {
    Write-Host "运行ID: $runId" -ForegroundColor Green
    Write-Host ""
    Write-Host "查看运行详情..." -ForegroundColor Yellow
    gh run view $runId
    
    Write-Host ""
    Write-Host "查看失败步骤..." -ForegroundColor Yellow
    gh run view $runId --log | Select-String -Pattern "Error|Failed|failed|error" -Context 2,2 | Select-Object -First 20
    
    Write-Host ""
    Write-Host "在浏览器中打开:" -ForegroundColor Cyan
    Write-Host "https://github.com/PMLiuyubin/enterprise-ai-platform/actions/runs/$runId" -ForegroundColor Yellow
} else {
    Write-Host "未找到运行记录" -ForegroundColor Red
}






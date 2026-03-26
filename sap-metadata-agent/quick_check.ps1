# 快速检查构建进度
Write-Host "`n检查构建进度..." -ForegroundColor Cyan

# 检查Python进程
$python = Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*python*"}
if ($python) {
    $runtime = (Get-Date) - $python.StartTime
    Write-Host "[运行中] 构建脚本 (运行了 $([math]::Round($runtime.TotalMinutes, 1)) 分钟)" -ForegroundColor Green
} else {
    Write-Host "[已停止] 构建脚本未运行" -ForegroundColor Yellow
}

# 检查数据资产
try {
    $url = "http://localhost:8005/api/data-assets?limit=1&include_total=True"
    $r = Invoke-WebRequest -Uri $url -TimeoutSec 5
    $total = $r.Headers['X-Total-Count']
    Write-Host "数据资产总数: $total" -ForegroundColor White
} catch {
    Write-Host "无法获取数据资产总数" -ForegroundColor Red
}

Write-Host "`n提示: 查看构建脚本控制台窗口查看详细进度" -ForegroundColor Yellow


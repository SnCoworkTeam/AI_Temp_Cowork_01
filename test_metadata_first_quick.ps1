# 快速测试元数据前置意图识别功能（PowerShell版本）

Write-Host "==========================================" -ForegroundColor Green
Write-Host "元数据前置意图识别快速测试" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# 测试邮件发送意图
Write-Host "`n测试1: 邮件发送意图识别" -ForegroundColor Yellow
$emailResponse = Invoke-RestMethod -Uri "http://localhost:8010/api/v1/intelligent" `
    -Method POST `
    -ContentType "application/json" `
    -Body (@{
        message = "发送邮件给yubin.liu@pcitc.com，主题是会议通知"
        user_id = "test_user"
    } | ConvertTo-Json)

Write-Host "任务类型: $($emailResponse.intent_analysis.task_type)" -ForegroundColor Cyan
Write-Host "置信度: $($emailResponse.intent_analysis.confidence)" -ForegroundColor Cyan
Write-Host "需要的工具: $($emailResponse.intent_analysis.required_tools -join ', ')" -ForegroundColor Cyan

Start-Sleep -Seconds 2

# 测试SAP查询意图
Write-Host "`n测试2: SAP查询意图识别" -ForegroundColor Yellow
$sapResponse = Invoke-RestMethod -Uri "http://localhost:8010/api/v1/intelligent" `
    -Method POST `
    -ContentType "application/json" `
    -Body (@{
        message = "查询销售订单"
        user_id = "test_user"
    } | ConvertTo-Json)

Write-Host "任务类型: $($sapResponse.intent_analysis.task_type)" -ForegroundColor Cyan
Write-Host "置信度: $($sapResponse.intent_analysis.confidence)" -ForegroundColor Cyan
Write-Host "需要的服务: $($sapResponse.intent_analysis.required_services -join ', ')" -ForegroundColor Cyan

Start-Sleep -Seconds 2

# 查看性能指标
Write-Host "`n测试3: 查看性能指标" -ForegroundColor Yellow
$metrics = Invoke-RestMethod -Uri "http://localhost:8010/api/v1/performance/metrics" -Method GET

Write-Host "总请求数: $($metrics.total_requests)" -ForegroundColor Cyan
Write-Host "缓存命中率: $([math]::Round($metrics.cache_hit_rate, 2))%" -ForegroundColor Cyan
Write-Host "平均耗时: $([math]::Round($metrics.avg_time_ms, 2))ms" -ForegroundColor Cyan
Write-Host "错误率: $([math]::Round($metrics.error_rate, 2))%" -ForegroundColor Cyan

Write-Host "`n==========================================" -ForegroundColor Green
Write-Host "测试完成" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green



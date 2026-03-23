# 测试5: 周报功能
# 测试 GET /api/v1/weekly-reports 和 POST /api/v1/weekly-reports

$API_URL = "http://43.143.139.197:8080"
$BASE_URL = "$API_URL/api/v1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试5: 周报功能" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 获取Token（创建周报需要）
$TOKEN = Read-Host "请输入认证Token（创建周报需要，查询可选）"
$HEADERS = @{
    "Content-Type" = "application/json"
}
if ($TOKEN) {
    $HEADERS["Authorization"] = "Bearer $TOKEN"
}

# 1. 测试获取周报列表
Write-Host "1. 测试获取周报列表" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Method GET -Uri "$BASE_URL/weekly-reports" -Headers $HEADERS
    Write-Host "   ✅ 成功" -ForegroundColor Green
    Write-Host "   周报总数: $($response.total)" -ForegroundColor Gray
    Write-Host "   返回周报数: $($response.items.Count)" -ForegroundColor Gray
    if ($response.items.Count -gt 0) {
        $firstReport = $response.items[0]
        Write-Host "   第一个周报: $($firstReport.project_name) - $($firstReport.report_date)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ❌ 失败: $($_.Exception.Message)" -ForegroundColor Red
}

# 2. 测试按项目筛选
Write-Host ""
Write-Host "2. 测试按项目筛选" -ForegroundColor Yellow
$projectId = Read-Host "请输入项目ID（或按Enter跳过）"
if ($projectId) {
    try {
        $response = Invoke-RestMethod -Method GET -Uri "$BASE_URL/weekly-reports?project_id=$projectId" -Headers $HEADERS
        Write-Host "   ✅ 成功" -ForegroundColor Green
        Write-Host "   该项目周报数: $($response.total)" -ForegroundColor Gray
    } catch {
        Write-Host "   ❌ 失败: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "   ⏭️  跳过" -ForegroundColor Yellow
}

# 3. 测试创建周报
Write-Host ""
Write-Host "3. 测试创建周报" -ForegroundColor Yellow
if (-not $TOKEN) {
    Write-Host "   ⏭️  跳过（需要Token）" -ForegroundColor Yellow
} else {
    $createProjectId = Read-Host "请输入项目ID（用于创建周报）"
    if ($createProjectId) {
        $reportData = @{
            project_id = $createProjectId
            report_date = (Get-Date).ToString("yyyy-MM-dd")
            week_number = [int](Get-Date -UFormat %V)
            content_plan = "本周计划完成项目初始化工作"
            content_achievement = "已完成项目创建和基础配置"
            issues_risks = "暂无重大风险"
            next_week_plan = "下周计划开始开发核心功能"
        } | ConvertTo-Json -Depth 10
        
        try {
            $response = Invoke-RestMethod -Method POST -Uri "$BASE_URL/weekly-reports" -Headers $HEADERS -Body $reportData
            Write-Host "   ✅ 创建成功" -ForegroundColor Green
            Write-Host "   周报ID: $($response.id)" -ForegroundColor Gray
            Write-Host "   项目名称: $($response.project_name)" -ForegroundColor Gray
            Write-Host "   报告日期: $($response.report_date)" -ForegroundColor Gray
        } catch {
            $statusCode = $_.Exception.Response.StatusCode.value__
            Write-Host "   ❌ 创建失败 (HTTP $statusCode)" -ForegroundColor Red
            Write-Host "   错误: $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "   ⏭️  跳过（未提供项目ID）" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan


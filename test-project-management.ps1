# 项目管理功能测试脚本
# 测试增删改查功能

$API_URL = "http://43.143.139.197:8080"
$BASE_URL = "$API_URL/api/v1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "项目管理功能测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 注意：需要有效的认证token
# 这里使用一个测试token，实际使用时需要从登录接口获取
$TOKEN = Read-Host "请输入认证Token（或按Enter跳过认证测试）"

if ([string]::IsNullOrWhiteSpace($TOKEN)) {
    Write-Host "⚠️  未提供Token，将跳过需要认证的测试" -ForegroundColor Yellow
    $SKIP_AUTH = $true
} else {
    $SKIP_AUTH = $false
    $HEADERS = @{
        "Authorization" = "Bearer $TOKEN"
        "Content-Type" = "application/json"
    }
}

$TEST_PROJECT_ID = $null
$TEST_PROJECT_CODE = "TEST-$(Get-Date -Format 'yyyyMMddHHmmss')"

# 测试结果统计
$testResults = @{
    passed = 0
    failed = 0
    skipped = 0
}

function Test-API {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Url,
        [hashtable]$Headers = @{},
        [object]$Body = $null,
        [bool]$RequireAuth = $false
    )
    
    Write-Host ""
    Write-Host "测试: $Name" -ForegroundColor Cyan
    Write-Host "  $Method $Url" -ForegroundColor Gray
    
    if ($RequireAuth -and $SKIP_AUTH) {
        Write-Host "  ⏭️  跳过（需要认证）" -ForegroundColor Yellow
        $script:testResults.skipped++
        return $null
    }
    
    try {
        $params = @{
            Method = $Method
            Uri = $Url
            Headers = $Headers
            ContentType = "application/json"
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
        }
        
        $response = Invoke-RestMethod @params
        
        Write-Host "  ✅ 成功" -ForegroundColor Green
        $script:testResults.passed++
        return $response
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        $errorMessage = $_.Exception.Message
        
        Write-Host "  ❌ 失败 (HTTP $statusCode)" -ForegroundColor Red
        Write-Host "     错误: $errorMessage" -ForegroundColor Red
        
        # 尝试获取详细错误信息
        try {
            $errorBody = $_.ErrorDetails.Message | ConvertFrom-Json
            if ($errorBody.detail) {
                Write-Host "     详情: $($errorBody.detail)" -ForegroundColor Red
            }
        } catch {
            # 忽略JSON解析错误
        }
        
        $script:testResults.failed++
        return $null
    }
}

# 1. 测试获取项目列表（GET）
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. 查询功能测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$listResponse = Test-API -Name "获取项目列表" -Method "GET" -Url "$BASE_URL/projects" -Headers $HEADERS
if ($listResponse) {
    Write-Host "  项目总数: $($listResponse.total)" -ForegroundColor Gray
    Write-Host "  返回项目数: $($listResponse.items.Count)" -ForegroundColor Gray
}

# 2. 测试创建项目（POST）
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "2. 创建功能测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$createBody = @{
    project_code = $TEST_PROJECT_CODE
    name = "测试项目 - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    description = "这是一个自动化测试创建的项目"
    status = "planning"
    priority = "medium"
    start_date = (Get-Date).ToString("yyyy-MM-dd")
    end_date = (Get-Date).AddMonths(3).ToString("yyyy-MM-dd")
    budget = 100000.00
}

$createResponse = Test-API -Name "创建项目" -Method "POST" -Url "$BASE_URL/projects" -Headers $HEADERS -Body $createBody -RequireAuth $true

if ($createResponse) {
    $TEST_PROJECT_ID = $createResponse.id
    Write-Host "  创建的项目ID: $TEST_PROJECT_ID" -ForegroundColor Gray
    Write-Host "  项目编码: $($createResponse.project_code)" -ForegroundColor Gray
}

# 3. 测试获取项目详情（GET）
if ($TEST_PROJECT_ID) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "3. 查询详情功能测试" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    $detailResponse = Test-API -Name "获取项目详情" -Method "GET" -Url "$BASE_URL/projects/$TEST_PROJECT_ID" -Headers $HEADERS
    if ($detailResponse) {
        Write-Host "  项目名称: $($detailResponse.name)" -ForegroundColor Gray
        Write-Host "  项目状态: $($detailResponse.status)" -ForegroundColor Gray
    }
}

# 4. 测试更新项目（PUT）
if ($TEST_PROJECT_ID) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "4. 更新功能测试" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    $updateBody = @{
        name = "测试项目 - 已更新 $(Get-Date -Format 'HH:mm:ss')"
        description = "这是更新后的项目描述"
        status = "active"
        priority = "high"
        progress_percent = 25.5
    }
    
    $updateResponse = Test-API -Name "更新项目" -Method "PUT" -Url "$BASE_URL/projects/$TEST_PROJECT_ID" -Headers $HEADERS -Body $updateBody -RequireAuth $true
    if ($updateResponse) {
        Write-Host "  更新后的名称: $($updateResponse.name)" -ForegroundColor Gray
        Write-Host "  更新后的状态: $($updateResponse.status)" -ForegroundColor Gray
        Write-Host "  更新后的进度: $($updateResponse.progress_percent)%" -ForegroundColor Gray
    }
}

# 5. 测试周报创建
if ($TEST_PROJECT_ID) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "5. 周报功能测试" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    $weeklyReportBody = @{
        project_id = $TEST_PROJECT_ID
        report_date = (Get-Date).ToString("yyyy-MM-dd")
        week_number = [int](Get-Date -UFormat %V)
        content_plan = "本周计划完成项目初始化工作"
        content_achievement = "已完成项目创建和基础配置"
        issues_risks = "暂无重大风险"
        next_week_plan = "下周计划开始开发核心功能"
    }
    
    $weeklyReportResponse = Test-API -Name "创建周报" -Method "POST" -Url "$BASE_URL/weekly-reports" -Headers $HEADERS -Body $weeklyReportBody -RequireAuth $true
    
    # 测试获取周报列表
    $weeklyListResponse = Test-API -Name "获取周报列表" -Method "GET" -Url "$BASE_URL/weekly-reports?project_id=$TEST_PROJECT_ID" -Headers $HEADERS
}

# 6. 测试月报创建
if ($TEST_PROJECT_ID) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "6. 月报功能测试" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    $monthlyReportBody = @{
        project_id = $TEST_PROJECT_ID
        report_month = (Get-Date).ToString("yyyy-MM")
        summary = "本月项目进展总结"
        achievements = "完成了项目初始化和基础架构搭建"
        challenges = "遇到了一些技术难点，但已解决"
        next_month_plan = "下月计划完成核心功能开发"
    }
    
    $monthlyReportResponse = Test-API -Name "创建月报" -Method "POST" -Url "$BASE_URL/monthly-reports" -Headers $HEADERS -Body $monthlyReportBody -RequireAuth $true
    
    # 测试获取月报列表
    $monthlyListResponse = Test-API -Name "获取月报列表" -Method "GET" -Url "$BASE_URL/monthly-reports?project_id=$TEST_PROJECT_ID" -Headers $HEADERS
}

# 7. 测试删除项目（DELETE）
if ($TEST_PROJECT_ID) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "7. 删除功能测试" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    $confirm = Read-Host "是否删除测试项目 $TEST_PROJECT_ID? (y/N)"
    if ($confirm -eq "y" -or $confirm -eq "Y") {
        $deleteResponse = Test-API -Name "删除项目" -Method "DELETE" -Url "$BASE_URL/projects/$TEST_PROJECT_ID" -Headers $HEADERS -RequireAuth $true
        if ($deleteResponse) {
            Write-Host "  项目已删除" -ForegroundColor Green
            $TEST_PROJECT_ID = $null
        }
    } else {
        Write-Host "  ⏭️  跳过删除测试" -ForegroundColor Yellow
        Write-Host "  测试项目ID: $TEST_PROJECT_ID (请手动删除)" -ForegroundColor Yellow
    }
}

# 测试结果汇总
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试结果汇总" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ 通过: $($testResults.passed)" -ForegroundColor Green
Write-Host "❌ 失败: $($testResults.failed)" -ForegroundColor Red
Write-Host "⏭️  跳过: $($testResults.skipped)" -ForegroundColor Yellow
Write-Host ""

if ($testResults.failed -eq 0) {
    Write-Host "🎉 所有测试通过！" -ForegroundColor Green
} else {
    Write-Host "⚠️  有测试失败，请检查上述错误信息" -ForegroundColor Yellow
}

Write-Host ""


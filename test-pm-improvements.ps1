# 测试项目管理功能完善
$API_URL = "http://43.143.139.197:8080"
$BASE_URL = "$API_URL/api/v1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "项目管理功能完善测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 登录获取Token
Write-Host "正在登录..." -ForegroundColor Yellow
$loginBody = @{
    username = "admin"
    password = "admin123456"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Method POST -Uri "$API_URL/api/auth/login" -Body $loginBody -ContentType "application/json"
    
    if ($loginResponse.access_token) {
        $TOKEN = $loginResponse.access_token
        Write-Host "✅ 登录成功" -ForegroundColor Green
    } else {
        Write-Host "❌ 登录失败" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ 登录失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

$HEADERS = @{
    "Authorization" = "Bearer $TOKEN"
    "Content-Type" = "application/json"
}

Write-Host ""

# 测试结果统计
$testResults = @{
    passed = 0
    failed = 0
    errors = @()
}

function Test-API {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Url,
        [hashtable]$Headers = @{},
        [object]$Body = $null
    )
    
    Write-Host "测试: $Name" -ForegroundColor Cyan
    Write-Host "  $Method $Url" -ForegroundColor Gray
    
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
        
        $script:testResults.errors += "${Name}: $errorMessage"
        $script:testResults.failed++
        return $null
    }
}

# 获取测试项目
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "步骤1: 获取测试项目" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$projectList = Test-API -Name "获取项目列表" -Method "GET" -Url "$BASE_URL/projects?limit=1" -Headers $HEADERS
$TEST_PROJECT_ID = $null
if ($projectList -and $projectList.items.Count -gt 0) {
    $TEST_PROJECT_ID = $projectList.items[0].id
    Write-Host "  使用项目: $($projectList.items[0].name) ($TEST_PROJECT_ID)" -ForegroundColor Gray
}

Write-Host ""

# 测试阶段管理
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "步骤2: 测试阶段管理CRUD" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($TEST_PROJECT_ID) {
    # 创建阶段
    $TEST_PHASE_ID = $null
    $createPhaseBody = @{
        project_id = $TEST_PROJECT_ID
        name = "测试阶段 - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        description = "这是一个测试阶段"
        start_date = (Get-Date).ToString("yyyy-MM-dd")
        end_date = (Get-Date).AddMonths(1).ToString("yyyy-MM-dd")
    }
    
    $createPhaseResponse = Test-API -Name "创建阶段" -Method "POST" -Url "$BASE_URL/project-phases" -Headers $HEADERS -Body $createPhaseBody
    if ($createPhaseResponse) {
        $TEST_PHASE_ID = $createPhaseResponse.id
        Write-Host "  创建的阶段ID: $TEST_PHASE_ID" -ForegroundColor Gray
        Write-Host "  自动设置的sequence: $($createPhaseResponse.sequence)" -ForegroundColor Gray
    }
    
    # 获取阶段详情
    if ($TEST_PHASE_ID) {
        Write-Host ""
        $phaseDetail = Test-API -Name "获取阶段详情" -Method "GET" -Url "$BASE_URL/project-phases/$TEST_PHASE_ID" -Headers $HEADERS
        
        # 更新阶段
        Write-Host ""
        $updatePhaseBody = @{
            name = "测试阶段 - 已更新 $(Get-Date -Format 'HH:mm:ss')"
            progress_percent = 30.0
        }
        $updatePhaseResponse = Test-API -Name "更新阶段" -Method "PUT" -Url "$BASE_URL/project-phases/$TEST_PHASE_ID" -Headers $HEADERS -Body $updatePhaseBody
        
        # 调整顺序
        Write-Host ""
        $reorderResponse = Test-API -Name "调整阶段顺序" -Method "PATCH" -Url "$BASE_URL/project-phases/$TEST_PHASE_ID/reorder?new_sequence=1" -Headers $HEADERS
    }
}

Write-Host ""

# 测试风险管理
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "步骤3: 测试风险管理CRUD" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($TEST_PROJECT_ID) {
    # 创建风险
    $TEST_RISK_ID = $null
    $createRiskBody = @{
        project_id = $TEST_PROJECT_ID
        name = "测试风险 - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        description = "这是一个测试风险"
        risk_level = "high"
        status = "open"
        mitigation_plan = "制定应对措施"
    }
    
    $createRiskResponse = Test-API -Name "创建风险" -Method "POST" -Url "$BASE_URL/risks" -Headers $HEADERS -Body $createRiskBody
    if ($createRiskResponse) {
        $TEST_RISK_ID = $createRiskResponse.id
        Write-Host "  创建的风险ID: $TEST_RISK_ID" -ForegroundColor Gray
    }
    
    # 获取风险详情
    if ($TEST_RISK_ID) {
        Write-Host ""
        $riskDetail = Test-API -Name "获取风险详情" -Method "GET" -Url "$BASE_URL/risks/$TEST_RISK_ID" -Headers $HEADERS
        
        # 更新风险
        Write-Host ""
        $updateRiskBody = @{
            status = "in_progress"
            mitigation_plan = "已制定应对措施并开始执行"
        }
        $updateRiskResponse = Test-API -Name "更新风险" -Method "PUT" -Url "$BASE_URL/risks/$TEST_RISK_ID" -Headers $HEADERS -Body $updateRiskBody
    }
}

Write-Host ""

# 测试数据验证
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "步骤4: 测试数据验证逻辑" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($TEST_PROJECT_ID) {
    # 获取另一个项目用于测试验证
    $projectList2 = Test-API -Name "获取项目列表" -Method "GET" -Url "$BASE_URL/projects?limit=2" -Headers $HEADERS
    $OTHER_PROJECT_ID = $null
    if ($projectList2 -and $projectList2.items.Count -gt 1) {
        $OTHER_PROJECT_ID = $projectList2.items[1].id
    }
    
    if ($OTHER_PROJECT_ID) {
        # 获取另一个项目的阶段
        $otherPhases = Test-API -Name "获取另一个项目的阶段" -Method "GET" -Url "$BASE_URL/project-phases?project_id=$OTHER_PROJECT_ID" -Headers $HEADERS
        if ($otherPhases -and $otherPhases.items.Count -gt 0) {
            $OTHER_PHASE_ID = $otherPhases.items[0].id
            
            # 尝试创建任务，使用错误的phase_id（应该失败）
            Write-Host ""
            $invalidTaskBody = @{
                project_id = $TEST_PROJECT_ID
                phase_id = $OTHER_PHASE_ID  # 属于另一个项目的阶段
                name = "测试任务 - 应该失败"
            }
            
            Write-Host "测试: 创建任务（使用错误的phase_id）" -ForegroundColor Cyan
            Write-Host "  应该返回400错误" -ForegroundColor Gray
            try {
                $response = Invoke-RestMethod -Method POST -Uri "$BASE_URL/tasks" -Headers $HEADERS -Body ($invalidTaskBody | ConvertTo-Json) -ContentType "application/json" -ErrorAction Stop
                Write-Host "  ⚠️  验证失败：应该返回错误但没有" -ForegroundColor Yellow
                $script:testResults.failed++
            } catch {
                if ($_.Exception.Response.StatusCode.value__ -eq 400) {
                    Write-Host "  ✅ 验证成功：正确返回400错误" -ForegroundColor Green
                    $script:testResults.passed++
                } else {
                    Write-Host "  ❌ 验证失败：返回了其他错误" -ForegroundColor Red
                    $script:testResults.failed++
                }
            }
        }
    }
}

Write-Host ""

# 测试周报/月报CRUD
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "步骤5: 测试周报/月报CRUD" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($TEST_PROJECT_ID) {
    # 创建周报
    $TEST_WEEKLY_REPORT_ID = $null
    $createWeeklyBody = @{
        project_id = $TEST_PROJECT_ID
        report_date = (Get-Date).ToString("yyyy-MM-dd")
        content_plan = "本周计划"
        content_achievement = "本周成果"
    }
    
    $createWeeklyResponse = Test-API -Name "创建周报" -Method "POST" -Url "$BASE_URL/weekly-reports" -Headers $HEADERS -Body $createWeeklyBody
    if ($createWeeklyResponse) {
        $TEST_WEEKLY_REPORT_ID = $createWeeklyResponse.id
        Write-Host "  创建的周报ID: $TEST_WEEKLY_REPORT_ID" -ForegroundColor Gray
    }
    
    # 获取周报详情
    if ($TEST_WEEKLY_REPORT_ID) {
        Write-Host ""
        $weeklyDetail = Test-API -Name "获取周报详情" -Method "GET" -Url "$BASE_URL/weekly-reports/$TEST_WEEKLY_REPORT_ID" -Headers $HEADERS
        
        # 更新周报
        Write-Host ""
        $updateWeeklyBody = @{
            content_achievement = "本周成果 - 已更新"
            next_week_plan = "下周计划"
        }
        $updateWeeklyResponse = Test-API -Name "更新周报" -Method "PUT" -Url "$BASE_URL/weekly-reports/$TEST_WEEKLY_REPORT_ID" -Headers $HEADERS -Body $updateWeeklyBody
    }
    
    # 创建月报
    Write-Host ""
    $TEST_MONTHLY_REPORT_ID = "$TEST_PROJECT_ID`_$(Get-Date -Format 'yyyy-MM')"
    $createMonthlyBody = @{
        project_id = $TEST_PROJECT_ID
        report_month = (Get-Date).ToString("yyyy-MM")
        summary = "月度总结"
        achievements = "月度成果"
    }
    
    $createMonthlyResponse = Test-API -Name "创建月报" -Method "POST" -Url "$BASE_URL/monthly-reports" -Headers $HEADERS -Body $createMonthlyBody
    if ($createMonthlyResponse) {
        $TEST_MONTHLY_REPORT_ID = $createMonthlyResponse.id
        Write-Host "  创建的月报ID: $TEST_MONTHLY_REPORT_ID" -ForegroundColor Gray
    }
    
    # 获取月报详情
    if ($TEST_MONTHLY_REPORT_ID) {
        Write-Host ""
        $monthlyDetail = Test-API -Name "获取月报详情" -Method "GET" -Url "$BASE_URL/monthly-reports/$TEST_MONTHLY_REPORT_ID" -Headers $HEADERS
        
        # 更新月报
        Write-Host ""
        $updateMonthlyBody = @{
            summary = "月度总结 - 已更新"
            achievements = "月度成果 - 已更新"
        }
        $updateMonthlyResponse = Test-API -Name "更新月报" -Method "PUT" -Url "$BASE_URL/monthly-reports/$TEST_MONTHLY_REPORT_ID" -Headers $HEADERS -Body $updateMonthlyBody
    }
}

# 测试结果汇总
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试结果汇总" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ 通过: $($testResults.passed)" -ForegroundColor Green
Write-Host "❌ 失败: $($testResults.failed)" -ForegroundColor Red
Write-Host ""

if ($testResults.errors.Count -gt 0) {
    Write-Host "错误详情:" -ForegroundColor Yellow
    foreach ($err in $testResults.errors) {
        Write-Host "  - $err" -ForegroundColor Red
    }
    Write-Host ""
}

if ($testResults.failed -eq 0) {
    Write-Host "🎉 所有测试通过！" -ForegroundColor Green
} else {
    Write-Host "⚠️  有测试失败，请检查上述错误信息" -ForegroundColor Yellow
}

Write-Host ""


# 运行所有项目管理功能测试
$API_URL = "http://43.143.139.197:8080"
$BASE_URL = "$API_URL/api/v1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "项目管理功能完整测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤1: 获取Token
Write-Host "步骤1: 获取认证Token" -ForegroundColor Yellow
$TOKEN = $null

# 尝试登录
$passwords = @("admin123", "admin123456", "admin")
foreach ($password in $passwords) {
    try {
        $loginBody = @{
            username = "admin"
            password = $password
        } | ConvertTo-Json
        
        $loginResponse = Invoke-RestMethod -Method POST -Uri "$API_URL/api/v1/auth/login" -Body $loginBody -ContentType "application/json" -ErrorAction Stop
        
        if ($loginResponse.access_token) {
            $TOKEN = $loginResponse.access_token
            Write-Host "  ✅ 登录成功 (密码: $password)" -ForegroundColor Green
            break
        }
    } catch {
        # 继续尝试
    }
}

if (-not $TOKEN) {
    Write-Host "  ⚠️  无法自动登录，将跳过需要认证的测试" -ForegroundColor Yellow
    Write-Host "  请手动输入Token或按Enter继续（仅测试查询功能）" -ForegroundColor Yellow
    $manualToken = Read-Host "Token"
    if ($manualToken) {
        $TOKEN = $manualToken
    }
}

$HEADERS = @{
    "Content-Type" = "application/json"
}
if ($TOKEN) {
    $HEADERS["Authorization"] = "Bearer $TOKEN"
    Write-Host "  Token已设置" -ForegroundColor Green
}

Write-Host ""

# 测试结果
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
    
    Write-Host "测试: $Name" -ForegroundColor Cyan
    Write-Host "  $Method $Url" -ForegroundColor Gray
    
    if ($RequireAuth -and -not $TOKEN) {
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
        
        $script:testResults.failed++
        return $null
    }
}

# 步骤2: 测试项目列表查询
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "步骤2: 测试项目列表查询" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$listResponse = Test-API -Name "获取项目列表" -Method "GET" -Url "$BASE_URL/projects" -Headers $HEADERS
if ($listResponse) {
    Write-Host "  项目总数: $($listResponse.total)" -ForegroundColor Gray
    Write-Host "  返回项目数: $($listResponse.items.Count)" -ForegroundColor Gray
}

# 步骤3: 测试创建项目
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "步骤3: 测试创建项目" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$TEST_PROJECT_ID = $null
$TEST_PROJECT_CODE = "TEST-$(Get-Date -Format 'yyyyMMddHHmmss')"

$createBody = @{
    project_code = $TEST_PROJECT_CODE
    name = "测试项目 - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    description = "自动化测试创建的项目"
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
}

# 步骤4: 测试获取项目详情
if ($TEST_PROJECT_ID) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "步骤4: 测试获取项目详情" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    $detailResponse = Test-API -Name "获取项目详情" -Method "GET" -Url "$BASE_URL/projects/$TEST_PROJECT_ID" -Headers $HEADERS
    if ($detailResponse) {
        Write-Host "  项目名称: $($detailResponse.name)" -ForegroundColor Gray
        Write-Host "  项目状态: $($detailResponse.status)" -ForegroundColor Gray
    }
}

# 步骤5: 测试更新项目
if ($TEST_PROJECT_ID) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "步骤5: 测试更新项目" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    $updateBody = @{
        name = "测试项目 - 已更新 $(Get-Date -Format 'HH:mm:ss')"
        status = "active"
        priority = "high"
        progress_percent = 25.5
    }
    
    $updateResponse = Test-API -Name "更新项目" -Method "PUT" -Url "$BASE_URL/projects/$TEST_PROJECT_ID" -Headers $HEADERS -Body $updateBody -RequireAuth $true
    if ($updateResponse) {
        Write-Host "  更新后名称: $($updateResponse.name)" -ForegroundColor Gray
        Write-Host "  更新后状态: $($updateResponse.status)" -ForegroundColor Gray
    }
}

# 步骤6: 测试周报功能
if ($TEST_PROJECT_ID) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "步骤6: 测试周报功能" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    # 创建周报
    $weeklyBody = @{
        project_id = $TEST_PROJECT_ID
        report_date = (Get-Date).ToString("yyyy-MM-dd")
        content_plan = "本周计划"
        content_achievement = "本周成果"
        next_week_plan = "下周计划"
    }
    
    $weeklyResponse = Test-API -Name "创建周报" -Method "POST" -Url "$BASE_URL/weekly-reports" -Headers $HEADERS -Body $weeklyBody -RequireAuth $true
    
    # 获取周报列表
    Test-API -Name "获取周报列表" -Method "GET" -Url "$BASE_URL/weekly-reports?project_id=$TEST_PROJECT_ID" -Headers $HEADERS
}

# 步骤7: 测试月报功能
if ($TEST_PROJECT_ID) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "步骤7: 测试月报功能" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    # 创建月报
    $monthlyBody = @{
        project_id = $TEST_PROJECT_ID
        report_month = (Get-Date).ToString("yyyy-MM")
        summary = "月度总结"
        achievements = "月度成果"
        challenges = "挑战问题"
    }
    
    $monthlyResponse = Test-API -Name "创建月报" -Method "POST" -Url "$BASE_URL/monthly-reports" -Headers $HEADERS -Body $monthlyBody -RequireAuth $true
    
    # 获取月报列表
    Test-API -Name "获取月报列表" -Method "GET" -Url "$BASE_URL/monthly-reports?project_id=$TEST_PROJECT_ID" -Headers $HEADERS
}

# 步骤8: 测试删除项目（可选）
if ($TEST_PROJECT_ID) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "步骤8: 测试删除项目" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "⚠️  警告: 删除操作不可逆" -ForegroundColor Red
    
    $confirm = Read-Host "是否删除测试项目? (yes/no)"
    if ($confirm -eq "yes") {
        Test-API -Name "删除项目" -Method "DELETE" -Url "$BASE_URL/projects/$TEST_PROJECT_ID" -Headers $HEADERS -RequireAuth $true
    } else {
        Write-Host "  ⏭️  跳过删除" -ForegroundColor Yellow
        Write-Host "  测试项目ID: $TEST_PROJECT_ID (请手动删除)" -ForegroundColor Yellow
        $script:testResults.skipped++
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


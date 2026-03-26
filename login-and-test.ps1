# 登录并执行完整测试
$API_URL = "http://43.143.139.197:8080"
$BASE_URL = "$API_URL/api/v1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "登录并执行完整测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 登录获取Token
Write-Host "正在登录..." -ForegroundColor Yellow
$loginBody = @{
    username = "admin"
    password = "admin123456"
} | ConvertTo-Json

# 尝试不同的登录端点
$loginEndpoints = @(
    "$API_URL/api/v1/auth/login",
    "$API_URL/auth/login",
    "$API_URL/api/auth/login"
)

$loginResponse = $null
foreach ($endpoint in $loginEndpoints) {
    try {
        Write-Host "尝试登录端点: $endpoint" -ForegroundColor Gray
        $loginResponse = Invoke-RestMethod -Method POST -Uri $endpoint -Body $loginBody -ContentType "application/json" -ErrorAction Stop
        Write-Host "登录端点: $endpoint" -ForegroundColor Gray
        break
    } catch {
        continue
    }
}

if ($loginResponse) {
    if ($loginResponse.access_token) {
        $TOKEN = $loginResponse.access_token
        Write-Host "✅ 登录成功" -ForegroundColor Green
        Write-Host "Token: $($TOKEN.Substring(0, [Math]::Min(50, $TOKEN.Length)))..." -ForegroundColor Gray
    } elseif ($loginResponse.token) {
        $TOKEN = $loginResponse.token
        Write-Host "✅ 登录成功" -ForegroundColor Green
        Write-Host "Token: $($TOKEN.Substring(0, [Math]::Min(50, $TOKEN.Length)))..." -ForegroundColor Gray
    } else {
        Write-Host "❌ 登录失败: 未返回token" -ForegroundColor Red
        Write-Host "响应内容: $($loginResponse | ConvertTo-Json)" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "❌ 登录失败: 无法连接到登录服务" -ForegroundColor Red
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
        
        # 尝试获取详细错误
        try {
            $errorStream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($errorStream)
            $errorBody = $reader.ReadToEnd()
            $reader.Close()
            $errorStream.Close()
            
            try {
                $errorJson = $errorBody | ConvertFrom-Json
                if ($errorJson.detail) {
                    Write-Host "     详情: $($errorJson.detail)" -ForegroundColor Red
                    $script:testResults.errors += "${Name}: $($errorJson.detail)"
                } else {
                    $script:testResults.errors += "${Name}: $errorBody"
                }
            } catch {
                $script:testResults.errors += "${Name}: $errorBody"
            }
        } catch {
            $script:testResults.errors += "${Name}: $errorMessage"
        }
        
        $script:testResults.failed++
        return $null
    }
}

# 测试1: 项目列表查询
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试1: 项目列表查询" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$listResponse = Test-API -Name "获取项目列表" -Method "GET" -Url "$BASE_URL/projects" -Headers $HEADERS
if ($listResponse) {
    Write-Host "  项目总数: $($listResponse.total)" -ForegroundColor Gray
}

# 测试2: 创建项目
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试2: 创建项目" -ForegroundColor Cyan
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

$createResponse = Test-API -Name "创建项目" -Method "POST" -Url "$BASE_URL/projects" -Headers $HEADERS -Body $createBody

if ($createResponse) {
    $TEST_PROJECT_ID = $createResponse.id
    Write-Host "  创建的项目ID: $TEST_PROJECT_ID" -ForegroundColor Gray
    Write-Host "  项目编码: $($createResponse.project_code)" -ForegroundColor Gray
}

# 测试3: 获取项目详情
if ($TEST_PROJECT_ID) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "测试3: 获取项目详情" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    $detailResponse = Test-API -Name "获取项目详情" -Method "GET" -Url "$BASE_URL/projects/$TEST_PROJECT_ID" -Headers $HEADERS
    if ($detailResponse) {
        Write-Host "  项目名称: $($detailResponse.name)" -ForegroundColor Gray
        Write-Host "  项目状态: $($detailResponse.status)" -ForegroundColor Gray
    }
}

# 测试4: 更新项目
if ($TEST_PROJECT_ID) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "测试4: 更新项目" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    $updateBody = @{
        name = "测试项目 - 已更新 $(Get-Date -Format 'HH:mm:ss')"
        description = "这是更新后的项目描述"
        status = "active"
        priority = "high"
        progress_percent = 25.5
    }
    
    $updateResponse = Test-API -Name "更新项目" -Method "PUT" -Url "$BASE_URL/projects/$TEST_PROJECT_ID" -Headers $HEADERS -Body $updateBody
    if ($updateResponse) {
        Write-Host "  更新后名称: $($updateResponse.name)" -ForegroundColor Gray
        Write-Host "  更新后状态: $($updateResponse.status)" -ForegroundColor Gray
        Write-Host "  更新后进度: $($updateResponse.progress_percent)%" -ForegroundColor Gray
    }
}

# 测试5: 创建周报
if ($TEST_PROJECT_ID) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "测试5: 创建周报" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    $weeklyBody = @{
        project_id = $TEST_PROJECT_ID
        report_date = (Get-Date).ToString("yyyy-MM-dd")
        week_number = [int](Get-Date -UFormat %V)
        content_plan = "本周计划完成项目初始化工作"
        content_achievement = "已完成项目创建和基础配置"
        issues_risks = "暂无重大风险"
        next_week_plan = "下周计划开始开发核心功能"
    }
    
    $weeklyResponse = Test-API -Name "创建周报" -Method "POST" -Url "$BASE_URL/weekly-reports" -Headers $HEADERS -Body $weeklyBody
    if ($weeklyResponse) {
        Write-Host "  周报ID: $($weeklyResponse.id)" -ForegroundColor Gray
        Write-Host "  报告日期: $($weeklyResponse.report_date)" -ForegroundColor Gray
    }
    
    # 测试获取周报列表
    Write-Host ""
    $weeklyListResponse = Test-API -Name "获取周报列表" -Method "GET" -Url "$BASE_URL/weekly-reports?project_id=$TEST_PROJECT_ID" -Headers $HEADERS
    if ($weeklyListResponse) {
        Write-Host "  该项目周报数: $($weeklyListResponse.total)" -ForegroundColor Gray
    }
}

# 测试6: 创建月报
if ($TEST_PROJECT_ID) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "测试6: 创建月报" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    $monthlyBody = @{
        project_id = $TEST_PROJECT_ID
        report_month = (Get-Date).ToString("yyyy-MM")
        summary = "本月项目进展总结"
        achievements = "完成了项目初始化和基础架构搭建"
        challenges = "遇到了一些技术难点，但已解决"
        next_month_plan = "下月计划完成核心功能开发"
    }
    
    $monthlyResponse = Test-API -Name "创建月报" -Method "POST" -Url "$BASE_URL/monthly-reports" -Headers $HEADERS -Body $monthlyBody
    if ($monthlyResponse) {
        Write-Host "  月报ID: $($monthlyResponse.id)" -ForegroundColor Gray
        Write-Host "  报告月份: $($monthlyResponse.report_month)" -ForegroundColor Gray
    }
    
    # 测试获取月报列表
    Write-Host ""
    $monthlyListResponse = Test-API -Name "获取月报列表" -Method "GET" -Url "$BASE_URL/monthly-reports?project_id=$TEST_PROJECT_ID" -Headers $HEADERS
    if ($monthlyListResponse) {
        Write-Host "  该项目月报数: $($monthlyListResponse.total)" -ForegroundColor Gray
    }
}

# 测试7: 删除项目（可选）
if ($TEST_PROJECT_ID) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "测试7: 删除项目" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "⚠️  警告: 删除操作不可逆，会级联删除相关数据" -ForegroundColor Red
    
    $confirm = Read-Host "是否删除测试项目? (yes/no)"
    if ($confirm -eq "yes") {
        $deleteResponse = Test-API -Name "删除项目" -Method "DELETE" -Url "$BASE_URL/projects/$TEST_PROJECT_ID" -Headers $HEADERS
        
        # 验证删除
        if ($deleteResponse) {
            Write-Host ""
            Write-Host "验证删除结果..." -ForegroundColor Yellow
            try {
                $check = Invoke-RestMethod -Method GET -Uri "$BASE_URL/projects/$TEST_PROJECT_ID" -Headers $HEADERS
                Write-Host "  ⚠️  项目仍然存在" -ForegroundColor Yellow
            } catch {
                if ($_.Exception.Response.StatusCode.value__ -eq 404) {
                    Write-Host "  ✅ 项目已成功删除（404 Not Found）" -ForegroundColor Green
                }
            }
        }
    } else {
        Write-Host "  ⏭️  跳过删除" -ForegroundColor Yellow
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


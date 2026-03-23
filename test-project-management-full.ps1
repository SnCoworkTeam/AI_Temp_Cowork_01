# 项目管理功能完整测试脚本
# 按照测试计划执行所有测试用例

$API_URL = "http://43.143.139.197:8080"
$BASE_URL = "$API_URL/api/v1"
$TEST_DATE = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "项目管理功能完整测试" -ForegroundColor Cyan
Write-Host "测试日期: $TEST_DATE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 测试结果统计
$testResults = @{
    total = 0
    passed = 0
    failed = 0
    skipped = 0
    details = @()
}

# 步骤1: 获取认证Token
Write-Host "步骤1: 获取认证Token" -ForegroundColor Yellow
$TOKEN = $null

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
        } elseif ($loginResponse.token) {
            $TOKEN = $loginResponse.token
            Write-Host "  ✅ 登录成功 (密码: $password)" -ForegroundColor Green
            break
        }
    } catch {
        continue
    }
}

if (-not $TOKEN) {
    Write-Host "  ❌ 登录失败，无法继续测试" -ForegroundColor Red
    Write-Host "  请检查用户名和密码" -ForegroundColor Yellow
    exit 1
}

$HEADERS = @{
    "Authorization" = "Bearer $TOKEN"
    "Content-Type" = "application/json"
}

Write-Host ""

# 测试函数
function Test-API {
    param(
        [string]$TestName,
        [string]$Method,
        [string]$Url,
        [object]$Body = $null,
        [int]$ExpectedStatus = 200,
        [scriptblock]$Validation = $null
    )
    
    $testResults.total++
    Write-Host "测试: $TestName" -ForegroundColor Cyan
    
    try {
        $params = @{
            Method = $Method
            Uri = $Url
            Headers = $HEADERS
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
        }
        
        $response = Invoke-RestMethod @params
        $statusCode = 200
        
        if ($statusCode -eq $ExpectedStatus) {
            if ($Validation) {
                $validationResult = & $Validation $response
                if ($validationResult) {
                    Write-Host "  ✅ 通过" -ForegroundColor Green
                    $testResults.passed++
                    $testResults.details += @{
                        Test = $TestName
                        Status = "PASSED"
                        Message = "测试通过"
                    }
                    return $true
                } else {
                    Write-Host "  ❌ 失败: 验证未通过" -ForegroundColor Red
                    $testResults.failed++
                    $testResults.details += @{
                        Test = $TestName
                        Status = "FAILED"
                        Message = "验证未通过"
                    }
                    return $false
                }
            } else {
                Write-Host "  ✅ 通过" -ForegroundColor Green
                $testResults.passed++
                $testResults.details += @{
                    Test = $TestName
                    Status = "PASSED"
                    Message = "测试通过"
                }
                return $true
            }
        } else {
            Write-Host "  ❌ 失败: 状态码 $statusCode (期望 $ExpectedStatus)" -ForegroundColor Red
            $testResults.failed++
            $testResults.details += @{
                Test = $TestName
                Status = "FAILED"
                Message = "状态码不匹配: $statusCode"
            }
            return $false
        }
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -eq $ExpectedStatus) {
            Write-Host "  ✅ 通过 (预期错误)" -ForegroundColor Green
            $testResults.passed++
            return $true
        } else {
            Write-Host "  ❌ 失败: $($_.Exception.Message)" -ForegroundColor Red
            $testResults.failed++
            $testResults.details += @{
                Test = $TestName
                Status = "FAILED"
                Message = $_.Exception.Message
            }
            return $false
        }
    }
}

# 存储测试中创建的项目ID
$TEST_PROJECT_ID = $null
$TEST_PROJECT_CODE = $null

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "一、项目基础管理功能测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# TC-001: 查看项目列表
Test-API -TestName "TC-001: 查看项目列表" `
    -Method "GET" `
    -Url "$BASE_URL/projects" `
    -Validation {
        param($response)
        if ($response.items -or $response.total -ge 0) {
            Write-Host "    项目总数: $($response.total)" -ForegroundColor Gray
            return $true
        }
        return $false
    }

# TC-002: 项目列表筛选（按状态）
Test-API -TestName "TC-002: 项目列表筛选（规划中）" `
    -Method "GET" `
    -Url "$BASE_URL/projects?status=planning" `
    -Validation {
        param($response)
        return $true
    }

# TC-003: 项目列表搜索（通过API无法直接测试前端搜索，但可以测试API参数）
Test-API -TestName "TC-003: 项目列表API可用性" `
    -Method "GET" `
    -Url "$BASE_URL/projects?skip=0&limit=10" `
    -Validation {
        param($response)
        return $true
    }

# TC-004: 创建新项目（基础信息）
$createProjectBody = @{
    name = "测试项目001"
    status = "planning"
    priority = "high"
}

$createResult = Test-API -TestName "TC-004: 创建新项目（基础信息）" `
    -Method "POST" `
    -Url "$BASE_URL/projects" `
    -Body $createProjectBody `
    -Validation {
        param($response)
        if ($response.id -and $response.project_code) {
            $script:TEST_PROJECT_ID = $response.id
            $script:TEST_PROJECT_CODE = $response.project_code
            Write-Host "    项目ID: $($response.id)" -ForegroundColor Gray
            Write-Host "    项目编码: $($response.project_code)" -ForegroundColor Gray
            return $true
        }
        return $false
    }

# TC-005: 创建项目（完整信息）
$fullProjectBody = @{
    name = "完整测试项目"
    description = "这是一个完整的测试项目"
    status = "planning"
    priority = "high"
    start_date = "2024-01-01"
    end_date = "2024-12-31"
    budget = 100000
    progress_percent = 0
    health_score = 100
    requires_weekly_report = $true
}

Test-API -TestName "TC-005: 创建项目（完整信息）" `
    -Method "POST" `
    -Url "$BASE_URL/projects" `
    -Body $fullProjectBody `
    -Validation {
        param($response)
        if ($response.id) {
            Write-Host "    项目ID: $($response.id)" -ForegroundColor Gray
            return $true
        }
        return $false
    }

# TC-007: 查看项目详情
if ($TEST_PROJECT_ID) {
    Test-API -TestName "TC-007: 查看项目详情" `
        -Method "GET" `
        -Url "$BASE_URL/projects/$TEST_PROJECT_ID" `
        -Validation {
            param($response)
            if ($response.id -eq $script:TEST_PROJECT_ID) {
                Write-Host "    项目名称: $($response.name)" -ForegroundColor Gray
                return $true
            }
            return $false
        }
} else {
    Write-Host "  ⚠️  跳过 TC-007: 没有可用的项目ID" -ForegroundColor Yellow
    $testResults.skipped++
}

# TC-008: 编辑项目基本信息
if ($TEST_PROJECT_ID) {
    $updateBody = @{
        name = "测试项目001（已修改）"
        description = "这是修改后的描述"
        status = "active"
    }
    
    Test-API -TestName "TC-008: 编辑项目基本信息" `
        -Method "PUT" `
        -Url "$BASE_URL/projects/$TEST_PROJECT_ID" `
        -Body $updateBody `
        -Validation {
            param($response)
            if ($response.name -like "*已修改*") {
                Write-Host "    更新后的名称: $($response.name)" -ForegroundColor Gray
                return $true
            }
            return $false
        }
} else {
    Write-Host "  ⚠️  跳过 TC-008: 没有可用的项目ID" -ForegroundColor Yellow
    $testResults.skipped++
}

# TC-010: 删除项目（先创建测试项目）
$deleteTestProjectBody = @{
    name = "待删除测试项目"
    status = "planning"
}

$deleteTestResult = Test-API -TestName "TC-010: 创建待删除的测试项目" `
    -Method "POST" `
    -Url "$BASE_URL/projects" `
    -Body $deleteTestProjectBody `
    -Validation {
        param($response)
        if ($response.id) {
            $script:DELETE_PROJECT_ID = $response.id
            Write-Host "    待删除项目ID: $($response.id)" -ForegroundColor Gray
            return $true
        }
        return $false
    }

if ($DELETE_PROJECT_ID) {
    Test-API -TestName "TC-010: 删除项目" `
        -Method "DELETE" `
        -Url "$BASE_URL/projects/$DELETE_PROJECT_ID" `
        -ExpectedStatus 200 `
        -Validation {
            param($response)
            return $true
        }
    
    # 验证删除成功
    Test-API -TestName "TC-010: 验证项目已删除" `
        -Method "GET" `
        -Url "$BASE_URL/projects/$DELETE_PROJECT_ID" `
        -ExpectedStatus 404 `
        -Validation {
            param($response)
            return $true
        }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "二、项目群管理功能测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# TC-013: 查看项目群列表
Test-API -TestName "TC-013: 查看项目群列表" `
    -Method "GET" `
    -Url "$BASE_URL/programs" `
    -Validation {
        param($response)
        if ($response.items -or $response.total -ge 0) {
            Write-Host "    项目群总数: $($response.total)" -ForegroundColor Gray
            return $true
        }
        return $false
    }

# TC-014: 创建项目群
$createProgramBody = @{
    name = "测试项目群001"
    description = "测试项目群描述"
    status = "planning"
}

$createProgramResult = Test-API -TestName "TC-014: 创建项目群" `
    -Method "POST" `
    -Url "$BASE_URL/programs" `
    -Body $createProgramBody `
    -Validation {
        param($response)
        if ($response.id -and $response.program_code) {
            $script:TEST_PROGRAM_ID = $response.id
            Write-Host "    项目群ID: $($response.id)" -ForegroundColor Gray
            Write-Host "    项目群编码: $($response.program_code)" -ForegroundColor Gray
            return $true
        }
        return $false
    }

# TC-015: 编辑项目群
if ($TEST_PROGRAM_ID) {
    $updateProgramBody = @{
        name = "测试项目群001（已修改）"
        description = "修改后的描述"
    }
    
    Test-API -TestName "TC-015: 编辑项目群" `
        -Method "PUT" `
        -Url "$BASE_URL/programs/$TEST_PROGRAM_ID" `
        -Body $updateProgramBody `
        -Validation {
            param($response)
            if ($response.name -like "*已修改*") {
                return $true
            }
            return $false
        }
}

# TC-016: 删除项目群
if ($TEST_PROGRAM_ID) {
    Test-API -TestName "TC-016: 删除项目群" `
        -Method "DELETE" `
        -Url "$BASE_URL/programs/$TEST_PROGRAM_ID" `
        -ExpectedStatus 200 `
        -Validation {
            param($response)
            return $true
        }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "三、关联功能模块测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# TC-017: 查看项目任务列表
if ($TEST_PROJECT_ID) {
    Test-API -TestName "TC-017: 查看项目任务列表" `
        -Method "GET" `
        -Url "$BASE_URL/tasks?project_id=$TEST_PROJECT_ID" `
        -Validation {
            param($response)
            if ($response.items -or $response.total -ge 0) {
                Write-Host "    任务总数: $($response.total)" -ForegroundColor Gray
                return $true
            }
            return $false
        }
}

# TC-021: 查看项目周报列表
if ($TEST_PROJECT_ID) {
    Test-API -TestName "TC-021: 查看项目周报列表" `
        -Method "GET" `
        -Url "$BASE_URL/weekly-reports?project_id=$TEST_PROJECT_ID" `
        -Validation {
            param($response)
            if ($response.items -or $response.total -ge 0) {
                Write-Host "    周报总数: $($response.total)" -ForegroundColor Gray
                return $true
            }
            return $false
        }
}

# TC-019: 查看项目计划列表
if ($TEST_PROJECT_ID) {
    Test-API -TestName "TC-019: 查看项目计划列表" `
        -Method "GET" `
        -Url "$BASE_URL/projects/$TEST_PROJECT_ID/plans" `
        -Validation {
            param($response)
            if ($response.items -or $response.total -ge 0) {
                Write-Host "    计划总数: $($response.total)" -ForegroundColor Gray
                return $true
            }
            return $false
        }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试结果汇总" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "总测试数: $($testResults.total)" -ForegroundColor White
Write-Host "通过: $($testResults.passed)" -ForegroundColor Green
Write-Host "失败: $($testResults.failed)" -ForegroundColor Red
Write-Host "跳过: $($testResults.skipped)" -ForegroundColor Yellow
Write-Host ""

if ($testResults.failed -eq 0) {
    Write-Host "✅ 所有测试通过！" -ForegroundColor Green
} else {
    Write-Host "⚠️  有 $($testResults.failed) 个测试失败" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "失败的测试:" -ForegroundColor Red
    foreach ($detail in $testResults.details) {
        if ($detail.Status -eq "FAILED") {
            Write-Host "  - $($detail.Test): $($detail.Message)" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "测试完成时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

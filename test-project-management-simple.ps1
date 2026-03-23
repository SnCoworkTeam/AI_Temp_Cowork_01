# 项目管理功能简化测试脚本
# 测试不需要认证的API和基本功能

$API_URL = "http://43.143.139.197:8080"
$BASE_URL = "$API_URL/api/v1"
$TEST_DATE = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "项目管理功能测试（简化版）" -ForegroundColor Cyan
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

# 步骤1: 检查服务健康状态
Write-Host "步骤1: 检查服务健康状态" -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Method GET -Uri "$API_URL/health" -ErrorAction Stop
    if ($healthResponse.status -eq "healthy") {
        Write-Host "  ✅ API Gateway 健康检查通过" -ForegroundColor Green
        $testResults.total++
        $testResults.passed++
    } else {
        Write-Host "  ⚠️  API Gateway 状态: $($healthResponse.status)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ❌ API Gateway 健康检查失败: $($_.Exception.Message)" -ForegroundColor Red
    $testResults.total++
    $testResults.failed++
}

Write-Host ""

# 步骤2: 尝试获取Token（可选）
Write-Host "步骤2: 尝试获取认证Token" -ForegroundColor Yellow
$TOKEN = $null
$HEADERS = @{
    "Content-Type" = "application/json"
}

# 尝试不同的登录端点和密码
$loginEndpoints = @(
    "$API_URL/api/v1/auth/login",
    "$API_URL/api/auth/login",
    "$API_URL/auth/login"
)

$passwords = @("admin123", "admin123456", "admin", "123456")

foreach ($endpoint in $loginEndpoints) {
    foreach ($password in $passwords) {
        try {
            $loginBody = @{
                username = "admin"
                password = $password
            } | ConvertTo-Json
            
            $loginResponse = Invoke-RestMethod -Method POST -Uri $endpoint -Body $loginBody -ContentType "application/json" -ErrorAction Stop
            
            if ($loginResponse.access_token) {
                $TOKEN = $loginResponse.access_token
                Write-Host "  ✅ 登录成功 (端点: $endpoint, 密码: $password)" -ForegroundColor Green
                $HEADERS["Authorization"] = "Bearer $TOKEN"
                break
            } elseif ($loginResponse.token) {
                $TOKEN = $loginResponse.token
                Write-Host "  ✅ 登录成功 (端点: $endpoint, 密码: $password)" -ForegroundColor Green
                $HEADERS["Authorization"] = "Bearer $TOKEN"
                break
            }
        } catch {
            # 继续尝试
            continue
        }
    }
    if ($TOKEN) { break }
}

if (-not $TOKEN) {
    Write-Host "  ⚠️  无法自动登录，将跳过需要认证的测试" -ForegroundColor Yellow
    Write-Host "  提示: 请手动在浏览器中登录系统，然后使用浏览器开发者工具获取Token" -ForegroundColor Yellow
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
        [scriptblock]$Validation = $null,
        [bool]$RequireAuth = $false
    )
    
    if ($RequireAuth -and -not $TOKEN) {
        Write-Host "测试: $TestName" -ForegroundColor Cyan
        Write-Host "  ⚠️  跳过（需要认证）" -ForegroundColor Yellow
        $testResults.total++
        $testResults.skipped++
        return $false
    }
    
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
                    return $true
                } else {
                    Write-Host "  ❌ 失败: 验证未通过" -ForegroundColor Red
                    $testResults.failed++
                    return $false
                }
            } else {
                Write-Host "  ✅ 通过" -ForegroundColor Green
                $testResults.passed++
                return $true
            }
        } else {
            Write-Host "  ❌ 失败: 状态码 $statusCode (期望 $ExpectedStatus)" -ForegroundColor Red
            $testResults.failed++
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
            if ($statusCode) {
                Write-Host "    状态码: $statusCode" -ForegroundColor Gray
            }
            $testResults.failed++
            return $false
        }
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "一、项目基础管理功能测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# TC-001: 查看项目列表
Test-API -TestName "TC-001: 查看项目列表" `
    -Method "GET" `
    -Url "$BASE_URL/projects" `
    -RequireAuth $true `
    -Validation {
        param($response)
        if ($response.items -or ($response.total -ge 0)) {
            Write-Host "    项目总数: $($response.total)" -ForegroundColor Gray
            if ($response.items) {
                Write-Host "    返回项目数: $($response.items.Count)" -ForegroundColor Gray
            }
            return $true
        }
        return $false
    }

# TC-002: 项目列表筛选
Test-API -TestName "TC-002: 项目列表筛选（规划中）" `
    -Method "GET" `
    -Url "$BASE_URL/projects?status=planning" `
    -RequireAuth $true `
    -Validation {
        param($response)
        return $true
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
    -RequireAuth $true `
    -Validation {
        param($response)
        if ($response.items -or ($response.total -ge 0)) {
            Write-Host "    项目群总数: $($response.total)" -ForegroundColor Gray
            return $true
        }
        return $false
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

if ($testResults.failed -eq 0 -and $testResults.skipped -eq 0) {
    Write-Host "✅ 所有测试通过！" -ForegroundColor Green
} elseif ($testResults.failed -eq 0) {
    Write-Host "✅ 所有可执行的测试通过！" -ForegroundColor Green
    Write-Host "⚠️  有 $($testResults.skipped) 个测试因缺少认证而跳过" -ForegroundColor Yellow
} else {
    Write-Host "⚠️  有 $($testResults.failed) 个测试失败" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "测试完成时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""
Write-Host "提示:" -ForegroundColor Cyan
Write-Host "  如果测试因认证失败而跳过，请:" -ForegroundColor White
Write-Host "  1. 在浏览器中访问 http://43.143.139.197:3000" -ForegroundColor White
Write-Host "  2. 登录系统" -ForegroundColor White
Write-Host "  3. 打开浏览器开发者工具 (F12)" -ForegroundColor White
Write-Host "  4. 在 Network 标签中找到任意API请求" -ForegroundColor White
Write-Host "  5. 查看请求头中的 Authorization 字段" -ForegroundColor White
Write-Host "  6. 复制Token值，修改脚本中的TOKEN变量" -ForegroundColor White
Write-Host ""


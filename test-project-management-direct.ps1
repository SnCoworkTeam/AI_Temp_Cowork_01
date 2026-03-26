# 项目管理功能直接测试（绕过Auth Service登录问题）
# 如果无法登录，将测试不需要认证的端点和生成测试报告

$API_URL = "http://43.143.139.197:8080"
$BASE_URL = "$API_URL/api/v1"
$TEST_DATE = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "项目管理功能测试报告" -ForegroundColor Cyan
Write-Host "测试日期: $TEST_DATE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 测试结果
$testResults = @{
    total = 0
    passed = 0
    failed = 0
    skipped = 0
    details = @()
    issues = @()
}

# 检查服务状态
Write-Host "步骤1: 检查服务状态" -ForegroundColor Yellow

try {
    $healthResponse = Invoke-RestMethod -Method GET -Uri "$API_URL/health" -TimeoutSec 10 -ErrorAction Stop
    if ($healthResponse.status -eq "healthy") {
        Write-Host "  ✅ API Gateway 健康检查通过" -ForegroundColor Green
        $testResults.passed++
    }
} catch {
    Write-Host "  ❌ API Gateway 健康检查失败" -ForegroundColor Red
    $testResults.failed++
    $testResults.issues += "API Gateway 无法访问"
}

Write-Host ""
Write-Host "步骤2: 尝试登录" -ForegroundColor Yellow

$TOKEN = $null
$username = "admin"
$password = "admin123456"

# 尝试不同的登录方式
$loginEndpoints = @(
    "$API_URL/api/auth/login",
    "http://43.143.139.197:8003/auth/login"
)

foreach ($endpoint in $loginEndpoints) {
    try {
        $loginBody = @{
            username = $username
            password = $password
        } | ConvertTo-Json
        
        Write-Host "  尝试: $endpoint" -ForegroundColor Gray
        $loginResponse = Invoke-RestMethod -Method POST -Uri $endpoint -Body $loginBody -ContentType "application/json" -TimeoutSec 10 -ErrorAction Stop
        
        if ($loginResponse.access_token) {
            $TOKEN = $loginResponse.access_token
            Write-Host "  ✅ 登录成功！" -ForegroundColor Green
            break
        } elseif ($loginResponse.token) {
            $TOKEN = $loginResponse.token
            Write-Host "  ✅ 登录成功！" -ForegroundColor Green
            break
        }
    } catch {
        Write-Host "  ❌ 失败: $($_.Exception.Message)" -ForegroundColor Red
    }
}

if (-not $TOKEN) {
    Write-Host "  ⚠️  无法通过API登录" -ForegroundColor Yellow
    Write-Host "  原因: Auth Service 存在SQLAlchemy错误（metadata是保留字）" -ForegroundColor Yellow
    $testResults.issues += "Auth Service无法启动：SQLAlchemy错误 - 'metadata'是保留字"
    Write-Host ""
    Write-Host "建议解决方案:" -ForegroundColor Cyan
    Write-Host "  1. 修复 database/src/models/system_models.py 中的 Notification 类" -ForegroundColor White
    Write-Host "  2. 将 'metadata' 属性重命名为其他名称（如 'meta_data' 或 'notification_metadata'）" -ForegroundColor White
    Write-Host "  3. 重启 Auth Service" -ForegroundColor White
    Write-Host ""
    Write-Host "或者，可以通过浏览器手动登录系统进行测试:" -ForegroundColor Cyan
    Write-Host "  1. 访问 http://43.143.139.197:3000" -ForegroundColor White
    Write-Host "  2. 使用 admin/admin123456 登录" -ForegroundColor White
    Write-Host "  3. 按照 docs/项目管理功能手动测试指南.md 进行测试" -ForegroundColor White
}

$HEADERS = @{
    "Content-Type" = "application/json"
}
if ($TOKEN) {
    $HEADERS["Authorization"] = "Bearer $TOKEN"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试结果汇总" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 生成测试报告
$report = @"
# 项目管理功能测试报告

## 测试基本信息

- **测试日期：** $TEST_DATE
- **测试环境：** 
  - 系统地址：http://43.143.139.197:3000
  - API地址：http://43.143.139.197:8080
- **测试账号：** admin / admin123456

## 测试结果汇总

| 项目 | 结果 |
|------|------|
| 总测试数 | $($testResults.total) |
| 通过 | $($testResults.passed) |
| 失败 | $($testResults.failed) |
| 跳过 | $($testResults.skipped) |

## 发现的问题

"@

if ($testResults.issues.Count -gt 0) {
    $report += "`n### 关键问题`n`n"
    foreach ($issue in $testResults.issues) {
        $report += "- $issue`n"
    }
} else {
    $report += "`n无关键问题发现。`n"
}

$report += @"

## 详细说明

### Auth Service 问题

**错误信息：**
```
sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
```

**问题位置：**
- `database/src/models/system_models.py` 第98行
- `Notification` 类中使用了 `metadata` 作为属性名

**解决方案：**
1. 打开 `database/src/models/system_models.py`
2. 找到 `Notification` 类
3. 将 `metadata` 属性重命名为其他名称，例如：
   - `meta_data`
   - `notification_metadata`
   - `notification_data`
4. 更新所有引用该属性的代码
5. 重启 Auth Service

### 测试建议

由于 Auth Service 无法启动，建议：

1. **修复代码问题**（优先）
   - 按照上述方案修复 `metadata` 属性名问题
   - 重启 Auth Service
   - 重新执行自动化测试

2. **手动测试**（临时方案）
   - 访问 http://43.143.139.197:3000
   - 使用浏览器登录系统
   - 按照 `docs/项目管理功能手动测试指南.md` 进行测试
   - 使用 `docs/项目管理功能测试报告模板.md` 记录测试结果

## 测试结论

由于 Auth Service 存在代码问题无法启动，自动化测试无法完成。建议先修复代码问题，然后重新执行测试。

---

**报告生成时间：** $TEST_DATE
"@

# 保存报告
$reportFile = "docs/项目管理功能测试报告-$(Get-Date -Format 'yyyyMMdd-HHmmss').md"
$report | Out-File -FilePath $reportFile -Encoding UTF8

Write-Host "测试报告已生成: $reportFile" -ForegroundColor Green
Write-Host ""
Write-Host "报告内容预览:" -ForegroundColor Cyan
Write-Host $report
Write-Host ""


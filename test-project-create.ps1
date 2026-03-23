# 测试2: 项目创建功能
# 测试 POST /api/v1/projects

$API_URL = "http://43.143.139.197:8080"
$BASE_URL = "$API_URL/api/v1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试2: 项目创建功能" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 获取Token（必需）
$TOKEN = Read-Host "请输入认证Token（必需）"
if (-not $TOKEN) {
    Write-Host "❌ Token不能为空" -ForegroundColor Red
    exit 1
}

$HEADERS = @{
    "Authorization" = "Bearer $TOKEN"
    "Content-Type" = "application/json"
}

# 生成唯一的项目编码
$timestamp = Get-Date -Format 'yyyyMMddHHmmss'
$projectCode = "TEST-$timestamp"

Write-Host "将创建测试项目:" -ForegroundColor Yellow
Write-Host "  项目编码: $projectCode" -ForegroundColor Gray
Write-Host ""

# 创建项目数据
$projectData = @{
    project_code = $projectCode
    name = "测试项目 - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    description = "这是一个自动化测试创建的项目"
    status = "planning"
    priority = "medium"
    start_date = (Get-Date).ToString("yyyy-MM-dd")
    end_date = (Get-Date).AddMonths(3).ToString("yyyy-MM-dd")
    budget = 100000.00
} | ConvertTo-Json -Depth 10

Write-Host "1. 测试创建项目" -ForegroundColor Yellow
Write-Host "   请求数据:" -ForegroundColor Gray
Write-Host "   $($projectData -replace '`"', '')" -ForegroundColor Gray
Write-Host ""

try {
    $response = Invoke-RestMethod -Method POST -Uri "$BASE_URL/projects" -Headers $HEADERS -Body $projectData
    Write-Host "   ✅ 创建成功" -ForegroundColor Green
    Write-Host "   项目ID: $($response.id)" -ForegroundColor Gray
    Write-Host "   项目编码: $($response.project_code)" -ForegroundColor Gray
    Write-Host "   项目名称: $($response.name)" -ForegroundColor Gray
    Write-Host "   项目状态: $($response.status)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   💾 项目ID已保存，可用于后续测试" -ForegroundColor Cyan
    Write-Host "   项目ID: $($response.id)" -ForegroundColor Yellow
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "   ❌ 创建失败 (HTTP $statusCode)" -ForegroundColor Red
    Write-Host "   错误: $($_.Exception.Message)" -ForegroundColor Red
    
    # 尝试获取详细错误
    try {
        $errorBody = $_.ErrorDetails.Message | ConvertFrom-Json
        if ($errorBody.detail) {
            Write-Host "   详情: $($errorBody.detail)" -ForegroundColor Red
        }
    } catch {
        # 忽略JSON解析错误
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan


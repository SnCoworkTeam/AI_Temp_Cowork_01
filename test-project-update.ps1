# 测试3: 项目更新功能
# 测试 PUT /api/v1/projects/{project_id}

$API_URL = "http://43.143.139.197:8080"
$BASE_URL = "$API_URL/api/v1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试3: 项目更新功能" -ForegroundColor Cyan
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

# 获取项目ID
$projectId = Read-Host "请输入要更新的项目ID"
if (-not $projectId) {
    Write-Host "❌ 项目ID不能为空" -ForegroundColor Red
    exit 1
}

# 1. 先获取项目当前信息
Write-Host ""
Write-Host "1. 获取项目当前信息" -ForegroundColor Yellow
try {
    $currentProject = Invoke-RestMethod -Method GET -Uri "$BASE_URL/projects/$projectId" -Headers $HEADERS
    Write-Host "   ✅ 成功" -ForegroundColor Green
    Write-Host "   当前名称: $($currentProject.name)" -ForegroundColor Gray
    Write-Host "   当前状态: $($currentProject.status)" -ForegroundColor Gray
    Write-Host "   当前进度: $($currentProject.progress_percent)%" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ 获取项目信息失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2. 更新项目
Write-Host ""
Write-Host "2. 测试更新项目" -ForegroundColor Yellow

$updateData = @{
    name = "测试项目 - 已更新 $(Get-Date -Format 'HH:mm:ss')"
    description = "这是更新后的项目描述"
    status = "active"
    priority = "high"
    progress_percent = 25.5
} | ConvertTo-Json -Depth 10

Write-Host "   更新数据:" -ForegroundColor Gray
Write-Host "   $($updateData -replace '`"', '')" -ForegroundColor Gray
Write-Host ""

try {
    $response = Invoke-RestMethod -Method PUT -Uri "$BASE_URL/projects/$projectId" -Headers $HEADERS -Body $updateData
    Write-Host "   ✅ 更新成功" -ForegroundColor Green
    Write-Host "   更新后名称: $($response.name)" -ForegroundColor Gray
    Write-Host "   更新后状态: $($response.status)" -ForegroundColor Gray
    Write-Host "   更新后进度: $($response.progress_percent)%" -ForegroundColor Gray
    Write-Host "   更新时间: $($response.updated_at)" -ForegroundColor Gray
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "   ❌ 更新失败 (HTTP $statusCode)" -ForegroundColor Red
    Write-Host "   错误: $($_.Exception.Message)" -ForegroundColor Red
    
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


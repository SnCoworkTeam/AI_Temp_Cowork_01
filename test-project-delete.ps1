# 测试4: 项目删除功能
# 测试 DELETE /api/v1/projects/{project_id}

$API_URL = "http://43.143.139.197:8080"
$BASE_URL = "$API_URL/api/v1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试4: 项目删除功能" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "⚠️  警告: 此操作将永久删除项目及其相关数据！" -ForegroundColor Red
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
$projectId = Read-Host "请输入要删除的项目ID"
if (-not $projectId) {
    Write-Host "❌ 项目ID不能为空" -ForegroundColor Red
    exit 1
}

# 1. 先获取项目信息确认
Write-Host ""
Write-Host "1. 获取项目信息确认" -ForegroundColor Yellow
try {
    $project = Invoke-RestMethod -Method GET -Uri "$BASE_URL/projects/$projectId" -Headers $HEADERS
    Write-Host "   ✅ 找到项目" -ForegroundColor Green
    Write-Host "   项目名称: $($project.name)" -ForegroundColor Gray
    Write-Host "   项目编码: $($project.project_code)" -ForegroundColor Gray
    Write-Host "   项目状态: $($project.status)" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ 项目不存在或无法访问: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2. 确认删除
Write-Host ""
$confirm = Read-Host "确认删除此项目? (输入 'yes' 确认)"
if ($confirm -ne "yes") {
    Write-Host "   ⏭️  已取消删除" -ForegroundColor Yellow
    exit 0
}

# 3. 执行删除
Write-Host ""
Write-Host "2. 执行删除操作" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Method DELETE -Uri "$BASE_URL/projects/$projectId" -Headers $HEADERS
    Write-Host "   ✅ 删除成功" -ForegroundColor Green
    if ($response.message) {
        Write-Host "   消息: $($response.message)" -ForegroundColor Gray
    }
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "   ❌ 删除失败 (HTTP $statusCode)" -ForegroundColor Red
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

# 4. 验证删除
Write-Host ""
Write-Host "3. 验证删除结果" -ForegroundColor Yellow
try {
    $check = Invoke-RestMethod -Method GET -Uri "$BASE_URL/projects/$projectId" -Headers $HEADERS
    Write-Host "   ⚠️  项目仍然存在" -ForegroundColor Yellow
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 404) {
        Write-Host "   ✅ 项目已成功删除（404 Not Found）" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  无法确认删除状态: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan


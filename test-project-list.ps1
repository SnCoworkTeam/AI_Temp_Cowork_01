# 测试1: 项目列表查询功能
# 测试 GET /api/v1/projects

$API_URL = "http://43.143.139.197:8080"
$BASE_URL = "$API_URL/api/v1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试1: 项目列表查询功能" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 获取Token（可选）
$TOKEN = Read-Host "请输入认证Token（可选，按Enter跳过）"
$HEADERS = @{
    "Content-Type" = "application/json"
}
if ($TOKEN) {
    $HEADERS["Authorization"] = "Bearer $TOKEN"
}

# 1. 测试获取项目列表（无参数）
Write-Host "1. 测试获取项目列表（无参数）" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Method GET -Uri "$BASE_URL/projects" -Headers $HEADERS
    Write-Host "   ✅ 成功" -ForegroundColor Green
    Write-Host "   项目总数: $($response.total)" -ForegroundColor Gray
    Write-Host "   返回项目数: $($response.items.Count)" -ForegroundColor Gray
    if ($response.items.Count -gt 0) {
        Write-Host "   第一个项目: $($response.items[0].name) ($($response.items[0].project_code))" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ❌ 失败: $($_.Exception.Message)" -ForegroundColor Red
}

# 2. 测试分页查询
Write-Host ""
Write-Host "2. 测试分页查询 (skip=0, limit=5)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Method GET -Uri "$BASE_URL/projects?skip=0&limit=5" -Headers $HEADERS
    Write-Host "   ✅ 成功" -ForegroundColor Green
    Write-Host "   返回项目数: $($response.items.Count)" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ 失败: $($_.Exception.Message)" -ForegroundColor Red
}

# 3. 测试状态过滤
Write-Host ""
Write-Host "3. 测试状态过滤 (status=active)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Method GET -Uri "$BASE_URL/projects?status=active" -Headers $HEADERS
    Write-Host "   ✅ 成功" -ForegroundColor Green
    Write-Host "   进行中项目数: $($response.total)" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ 失败: $($_.Exception.Message)" -ForegroundColor Red
}

# 4. 测试获取项目详情（如果有项目）
Write-Host ""
Write-Host "4. 测试获取项目详情" -ForegroundColor Yellow
$projectId = Read-Host "请输入项目ID（或按Enter跳过）"
if ($projectId) {
    try {
        $response = Invoke-RestMethod -Method GET -Uri "$BASE_URL/projects/$projectId" -Headers $HEADERS
        Write-Host "   ✅ 成功" -ForegroundColor Green
        Write-Host "   项目名称: $($response.name)" -ForegroundColor Gray
        Write-Host "   项目编码: $($response.project_code)" -ForegroundColor Gray
        Write-Host "   项目状态: $($response.status)" -ForegroundColor Gray
        Write-Host "   进度: $($response.progress_percent)%" -ForegroundColor Gray
    } catch {
        Write-Host "   ❌ 失败: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "   ⏭️  跳过" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan


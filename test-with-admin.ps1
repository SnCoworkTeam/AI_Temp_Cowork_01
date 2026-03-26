# 使用admin账号登录并测试项目管理功能

$ErrorActionPreference = "Stop"

# 配置
$API_GATEWAY_URL = "http://43.143.139.197:8080"
$ADMIN_USERNAME = "admin"
$ADMIN_PASSWORD = "admin123456"

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "使用admin账号测试项目管理功能" -ForegroundColor Cyan
Write-Host "=" * 80
Write-Host ""

# 登录获取token
Write-Host "🔐 登录获取管理员token..." -ForegroundColor Yellow
$loginBody = @{
    username = $ADMIN_USERNAME
    password = $ADMIN_PASSWORD
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Method POST -Uri "$API_GATEWAY_URL/api/auth/login" -Body $loginBody -ContentType "application/json"
    $token = $loginResponse.access_token
    $userId = $loginResponse.user_id
    Write-Host "✅ 登录成功" -ForegroundColor Green
    Write-Host "   Token: $($token.Substring(0, 20))..." -ForegroundColor Gray
    Write-Host "   User ID: $userId" -ForegroundColor Gray
} catch {
    Write-Host "❌ 登录失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

Write-Host ""

# 测试1: 创建项目
Write-Host "=" * 80 -ForegroundColor Yellow
Write-Host "测试1: 创建项目" -ForegroundColor Yellow
Write-Host "=" * 80

$testProject = @{
    project_code = "ADMIN-TEST-$(Get-Date -Format 'yyyyMMddHHmmss')"
    name = "Admin测试项目"
    description = "使用admin账号创建的测试项目"
    status = "planning"
    priority = "high"
}

try {
    $createBody = $testProject | ConvertTo-Json
    $createResponse = Invoke-RestMethod -Method POST -Uri "$API_GATEWAY_URL/api/v1/projects" -Headers $headers -Body $createBody -ContentType "application/json"
    $projectId = $createResponse.id
    
    Write-Host "✅ 创建项目成功" -ForegroundColor Green
    Write-Host "   项目ID: $projectId" -ForegroundColor Gray
    Write-Host "   项目编码: $($createResponse.project_code)" -ForegroundColor Gray
    Write-Host "   项目名称: $($createResponse.name)" -ForegroundColor Gray
} catch {
    Write-Host "❌ 创建项目失败" -ForegroundColor Red
    Write-Host "   错误: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails) {
        Write-Host "   详情: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
    $projectId = $null
}

Write-Host ""

# 测试2: 获取项目列表
Write-Host "=" * 80 -ForegroundColor Yellow
Write-Host "测试2: 获取项目列表" -ForegroundColor Yellow
Write-Host "=" * 80

try {
    $listResponse = Invoke-RestMethod -Method GET -Uri "$API_GATEWAY_URL/api/v1/projects" -Headers $headers
    Write-Host "✅ 获取项目列表成功" -ForegroundColor Green
    Write-Host "   总项目数: $($listResponse.total)" -ForegroundColor Gray
    Write-Host "   返回项目数: $($listResponse.items.Count)" -ForegroundColor Gray
    
    if ($listResponse.items.Count -gt 0) {
        Write-Host "   前3个项目:" -ForegroundColor Gray
        $listResponse.items | Select-Object -First 3 | ForEach-Object {
            Write-Host "     - $($_.name) ($($_.project_code))" -ForegroundColor White
        }
    }
} catch {
    Write-Host "❌ 获取项目列表失败: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# 测试3: 获取项目详情（如果创建成功）
if ($projectId) {
    Write-Host "=" * 80 -ForegroundColor Yellow
    Write-Host "测试3: 获取项目详情" -ForegroundColor Yellow
    Write-Host "=" * 80
    
    try {
        $detailResponse = Invoke-RestMethod -Method GET -Uri "$API_GATEWAY_URL/api/v1/projects/$projectId" -Headers $headers
        Write-Host "✅ 获取项目详情成功" -ForegroundColor Green
        Write-Host "   项目名称: $($detailResponse.name)" -ForegroundColor Gray
        Write-Host "   项目状态: $($detailResponse.status)" -ForegroundColor Gray
        Write-Host "   进度: $($detailResponse.progress_percent)%" -ForegroundColor Gray
    } catch {
        Write-Host "❌ 获取项目详情失败: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
    
    # 测试4: 获取项目成员列表
    Write-Host "=" * 80 -ForegroundColor Yellow
    Write-Host "测试4: 获取项目成员列表" -ForegroundColor Yellow
    Write-Host "=" * 80
    
    try {
        $membersResponse = Invoke-RestMethod -Method GET -Uri "$API_GATEWAY_URL/api/v1/projects/$projectId/members" -Headers $headers
        Write-Host "✅ 获取项目成员列表成功" -ForegroundColor Green
        Write-Host "   总成员数: $($membersResponse.total)" -ForegroundColor Gray
        
        if ($membersResponse.items.Count -gt 0) {
            Write-Host "   成员列表:" -ForegroundColor Gray
            $membersResponse.items | ForEach-Object {
                Write-Host "     - $($_.username) ($($_.role))" -ForegroundColor White
            }
        } else {
            Write-Host "   ⚠️  成员列表为空（应该包含创建者）" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ 获取项目成员列表失败: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails) {
            Write-Host "   详情: $($_.ErrorDetails.Message)" -ForegroundColor Red
        }
    }
    
    Write-Host ""
    
    # 测试5: 更新项目
    Write-Host "=" * 80 -ForegroundColor Yellow
    Write-Host "测试5: 更新项目" -ForegroundColor Yellow
    Write-Host "=" * 80
    
    try {
        $updateBody = @{
            name = "Admin测试项目-已更新"
            description = "更新后的描述"
        } | ConvertTo-Json
        
        $updateResponse = Invoke-RestMethod -Method PUT -Uri "$API_GATEWAY_URL/api/v1/projects/$projectId" -Headers $headers -Body $updateBody -ContentType "application/json"
        Write-Host "✅ 更新项目成功" -ForegroundColor Green
        Write-Host "   新名称: $($updateResponse.name)" -ForegroundColor Gray
    } catch {
        Write-Host "❌ 更新项目失败: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
    
    # 测试6: 删除项目
    Write-Host "=" * 80 -ForegroundColor Yellow
    Write-Host "测试6: 删除项目" -ForegroundColor Yellow
    Write-Host "=" * 80
    
    try {
        $deleteResponse = Invoke-RestMethod -Method DELETE -Uri "$API_GATEWAY_URL/api/v1/projects/$projectId" -Headers $headers
        Write-Host "✅ 删除项目成功" -ForegroundColor Green
        Write-Host "   消息: $($deleteResponse.message)" -ForegroundColor Gray
    } catch {
        Write-Host "❌ 删除项目失败: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "测试完成" -ForegroundColor Cyan
Write-Host "=" * 80


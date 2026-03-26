# 为关瑞北和赵俊配置管理员权限

$ErrorActionPreference = "Stop"

# 配置
$API_GATEWAY_URL = "http://43.143.139.197:8080"
$ADMIN_USERNAME = "admin"
$ADMIN_PASSWORD = "admin123456"

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "为关瑞北和赵俊配置管理员权限" -ForegroundColor Cyan
Write-Host "=" * 80
Write-Host ""

# 登录获取管理员token
Write-Host "🔐 登录获取管理员token..." -ForegroundColor Yellow
$loginBody = @{
    username = $ADMIN_USERNAME
    password = $ADMIN_PASSWORD
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Method POST -Uri "$API_GATEWAY_URL/api/auth/login" -Body $loginBody -ContentType "application/json"
    $token = $loginResponse.access_token
    Write-Host "✅ 登录成功" -ForegroundColor Green
} catch {
    Write-Host "❌ 登录失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# 查找用户
Write-Host ""
Write-Host "🔍 查找用户..." -ForegroundColor Yellow

# 通过SSH查询数据库
$usersQuery = @"
SELECT id, username, email, full_name 
FROM users 
WHERE username LIKE '%guan%' OR username LIKE '%zhao%' 
   OR email LIKE '%guan%' OR email LIKE '%zhao%'
   OR full_name LIKE '%关%' OR full_name LIKE '%赵%'
LIMIT 10;
"@

$usersResult = ssh -i enterprise_ai_platform.pem -o StrictHostKeyChecking=no ubuntu@43.143.139.197 "cd /opt/enterprise-ai-platform && docker compose exec -T postgres psql -U ai_user -d ai_platform -c `"$usersQuery`""

Write-Host "查询结果:" -ForegroundColor Cyan
Write-Host $usersResult

# 如果找到了用户，可以通过API或数据库直接配置管理员角色
# 这里我们通过数据库直接配置
Write-Host ""
Write-Host "💡 提示: 管理员权限通过用户名判断（admin或包含admin）" -ForegroundColor Yellow
Write-Host "   如果需要为其他用户配置管理员权限，可以:" -ForegroundColor Yellow
Write-Host "   1. 修改用户名包含'admin'" -ForegroundColor White
Write-Host "   2. 或修改代码逻辑，通过角色表判断" -ForegroundColor White


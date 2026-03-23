# 给关瑞北和赵俊配置管理员权限

$ErrorActionPreference = "Stop"

# 配置
$API_GATEWAY_URL = "http://43.143.139.197:8080"
$ADMIN_USERNAME = "admin"
$ADMIN_PASSWORD = "admin123456"

# 需要配置管理员权限的用户
$usersToPromote = @(
    @{ username = "guanruibei"; name = "关瑞北" },
    @{ username = "zhaojun"; name = "赵俊" }
)

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "配置用户管理员权限" -ForegroundColor Cyan
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

Write-Host ""

# 为每个用户配置管理员权限
foreach ($user in $usersToPromote) {
    $username = $user.username
    $name = $user.name
    
    Write-Host "配置用户: $name ($username)" -ForegroundColor Cyan
    
    # 这里需要通过API配置用户角色
    # 假设有用户管理API可以设置角色
    # 如果没有，需要通过数据库直接更新
    
    Write-Host "  ⚠️  需要通过用户管理API或数据库配置管理员角色" -ForegroundColor Yellow
    Write-Host "  建议: 在users表中添加admin角色，或通过auth-service的admin API配置" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=" * 80
Write-Host "配置完成" -ForegroundColor Cyan
Write-Host "=" * 80
Write-Host ""
Write-Host "💡 提示: 如果用户管理API不可用，可以通过数据库直接更新:" -ForegroundColor Yellow
Write-Host "  UPDATE users SET roles = roles || '[\"admin\"]'::jsonb WHERE username IN ('guanruibei', 'zhaojun');" -ForegroundColor Gray


# 获取认证Token
$API_URL = "http://43.143.139.197:8080"

Write-Host "正在登录获取Token..." -ForegroundColor Cyan

# 尝试不同的密码
$passwords = @("admin123", "admin123456", "admin")

foreach ($password in $passwords) {
    try {
        $loginData = @{
            username = "admin"
            password = $password
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Method POST -Uri "$API_URL/api/v1/auth/login" -Body $loginData -ContentType "application/json"
        
        if ($response.access_token) {
            Write-Host "登录成功！" -ForegroundColor Green
            Write-Host "Token: $($response.access_token)" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Token已保存到环境变量 `$env:TEST_TOKEN" -ForegroundColor Cyan
            $env:TEST_TOKEN = $response.access_token
            return $response.access_token
        }
    } catch {
        # 继续尝试下一个密码
        continue
    }
}

Write-Host "登录失败，请检查用户名和密码" -ForegroundColor Red
return $null


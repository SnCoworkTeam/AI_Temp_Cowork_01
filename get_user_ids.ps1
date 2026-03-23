# 获取用户ID（通过用户名）
# 用于辅助关联用户到项目

$ErrorActionPreference = "Stop"

# 配置
$API_GATEWAY_URL = "http://43.143.139.197:8080"
$EXCEL_FILE = "中化国际数字化部员工统计_20251204.xlsx"

Write-Host "获取用户ID映射表..." -ForegroundColor Cyan
Write-Host ""

# 登录获取管理员token
$loginBody = @{
    username = "admin"
    password = "admin123456"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Method POST -Uri "$API_GATEWAY_URL/api/auth/login" -Body $loginBody -ContentType "application/json"
    $token = $loginResponse.access_token
} catch {
    Write-Host "❌ 登录失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# 读取Excel文件
$pythonScript = @"
import pandas as pd
import json
import sys

try:
    df = pd.read_excel('$EXCEL_FILE', sheet_name=0)
    
    name_col = None
    email_col = None
    
    for col in df.columns:
        col_str = str(col)
        if '姓名' in col_str or 'name' in col_str.lower():
            name_col = col
        elif '邮箱' in col_str or 'email' in col_str.lower() or 'mail' in col_str.lower():
            email_col = col
    
    if not name_col or not email_col:
        print(json.dumps({'error': f'无法识别姓名或邮箱列'}))
        sys.exit(1)
    
    users = []
    for idx, row in df.iterrows():
        name = str(row[name_col]).strip() if pd.notna(row[name_col]) else ""
        email = str(row[email_col]).strip() if pd.notna(row[email_col]) else ""
        
        if not email:
            continue
        
        username = email.split('@')[0] if '@' in email else email
        
        users.append({
            'name': name,
            'email': email,
            'username': username
        })
    
    print(json.dumps({'users': users}))
except Exception as e:
    print(json.dumps({'error': str(e)}))
    sys.exit(1)
"@

$pythonScript | Out-File -FilePath "temp_read_excel.py" -Encoding UTF8
$result = python temp_read_excel.py 2>&1
Remove-Item "temp_read_excel.py" -ErrorAction SilentlyContinue

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 读取Excel文件失败" -ForegroundColor Red
    exit 1
}

$data = $result | ConvertFrom-Json
$users = $data.users

# 通过数据库查询获取用户ID（需要SSH访问）
# 或者创建一个API端点来查询用户

Write-Host "由于没有用户查询API，建议通过以下方式获取用户ID:" -ForegroundColor Yellow
Write-Host "1. 通过数据库查询: SELECT id, username, email FROM users WHERE username IN (...)" -ForegroundColor White
Write-Host "2. 创建用户查询API端点" -ForegroundColor White
Write-Host "3. 在创建用户时保存用户ID映射" -ForegroundColor White
Write-Host ""

# 创建一个用户ID映射文件（JSON格式）
$userMap = @{}

foreach ($user in $users) {
    $userMap[$user.username] = @{
        name = $user.name
        email = $user.email
        user_id = $null  # 需要手动填写或通过API获取
    }
}

$userMap | ConvertTo-Json -Depth 3 | Out-File -FilePath "user_id_map.json" -Encoding UTF8
Write-Host "✅ 已创建用户映射文件: user_id_map.json" -ForegroundColor Green
Write-Host "   请手动填写user_id字段，或通过API获取" -ForegroundColor Yellow


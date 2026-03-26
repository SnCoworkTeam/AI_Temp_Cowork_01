# 从Excel文件批量创建用户账号
# 用户名使用邮箱前缀

$ErrorActionPreference = "Stop"

# 配置
$API_GATEWAY_URL = "http://43.143.139.197:8080"
$EXCEL_FILE = "中化国际数字化部员工统计_20251204.xlsx"
$DEFAULT_PASSWORD = "Sinochem@2025"  # 默认密码，首次登录后需要修改

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "从Excel文件批量创建用户账号" -ForegroundColor Cyan
Write-Host "=" * 80
Write-Host ""

# 检查Excel文件是否存在
if (-not (Test-Path $EXCEL_FILE)) {
    Write-Host "❌ Excel文件不存在: $EXCEL_FILE" -ForegroundColor Red
    exit 1
}

Write-Host "📄 读取Excel文件: $EXCEL_FILE" -ForegroundColor Yellow

# 使用Python读取Excel文件
$pythonScript = @"
import pandas as pd
import json
import sys

try:
    df = pd.read_excel('$EXCEL_FILE', sheet_name=0)
    
    # 识别列
    name_col = None
    email_col = None
    
    for col in df.columns:
        col_str = str(col)
        if '姓名' in col_str or 'name' in col_str.lower():
            name_col = col
        elif '邮箱' in col_str or 'email' in col_str.lower() or 'mail' in col_str.lower():
            email_col = col
    
    if not name_col or not email_col:
        print(json.dumps({'error': f'无法识别姓名或邮箱列。可用列: {list(df.columns)}'}))
        sys.exit(1)
    
    # 提取数据
    users = []
    for idx, row in df.iterrows():
        name = str(row[name_col]).strip() if pd.notna(row[name_col]) else ""
        email = str(row[email_col]).strip() if pd.notna(row[email_col]) else ""
        
        if not email:
            continue
        
        # 从邮箱提取用户名
        username = email.split('@')[0] if '@' in email else email
        
        users.append({
            'name': name,
            'email': email,
            'username': username
        })
    
    print(json.dumps({'users': users, 'total': len(users)}))
except Exception as e:
    print(json.dumps({'error': str(e)}))
    sys.exit(1)
"@

$pythonScript | Out-File -FilePath "temp_read_excel.py" -Encoding UTF8
$result = python temp_read_excel.py 2>&1
Remove-Item "temp_read_excel.py" -ErrorAction SilentlyContinue

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 读取Excel文件失败" -ForegroundColor Red
    Write-Host $result
    exit 1
}

$data = $result | ConvertFrom-Json

if ($data.error) {
    Write-Host "❌ 错误: $($data.error)" -ForegroundColor Red
    exit 1
}

$users = $data.users
$total = $data.total

Write-Host "✅ 读取成功，共 $total 条记录" -ForegroundColor Green
Write-Host ""

# 登录获取管理员token
Write-Host "🔐 登录获取管理员token..." -ForegroundColor Yellow
$loginBody = @{
    username = "admin"
    password = "admin123456"
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

# 创建用户
Write-Host ""
Write-Host "=" * 80
Write-Host "开始创建用户..." -ForegroundColor Cyan
Write-Host "=" * 80
Write-Host ""

$successCount = 0
$failCount = 0
$skipCount = 0
$userMap = @{}  # 用户ID映射表：username -> user_id

foreach ($user in $users) {
    $name = $user.name
    $email = $user.email
    $username = $user.username
    
    Write-Host "创建用户: $name ($username) - $email" -ForegroundColor Gray
    
    $registerBody = @{
        username = $username
        email = $email
        password = $DEFAULT_PASSWORD
        full_name = $name
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Method POST -Uri "$API_GATEWAY_URL/api/auth/register" -Headers $headers -Body $registerBody -ContentType "application/json"
        
        # 保存用户ID
        if ($response.user_id) {
            $userMap[$username] = @{
                user_id = $response.user_id
                name = $name
                email = $email
            }
            Write-Host "  ✅ 创建成功 (ID: $($response.user_id))" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "  ✅ 创建成功（但未返回用户ID）" -ForegroundColor Green
            $successCount++
        }
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        $errorMessage = $_.Exception.Message
        
        if ($statusCode -eq 400 -or $statusCode -eq 409) {
            # 用户已存在，尝试获取用户ID
            Write-Host "  ⚠️  用户已存在，尝试获取用户ID..." -ForegroundColor Yellow
            
            # 尝试通过登录获取用户信息（需要密码）
            # 或者通过其他方式获取用户ID
            # 暂时标记为需要后续查询
            $userMap[$username] = @{
                user_id = $null  # 需要后续查询
                name = $name
                email = $email
            }
            $skipCount++
        } else {
            Write-Host "  ❌ 创建失败: $statusCode - $errorMessage" -ForegroundColor Red
            $failCount++
        }
    }
}

# 保存用户ID映射到文件
if ($userMap.Count -gt 0) {
    $userMap | ConvertTo-Json -Depth 3 | Out-File -FilePath "user_id_map.json" -Encoding UTF8
    Write-Host ""
    Write-Host "✅ 用户ID映射已保存到: user_id_map.json" -ForegroundColor Green
    Write-Host "   提示: 对于已存在的用户，需要运行 query_users_from_db.ps1 获取用户ID" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=" * 80
Write-Host "创建完成" -ForegroundColor Cyan
Write-Host "=" * 80
Write-Host "✅ 成功: $successCount" -ForegroundColor Green
Write-Host "⚠️  跳过: $skipCount" -ForegroundColor Yellow
Write-Host "❌ 失败: $failCount" -ForegroundColor Red
Write-Host "📊 总计: $total" -ForegroundColor Cyan
Write-Host ""
Write-Host "默认密码: $DEFAULT_PASSWORD" -ForegroundColor Yellow
Write-Host "提示: 用户首次登录后应修改密码" -ForegroundColor Yellow


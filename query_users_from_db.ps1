# 从数据库查询用户ID并创建映射文件
# 需要SSH访问服务器

$ErrorActionPreference = "Stop"

# 配置
$EXCEL_FILE = "中化国际数字化部员工统计_20251204.xlsx"
$USER_ID_MAP_FILE = "user_id_map.json"
$SSH_HOST = "43.143.139.197"
$SSH_USER = "ubuntu"
$SSH_KEY = "enterprise_ai_platform.pem"

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "从数据库查询用户ID" -ForegroundColor Cyan
Write-Host "=" * 80
Write-Host ""

# 读取Excel文件获取用户名列表
Write-Host "📄 读取Excel文件..." -ForegroundColor Yellow
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
$usernames = $users | ForEach-Object { $_.username }

Write-Host "✅ 读取成功，共 $($users.Count) 个用户" -ForegroundColor Green
Write-Host ""

# 构建SQL查询
$usernameList = ($usernames | ForEach-Object { "'$_'" }) -join ","
$sqlQuery = "SELECT id, username, email, full_name FROM users WHERE username IN ($usernameList);"

Write-Host "📋 SQL查询:" -ForegroundColor Yellow
Write-Host $sqlQuery -ForegroundColor Gray
Write-Host ""

# 通过SSH执行查询
Write-Host "🔍 通过SSH查询数据库..." -ForegroundColor Yellow

$queryScript = @"
import psycopg2
import json
import sys
import os

try:
    # 从环境变量或默认值获取数据库连接信息
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'postgres'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'enterprise_ai'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres')
    )
    
    cur = conn.cursor()
    
    # 查询用户
    usernames = [$($usernames | ForEach-Object { "'$_'" } | Join-String -Separator ',')]
    placeholders = ','.join(['%s'] * len(usernames))
    query = f"SELECT id, username, email, full_name FROM users WHERE username IN ({placeholders})"
    
    cur.execute(query, usernames)
    results = cur.fetchall()
    
    user_map = {}
    for row in results:
        user_id, username, email, full_name = row
        user_map[username] = {
            'user_id': str(user_id),
            'email': email,
            'full_name': full_name or ''
        }
    
    cur.close()
    conn.close()
    
    print(json.dumps({'user_map': user_map, 'found': len(user_map), 'total': len(usernames)}))
except Exception as e:
    print(json.dumps({'error': str(e), 'user_map': {}, 'found': 0, 'total': len(usernames)}))
"@

# 上传查询脚本到服务器并执行
$queryScript | Out-File -FilePath "temp_query_users.py" -Encoding UTF8

Write-Host "📤 上传查询脚本到服务器..." -ForegroundColor Yellow
scp -i $SSH_KEY -o StrictHostKeyChecking=no temp_query_users.py ${SSH_USER}@${SSH_HOST}:/tmp/query_users.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 上传脚本失败" -ForegroundColor Red
    Remove-Item "temp_query_users.py" -ErrorAction SilentlyContinue
    exit 1
}

Write-Host "✅ 上传成功" -ForegroundColor Green

# 执行查询
Write-Host "⚙️  执行查询..." -ForegroundColor Yellow
$queryResult = ssh -i $SSH_KEY -o StrictHostKeyChecking=no ${SSH_USER}@${SSH_HOST} "cd /opt/enterprise-ai-platform && docker compose exec -T database python /tmp/query_users.py"

Remove-Item "temp_query_users.py" -ErrorAction SilentlyContinue

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 查询失败" -ForegroundColor Red
    exit 1
}

# 解析结果
try {
    $queryData = $queryResult | ConvertFrom-Json
    
    if ($queryData.error) {
        Write-Host "❌ 查询错误: $($queryData.error)" -ForegroundColor Red
        exit 1
    }
    
    $userMap = $queryData.user_map
    $found = $queryData.found
    $total = $queryData.total
    
    Write-Host "✅ 查询成功，找到 $found / $total 个用户" -ForegroundColor Green
    Write-Host ""
    
    # 创建完整的用户映射（包含未找到的用户）
    $fullUserMap = @{}
    foreach ($user in $users) {
        $username = $user.username
        if ($userMap.PSObject.Properties.Name -contains $username) {
            $fullUserMap[$username] = @{
                user_id = $userMap.$username.user_id
                name = $user.name
                email = $user.email
            }
        } else {
            $fullUserMap[$username] = @{
                user_id = $null
                name = $user.name
                email = $user.email
            }
            Write-Host "⚠️  未找到用户: $username" -ForegroundColor Yellow
        }
    }
    
    # 保存到文件
    $fullUserMap | ConvertTo-Json -Depth 3 | Out-File -FilePath $USER_ID_MAP_FILE -Encoding UTF8
    Write-Host ""
    Write-Host "✅ 用户ID映射已保存到: $USER_ID_MAP_FILE" -ForegroundColor Green
    
} catch {
    Write-Host "❌ 解析查询结果失败: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "查询结果:" -ForegroundColor Yellow
    Write-Host $queryResult
    exit 1
}


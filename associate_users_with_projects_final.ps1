# 将用户与项目关联（最终版）
# 通过用户ID映射文件或数据库查询获取用户ID

$ErrorActionPreference = "Stop"

# 配置
$API_GATEWAY_URL = "http://43.143.139.197:8080"
$EXCEL_FILE = "中化国际数字化部员工统计_20251204.xlsx"
$USER_ID_MAP_FILE = "user_id_map.json"  # 用户ID映射文件（可选）

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "将用户与项目关联" -ForegroundColor Cyan
Write-Host "=" * 80
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

# 读取Excel文件获取用户列表
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
    exit 1
}

$data = $result | ConvertFrom-Json
$users = $data.users
$totalUsers = $data.total

Write-Host "✅ 读取成功，共 $totalUsers 个用户" -ForegroundColor Green
Write-Host ""

# 尝试加载用户ID映射文件
$userMap = @{}
if (Test-Path $USER_ID_MAP_FILE) {
    Write-Host "📋 加载用户ID映射文件..." -ForegroundColor Yellow
    try {
        $mapData = Get-Content $USER_ID_MAP_FILE -Raw | ConvertFrom-Json
        foreach ($key in $mapData.PSObject.Properties.Name) {
            $userMap[$key] = $mapData.$key.user_id
        }
        Write-Host "✅ 已加载 $($userMap.Count) 个用户ID映射" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  加载用户ID映射文件失败，将尝试通过其他方式获取" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  用户ID映射文件不存在，将通过数据库查询获取用户ID" -ForegroundColor Yellow
    Write-Host "   建议先运行 get_user_ids.ps1 创建映射文件" -ForegroundColor Yellow
}

# 如果映射文件不完整，尝试通过数据库查询获取用户ID
if ($userMap.Count -lt $totalUsers) {
    Write-Host ""
    Write-Host "🔍 通过数据库查询获取用户ID..." -ForegroundColor Yellow
    
    # 通过SSH查询数据库
    $usernames = $users | ForEach-Object { $_.username }
    $usernameList = $usernames -join "','"
    
    $queryScript = @"
import psycopg2
import json
import sys
import os

try:
    # 数据库连接信息
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'enterprise_ai'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres')
    )
    
    cur = conn.cursor()
    
    # 查询用户
    usernames = ['$($usernames -join "','")']
    placeholders = ','.join(['%s'] * len(usernames))
    query = f"SELECT id, username, email FROM users WHERE username IN ({placeholders})"
    
    cur.execute(query, usernames)
    results = cur.fetchall()
    
    user_map = {}
    for row in results:
        user_id, username, email = row
        user_map[username] = str(user_id)
    
    cur.close()
    conn.close()
    
    print(json.dumps({'user_map': user_map}))
except Exception as e:
    print(json.dumps({'error': str(e), 'user_map': {}}))
"@

    # 通过SSH执行查询
    Write-Host "   通过SSH查询数据库..." -ForegroundColor Gray
    
    # 这里需要SSH访问服务器
    # 暂时跳过，使用手动输入的方式
    Write-Host "   ⚠️  需要SSH访问，暂时跳过自动查询" -ForegroundColor Yellow
    Write-Host "   请手动填写用户ID，或使用以下SQL查询:" -ForegroundColor Yellow
    Write-Host "   SELECT id, username, email FROM users WHERE username IN ('$($usernames -join "','")');" -ForegroundColor Gray
    Write-Host ""
    
    # 提示用户手动输入用户ID
    Write-Host "💡 建议: 创建一个用户查询API端点，或使用数据库查询工具获取用户ID" -ForegroundColor Yellow
    Write-Host ""
}

# 获取项目列表
Write-Host "📋 获取项目列表..." -ForegroundColor Yellow
try {
    $projectsResponse = Invoke-RestMethod -Method GET -Uri "$API_GATEWAY_URL/api/v1/projects" -Headers $headers
    $projects = $projectsResponse.items
    
    if ($projects.Count -eq 0) {
        Write-Host "⚠️  没有找到项目，请先创建项目" -ForegroundColor Yellow
        exit 0
    }
    
    Write-Host "✅ 找到 $($projects.Count) 个项目" -ForegroundColor Green
    Write-Host ""
    
    # 显示项目列表
    Write-Host "项目列表:" -ForegroundColor Cyan
    for ($i = 0; $i -lt $projects.Count; $i++) {
        $project = $projects[$i]
        Write-Host "  $($i + 1). $($project.name) ($($project.project_code)) - ID: $($project.id)" -ForegroundColor White
    }
    Write-Host ""
    
} catch {
    Write-Host "❌ 获取项目列表失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 选择项目
Write-Host "请选择要关联的项目（输入项目编号，多个项目用逗号分隔，或输入 'all' 关联所有项目）:" -ForegroundColor Yellow
$projectSelection = Read-Host

$selectedProjects = @()

if ($projectSelection -eq "all") {
    $selectedProjects = $projects
    Write-Host "✅ 已选择所有项目" -ForegroundColor Green
} else {
    $indices = $projectSelection -split ',' | ForEach-Object { [int]$_.Trim() - 1 }
    foreach ($idx in $indices) {
        if ($idx -ge 0 -and $idx -lt $projects.Count) {
            $selectedProjects += $projects[$idx]
        } else {
            Write-Host "⚠️  无效的项目编号: $($idx + 1)" -ForegroundColor Yellow
        }
    }
}

if ($selectedProjects.Count -eq 0) {
    Write-Host "❌ 没有选择任何项目" -ForegroundColor Red
    exit 1
}

Write-Host "已选择 $($selectedProjects.Count) 个项目" -ForegroundColor Green
Write-Host ""

# 选择角色
Write-Host "请选择用户角色:" -ForegroundColor Yellow
Write-Host "  1. manager (项目经理 - 所有权限)" -ForegroundColor White
Write-Host "  2. member (项目成员 - 创建、查看、更新)" -ForegroundColor White
Write-Host "  3. viewer (查看者 - 只能查看)" -ForegroundColor White
Write-Host ""
$roleSelection = Read-Host "输入角色编号 (默认: 2-member)"

$role = "member"
switch ($roleSelection) {
    "1" { $role = "manager" }
    "2" { $role = "member" }
    "3" { $role = "viewer" }
    default { $role = "member" }
}

Write-Host "✅ 已选择角色: $role" -ForegroundColor Green
Write-Host ""

# 开始关联用户到项目
Write-Host "=" * 80
Write-Host "开始关联用户到项目..." -ForegroundColor Cyan
Write-Host "=" * 80
Write-Host ""

$totalSuccess = 0
$totalFail = 0
$totalSkip = 0

foreach ($project in $selectedProjects) {
    Write-Host ""
    Write-Host "📁 项目: $($project.name) ($($project.project_code))" -ForegroundColor Cyan
    Write-Host "-" * 60
    
    $projectSuccess = 0
    $projectFail = 0
    $projectSkip = 0
    
    foreach ($user in $users) {
        $username = $user.username
        $name = $user.name
        $email = $user.email
        
        Write-Host "  关联用户: $name ($username)" -ForegroundColor Gray -NoNewline
        
        # 获取用户ID
        $userId = $userMap[$username]
        
        if (-not $userId) {
            Write-Host " - ⚠️  未找到用户ID，跳过" -ForegroundColor Yellow
            $projectSkip++
            $totalSkip++
            continue
        }
        
        # 添加用户到项目
        $memberBody = @{
            user_id = $userId
            role = $role
            joined_at = (Get-Date -Format "yyyy-MM-dd")
        } | ConvertTo-Json
        
        try {
            $response = Invoke-RestMethod -Method POST -Uri "$API_GATEWAY_URL/api/v1/projects/$($project.id)/members" -Headers $headers -Body $memberBody -ContentType "application/json"
            Write-Host " - ✅ 成功" -ForegroundColor Green
            $projectSuccess++
            $totalSuccess++
        } catch {
            $statusCode = $_.Exception.Response.StatusCode.value__
            $errorMessage = $_.Exception.Message
            
            if ($statusCode -eq 404) {
                Write-Host " - ⚠️  用户不存在，跳过" -ForegroundColor Yellow
                $projectSkip++
                $totalSkip++
            } elseif ($statusCode -eq 400 -or $statusCode -eq 409) {
                Write-Host " - ⚠️  用户已是成员，跳过" -ForegroundColor Yellow
                $projectSkip++
                $totalSkip++
            } else {
                Write-Host " - ❌ 失败: $statusCode - $errorMessage" -ForegroundColor Red
                $projectFail++
                $totalFail++
            }
        }
    }
    
    Write-Host ""
    Write-Host "  项目统计: ✅ $projectSuccess | ⚠️  $projectSkip | ❌ $projectFail" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "=" * 80
Write-Host "关联完成" -ForegroundColor Cyan
Write-Host "=" * 80
Write-Host "✅ 成功: $totalSuccess" -ForegroundColor Green
Write-Host "⚠️  跳过: $totalSkip" -ForegroundColor Yellow
Write-Host "❌ 失败: $totalFail" -ForegroundColor Red
Write-Host "📊 总计: $($totalSuccess + $totalSkip + $totalFail)" -ForegroundColor Cyan


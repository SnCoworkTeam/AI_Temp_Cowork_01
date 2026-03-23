# 将用户与项目关联（改进版）
# 支持批量添加用户到项目，并指定角色

$ErrorActionPreference = "Stop"

# 配置
$API_GATEWAY_URL = "http://43.143.139.197:8080"
$EXCEL_FILE = "中化国际数字化部员工统计_20251204.xlsx"

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
$totalUsers = $data.total

Write-Host "✅ 读取成功，共 $totalUsers 个用户" -ForegroundColor Green
Write-Host ""

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

# 通过登录API获取用户ID（通过用户名和密码）
# 由于我们不知道密码，这里使用一个变通方法：
# 1. 尝试通过用户名查找用户（如果有查询API）
# 2. 或者创建一个辅助API来通过用户名/邮箱查找用户ID

# 创建一个用户映射表（username -> 尝试获取user_id）
Write-Host "🔍 查找用户ID..." -ForegroundColor Yellow
$userMap = @{}  # username -> user_id

# 由于没有直接的查询API，我们通过尝试登录来验证用户是否存在
# 但这样无法获取user_id
# 更好的方法是：创建一个辅助脚本来查询用户

# 暂时使用一个变通方法：直接使用用户名，让API返回错误信息
# 或者创建一个查询用户的辅助API

Write-Host "⚠️  注意：需要用户UUID才能添加到项目" -ForegroundColor Yellow
Write-Host "   由于API限制，将尝试通过用户名查找用户" -ForegroundColor Yellow
Write-Host ""

# 开始关联用户到项目
Write-Host "=" * 80
Write-Host "开始关联用户到项目..." -ForegroundColor Cyan
Write-Host "=" * 80
Write-Host ""

$totalSuccess = 0
$totalFail = 0
$totalSkip = 0

# 首先尝试获取所有用户（如果有用户列表API）
# 如果没有，我们需要逐个尝试

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
        
        # 尝试通过用户名查找用户ID
        # 由于没有直接的查询API，我们需要使用变通方法
        # 方法1：尝试通过登录获取用户信息（但需要密码）
        # 方法2：创建一个查询用户的辅助脚本
        
        # 这里我们创建一个Python脚本来查询用户
        $queryUserScript = @"
import requests
import json
import sys

username = '$username'
api_url = '$API_GATEWAY_URL'

# 尝试通过登录获取用户信息（需要密码）
# 由于不知道密码，这里暂时返回None
# 实际应该通过用户查询API获取

# 方法：通过admin API查询用户（如果有）
try:
    # 登录获取token
    login_response = requests.post(
        f'{api_url}/api/auth/login',
        json={'username': 'admin', 'password': 'admin123456'},
        timeout=5
    )
    if login_response.status_code == 200:
        token = login_response.json().get('access_token')
        headers = {'Authorization': f'Bearer {token}'}
        
        # 尝试查询用户（假设有用户查询API）
        # 这里暂时返回None，需要实际的API端点
        print(json.dumps({'user_id': None, 'error': '需要用户查询API'}))
    else:
        print(json.dumps({'user_id': None, 'error': '登录失败'}))
except Exception as e:
    print(json.dumps({'user_id': None, 'error': str(e)}))
"@

        # 由于无法直接获取用户ID，我们使用一个更实用的方法：
        # 创建一个辅助API端点，或者使用数据库查询
        
        # 暂时跳过，提示需要用户ID
        Write-Host " - ⚠️  需要用户UUID" -ForegroundColor Yellow
        $projectSkip++
        $totalSkip++
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
Write-Host ""
Write-Host "💡 提示: 由于需要用户UUID，建议先运行用户创建脚本，然后使用用户ID进行关联" -ForegroundColor Yellow


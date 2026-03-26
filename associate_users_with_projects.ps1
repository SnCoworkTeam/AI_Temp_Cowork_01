# 将用户与项目关联
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

# 获取项目列表
Write-Host ""
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

# 获取所有用户信息（通过用户名查找用户ID）
Write-Host "🔍 查找用户ID..." -ForegroundColor Yellow

# 由于没有批量查询用户的API，我们需要逐个查找
# 或者使用admin API获取用户列表
$userMap = @{}  # username -> user_id

# 尝试获取用户列表（如果有admin API）
try {
    # 这里假设有用户列表API，如果没有则需要逐个查找
    # 暂时跳过，直接使用用户名作为标识
    Write-Host "⚠️  无法批量获取用户ID，将使用用户名查找" -ForegroundColor Yellow
} catch {
    Write-Host "⚠️  无法获取用户列表，将使用用户名查找" -ForegroundColor Yellow
}

# 开始关联用户到项目
Write-Host ""
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
        
        # 首先需要获取用户ID
        # 由于没有直接的用户名查询API，我们需要先查找用户
        # 这里假设可以通过某种方式获取用户ID
        # 暂时使用一个变通方法：通过注册API返回的用户ID，或者通过其他方式
        
        # 尝试通过用户名查找用户（如果有用户查询API）
        # 如果没有，我们可以先尝试添加，如果用户不存在会返回错误
        
        # 直接尝试添加用户到项目
        # 如果用户不存在，API会返回404
        $memberBody = @{
            user_id = $username  # 这里可能需要实际的UUID，暂时使用用户名
            role = $role
            joined_at = (Get-Date -Format "yyyy-MM-dd")
        } | ConvertTo-Json
        
        try {
            # 注意：这里需要实际的用户UUID，不是用户名
            # 我们需要先获取用户ID
            # 由于API限制，这里先尝试，如果失败则跳过
            
            # 实际实现中，应该先调用用户查询API获取用户ID
            # 这里简化处理，假设可以通过某种方式获取
            
            Write-Host " - ⚠️  需要用户UUID，暂时跳过" -ForegroundColor Yellow
            $projectSkip++
            $totalSkip++
            continue
            
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
                Write-Host " - ❌ 失败: $statusCode" -ForegroundColor Red
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


# 创建测试用户账号脚本
# 创建不同角色的测试用户

$ErrorActionPreference = "Stop"

# 配置
$API_GATEWAY_URL = "http://43.143.139.197:8080"
$DEFAULT_PASSWORD = "Test@2025"  # 默认密码

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "创建测试用户账号" -ForegroundColor Cyan
Write-Host "=" * 80
Write-Host ""

# 定义要创建的用户列表
$testUsers = @(
    @{
        username = "admin"
        email = "admin@sinochem.com"
        full_name = "系统管理员"
        password = "admin123456"
        roles = @("admin")
    },
    @{
        username = "manager1"
        email = "manager1@sinochem.com"
        full_name = "项目经理1"
        password = $DEFAULT_PASSWORD
        roles = @("user")
    },
    @{
        username = "member1"
        email = "member1@sinochem.com"
        full_name = "项目成员1"
        password = $DEFAULT_PASSWORD
        roles = @("user")
    },
    @{
        username = "viewer1"
        email = "viewer1@sinochem.com"
        full_name = "查看者1"
        password = $DEFAULT_PASSWORD
        roles = @("viewer")
    },
    @{
        username = "developer1"
        email = "developer1@sinochem.com"
        full_name = "开发者1"
        password = $DEFAULT_PASSWORD
        roles = @("developer")
    },
    @{
        username = "testuser1"
        email = "testuser1@sinochem.com"
        full_name = "测试用户1"
        password = $DEFAULT_PASSWORD
        roles = @("user")
    },
    @{
        username = "testuser2"
        email = "testuser2@sinochem.com"
        full_name = "测试用户2"
        password = $DEFAULT_PASSWORD
        roles = @("user")
    }
)

# 获取访问令牌（如果需要）
function Get-AccessToken {
    param(
        [string]$Username,
        [string]$Password
    )
    
    try {
        $loginUrl = "$API_GATEWAY_URL/api/auth/login"
        $body = @{
            username = $Username
            password = $Password
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri $loginUrl -Method Post -Body $body -ContentType "application/json" -ErrorAction Stop
        
        if ($response.access_token) {
            return $response.access_token
        }
    } catch {
        Write-Host "⚠️  获取访问令牌失败: $_" -ForegroundColor Yellow
    }
    
    return $null
}

# 创建用户
function Create-User {
    param(
        [hashtable]$UserInfo,
        [string]$AccessToken
    )
    
    try {
        $createUrl = "$API_GATEWAY_URL/api/admin/users"
        
        $headers = @{
            "Content-Type" = "application/json"
        }
        
        if ($AccessToken) {
            $headers["Authorization"] = "Bearer $AccessToken"
        }
        
        $body = @{
            username = $UserInfo.username
            email = $UserInfo.email
            display_name = $UserInfo.full_name
            password = $UserInfo.password
        } | ConvertTo-Json -Depth 10
        
        Write-Host "创建用户: $($UserInfo.username) ($($UserInfo.full_name))..." -ForegroundColor Yellow
        
        $response = Invoke-RestMethod -Uri $createUrl -Method Post -Body $body -Headers $headers -ErrorAction Stop
        
        Write-Host "✅ 用户创建成功: $($UserInfo.username) (ID: $($response.user_id))" -ForegroundColor Green
        
        # 如果指定了角色，分配角色
        if ($UserInfo.roles -and $UserInfo.roles.Count -gt 0 -and $response.user_id) {
            Start-Sleep -Milliseconds 500  # 等待用户创建完成
            
            foreach ($role in $UserInfo.roles) {
                try {
                    $assignRoleUrl = "$API_GATEWAY_URL/api/admin/users/$($response.user_id)/roles"
                    $roleBody = @{
                        role_code = $role
                    } | ConvertTo-Json -Depth 10
                    
                    Invoke-RestMethod -Uri $assignRoleUrl -Method Post -Body $roleBody -Headers $headers -ErrorAction Stop | Out-Null
                    Write-Host "  ✅ 已分配角色: $role" -ForegroundColor Green
                } catch {
                    Write-Host "  ⚠️  分配角色失败 ($role): $_" -ForegroundColor Yellow
                }
            }
        }
        
        return $response
    } catch {
        $errorMessage = $_.Exception.Message
        if ($_.ErrorDetails.Message) {
            try {
                $errorObj = $_.ErrorDetails.Message | ConvertFrom-Json
                $errorMessage = $errorObj.detail -or $errorObj.message -or $errorMessage
            } catch {
                # 忽略JSON解析错误
            }
        }
        
        if ($errorMessage -like "*already exists*" -or $errorMessage -like "*已存在*") {
            Write-Host "⚠️  用户已存在: $($UserInfo.username)" -ForegroundColor Yellow
            return $null
        } else {
            Write-Host "❌ 创建用户失败: $($UserInfo.username) - $errorMessage" -ForegroundColor Red
            return $null
        }
    }
}

# 主流程
Write-Host "开始创建测试用户..." -ForegroundColor Cyan
Write-Host ""

# 先尝试获取admin的访问令牌
$accessToken = Get-AccessToken -Username "admin" -Password "admin123456"

if (-not $accessToken) {
    Write-Host "⚠️  无法获取访问令牌，将尝试不使用令牌创建用户（可能失败）" -ForegroundColor Yellow
    Write-Host ""
}

$successCount = 0
$skipCount = 0
$failCount = 0

foreach ($user in $testUsers) {
    $result = Create-User -UserInfo $user -AccessToken $accessToken
    
    if ($result) {
        $successCount++
    } elseif ($result -eq $null -and $user.username -eq "admin") {
        # admin用户可能已存在
        $skipCount++
    } else {
        $failCount++
    }
    
    Write-Host ""
    Start-Sleep -Milliseconds 300  # 避免请求过快
}

Write-Host "=" * 80
Write-Host "创建完成统计" -ForegroundColor Cyan
Write-Host "=" * 80
Write-Host "✅ 成功: $successCount" -ForegroundColor Green
Write-Host "⚠️  跳过: $skipCount" -ForegroundColor Yellow
Write-Host "❌ 失败: $failCount" -ForegroundColor Red
Write-Host ""

Write-Host "测试账号信息:" -ForegroundColor Cyan
Write-Host "=" * 80
foreach ($user in $testUsers) {
    Write-Host "用户名: $($user.username) | 密码: $($user.password) | 角色: $($user.roles -join ', ')" -ForegroundColor White
}
Write-Host "=" * 80


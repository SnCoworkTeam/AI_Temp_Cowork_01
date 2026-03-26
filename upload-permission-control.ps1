# 上传权限控制功能相关代码到服务器
# 包括：API权限检查、菜单权限过滤、用户权限端点

$serverHost = "43.143.139.197"
$serverUser = "ubuntu"
$serverKey = "enterprise_ai_platform.pem"
$remoteBasePath = "/home/ubuntu/enterprise-ai-platform"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "上传权限控制功能代码到服务器" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 检查密钥文件是否存在
if (-not (Test-Path $serverKey)) {
    Write-Host "错误: 找不到密钥文件 $serverKey" -ForegroundColor Red
    Write-Host "请确保密钥文件在项目根目录" -ForegroundColor Yellow
    exit 1
}

# 定义要上传的文件
$filesToUpload = @(
    # 后端 - 权限检查相关
    @{
        Local = "project-management/src/routes/tasks.py"
        Remote = "$remoteBasePath/project-management/src/routes/tasks.py"
    },
    @{
        Local = "project-management/src/routes/milestones.py"
        Remote = "$remoteBasePath/project-management/src/routes/milestones.py"
    },
    @{
        Local = "project-management/src/routes/phases.py"
        Remote = "$remoteBasePath/project-management/src/routes/phases.py"
    },
    @{
        Local = "project-management/src/routes/risks.py"
        Remote = "$remoteBasePath/project-management/src/routes/risks.py"
    },
    @{
        Local = "project-management/src/routes/weekly_reports.py"
        Remote = "$remoteBasePath/project-management/src/routes/weekly_reports.py"
    },
    @{
        Local = "project-management/src/routes/monthly_reports.py"
        Remote = "$remoteBasePath/project-management/src/routes/monthly_reports.py"
    },
    @{
        Local = "project-management/src/middleware/resource_permissions.py"
        Remote = "$remoteBasePath/project-management/src/middleware/resource_permissions.py"
    },
    # 后端 - 用户权限端点
    @{
        Local = "auth-service/src/routes/users.py"
        Remote = "$remoteBasePath/auth-service/src/routes/users.py"
    },
    @{
        Local = "auth-service/src/services/user_service.py"
        Remote = "$remoteBasePath/auth-service/src/services/user_service.py"
    },
    @{
        Local = "auth-service/src/repositories/user_repository.py"
        Remote = "$remoteBasePath/auth-service/src/repositories/user_repository.py"
    },
    @{
        Local = "auth-service/src/middleware/permission_middleware.py"
        Remote = "$remoteBasePath/auth-service/src/middleware/permission_middleware.py"
    },
    # 前端 - 菜单权限过滤
    @{
        Local = "web-ui/src/components/Layout/Sidebar.tsx"
        Remote = "$remoteBasePath/web-ui/src/components/Layout/Sidebar.tsx"
    },
    @{
        Local = "web-ui/src/contexts/AuthContext.tsx"
        Remote = "$remoteBasePath/web-ui/src/contexts/AuthContext.tsx"
    },
    @{
        Local = "web-ui/src/lib/api/auth.ts"
        Remote = "$remoteBasePath/web-ui/src/lib/api/auth.ts"
    },
    # API Gateway - 用户路由代理
    @{
        Local = "api-gateway/src/main.py"
        Remote = "$remoteBasePath/api-gateway/src/main.py"
    }
)

# 先创建所有需要的远程目录
Write-Host "`n📁 创建远程目录..." -ForegroundColor Cyan
$remoteDirs = @(
    "$remoteBasePath/project-management/src/routes",
    "$remoteBasePath/project-management/src/middleware",
    "$remoteBasePath/auth-service/src/routes",
    "$remoteBasePath/auth-service/src/services",
    "$remoteBasePath/auth-service/src/repositories",
    "$remoteBasePath/auth-service/src/middleware",
    "$remoteBasePath/web-ui/src/components/Layout",
    "$remoteBasePath/web-ui/src/contexts",
    "$remoteBasePath/web-ui/src/lib/api",
    "$remoteBasePath/api-gateway/src"
)

foreach ($dir in $remoteDirs) {
    Write-Host "创建: $dir" -ForegroundColor Gray
    ssh -i $serverKey -o StrictHostKeyChecking=no "$serverUser@$serverHost" "mkdir -p `"$dir`"" 2>&1 | Out-Null
}

Write-Host "`n📤 上传文件..." -ForegroundColor Cyan

# 上传文件
$uploadedCount = 0
$failedCount = 0

foreach ($file in $filesToUpload) {
    $localPath = $file.Local
    $remotePath = $file.Remote
    
    if (-not (Test-Path $localPath)) {
        Write-Host "⚠️  跳过: 本地文件不存在 - $localPath" -ForegroundColor Yellow
        $failedCount++
        continue
    }
    
    Write-Host "📤 上传: $localPath" -ForegroundColor Cyan
    
    # 确保远程目录存在
    $remoteDir = Split-Path -Path $remotePath -Parent
    $mkdirCmd = "mkdir -p `"$remoteDir`""
    
    try {
        # 创建远程目录（使用bash -c确保命令正确执行）
        $mkdirResult = ssh -i $serverKey -o StrictHostKeyChecking=no "$serverUser@$serverHost" "bash -c `"$mkdirCmd`"" 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "   ⚠️  创建目录失败: $mkdirResult" -ForegroundColor Yellow
        }
        
        # 上传文件
        $scpResult = scp -i $serverKey -o StrictHostKeyChecking=no $localPath "$serverUser@$serverHost`:$remotePath" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ 成功" -ForegroundColor Green
            $uploadedCount++
        } else {
            Write-Host "   ❌ 失败: $scpResult" -ForegroundColor Red
            $failedCount++
        }
    } catch {
        Write-Host "   ❌ 错误: $_" -ForegroundColor Red
        $failedCount++
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "上传完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "成功: $uploadedCount 个文件" -ForegroundColor Green
Write-Host "失败: $failedCount 个文件" -ForegroundColor $(if ($failedCount -eq 0) { "Green" } else { "Red" })

# 重启服务
if ($failedCount -eq 0) {
    Write-Host "`n🔄 重启服务..." -ForegroundColor Yellow
    
    $restartCommands = @(
        "cd $remoteBasePath && docker compose restart project-management",
        "cd $remoteBasePath && docker compose restart auth-service",
        "cd $remoteBasePath && docker compose restart api-gateway",
        "cd $remoteBasePath && docker compose restart web-ui"
    )
    
    foreach ($cmd in $restartCommands) {
        Write-Host "执行: $cmd" -ForegroundColor Cyan
        ssh -i $serverKey -o StrictHostKeyChecking=no "$serverUser@$serverHost" $cmd 2>&1 | ForEach-Object {
            Write-Host "   $_" -ForegroundColor Gray
        }
    }
    
    Write-Host "`n✅ 服务重启完成！" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  由于有文件上传失败，跳过服务重启" -ForegroundColor Yellow
}

Write-Host "`n完成！" -ForegroundColor Green


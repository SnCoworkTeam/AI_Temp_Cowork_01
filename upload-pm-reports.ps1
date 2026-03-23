# 上传周月进度报告功能到服务器
# 服务器配置: 43.143.139.197
# 用户: ubuntu
# 密钥: enterprise_ai_platform.pem

$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"
$SERVER_PATH = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "上传周月进度报告功能到服务器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查密钥文件
if (-not (Test-Path $SSH_KEY)) {
    Write-Host "错误: 找不到密钥文件 $SSH_KEY" -ForegroundColor Red
    exit 1
}

# 设置密钥文件权限（Windows需要）
Write-Host "设置密钥文件权限..." -ForegroundColor Yellow
icacls $SSH_KEY /inheritance:r /grant "$env:USERNAME:(R)" | Out-Null

# 1. 上传 project-management 服务（周报和月报API）
Write-Host ""
Write-Host "1. 上传 project-management 服务..." -ForegroundColor Cyan
$pmFiles = @(
    "project-management/src/routes/weekly_reports.py",
    "project-management/src/routes/monthly_reports.py"
)

foreach ($file in $pmFiles) {
    if (Test-Path $file) {
        $remoteDir = "$SERVER_PATH/$(Split-Path $file -Parent)"
        Write-Host "  上传 $file ..." -ForegroundColor Gray
        
        # 确保远程目录存在
        $mkdirCmd = "mkdir -p `"$remoteDir`""
        & ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SERVER $mkdirCmd 2>&1 | Out-Null
        
        # 上传文件
        & scp -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $file "${SERVER}:$SERVER_PATH/$file"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ $file" -ForegroundColor Green
        } else {
            Write-Host "  ❌ $file 上传失败" -ForegroundColor Red
        }
    } else {
        Write-Host "  ⚠️  文件不存在: $file" -ForegroundColor Yellow
    }
}

# 2. 上传 web-ui 前端页面
Write-Host ""
Write-Host "2. 上传 web-ui 前端页面..." -ForegroundColor Cyan
$webFiles = @(
    "web-ui/src/app/admin/projects/weekly-reports/create/page.tsx",
    "web-ui/src/app/admin/projects/monthly-reports/create/page.tsx",
    "web-ui/src/app/admin/projects/progress-reports/page.tsx",
    "web-ui/src/app/admin/projects/weekly-reports/page.tsx",
    "web-ui/src/app/admin/projects/monthly-reports/page.tsx"
)

foreach ($file in $webFiles) {
    if (Test-Path $file) {
        $remoteDir = "$SERVER_PATH/$(Split-Path $file -Parent)"
        Write-Host "  上传 $file ..." -ForegroundColor Gray
        
        # 确保远程目录存在（使用 -p 参数创建多级目录）
        $mkdirCmd = "mkdir -p `"$remoteDir`""
        $mkdirResult = & ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SERVER $mkdirCmd 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ⚠️  创建目录失败: $remoteDir" -ForegroundColor Yellow
            Write-Host "     $mkdirResult" -ForegroundColor Gray
        }
        
        # 上传文件
        & scp -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $file "${SERVER}:$SERVER_PATH/$file"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ $file" -ForegroundColor Green
        } else {
            Write-Host "  ❌ $file 上传失败" -ForegroundColor Red
            # 尝试再次创建目录并上传
            Write-Host "    重试创建目录并上传..." -ForegroundColor Yellow
            & ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SERVER "mkdir -p `"$remoteDir`"" 2>&1 | Out-Null
            & scp -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $file "${SERVER}:$SERVER_PATH/$file"
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ $file (重试成功)" -ForegroundColor Green
            }
        }
    } else {
        Write-Host "  ⚠️  文件不存在: $file" -ForegroundColor Yellow
    }
}

# 3. 上传文档文件（可选）
Write-Host ""
Write-Host "3. 上传文档文件..." -ForegroundColor Cyan
$docFiles = @(
    "项目管理功能分析和技术债务报告.md",
    "周月进度报告功能实现总结.md"
)

foreach ($file in $docFiles) {
    if (Test-Path $file) {
        Write-Host "  上传 $file ..." -ForegroundColor Gray
        & scp -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $file "${SERVER}:$SERVER_PATH/$file"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ $file" -ForegroundColor Green
        } else {
            Write-Host "  ❌ $file 上传失败" -ForegroundColor Red
        }
    }
}

# 4. 重启相关服务
Write-Host ""
Write-Host "4. 重启服务..." -ForegroundColor Yellow
$restartCmd = "cd $SERVER_PATH && docker compose restart project-management web-ui"
Write-Host "  执行: $restartCmd" -ForegroundColor Gray
& ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SERVER $restartCmd

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ 服务重启成功" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  服务重启可能失败，请手动检查" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "上传完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "请检查服务状态:" -ForegroundColor Yellow
Write-Host "  ssh -i $SSH_KEY $SERVER 'cd $SERVER_PATH && docker compose ps'" -ForegroundColor Gray
Write-Host ""


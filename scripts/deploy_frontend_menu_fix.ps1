# 前端菜单修复部署脚本
# 部署最新的菜单配置和企业架构页面到应用服务器

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Green
Write-Host "前端菜单修复部署" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# 服务器配置
$APP_SERVER_HOST = "43.143.139.197"
$APP_SERVER_USER = "ubuntu"
$APP_SERVER_KEY = ".\enterprise_ai_platform.pem"
$REMOTE_PATH = "/opt/enterprise-ai-platform"

# 检查密钥文件
if (-not (Test-Path $APP_SERVER_KEY)) {
    Write-Host "错误: SSH密钥文件不存在: $APP_SERVER_KEY" -ForegroundColor Red
    Write-Host "请确保密钥文件在项目根目录下" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n服务器配置:" -ForegroundColor Cyan
Write-Host "  服务器: $APP_SERVER_USER@$APP_SERVER_HOST"
Write-Host "  密钥: $APP_SERVER_KEY"
Write-Host "  远程路径: $REMOTE_PATH"

# 1. 测试SSH连接
Write-Host "`n1. 测试SSH连接..." -ForegroundColor Yellow
try {
    $testResult = ssh -i $APP_SERVER_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$APP_SERVER_USER@$APP_SERVER_HOST" "echo '连接成功'" 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "SSH连接失败"
    }
    Write-Host "✅ SSH连接成功" -ForegroundColor Green
} catch {
    Write-Host "❌ SSH连接失败: $_" -ForegroundColor Red
    exit 1
}

# 2. 上传Sidebar.tsx（菜单配置）
Write-Host "`n2. 上传菜单配置文件..." -ForegroundColor Yellow
$sidebarPath = "web-ui\src\components\Layout\Sidebar.tsx"
if (-not (Test-Path $sidebarPath)) {
    Write-Host "❌ 文件不存在: $sidebarPath" -ForegroundColor Red
    exit 1
}

$remoteSidebarPath = "$REMOTE_PATH/web-ui/src/components/Layout"
ssh -i $APP_SERVER_KEY "$APP_SERVER_USER@$APP_SERVER_HOST" "mkdir -p $remoteSidebarPath" | Out-Null
scp -i $APP_SERVER_KEY "$sidebarPath" "${APP_SERVER_USER}@${APP_SERVER_HOST}:${remoteSidebarPath}/Sidebar.tsx"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Sidebar.tsx 上传成功" -ForegroundColor Green
} else {
    Write-Host "❌ Sidebar.tsx 上传失败" -ForegroundColor Red
    exit 1
}

# 3. 上传所有企业架构页面
Write-Host "`n3. 上传企业架构页面..." -ForegroundColor Yellow

$eaPages = @(
    "web-ui\src\app\enterprise-architecture\page.tsx",
    "web-ui\src\app\enterprise-architecture\layout.tsx",
    "web-ui\src\app\enterprise-architecture\organization\page.tsx",
    "web-ui\src\app\enterprise-architecture\business\page.tsx",
    "web-ui\src\app\enterprise-architecture\application\page.tsx",
    "web-ui\src\app\enterprise-architecture\data\page.tsx",
    "web-ui\src\app\enterprise-architecture\technology\page.tsx",
    "web-ui\src\app\enterprise-architecture\technology\instances\page.tsx",
    "web-ui\src\app\enterprise-architecture\technology\standardization\page.tsx",
    "web-ui\src\app\enterprise-architecture\relationships\page.tsx"
)

$remoteEaPath = "$REMOTE_PATH/web-ui/src/app/enterprise-architecture"
# 先创建所有需要的目录
$directories = @(
    "$REMOTE_PATH/web-ui/src/app/enterprise-architecture",
    "$REMOTE_PATH/web-ui/src/app/enterprise-architecture/organization",
    "$REMOTE_PATH/web-ui/src/app/enterprise-architecture/business",
    "$REMOTE_PATH/web-ui/src/app/enterprise-architecture/application",
    "$REMOTE_PATH/web-ui/src/app/enterprise-architecture/data",
    "$REMOTE_PATH/web-ui/src/app/enterprise-architecture/technology",
    "$REMOTE_PATH/web-ui/src/app/enterprise-architecture/technology/instances",
    "$REMOTE_PATH/web-ui/src/app/enterprise-architecture/technology/standardization",
    "$REMOTE_PATH/web-ui/src/app/enterprise-architecture/relationships"
)
Write-Host "  创建远程目录..." -ForegroundColor Cyan
foreach ($dir in $directories) {
    ssh -i $APP_SERVER_KEY "$APP_SERVER_USER@$APP_SERVER_HOST" "mkdir -p $dir" | Out-Null
}

foreach ($page in $eaPages) {
    if (Test-Path $page) {
        $relativePath = $page -replace "^web-ui\\src\\app\\", "" -replace "\\", "/"
        $remotePagePath = "$REMOTE_PATH/web-ui/src/app/$relativePath"
        $remoteDir = Split-Path $remotePagePath -Parent
        
        scp -i $APP_SERVER_KEY "$page" "${APP_SERVER_USER}@${APP_SERVER_HOST}:${remotePagePath}"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ $(Split-Path $page -Leaf)" -ForegroundColor Green
        } else {
            Write-Host "  ❌ $(Split-Path $page -Leaf) 上传失败" -ForegroundColor Red
        }
    } else {
        Write-Host "  ⚠️  文件不存在: $page" -ForegroundColor Yellow
    }
}

# 4. 上传enterpriseArchitectureService.ts
Write-Host "`n4. 上传前端服务文件..." -ForegroundColor Yellow
$serviceFile = "web-ui\src\services\enterpriseArchitectureService.ts"
if (Test-Path $serviceFile) {
    $remoteServicePath = "$REMOTE_PATH/web-ui/src/services"
    ssh -i $APP_SERVER_KEY "$APP_SERVER_USER@$APP_SERVER_HOST" "mkdir -p $remoteServicePath" | Out-Null
    scp -i $APP_SERVER_KEY "$serviceFile" "${APP_SERVER_USER}@${APP_SERVER_HOST}:${remoteServicePath}/enterpriseArchitectureService.ts"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ enterpriseArchitectureService.ts 上传成功" -ForegroundColor Green
    }
}

# 5. 在服务器上重新构建前端
Write-Host "`n5. 在服务器上重新构建前端..." -ForegroundColor Yellow
$buildCmd = "cd $REMOTE_PATH/web-ui && npm install && npm run build"

ssh -i $APP_SERVER_KEY "$APP_SERVER_USER@$APP_SERVER_HOST" $buildCmd
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 前端构建成功" -ForegroundColor Green
} else {
    Write-Host "⚠️  前端构建可能有问题，请检查" -ForegroundColor Yellow
}

# 6. 重启Next.js服务
Write-Host "`n6. 重启Next.js服务..." -ForegroundColor Yellow
$restartCmd = "cd $REMOTE_PATH && (docker compose restart web-ui 2>/dev/null || docker-compose restart web-ui 2>/dev/null || echo '请手动重启web-ui服务')"

ssh -i $APP_SERVER_KEY "$APP_SERVER_USER@$APP_SERVER_HOST" $restartCmd
Write-Host "✅ 服务重启命令已执行" -ForegroundColor Green

# 完成
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "✅ 前端菜单修复部署完成" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`n请访问 http://$APP_SERVER_HOST`:3000 验证菜单配置" -ForegroundColor Cyan
Write-Host "`n验证步骤:" -ForegroundColor Yellow
Write-Host "  1. 清除浏览器缓存 (Ctrl+Shift+R)" -ForegroundColor White
Write-Host "  2. 检查企业架构菜单是否有9个子菜单项" -ForegroundColor White
Write-Host "  3. 检查菜单是否可以折叠/展开" -ForegroundColor White


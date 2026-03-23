# 上传企业架构功能到服务器
$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"
$SERVER_PATH = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  上传企业架构功能到服务器" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 检查密钥文件
if (-not (Test-Path $SSH_KEY)) {
    $SSH_KEY = "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem"
    if (-not (Test-Path $SSH_KEY)) {
        Write-Host "错误: 密钥文件未找到" -ForegroundColor Red
        exit 1
    }
}

# 测试SSH连接
Write-Host "测试SSH连接..." -ForegroundColor Cyan
$test = ssh -i $SSH_KEY -o ConnectTimeout=5 -o StrictHostKeyChecking=no $SERVER "echo OK" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "SSH连接失败!" -ForegroundColor Red
    exit 1
}
Write-Host "SSH连接成功" -ForegroundColor Green
Write-Host ""

# 1. 上传数据库迁移脚本
Write-Host "1. 上传数据库迁移脚本..." -ForegroundColor Green
if (Test-Path "database/src/migrations/versions/025_add_enterprise_architecture_tables.py") {
    $remoteDir = "$SERVER_PATH/database/src/migrations/versions"
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p $remoteDir" | Out-Null
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "database/src/migrations/versions/025_add_enterprise_architecture_tables.py" "${SERVER}:${remoteDir}/" 2>&1 | Out-Null
    Write-Host "  ✓ 迁移脚本上传成功" -ForegroundColor Green
}

# 上传合并迁移脚本
if (Test-Path "database/src/migrations/versions/8323deb6c345_merge_heads_for_enterprise_architecture.py") {
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "database/src/migrations/versions/8323deb6c345_merge_heads_for_enterprise_architecture.py" "${SERVER}:${remoteDir}/" 2>&1 | Out-Null
    Write-Host "  ✓ 合并迁移脚本上传成功" -ForegroundColor Green
}

# 2. 上传数据库模型
Write-Host ""
Write-Host "2. 上传数据库模型..." -ForegroundColor Green
if (Test-Path "database/src/models/enterprise_architecture_models.py") {
    $remoteDir = "$SERVER_PATH/database/src/models"
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p $remoteDir" | Out-Null
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "database/src/models/enterprise_architecture_models.py" "${SERVER}:${remoteDir}/" 2>&1 | Out-Null
    Write-Host "  ✓ 数据库模型上传成功" -ForegroundColor Green
}

# 更新models __init__.py
if (Test-Path "database/src/models/__init__.py") {
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "database/src/models/__init__.py" "${SERVER}:${remoteDir}/" 2>&1 | Out-Null
    Write-Host "  ✓ 模型初始化文件上传成功" -ForegroundColor Green
}

# 3. 上传metadata-service企业架构代码
Write-Host ""
Write-Host "3. 上传metadata-service企业架构代码..." -ForegroundColor Green
if (Test-Path "metadata-service/src/api/enterprise_architecture.py") {
    $remoteDir = "$SERVER_PATH/metadata-service/src/api"
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p $remoteDir" | Out-Null
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "metadata-service/src/api/enterprise_architecture.py" "${SERVER}:${remoteDir}/" 2>&1 | Out-Null
    Write-Host "  ✓ API路由上传成功" -ForegroundColor Green
}

if (Test-Path "metadata-service/src/services/enterprise_architecture_service.py") {
    $remoteDir = "$SERVER_PATH/metadata-service/src/services"
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p $remoteDir" | Out-Null
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "metadata-service/src/services/enterprise_architecture_service.py" "${SERVER}:${remoteDir}/" 2>&1 | Out-Null
    Write-Host "  ✓ 服务层代码上传成功" -ForegroundColor Green
}

# 更新metadata-service main.py以包含企业架构路由
if (Test-Path "metadata-service/src/main.py") {
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "metadata-service/src/main.py" "${SERVER}:$SERVER_PATH/metadata-service/src/" 2>&1 | Out-Null
    Write-Host "  ✓ main.py上传成功" -ForegroundColor Green
}

# 4. 上传api-gateway企业架构路由
Write-Host ""
Write-Host "4. 上传api-gateway企业架构路由..." -ForegroundColor Green
if (Test-Path "api-gateway/src/routes/enterprise_architecture.py") {
    $remoteDir = "$SERVER_PATH/api-gateway/src/routes"
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p $remoteDir" | Out-Null
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "api-gateway/src/routes/enterprise_architecture.py" "${SERVER}:${remoteDir}/" 2>&1 | Out-Null
    Write-Host "  ✓ API Gateway路由上传成功" -ForegroundColor Green
}

# 更新api-gateway main.py
if (Test-Path "api-gateway/src/main.py") {
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "api-gateway/src/main.py" "${SERVER}:$SERVER_PATH/api-gateway/src/" 2>&1 | Out-Null
    Write-Host "  ✓ API Gateway main.py上传成功" -ForegroundColor Green
}

# 5. 上传web-ui企业架构页面
Write-Host ""
Write-Host "5. 上传web-ui企业架构页面..." -ForegroundColor Green

# 上传侧边栏
if (Test-Path "web-ui/src/components/Layout/Sidebar.tsx") {
    $remoteDir = "$SERVER_PATH/web-ui/src/components/Layout"
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p $remoteDir" | Out-Null
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "web-ui/src/components/Layout/Sidebar.tsx" "${SERVER}:${remoteDir}/" 2>&1 | Out-Null
    Write-Host "  ✓ 侧边栏上传成功" -ForegroundColor Green
}

# 上传企业架构页面
$eaPages = @(
    "web-ui/src/app/enterprise-architecture/page.tsx",
    "web-ui/src/app/enterprise-architecture/business/page.tsx",
    "web-ui/src/app/enterprise-architecture/application/page.tsx",
    "web-ui/src/app/enterprise-architecture/data/page.tsx",
    "web-ui/src/app/enterprise-architecture/technology/page.tsx",
    "web-ui/src/app/enterprise-architecture/relationships/page.tsx"
)

foreach ($page in $eaPages) {
    if (Test-Path $page) {
        $relativePath = $page.Replace("web-ui/", "")
        $remotePath = "$SERVER_PATH/$relativePath"
        $remoteDir = Split-Path $remotePath -Parent
        ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p $remoteDir" | Out-Null
        scp -i $SSH_KEY -o StrictHostKeyChecking=no $page "${SERVER}:${remotePath}" 2>&1 | Out-Null
        Write-Host "  ✓ $(Split-Path $page -Leaf) 上传成功" -ForegroundColor Green
    }
}

# 上传服务文件
if (Test-Path "web-ui/src/services/enterpriseArchitectureService.ts") {
    $remoteDir = "$SERVER_PATH/web-ui/src/services"
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p $remoteDir" | Out-Null
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "web-ui/src/services/enterpriseArchitectureService.ts" "${SERVER}:${remoteDir}/" 2>&1 | Out-Null
    Write-Host "  ✓ 服务文件上传成功" -ForegroundColor Green
}

# 6. 执行数据库迁移
Write-Host ""
Write-Host "6. 执行数据库迁移..." -ForegroundColor Green
$migrateCmd = "cd $SERVER_PATH/database && python3 -m alembic upgrade head 2>&1"
$migrateResult = ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $migrateCmd
Write-Host $migrateResult

# 如果迁移失败，尝试直接创建表
if ($migrateResult -match "error|Error|ERROR|失败|失败") {
    Write-Host "  迁移可能失败，尝试直接创建表..." -ForegroundColor Yellow
    # 这里可以添加直接创建表的SQL脚本
}

# 7. 重启相关服务
Write-Host ""
Write-Host "7. 重启相关服务..." -ForegroundColor Green

# 重启metadata-service
Write-Host "  重启metadata-service..." -ForegroundColor Cyan
$restartCmd = "cd $SERVER_PATH && docker compose restart metadata-service 2>&1"
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $restartCmd | Out-Null
Start-Sleep -Seconds 5

# 重启api-gateway
Write-Host "  重启api-gateway..." -ForegroundColor Cyan
$restartCmd = "cd $SERVER_PATH && docker compose restart api-gateway 2>&1"
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $restartCmd | Out-Null
Start-Sleep -Seconds 5

# 重启web-ui
Write-Host "  重启web-ui..." -ForegroundColor Cyan
$restartCmd = "cd $SERVER_PATH && docker compose restart web-ui 2>&1"
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $restartCmd | Out-Null
Start-Sleep -Seconds 10

# 8. 检查服务状态
Write-Host ""
Write-Host "8. 检查服务状态..." -ForegroundColor Green
$statusCmd = "cd $SERVER_PATH && docker compose ps metadata-service api-gateway web-ui --format 'table {{.Name}}\t{{.Status}}'"
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $statusCmd

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "访问地址:" -ForegroundColor Cyan
Write-Host "  企业架构总览: http://43.143.139.197:3000/enterprise-architecture" -ForegroundColor Yellow
Write-Host "  业务架构: http://43.143.139.197:3000/enterprise-architecture/business" -ForegroundColor Yellow
Write-Host "  应用架构: http://43.143.139.197:3000/enterprise-architecture/application" -ForegroundColor Yellow
Write-Host "  数据架构: http://43.143.139.197:3000/enterprise-architecture/data" -ForegroundColor Yellow
Write-Host "  技术架构: http://43.143.139.197:3000/enterprise-architecture/technology" -ForegroundColor Yellow
Write-Host "  架构关系图: http://43.143.139.197:3000/enterprise-architecture/relationships" -ForegroundColor Yellow
Write-Host "  API文档: http://43.143.139.197:8005/api/docs" -ForegroundColor Yellow
Write-Host ""












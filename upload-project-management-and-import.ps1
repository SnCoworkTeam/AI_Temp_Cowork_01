# 上传项目管理服务并导入Excel数据
$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"
$SERVER_PATH = "/opt/enterprise-ai-platform"
$EXCEL_FILE = "2025项目周月进度报告 (1).xlsx"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  上传项目管理服务并导入Excel数据" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 检查密钥文件
if (-not (Test-Path $SSH_KEY)) {
    $SSH_KEY = "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem"
    if (-not (Test-Path $SSH_KEY)) {
        Write-Host "错误: 密钥文件未找到" -ForegroundColor Red
        Write-Host "请确保密钥文件存在: $SSH_KEY" -ForegroundColor Yellow
        exit 1
    }
}
Write-Host "使用密钥文件: $SSH_KEY" -ForegroundColor Cyan

# 测试SSH连接
Write-Host ""
Write-Host "测试SSH连接..." -ForegroundColor Cyan
$test = ssh -i $SSH_KEY -o ConnectTimeout=5 -o StrictHostKeyChecking=no $SERVER "echo OK" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "SSH连接失败!" -ForegroundColor Red
    Write-Host $test
    exit 1
}
Write-Host "SSH连接成功" -ForegroundColor Green

# 1. 上传数据库迁移脚本
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  1. 上传数据库迁移脚本" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
if (Test-Path "database/src/migrations/versions/024_add_project_management_tables.py") {
    Write-Host "上传迁移脚本..." -ForegroundColor Yellow
    $remoteDir = "$SERVER_PATH/database/src/migrations/versions"
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p $remoteDir" 2>&1 | Out-Null
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "database/src/migrations/versions/024_add_project_management_tables.py" "${SERVER}:${remoteDir}/" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 迁移脚本上传成功" -ForegroundColor Green
    } else {
        Write-Host "❌ 迁移脚本上传失败" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "❌ 迁移脚本不存在" -ForegroundColor Red
    exit 1
}

# 2. 上传项目管理服务代码
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  2. 上传项目管理服务代码" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
if (Test-Path "project-management") {
    Write-Host "上传 project-management 目录..." -ForegroundColor Yellow
    scp -i $SSH_KEY -r -o StrictHostKeyChecking=no "project-management" "${SERVER}:${SERVER_PATH}/" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ project-management 上传成功" -ForegroundColor Green
    } else {
        Write-Host "❌ project-management 上传失败" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "❌ project-management 目录不存在" -ForegroundColor Red
    exit 1
}

# 3. 上传数据库模型（如果不存在）
Write-Host ""
Write-Host "检查数据库模型..." -ForegroundColor Cyan
if (Test-Path "database/src/models/project_models.py") {
    Write-Host "上传 project_models.py..." -ForegroundColor Yellow
    $remoteDir = "$SERVER_PATH/database/src/models"
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "mkdir -p $remoteDir" 2>&1 | Out-Null
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "database/src/models/project_models.py" "${SERVER}:${remoteDir}/" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ project_models.py 上传成功" -ForegroundColor Green
    }
}

# 4. 上传docker-compose.yml
Write-Host ""
Write-Host "上传 docker-compose.yml..." -ForegroundColor Cyan
if (Test-Path "docker-compose.yml") {
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "docker-compose.yml" "${SERVER}:${SERVER_PATH}/" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ docker-compose.yml 上传成功" -ForegroundColor Green
    }
}

# 5. 上传Excel文件
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  3. 上传Excel文件" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
if (Test-Path $EXCEL_FILE) {
    Write-Host "上传Excel文件: $EXCEL_FILE" -ForegroundColor Yellow
    $remoteExcelPath = "$SERVER_PATH/$EXCEL_FILE"
    scp -i $SSH_KEY -o StrictHostKeyChecking=no $EXCEL_FILE "${SERVER}:${remoteExcelPath}" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Excel文件上传成功" -ForegroundColor Green
    } else {
        Write-Host "❌ Excel文件上传失败" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "⚠️  Excel文件不存在: $EXCEL_FILE" -ForegroundColor Yellow
    Write-Host "   将跳过Excel导入步骤" -ForegroundColor Yellow
}

# 6. 执行数据库迁移
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  4. 执行数据库迁移" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "执行数据库迁移..." -ForegroundColor Yellow
$migrateCmd = "cd $SERVER_PATH/database && alembic upgrade head"
$migrateResult = ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $migrateCmd 2>&1
Write-Host $migrateResult
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 数据库迁移成功" -ForegroundColor Green
} else {
    Write-Host "⚠️  数据库迁移可能有问题，请检查输出" -ForegroundColor Yellow
}

# 7. 重启项目管理服务
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  5. 重启项目管理服务" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "停止现有服务..." -ForegroundColor Yellow
$stopCmd = "cd $SERVER_PATH && docker compose stop project-management 2>&1 || true"
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $stopCmd | Out-Null

Write-Host "构建并启动服务..." -ForegroundColor Yellow
$startCmd = "cd $SERVER_PATH && docker compose up -d --build project-management"
$startResult = ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $startCmd 2>&1
Write-Host $startResult

Write-Host ""
Write-Host "等待服务启动..." -ForegroundColor Cyan
Start-Sleep -Seconds 15

# 8. 检查服务状态
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  6. 检查服务状态" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
$statusCmd = "cd $SERVER_PATH && docker compose ps project-management"
Write-Host "服务状态:" -ForegroundColor Cyan
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $statusCmd

Write-Host ""
Write-Host "服务日志（最后30行）:" -ForegroundColor Cyan
$logCmd = "cd $SERVER_PATH && docker compose logs --tail=30 project-management"
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $logCmd

# 9. 测试健康检查
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  7. 测试健康检查" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "测试健康检查端点..." -ForegroundColor Cyan
Start-Sleep -Seconds 5
try {
    $healthResponse = Invoke-WebRequest -Uri "http://43.143.139.197:8016/api/health" -TimeoutSec 10 -ErrorAction Stop
    if ($healthResponse.StatusCode -eq 200) {
        Write-Host "✅ 服务健康检查通过" -ForegroundColor Green
        Write-Host $healthResponse.Content
    }
} catch {
    Write-Host "⚠️  健康检查失败，服务可能还在启动中" -ForegroundColor Yellow
    Write-Host "   错误: $_" -ForegroundColor Yellow
}

# 10. 导入Excel数据（如果文件存在）
if (Test-Path $EXCEL_FILE) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  8. 导入Excel数据" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "等待服务完全启动..." -ForegroundColor Cyan
    Start-Sleep -Seconds 10
    
    Write-Host "准备导入Excel文件..." -ForegroundColor Yellow
    Write-Host "注意: Excel导入需要通过Web界面或API调用" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "可以通过以下方式导入:" -ForegroundColor Cyan
    Write-Host "  1. Web界面: http://43.143.139.197:3000/admin/projects/import" -ForegroundColor Yellow
    Write-Host "  2. API调用:" -ForegroundColor Yellow
    Write-Host "     curl -X POST http://43.143.139.197:8080/api/v1/projects/import/excel \`" -ForegroundColor Gray
    Write-Host "       -H 'Authorization: Bearer YOUR_TOKEN' \`" -ForegroundColor Gray
    Write-Host "       -F 'file=@$EXCEL_FILE'" -ForegroundColor Gray
    
    # 上传导入脚本
    Write-Host ""
    Write-Host "上传Excel导入脚本..." -ForegroundColor Cyan
    if (Test-Path "scripts/import_excel_to_server.py") {
        scp -i $SSH_KEY -o StrictHostKeyChecking=no "scripts/import_excel_to_server.py" "${SERVER}:${SERVER_PATH}/" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 导入脚本上传成功" -ForegroundColor Green
        }
    }
    
    # 尝试通过API导入
    Write-Host ""
    Write-Host "尝试通过API导入Excel数据..." -ForegroundColor Cyan
    Write-Host "等待服务完全启动..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    # 执行导入脚本
    Write-Host "执行Excel导入..." -ForegroundColor Yellow
    $importCmd = "cd $SERVER_PATH && python3 import_excel_to_server.py"
    $importResult = ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER $importCmd 2>&1
    Write-Host $importResult
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Excel导入完成" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Excel导入可能失败，请检查输出" -ForegroundColor Yellow
        Write-Host "   可以通过Web界面手动导入: http://43.143.139.197:3000/admin/projects/import" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步操作:" -ForegroundColor Cyan
Write-Host "  1. 访问服务健康检查: http://43.143.139.197:8016/api/health" -ForegroundColor Yellow
Write-Host "  2. 访问API文档: http://43.143.139.197:8016/docs" -ForegroundColor Yellow
Write-Host "  3. 访问项目管理页面: http://43.143.139.197:3000/admin/projects" -ForegroundColor Yellow
Write-Host "  4. 导入Excel: http://43.143.139.197:3000/admin/projects/import" -ForegroundColor Yellow
Write-Host ""
Write-Host "查看服务日志:" -ForegroundColor Cyan
Write-Host "  ssh -i $SSH_KEY $SERVER" -ForegroundColor Yellow
Write-Host "  cd $SERVER_PATH" -ForegroundColor Yellow
Write-Host "  docker compose logs -f project-management" -ForegroundColor Yellow
Write-Host ""


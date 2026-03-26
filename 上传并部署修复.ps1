# 上传修复文件到服务器并部署
$SERVER = "ubuntu@43.143.139.197"
$KEY = "enterprise_ai_platform.pem"
$PROJECT_PATH = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "上传修复文件到服务器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查密钥
if (-not (Test-Path $KEY)) {
    Write-Host "✗ 密钥文件不存在: $KEY" -ForegroundColor Red
    exit 1
}

# 测试SSH连接
Write-Host "1. 测试SSH连接..." -ForegroundColor Yellow
$testResult = ssh -i $KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SERVER "echo 'Connection OK'" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ SSH连接失败" -ForegroundColor Red
    Write-Host $testResult
    exit 1
}
Write-Host "   ✓ SSH连接成功" -ForegroundColor Green

# 上传文件
Write-Host "`n2. 上传修改的文件..." -ForegroundColor Yellow
$files = @(
    "database/src/models/system_models.py",
    "knowledge-base/src/repositories/search_history_repository.py",
    "knowledge-base/src/core/embedding_manager.py"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "   上传: $file" -ForegroundColor Gray
        $remoteDir = Split-Path "$PROJECT_PATH/$file" -Parent
        ssh -i $KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SERVER "mkdir -p $remoteDir" | Out-Null
        scp -i $KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$file" "${SERVER}:${PROJECT_PATH}/${file}" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✓ $file 上传成功" -ForegroundColor Green
        } else {
            Write-Host "   ✗ $file 上传失败" -ForegroundColor Red
        }
    }
}

# 安装依赖
Write-Host "`n3. 安装sentence-transformers依赖..." -ForegroundColor Yellow
$installCmd = "docker exec enterprise-ai-knowledge-base pip install --upgrade sentence-transformers huggingface-hub --no-cache-dir"
ssh -i $KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SERVER $installCmd
Write-Host "   依赖安装完成" -ForegroundColor Green

# 重启服务
Write-Host "`n4. 重启知识库服务..." -ForegroundColor Yellow
$restartCmd = "cd $PROJECT_PATH && docker compose restart knowledge-base"
ssh -i $KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SERVER $restartCmd
Write-Host "   服务重启完成" -ForegroundColor Green

# 等待服务启动
Write-Host "`n5. 等待服务启动（30秒）..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# 检查服务状态
Write-Host "`n6. 检查服务状态..." -ForegroundColor Yellow
$statusCmd = "cd $PROJECT_PATH && docker compose ps knowledge-base"
ssh -i $KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SERVER $statusCmd

# 检查模型
Write-Host "`n7. 检查模型加载状态..." -ForegroundColor Yellow
$checkCmd = "docker exec enterprise-ai-knowledge-base python -c `"import sys; sys.path.insert(0, '/app'); from src.core.embedding_manager import get_embedding_manager; em = get_embedding_manager(); print('Model available:', em.is_available()); print('Has model:', em.model is not None)`""
ssh -i $KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SERVER $checkCmd

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "部署完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan


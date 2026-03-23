# 上传修复文件到服务器并重启服务
# 服务器配置：43.143.139.197

$SERVER = "ubuntu@43.143.139.197"
$KEY = "enterprise_ai_platform.pem"
$PROJECT_PATH = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "上传修复文件到服务器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查密钥文件
if (-not (Test-Path $KEY)) {
    Write-Host "✗ 密钥文件不存在: $KEY" -ForegroundColor Red
    exit 1
}

Write-Host "1. 上传修改的文件..." -ForegroundColor Yellow

# 上传修改的文件
$files = @(
    "database/src/models/system_models.py",
    "knowledge-base/src/repositories/search_history_repository.py",
    "knowledge-base/src/core/embedding_manager.py"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "   上传: $file" -ForegroundColor Gray
        scp -i $KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$file" "${SERVER}:${PROJECT_PATH}/${file}"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✓ $file 上传成功" -ForegroundColor Green
        } else {
            Write-Host "   ✗ $file 上传失败" -ForegroundColor Red
        }
    } else {
        Write-Host "   ⚠ 文件不存在: $file" -ForegroundColor Yellow
    }
}

Write-Host "`n2. 在服务器上安装依赖..." -ForegroundColor Yellow

# 安装sentence-transformers依赖
$installCmd = "cd $PROJECT_PATH && docker exec enterprise-ai-knowledge-base pip install --upgrade sentence-transformers huggingface-hub --no-cache-dir"
ssh -i $KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SERVER $installCmd

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ 依赖安装成功" -ForegroundColor Green
} else {
    Write-Host "   ⚠ 依赖安装可能有问题，继续执行..." -ForegroundColor Yellow
}

Write-Host "`n3. 重启知识库服务..." -ForegroundColor Yellow

# 重启服务
$restartCmd = "cd $PROJECT_PATH && docker compose restart knowledge-base"
ssh -i $KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SERVER $restartCmd

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ 服务重启成功" -ForegroundColor Green
} else {
    Write-Host "   ✗ 服务重启失败" -ForegroundColor Red
    exit 1
}

Write-Host "`n4. 等待服务启动（30秒）..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host "`n5. 检查服务状态..." -ForegroundColor Yellow

# 检查服务状态
$statusCmd = "cd $PROJECT_PATH && docker compose ps knowledge-base"
ssh -i $KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SERVER $statusCmd

Write-Host "`n6. 检查模型加载状态..." -ForegroundColor Yellow

# 检查模型是否加载
$checkModelCmd = "docker exec enterprise-ai-knowledge-base python -c `"import sys; sys.path.insert(0, '/app'); from src.core.embedding_manager import get_embedding_manager; em = get_embedding_manager(); print('Model available:', em.is_available()); print('Has model:', em.model is not None)`""
ssh -i $KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SERVER $checkModelCmd

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "上传和部署完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "查看服务日志: ssh -i $KEY $SERVER 'docker logs enterprise-ai-knowledge-base --tail 50'" -ForegroundColor Green
Write-Host ""


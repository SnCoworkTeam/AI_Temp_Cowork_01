# 上传知识库内存优化代码到服务器
# Author: Claude Code
# Description: 上传memory_optimizer.py和优化后的document_service.py到服务器

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  知识库内存优化 - 上传到服务器" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 服务器配置
$SERVER_HOST = "ubuntu@43.143.139.197"
$SERVER_PATH = "/opt/enterprise-ai-platform"
$SSH_KEY = "enterprise_ai_platform.pem"

# 检查SSH密钥
if (-not (Test-Path $SSH_KEY)) {
    Write-Host "❌ SSH密钥不存在: $SSH_KEY" -ForegroundColor Red
    exit 1
}

# 需要上传的文件
$filesToUpload = @(
    @{
        local = "knowledge-base\src\core\memory_optimizer.py"
        remote = "knowledge-base/src/core/memory_optimizer.py"
        desc = "内存优化器"
    },
    @{
        local = "knowledge-base\src\services\document_service.py"
        remote = "knowledge-base/src/services/document_service.py"
        desc = "优化后的文档服务"
    }
)

Write-Host "📋 准备上传以下文件:" -ForegroundColor Cyan
foreach ($file in $filesToUpload) {
    Write-Host "   - $($file.desc): $($file.local)" -ForegroundColor Gray
}
Write-Host ""

# 1. 检查服务器连接
Write-Host "🔌 步骤 1: 检查服务器连接..." -ForegroundColor Cyan
try {
    $testCmd = "ssh -i $SSH_KEY -o ConnectTimeout=10 -o StrictHostKeyChecking=no $SERVER_HOST 'echo OK'"
    $result = Invoke-Expression $testCmd 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "SSH连接失败"
    }
    Write-Host "✅ 服务器连接成功" -ForegroundColor Green
} catch {
    Write-Host "❌ 服务器连接失败: $_" -ForegroundColor Red
    Write-Host "   请检查:" -ForegroundColor Yellow
    Write-Host "   1. SSH密钥权限是否正确" -ForegroundColor Yellow
    Write-Host "   2. 服务器地址是否正确: $SERVER_HOST" -ForegroundColor Yellow
    Write-Host "   3. 网络连接是否正常" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# 2. 备份原文件
Write-Host "💾 步骤 2: 备份原文件..." -ForegroundColor Cyan
$backupDir = "$SERVER_PATH/backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
$backupCmd = @"
mkdir -p $backupDir && \
cp -r $SERVER_PATH/knowledge-base/src/services/document_service.py $backupDir/ 2>/dev/null || true && \
echo "Backup created at: $backupDir"
"@

ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER_HOST $backupCmd
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 备份完成: $backupDir" -ForegroundColor Green
} else {
    Write-Host "⚠️  备份失败，继续上传..." -ForegroundColor Yellow
}
Write-Host ""

# 3. 上传文件
Write-Host "📤 步骤 3: 上传文件..." -ForegroundColor Cyan
$uploadSuccess = $true

foreach ($file in $filesToUpload) {
    Write-Host "   上传: $($file.desc)..." -ForegroundColor Gray

    $localPath = $file.local
    $remotePath = "$SERVER_PATH/$($file.remote)"

    # 检查本地文件是否存在
    if (-not (Test-Path $localPath)) {
        Write-Host "   ❌ 本地文件不存在: $localPath" -ForegroundColor Red
        $uploadSuccess = $false
        continue
    }

    # 使用scp上传
    $scpCmd = "scp -i $SSH_KEY -o StrictHostKeyChecking=no `"$localPath`" ${SERVER_HOST}:$remotePath"
    Invoke-Expression $scpCmd 2>&1 | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ 上传成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 上传失败" -ForegroundColor Red
        $uploadSuccess = $false
    }
}
Write-Host ""

if (-not $uploadSuccess) {
    Write-Host "❌ 部分文件上传失败" -ForegroundColor Red
    exit 1
}

# 4. 重启知识库服务
Write-Host "🔄 步骤 4: 重启知识库服务..." -ForegroundColor Cyan
$restartCmd = @"
cd $SERVER_PATH && \
sudo docker compose restart knowledge-base && \
echo "Service restarted"
"@

ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER_HOST $restartCmd
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 知识库服务重启成功" -ForegroundColor Green
} else {
    Write-Host "❌ 服务重启失败" -ForegroundColor Red
    Write-Host "   请手动重启服务: sudo docker compose restart knowledge-base" -ForegroundColor Yellow
}
Write-Host ""

# 5. 等待服务启动
Write-Host "⏳ 步骤 5: 等待服务启动..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

# 6. 检查服务状态
Write-Host "🔍 步骤 6: 检查服务状态..." -ForegroundColor Cyan
$checkCmd = @"
cd $SERVER_PATH && \
sudo docker compose ps knowledge-base && \
sudo docker compose logs --tail 20 knowledge-base | grep -i 'memory\|started\|error' || echo 'No relevant logs'
"@

ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER_HOST $checkCmd
Write-Host ""

# 7. 显示内存使用情况
Write-Host "📊 步骤 7: 检查内存使用情况..." -ForegroundColor Cyan
$memoryCmd = @"
cd $SERVER_PATH && \
echo '=== 容器内存使用 ===' && \
sudo docker stats --no-stream --format 'table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}' knowledge-base && \
echo '' && \
echo '=== 系统内存 ===' && \
free -h
"@

ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER_HOST $memoryCmd
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ 部署完成!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📝 下一步操作:" -ForegroundColor Cyan
Write-Host "   1. 运行测试脚本测试F5文档处理" -ForegroundColor Gray
Write-Host "      python test_f5_document_with_memory_optimization.py" -ForegroundColor Gray
Write-Host "   2. 监控服务器内存使用情况" -ForegroundColor Gray
Write-Host "   3. 查看处理日志" -ForegroundColor Gray
Write-Host "      ssh -i $SSH_KEY $SERVER_HOST 'cd $SERVER_PATH && sudo docker compose logs -f knowledge-base'" -ForegroundColor Gray
Write-Host ""

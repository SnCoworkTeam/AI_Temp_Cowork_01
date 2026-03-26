# 修复知识库文档处理问题 - 部署脚本
# 此脚本将修复后的代码部署到服务器

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "修复知识库文档处理卡住问题" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 配置
$SERVER_USER = "ubuntu"
$SERVER_HOST = "43.143.139.197"
$KEY_FILE = "enterprise_ai_platform.pem"
$REMOTE_DIR = "/opt/enterprise-ai-platform"

Write-Host "[1/5] 准备上传修复文件..." -ForegroundColor Yellow

# 要上传的文件列表
$files = @(
    @{Local="knowledge-base\src\routes\documents_db.py"; Remote="knowledge-base/src/routes/documents_db.py"},
    @{Local="knowledge-base\src\services\document_service.py"; Remote="knowledge-base/src/services/document_service.py"},
    @{Local="knowledge-base\src\config.py"; Remote="knowledge-base/src/config.py"}
)

# 创建临时目录
$tempDir = "temp_fix"
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

# 复制文件到临时目录，保持目录结构
foreach ($file in $files) {
    $localPath = $file.Local
    $remotePath = $file.Remote

    if (Test-Path $localPath) {
        $targetDir = Join-Path $tempDir (Split-Path $remotePath -Parent)
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        Copy-Item $localPath -Destination (Join-Path $tempDir $remotePath) -Force
        Write-Host "  ✓ 准备文件: $localPath" -ForegroundColor Green
    } else {
        Write-Host "  ✗ 文件不存在: $localPath" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "[2/5] 上传文件到服务器..." -ForegroundColor Yellow

# 创建tar包
$tarFile = "knowledge_base_fix.tar.gz"
tar -czf $tarFile -C $tempDir .

if (-not (Test-Path $tarFile)) {
    Write-Host "  ✗ 创建tar包失败" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ 创建tar包: $tarFile" -ForegroundColor Green

# 上传tar包到服务器
Write-Host "  正在上传到服务器..." -ForegroundColor Cyan
scp -i $KEY_FILE $tarFile "${SERVER_USER}@${SERVER_HOST}:${REMOTE_DIR}/"

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ 上传失败" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ 上传成功" -ForegroundColor Green

Write-Host ""
Write-Host "[3/5] 解压并应用修复..." -ForegroundColor Yellow

$extractCommand = @"
cd $REMOTE_DIR && \
tar -xzf knowledge_base_fix.tar.gz && \
rm knowledge_base_fix.tar.gz && \
echo '✓ 文件解压成功'
"@

ssh -i $KEY_FILE "${SERVER_USER}@${SERVER_HOST}" $extractCommand

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ 解压失败" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ 文件解压成功" -ForegroundColor Green

Write-Host ""
Write-Host "[4/5] 重启知识库服务..." -ForegroundColor Yellow

$restartCommand = @"
cd $REMOTE_DIR && \
sudo docker compose restart knowledge-base && \
echo '等待服务启动...' && \
sleep 10
"@

ssh -i $KEY_FILE "${SERVER_USER}@${SERVER_HOST}" $restartCommand

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ 重启失败" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ 服务重启成功" -ForegroundColor Green

Write-Host ""
Write-Host "[5/5] 验证服务状态..." -ForegroundColor Yellow

$checkCommand = @"
cd $REMOTE_DIR && \
echo '检查容器状态:' && \
sudo docker ps --filter name=knowledge-base --format 'table {{.Names}}\t{{.Status}}' && \
echo '' && \
echo '检查最新日志:' && \
sudo docker logs --tail 20 enterprise-ai-knowledge-base 2>&1 | grep -v health
"@

ssh -i $KEY_FILE "${SERVER_USER}@${SERVER_HOST}" $checkCommand

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "修复完成!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "修改内容:" -ForegroundColor Yellow
Write-Host "  1. 文档上传默认改为同步处理（process_async=False）" -ForegroundColor White
Write-Host "  2. 添加详细的处理日志记录" -ForegroundColor White
Write-Host "  3. 添加文档处理超时配置" -ForegroundColor White
Write-Host "  4. 改进错误处理和状态更新" -ForegroundColor White
Write-Host ""
Write-Host "下一步:" -ForegroundColor Yellow
Write-Host "  1. 访问前端界面上传测试文档" -ForegroundColor White
Write-Host "  2. 观察日志: ssh -i $KEY_FILE ${SERVER_USER}@${SERVER_HOST} 'cd $REMOTE_DIR && sudo docker logs -f enterprise-ai-knowledge-base'" -ForegroundColor White
Write-Host "  3. 检查文档状态是否从'处理中'变为'已完成'" -ForegroundColor White
Write-Host ""

# 清理
Remove-Item -Recurse -Force $tempDir
Remove-Item -Force $tarFile

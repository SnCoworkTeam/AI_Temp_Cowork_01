# 快速上传脚本 - 统一意图识别LLM增强
# 简化版，直接上传核心文件

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  统一意图识别LLM增强 - 快速上传" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 配置（请根据实际情况修改）
$SERVER_HOST = $env:UPLOAD_SERVER_HOST
$SERVER_PATH = $env:UPLOAD_SERVER_PATH

if (-not $SERVER_HOST) {
    $SERVER_HOST = Read-Host "请输入服务器地址 (例如: user@192.168.1.100 或留空跳过)"
}

if (-not $SERVER_PATH) {
    $SERVER_PATH = Read-Host "请输入服务器路径 (例如: /opt/enterprise-ai-platform 或留空使用默认)"
}

if ([string]::IsNullOrEmpty($SERVER_PATH)) {
    $SERVER_PATH = "/opt/enterprise-ai-platform"
}

if ([string]::IsNullOrEmpty($SERVER_HOST)) {
    Write-Host "[跳过] 未提供服务器地址，跳过上传" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "如需上传，请设置环境变量:" -ForegroundColor Cyan
    Write-Host "  `$env:UPLOAD_SERVER_HOST = 'user@server'" -ForegroundColor Yellow
    Write-Host "  `$env:UPLOAD_SERVER_PATH = '/opt/enterprise-ai-platform'" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "或手动上传以下文件:" -ForegroundColor Cyan
    Write-Host "  services/llm_client.py" -ForegroundColor Yellow
    Write-Host "  services/semantic_engine_adapter.py" -ForegroundColor Yellow
    Write-Host "  services/unified_intent_service.py" -ForegroundColor Yellow
    exit 0
}

# 需要上传的文件
$filesToUpload = @(
    "services/llm_client.py",
    "services/semantic_engine_adapter.py",
    "services/unified_intent_service.py"
)

Write-Host "[检查] 检查文件..." -ForegroundColor Cyan
$missingFiles = @()
foreach ($file in $filesToUpload) {
    if (Test-Path $file) {
        $fileInfo = Get-Item $file
        Write-Host "  [OK] $file ($($fileInfo.Length) bytes)" -ForegroundColor Gray
    } else {
        Write-Host "  [WARN] 文件不存在: $file" -ForegroundColor Yellow
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "[错误] 以下文件不存在，无法上传" -ForegroundColor Red
    $missingFiles | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    exit 1
}

Write-Host ""
Write-Host "[上传] 开始上传文件到服务器..." -ForegroundColor Cyan
Write-Host "  目标: $SERVER_HOST:$SERVER_PATH" -ForegroundColor Yellow

try {
    # 上传文件
    foreach ($file in $filesToUpload) {
        $destPath = "$SERVER_HOST`:$SERVER_PATH/$file"
        Write-Host "  上传: $file -> $destPath" -ForegroundColor Gray
        
        scp $file $destPath 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    [OK] 上传成功" -ForegroundColor Green
        } else {
            Write-Host "    [错误] 上传失败" -ForegroundColor Red
            exit 1
        }
    }
    
    Write-Host ""
    Write-Host "[OK] 所有文件上传成功！" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步操作:" -ForegroundColor Cyan
    Write-Host "  1. SSH登录服务器: ssh $SERVER_HOST" -ForegroundColor Yellow
    Write-Host "  2. 进入项目目录: cd $SERVER_PATH" -ForegroundColor Yellow
    Write-Host "  3. 设置环境变量（参考 DEPLOYMENT_GUIDE.md）" -ForegroundColor Yellow
    Write-Host "  4. 安装依赖: pip install httpx langchain-openai" -ForegroundColor Yellow
    Write-Host "  5. 重启服务: docker-compose restart unified-intent-service" -ForegroundColor Yellow
    Write-Host "  6. 验证部署: curl http://localhost:8002/health" -ForegroundColor Yellow
    
} catch {
    Write-Host "[错误] 上传过程出错: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""



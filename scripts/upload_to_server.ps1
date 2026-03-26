# 统一意图识别LLM增强 - 服务器上传脚本
# 适用于Windows PowerShell

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  统一意图识别LLM增强 - 服务器上传" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 配置
$SERVER_HOST = Read-Host "请输入服务器地址 (例如: user@192.168.1.100)"
$SERVER_PATH = Read-Host "请输入服务器路径 (例如: /opt/enterprise-ai-platform)" 
$USE_SSH = $true

# 检查SSH连接
if ($USE_SSH) {
    Write-Host "[检查] SSH连接..." -ForegroundColor Cyan
    $sshTest = ssh -o ConnectTimeout=5 $SERVER_HOST "echo 'SSH连接成功'" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[错误] SSH连接失败，请检查:" -ForegroundColor Red
        Write-Host "  1. SSH密钥是否配置" -ForegroundColor Yellow
        Write-Host "  2. 服务器地址是否正确" -ForegroundColor Yellow
        Write-Host "  3. 网络连接是否正常" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "[OK] SSH连接成功" -ForegroundColor Green
}

# 需要上传的文件列表
$filesToUpload = @(
    "services/llm_client.py",
    "services/semantic_engine_adapter.py",
    "services/unified_intent_service.py",
    "api/unified_intent_api.py",
    "api/collaborative_interface_api.py",
    "tests/test_unified_intent_llm_enhancement.py",
    "docs/UNIFIED_INTENT_LLM_ENHANCEMENT_PLAN_V2.md",
    "DEPLOYMENT_GUIDE.md",
    "DEPLOYMENT_CHECKLIST.md",
    "LLM_ENHANCEMENT_DEPLOYMENT_SUMMARY.md"
)

# 创建临时目录
$tempDir = New-TemporaryFile | ForEach-Object { Remove-Item $_; New-Item -ItemType Directory -Path $_ }
Write-Host "[准备] 创建临时目录: $tempDir" -ForegroundColor Cyan

# 复制文件到临时目录
Write-Host "[准备] 复制文件..." -ForegroundColor Cyan
foreach ($file in $filesToUpload) {
    if (Test-Path $file) {
        $destPath = Join-Path $tempDir $file
        $destDir = Split-Path $destPath -Parent
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        Copy-Item $file $destPath -Force
        Write-Host "  [OK] $file" -ForegroundColor Gray
    } else {
        Write-Host "  [WARN] 文件不存在: $file" -ForegroundColor Yellow
    }
}

# 创建部署说明文件
$deployNote = @"
# 统一意图识别LLM增强 - 部署说明

## 部署步骤

1. 设置环境变量:
   export DEEPSEEK_API_KEY=your-api-key
   export LLM_BASE_URL=https://api.deepseek.com
   export LLM_MODEL=deepseek-chat
   export UNIFIED_INTENT_USE_LLM=true

2. 安装依赖:
   pip install httpx langchain-openai

3. 重启服务:
   docker-compose restart unified-intent-service
   # 或
   systemctl restart unified-intent-service

4. 验证部署:
   curl http://localhost:8002/health
   curl -X POST http://localhost:8002/api/v1/intent/understand -H "Content-Type: application/json" -d '{"user_input": "创建采购订单"}'

## 回滚方法

如果出现问题，可以快速回滚:
   export UNIFIED_INTENT_USE_LLM=false
   docker-compose restart unified-intent-service
"@

$deployNotePath = Join-Path $tempDir "DEPLOY_NOTE.md"
$deployNote | Out-File -FilePath $deployNotePath -Encoding UTF8

Write-Host "[OK] 文件准备完成" -ForegroundColor Green
Write-Host ""

# 上传到服务器
Write-Host "[上传] 开始上传文件到服务器..." -ForegroundColor Cyan
Write-Host "  目标: $SERVER_HOST:$SERVER_PATH" -ForegroundColor Yellow

try {
    # 使用scp上传
    $scpCommand = "scp -r `"$tempDir\*`" ${SERVER_HOST}:${SERVER_PATH}/"
    Write-Host "  执行命令: $scpCommand" -ForegroundColor Gray
    
    # 执行上传
    & scp -r "$tempDir\*" "${SERVER_HOST}:${SERVER_PATH}/" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] 文件上传成功" -ForegroundColor Green
    } else {
        Write-Host "[错误] 文件上传失败" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "[错误] 上传过程出错: $_" -ForegroundColor Red
    exit 1
}

# 清理临时目录
Write-Host "[清理] 删除临时目录..." -ForegroundColor Cyan
Remove-Item -Path $tempDir -Recurse -Force

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  上传完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步操作:" -ForegroundColor Cyan
Write-Host "  1. SSH登录服务器: ssh $SERVER_HOST" -ForegroundColor Yellow
Write-Host "  2. 进入项目目录: cd $SERVER_PATH" -ForegroundColor Yellow
Write-Host "  3. 设置环境变量（参考 DEPLOY_NOTE.md）" -ForegroundColor Yellow
Write-Host "  4. 重启服务" -ForegroundColor Yellow
Write-Host "  5. 验证部署" -ForegroundColor Yellow
Write-Host ""



#!/usr/bin/env pwsh
# 检查"从采购到付款"流程是否已上传到服务器

$ErrorActionPreference = "Stop"

$SSH_KEY = "E:\enterprise-ai-platform\enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"
$REMOTE_BASE = "/opt/enterprise-ai-platform"
$BPMN_FILE = "procure_to_pay.bpmn"
$REMOTE_BPMN_PATH = "$REMOTE_BASE/workflow-engine/bpmn/$BPMN_FILE"

Write-Host "`n=== 检查从采购到付款流程上传状态 ===" -ForegroundColor Green

# 检查本地文件
Write-Host "`n1. 检查本地BPMN文件..." -ForegroundColor Cyan
$localBpmnFile = "workflow-engine/bpmn/$BPMN_FILE"
if (Test-Path $localBpmnFile) {
    $localFileInfo = Get-Item $localBpmnFile
    Write-Host "✅ 本地文件存在: $localBpmnFile" -ForegroundColor Green
    Write-Host "   文件大小: $($localFileInfo.Length) 字节" -ForegroundColor Gray
    Write-Host "   修改时间: $($localFileInfo.LastWriteTime)" -ForegroundColor Gray
} else {
    Write-Host "❌ 本地文件不存在: $localBpmnFile" -ForegroundColor Red
    exit 1
}

# 检查SSH密钥
Write-Host "`n2. 检查SSH密钥..." -ForegroundColor Cyan
if (-not (Test-Path $SSH_KEY)) {
    Write-Host "❌ SSH密钥文件不存在: $SSH_KEY" -ForegroundColor Red
    exit 1
}
Write-Host "✅ SSH密钥文件存在" -ForegroundColor Green

# 检查服务器连接
Write-Host "`n3. 测试服务器连接..." -ForegroundColor Cyan
try {
    $testConnection = ssh -i $SSH_KEY -o ConnectTimeout=10 -o StrictHostKeyChecking=no $SERVER "echo '连接成功'" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 服务器连接成功" -ForegroundColor Green
    } else {
        Write-Host "❌ 服务器连接失败: $testConnection" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ 服务器连接异常: $_" -ForegroundColor Red
    exit 1
}

# 检查服务器上的BPMN文件
Write-Host "`n4. 检查服务器上的BPMN文件..." -ForegroundColor Cyan
$remoteCheck = ssh -i $SSH_KEY $SERVER "if [ -f `"$REMOTE_BPMN_PATH`" ]; then echo 'FILE_EXISTS'; ls -lh `"$REMOTE_BPMN_PATH`"; stat -c 'SIZE:%s|MTIME:%y' `"$REMOTE_BPMN_PATH`"; else echo 'FILE_NOT_EXISTS'; echo '检查目录是否存在:'; ls -la `"$REMOTE_BASE/workflow-engine/bpmn/`" 2>&1 || echo '目录不存在'; fi" 2>&1

if ($remoteCheck -match "FILE_EXISTS") {
    Write-Host "✅ 服务器上文件存在: $REMOTE_BPMN_PATH" -ForegroundColor Green
    Write-Host "`n文件详情:" -ForegroundColor Yellow
    $remoteCheck | Where-Object { $_ -notmatch "FILE_EXISTS" } | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
    
    # 提取文件信息
    if ($remoteCheck -match "SIZE:(\d+)\|MTIME:(.+)") {
        $remoteSize = $matches[1]
        $remoteMtime = $matches[2]
        Write-Host "`n服务器文件信息:" -ForegroundColor Yellow
        Write-Host "   文件大小: $remoteSize 字节" -ForegroundColor Gray
        Write-Host "   修改时间: $remoteMtime" -ForegroundColor Gray
        
        # 比较文件大小
        if ([int]$remoteSize -eq $localFileInfo.Length) {
            Write-Host "✅ 文件大小一致" -ForegroundColor Green
        } else {
            Write-Host "⚠️  文件大小不一致 (本地: $($localFileInfo.Length), 服务器: $remoteSize)" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "❌ 服务器上文件不存在: $REMOTE_BPMN_PATH" -ForegroundColor Red
    Write-Host "`n服务器响应:" -ForegroundColor Yellow
    $remoteCheck | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
}

# 检查工作流引擎是否已部署该流程
Write-Host "`n5. 检查工作流引擎部署状态..." -ForegroundColor Cyan
$deploymentCheck = ssh -i $SSH_KEY $SERVER "if systemctl is-active --quiet workflow-engine 2>/dev/null; then echo 'SERVICE_RUNNING'; elif docker ps 2>/dev/null | grep -q workflow-engine; then echo 'DOCKER_RUNNING'; else echo 'SERVICE_NOT_RUNNING'; fi; if [ -d `"$REMOTE_BASE/workflow-engine`" ]; then echo 'WORKFLOW_DIR_EXISTS'; find `"$REMOTE_BASE/workflow-engine`" -name '*procure*' -o -name '*pay*' 2>/dev/null | head -5; fi" 2>&1

Write-Host "`n部署状态:" -ForegroundColor Yellow
$deploymentCheck | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }

Write-Host "`n=== 检查完成 ===" -ForegroundColor Green


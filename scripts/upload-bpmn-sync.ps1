#!/usr/bin/env pwsh
# 上传BPMN同步脚本和文件到服务器

$ErrorActionPreference = "Stop"

$SSH_KEY = "E:\enterprise-ai-platform\enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"
$REMOTE_BASE = "/opt/enterprise-ai-platform"

Write-Host "`n=== 上传BPMN同步文件到服务器 ===" -ForegroundColor Green

# 检查SSH密钥
if (-not (Test-Path $SSH_KEY)) {
    Write-Host "❌ SSH密钥文件不存在: $SSH_KEY" -ForegroundColor Red
    exit 1
}

# 1. 上传同步脚本
Write-Host "`n1. 上传同步脚本..." -ForegroundColor Cyan
$scriptFile = "scripts/sync_bpmn_to_server.py"
if (-not (Test-Path $scriptFile)) {
    Write-Host "⚠️  脚本文件不存在: $scriptFile，跳过脚本上传" -ForegroundColor Yellow
    $remoteScriptPath = "$REMOTE_BASE/scripts/sync_bpmn_to_server.py"
} else {
    $remoteScriptPath = "$REMOTE_BASE/scripts/sync_bpmn_to_server.py"
    $tempScriptPath = "~/sync_bpmn_to_server.py"
    scp -i $SSH_KEY $scriptFile "${SERVER}:${tempScriptPath}" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 脚本上传到临时位置成功" -ForegroundColor Green
        ssh -i $SSH_KEY $SERVER "sudo mv ~/sync_bpmn_to_server.py `"$remoteScriptPath`" && sudo chown ubuntu:ubuntu `"$remoteScriptPath`"" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 脚本移动到目标位置成功" -ForegroundColor Green
        } else {
            Write-Host "❌ 脚本移动失败" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "❌ 脚本上传失败" -ForegroundColor Red
        exit 1
    }
}

# 2. 确保远程scripts目录存在
Write-Host "`n2. 确保远程目录存在..." -ForegroundColor Cyan
ssh -i $SSH_KEY $SERVER "sudo mkdir -p $REMOTE_BASE/scripts $REMOTE_BASE/workflow-engine/bpmn && sudo chown -R ubuntu:ubuntu $REMOTE_BASE" 2>&1 | Out-Null

# 3. 上传BPMN文件
Write-Host "`n3. 上传BPMN文件..." -ForegroundColor Cyan
$bpmnFile = "workflow-engine/bpmn/procure_to_pay.bpmn"
if (-not (Test-Path $bpmnFile)) {
    Write-Host "❌ BPMN文件不存在: $bpmnFile" -ForegroundColor Red
    exit 1
}

# 先上传到临时目录
$tempRemotePath = "~/procure_to_pay.bpmn"
$remoteBpmnPath = "$REMOTE_BASE/workflow-engine/bpmn/procure_to_pay.bpmn"
scp -i $SSH_KEY $bpmnFile "${SERVER}:${tempRemotePath}" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ BPMN文件上传到临时位置成功" -ForegroundColor Green
    # 使用sudo移动到目标位置
    Write-Host "   移动到目标位置..." -ForegroundColor Cyan
    ssh -i $SSH_KEY $SERVER "sudo mv ~/procure_to_pay.bpmn `"$remoteBpmnPath`" && sudo chown ubuntu:ubuntu `"$remoteBpmnPath`"" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ BPMN文件移动到目标位置成功" -ForegroundColor Green
    } else {
        Write-Host "❌ BPMN文件移动失败" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "❌ BPMN文件上传失败" -ForegroundColor Red
    exit 1
}

# 4. 设置执行权限
Write-Host "`n4. 设置执行权限..." -ForegroundColor Cyan
ssh -i $SSH_KEY $SERVER "chmod +x $remoteScriptPath" 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 权限设置成功" -ForegroundColor Green
}

# 5. 验证上传结果
Write-Host "`n5. 验证上传结果..." -ForegroundColor Cyan
$verifyResult = ssh -i $SSH_KEY $SERVER "echo '=== 脚本文件 ==='; ls -lh `"$remoteScriptPath`" 2>&1; echo ''; echo '=== BPMN文件 ==='; ls -lh `"$remoteBpmnPath`" 2>&1; echo ''; echo '=== BPMN文件MD5 ==='; md5sum `"$remoteBpmnPath`" 2>&1" 2>&1

Write-Host $verifyResult

Write-Host "`n=== 上传完成 ===" -ForegroundColor Green
Write-Host "`n在服务器上运行同步命令：" -ForegroundColor Yellow
Write-Host "  cd $REMOTE_BASE" -ForegroundColor White
Write-Host "  python3 scripts/sync_bpmn_to_server.py --bpmn workflow-engine/bpmn/procure_to_pay.bpmn --server http://localhost:8080" -ForegroundColor White


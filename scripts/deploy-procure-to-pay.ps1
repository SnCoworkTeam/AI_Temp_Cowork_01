#!/usr/bin/env pwsh
# 部署"从采购到付款"流程到工作流引擎

$ErrorActionPreference = "Stop"

$SSH_KEY = "E:\enterprise-ai-platform\enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"
$REMOTE_BPMN = "/opt/enterprise-ai-platform/workflow-engine/bpmn/procure_to_pay.bpmn"
$API_SERVER = "http://localhost:8080"

Write-Host "`n=== 部署从采购到付款流程 ===" -ForegroundColor Green

# 1. 上传BPMN文件并解析
Write-Host "`n1. 上传并解析BPMN文件..." -ForegroundColor Cyan
$uploadResult = ssh -i $SSH_KEY $SERVER @"
curl -s -X POST \
  -F "file=@$REMOTE_BPMN" \
  "$API_SERVER/api/v1/bpmn/upload" | python3 -m json.tool
"@ 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ BPMN上传失败" -ForegroundColor Red
    Write-Host $uploadResult
    exit 1
}

# 解析返回的JSON
try {
    $workflowDef = $uploadResult | ConvertFrom-Json
    Write-Host "✅ BPMN解析成功" -ForegroundColor Green
    Write-Host "   工作流名称: $($workflowDef.name)" -ForegroundColor Gray
    Write-Host "   节点数量: $($workflowDef.nodes.Count)" -ForegroundColor Gray
} catch {
    Write-Host "❌ 解析响应失败: $_" -ForegroundColor Red
    Write-Host "响应内容: $uploadResult" -ForegroundColor Yellow
    exit 1
}

# 2. 保存工作流到数据库
Write-Host "`n2. 保存工作流到数据库..." -ForegroundColor Cyan

# 构建保存请求的JSON
$savePayload = @{
    workflow = @{
        name = $workflowDef.name
        description = if ($workflowDef.description) { $workflowDef.description } else { "" }
        version = if ($workflowDef.version) { $workflowDef.version } else { "1.0.0" }
        nodes = $workflowDef.nodes
        connections = $workflowDef.connections
        start_node_id = $workflowDef.start_node_id
        end_node_ids = if ($workflowDef.end_node_ids) { $workflowDef.end_node_ids } else { @() }
        variables = if ($workflowDef.variables) { $workflowDef.variables } else { @{} }
        metadata = if ($workflowDef.metadata) { $workflowDef.metadata } else { @{} }
    }
    overwrite = $true
} | ConvertTo-Json -Depth 10

# 将JSON保存到临时文件
$tempJsonFile = "/tmp/workflow_save_$(Get-Date -Format 'yyyyMMddHHmmss').json"
$savePayload | Out-File -FilePath $tempJsonFile -Encoding utf8

Write-Host "   工作流名称: $($workflowDef.name)" -ForegroundColor Gray
Write-Host "   覆盖已存在: True" -ForegroundColor Gray

# 尝试多个API路径
$apiPaths = @(
    "$API_SERVER/api/workflows",
    "$API_SERVER/api/v1/workflows"
)

$saveSuccess = $false
foreach ($apiPath in $apiPaths) {
    Write-Host "   尝试URL: $apiPath" -ForegroundColor Gray
    
    $saveResult = ssh -i $SSH_KEY $SERVER @"
# 上传JSON文件到服务器
cat > /tmp/workflow_save.json << 'EOFPayload'
$savePayload
EOFPayload

# 调用API保存工作流
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d @/tmp/workflow_save.json \
  "$apiPath" | python3 -m json.tool
"@ 2>&1
    
    if ($LASTEXITCODE -eq 0 -and $saveResult -match '"workflow_id"|"id"') {
        Write-Host "✅ 工作流保存成功" -ForegroundColor Green
        Write-Host $saveResult
        $saveSuccess = $true
        break
    } else {
        Write-Host "   HTTP错误或响应异常" -ForegroundColor Yellow
        Write-Host "   响应: $($saveResult -join "`n")" -ForegroundColor Gray
    }
}

# 清理临时文件
Remove-Item -Path $tempJsonFile -ErrorAction SilentlyContinue
ssh -i $SSH_KEY $SERVER "rm -f /tmp/workflow_save.json" 2>&1 | Out-Null

if (-not $saveSuccess) {
    Write-Host "`n❌ 工作流保存失败" -ForegroundColor Red
    exit 1
}

# 3. 验证部署结果
Write-Host "`n3. 验证部署结果..." -ForegroundColor Cyan
$verifyResult = ssh -i $SSH_KEY $SERVER "curl -s '$API_SERVER/api/workflows' | python3 -c `"import sys, json; data=json.load(sys.stdin); workflows=[w for w in data.get('workflows', []) if '采购' in w.get('name', '') or '付款' in w.get('name', '')]; print(json.dumps(workflows, indent=2, ensure_ascii=False))`"" 2>&1

if ($verifyResult -match $workflowDef.name) {
    Write-Host "✅ 流程已成功部署并在列表中可见" -ForegroundColor Green
    Write-Host $verifyResult
} else {
    Write-Host "⚠️  验证结果不确定，请手动检查" -ForegroundColor Yellow
    Write-Host $verifyResult
}

Write-Host "`n=== 部署完成 ===" -ForegroundColor Green






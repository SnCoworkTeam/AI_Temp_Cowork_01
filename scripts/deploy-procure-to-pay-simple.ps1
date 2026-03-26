#!/usr/bin/env pwsh
# 部署"从采购到付款"流程到工作流引擎（简化版）

$ErrorActionPreference = "Stop"

$SSH_KEY = "E:\enterprise-ai-platform\enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"
$REMOTE_BASE = "/opt/enterprise-ai-platform"
$BPMN_FILE = "$REMOTE_BASE/workflow-engine/bpmn/procure_to_pay.bpmn"
$API_SERVER = "http://localhost:8080"

Write-Host "`n=== 部署从采购到付款流程 ===" -ForegroundColor Green

# 在服务器上创建并运行部署脚本
$deployScript = @"
#!/bin/bash
set -e

BPMN_FILE="$BPMN_FILE"
API_SERVER="$API_SERVER"

echo "📤 步骤1: 上传并解析BPMN文件..."
UPLOAD_RESPONSE=\$(curl -s -X POST -F "file=@\$BPMN_FILE" "\$API_SERVER/api/v1/bpmn/upload")
echo "\$UPLOAD_RESPONSE" | python3 -m json.tool

# 提取工作流定义
WORKFLOW_NAME=\$(echo "\$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['name'])" 2>/dev/null || echo "采购到付款流程")

echo ""
echo "💾 步骤2: 保存工作流到数据库..."

# 构建保存请求
SAVE_PAYLOAD=\$(echo "\$UPLOAD_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
payload = {
    'workflow': {
        'name': data.get('name', '采购到付款流程'),
        'description': data.get('description', ''),
        'version': data.get('version', '1.0.0'),
        'nodes': data.get('nodes', []),
        'connections': data.get('connections', []),
        'start_node_id': data.get('start_node_id'),
        'end_node_ids': data.get('end_node_ids', []),
        'variables': data.get('variables', {}),
        'metadata': data.get('metadata', {})
    },
    'overwrite': True
}
print(json.dumps(payload, ensure_ascii=False))
")

# 尝试保存到数据库
for API_PATH in "\$API_SERVER/api/workflows" "\$API_SERVER/api/v1/workflows"; do
    echo "   尝试: \$API_PATH"
    SAVE_RESPONSE=\$(curl -s -X POST -H "Content-Type: application/json" -d "\$SAVE_PAYLOAD" "\$API_PATH")
    HTTP_CODE=\$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "\$SAVE_PAYLOAD" "\$API_PATH")
    
    if [ "\$HTTP_CODE" = "200" ] || [ "\$HTTP_CODE" = "201" ]; then
        echo "✅ 工作流保存成功"
        echo "\$SAVE_RESPONSE" | python3 -m json.tool
        break
    else
        echo "   HTTP \$HTTP_CODE: \$(echo "\$SAVE_RESPONSE" | head -c 200)"
    fi
done

echo ""
echo "🔍 步骤3: 验证部署结果..."
VERIFY_RESPONSE=\$(curl -s "\$API_SERVER/api/workflows")
WORKFLOW_FOUND=\$(echo "\$VERIFY_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); workflows=[w for w in data.get('workflows', []) if '采购' in w.get('name', '') or '付款' in w.get('name', '')]; print('FOUND' if workflows else 'NOT_FOUND'); [print(json.dumps(w, indent=2, ensure_ascii=False)) for w in workflows]" 2>/dev/null || echo "NOT_FOUND")

if echo "\$WORKFLOW_FOUND" | grep -q "FOUND"; then
    echo "✅ 流程已成功部署并在列表中可见"
    echo "\$VERIFY_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); workflows=[w for w in data.get('workflows', []) if '采购' in w.get('name', '') or '付款' in w.get('name', '')]; [print(json.dumps(w, indent=2, ensure_ascii=False)) for w in workflows]"
else
    echo "⚠️  未在列表中找到流程，显示所有工作流:"
    echo "\$VERIFY_RESPONSE" | python3 -m json.tool | head -50
fi
"@

# 将脚本上传到服务器并执行
Write-Host "`n正在部署流程..." -ForegroundColor Cyan
$deployScript | ssh -i $SSH_KEY $SERVER "cat > /tmp/deploy_workflow.sh && chmod +x /tmp/deploy_workflow.sh && bash /tmp/deploy_workflow.sh && rm -f /tmp/deploy_workflow.sh" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ 部署完成" -ForegroundColor Green
} else {
    Write-Host "`n❌ 部署失败" -ForegroundColor Red
    exit 1
}






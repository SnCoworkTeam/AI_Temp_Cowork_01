#!/bin/bash
set -e

BPMN_FILE="/opt/enterprise-ai-platform/workflow-engine/bpmn/procure_to_pay.bpmn"
API_SERVER="http://localhost:8002"
GATEWAY_SERVER="http://localhost:8080"

echo "📤 Step 1: Upload and parse BPMN file..."
UPLOAD_RESPONSE=$(curl -s -X POST -F "file=@$BPMN_FILE" "$API_SERVER/api/v1/bpmn/upload")

# Check if upload was successful
if echo "$UPLOAD_RESPONSE" | grep -q '"detail"'; then
    echo "❌ BPMN upload failed:"
    echo "$UPLOAD_RESPONSE" | python3 -m json.tool
    exit 1
fi

echo "$UPLOAD_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('✅ BPMN parsed successfully')
print('   Workflow name:', data.get('name', 'N/A'))
print('   Nodes count:', len(data.get('nodes', [])))
print('   Connections count:', len(data.get('connections', [])))
"

echo ""
echo "💾 Step 2: Save workflow to database..."

# Build save payload and convert node types
SAVE_PAYLOAD=$(echo "$UPLOAD_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)

# Convert node types: 'task' -> 'llm' (for database compatibility)
nodes = data.get('nodes', [])
for node in nodes:
    # Convert 'task' to 'llm' if it's a user task or service task
    if node.get('node_type') == 'task':
        # Check if it's an AI node (has agent config) or user task
        config = node.get('config', {})
        if 'agent_id' in config or 'assignee' in config:
            node['node_type'] = 'llm'
        else:
            # For service tasks without AI config, use 'http'
            node['node_type'] = 'http'

payload = {
    'workflow': {
        'name': data.get('name', 'Procure to Pay'),
        'description': data.get('description', ''),
        'version': data.get('version', '1.0.0'),
        'nodes': nodes,
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

# Try to save to database
for API_PATH in "$GATEWAY_SERVER/api/workflows" "$GATEWAY_SERVER/api/v1/workflows"; do
    echo "   Trying: $API_PATH"
    SAVE_RESPONSE=$(echo "$SAVE_PAYLOAD" | curl -s -X POST -H "Content-Type: application/json" -d @- "$API_PATH")
    HTTP_CODE=$(echo "$SAVE_PAYLOAD" | curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d @- "$API_PATH")
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
        echo "✅ Workflow saved successfully"
        echo "$SAVE_RESPONSE" | python3 -m json.tool
        break
    else
        echo "   HTTP $HTTP_CODE: $(echo "$SAVE_RESPONSE" | head -c 200)"
    fi
done

echo ""
echo "🔍 Step 3: Verify deployment..."
VERIFY_RESPONSE=$(curl -s "$GATEWAY_SERVER/api/workflows")
echo "$VERIFY_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    workflows = data.get('workflows', [])
    found = [w for w in workflows if '采购' in w.get('name', '') or '付款' in w.get('name', '') or 'Procure' in w.get('name', '')]
    if found:
        print('✅ Workflow found in list:')
        for w in found:
            print(f\"   - {w.get('name')} (ID: {w.get('id')}, Status: {w.get('status')})\")
    else:
        print('⚠️  Workflow not found in list. Showing all workflows:')
        for w in workflows[:5]:
            print(f\"   - {w.get('name')} (ID: {w.get('id')})\")
except Exception as e:
    print(f'Error: {e}')
    print('Response:', sys.stdin.read()[:500])
"


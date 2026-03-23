# 检查智能体数量

$serverIP = "43.143.139.197"
$serverUser = "ubuntu"
$keyFile = "enterprise_ai_platform.pem"

if (-not (Test-Path $keyFile)) {
    Write-Host "错误: 找不到SSH密钥文件 $keyFile" -ForegroundColor Red
    exit 1
}

$keyPath = Resolve-Path $keyFile

Write-Host "`n=== 检查数据库中的智能体数量 ===" -ForegroundColor Cyan
$dbCount = ssh -i $keyPath -o StrictHostKeyChecking=no $serverUser@$serverIP "cd /opt/enterprise-ai-platform && docker compose exec -T postgres psql -U ai_user -d ai_platform -c 'SELECT COUNT(*) FROM agents;' 2>&1" 2>&1
Write-Host $dbCount

Write-Host "`n=== 检查知识图谱中的智能体节点数量 ===" -ForegroundColor Cyan
$kgCount = ssh -i $keyPath -o StrictHostKeyChecking=no $serverUser@$serverIP "cd /opt/enterprise-ai-platform && docker compose exec -T postgres psql -U ai_user -d ai_platform -c \"SELECT COUNT(*) FROM knowledge_graph_nodes WHERE node_type = 'concept' AND label LIKE 'agent_%';\" 2>&1" 2>&1
Write-Host $kgCount

Write-Host "`n=== 检查智能体服务API返回的数量 ===" -ForegroundColor Cyan
$apiCount = ssh -i $keyPath -o StrictHostKeyChecking=no $serverUser@$serverIP "curl -s http://localhost:8080/api/v1/agents 2>&1 | python3 -c \"import sys, json; data=json.load(sys.stdin); print('Total:', len(data.get('agents', [])) if isinstance(data, dict) else len(data) if isinstance(data, list) else 0)\" 2>&1" 2>&1
Write-Host $apiCount

Write-Host "`n=== 检查元数据服务中的智能体实体数量 ===" -ForegroundColor Cyan
$metadataCount = ssh -i $keyPath -o StrictHostKeyChecking=no $serverUser@$serverIP "curl -s 'http://localhost:8005/api/knowledge-graph/nodes?node_type=concept&limit=1000' 2>&1 | python3 -c \"import sys, json; data=json.load(sys.stdin); nodes=[n for n in data.get('nodes', []) if 'agent' in str(n.get('label', '')).lower()]; print('Agent nodes in KG:', len(nodes))\" 2>&1" 2>&1
Write-Host $metadataCount

Write-Host "`n=== 检查agents表中的智能体详情 ===" -ForegroundColor Cyan
$agentDetails = ssh -i $keyPath -o StrictHostKeyChecking=no $serverUser@$serverIP "cd /opt/enterprise-ai-platform && docker compose exec -T postgres psql -U ai_user -d ai_platform -c 'SELECT id, name, created_at FROM agents ORDER BY created_at DESC LIMIT 10;' 2>&1" 2>&1
Write-Host $agentDetails




# 检查服务器上的数据库数据

$serverIP = "43.143.139.197"
$serverUser = "ubuntu"
$keyFile = "enterprise_ai_platform.pem"

if (-not (Test-Path $keyFile)) {
    Write-Host "错误: 找不到SSH密钥文件 $keyFile" -ForegroundColor Red
    exit 1
}

$keyPath = Resolve-Path $keyFile

Write-Host "`n=== 检查知识图谱数据 ===" -ForegroundColor Cyan
$kgResult = ssh -i $keyPath -o StrictHostKeyChecking=no $serverUser@$serverIP "cd /opt/enterprise-ai-platform && docker compose exec -T postgres psql -U ai_user -d ai_platform -c 'SELECT COUNT(*) as node_count FROM knowledge_graph_nodes; SELECT COUNT(*) as edge_count FROM knowledge_graph_edges;' 2>&1" 2>&1
Write-Host $kgResult

Write-Host "`n=== 检查知识库数据 ===" -ForegroundColor Cyan
$kbResult = ssh -i $keyPath -o StrictHostKeyChecking=no $serverUser@$serverIP "cd /opt/enterprise-ai-platform && docker compose exec -T postgres psql -U ai_user -d ai_platform -c 'SELECT COUNT(*) as kb_count FROM knowledge_bases; SELECT COUNT(*) as doc_count FROM documents;' 2>&1" 2>&1
Write-Host $kbResult

Write-Host "`n=== 检查文档数据详情 ===" -ForegroundColor Cyan
$docDetail = ssh -i $keyPath -o StrictHostKeyChecking=no $serverUser@$serverIP "cd /opt/enterprise-ai-platform && docker compose exec -T postgres psql -U ai_user -d ai_platform -c 'SELECT id, title, knowledge_base_id, created_at FROM documents LIMIT 10;' 2>&1" 2>&1
Write-Host $docDetail

Write-Host "`n=== 检查知识图谱节点示例 ===" -ForegroundColor Cyan
$nodeSample = ssh -i $keyPath -o StrictHostKeyChecking=no $serverUser@$serverIP "cd /opt/enterprise-ai-platform && docker compose exec -T postgres psql -U ai_user -d ai_platform -c 'SELECT id, label, node_type FROM knowledge_graph_nodes LIMIT 10;' 2>&1" 2>&1
Write-Host $nodeSample




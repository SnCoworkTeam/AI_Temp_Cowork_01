# 简单的Neo4j检查脚本
param(
    [string]$ServerHost = "43.143.139.197",
    [string]$ServerUser = "ubuntu",
    [string]$ServerKey = "E:\enterprise-ai-platform\Neo4j.pem"
)

Write-Host "上传检查脚本..." -ForegroundColor Yellow
scp -i $ServerKey -o StrictHostKeyChecking=no "E:\enterprise-ai-platform\scripts\check_neo4j_on_server.py" "${ServerUser}@${ServerHost}:/opt/enterprise-ai-platform/scripts/" 2>&1 | Out-Null

Write-Host "执行检查..." -ForegroundColor Yellow
$result = ssh -i $ServerKey -o StrictHostKeyChecking=no "${ServerUser}@${ServerHost}" "cd /opt/enterprise-ai-platform && source .env 2>/dev/null && python3 scripts/check_neo4j_on_server.py" 2>&1

Write-Host $result
$result | Out-File -FilePath "neo4j_check_result.json" -Encoding UTF8


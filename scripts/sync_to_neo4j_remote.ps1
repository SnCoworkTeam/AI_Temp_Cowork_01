# 同步企业架构数据到Neo4j服务器
$ErrorActionPreference = "Stop"

$APP_SERVER = "43.143.139.197"
$APP_SERVER_KEY = ".\enterprise_ai_platform.pem"
$APP_SERVER_USER = "ubuntu"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "同步企业架构数据到Neo4j服务器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. 上传同步脚本
Write-Host "`n[1/2] 上传同步脚本..." -ForegroundColor Yellow
try {
    scp -i $APP_SERVER_KEY -o ConnectTimeout=10 "scripts/sync_to_neo4j_server.py" "${APP_SERVER_USER}@${APP_SERVER}:/tmp/sync_to_neo4j.py" 2>&1 | Out-String
    Write-Host "✅ 脚本上传成功" -ForegroundColor Green
} catch {
    Write-Host "❌ 脚本上传失败: $_" -ForegroundColor Red
    exit 1
}

# 2. 在Docker容器中执行同步脚本
Write-Host "`n[2/2] 在Docker容器中执行同步..." -ForegroundColor Yellow
$sshTarget = "${APP_SERVER_USER}@${APP_SERVER}"
$syncCommand = "cd /opt/enterprise-ai-platform; docker compose exec -T metadata-service python /tmp/sync_to_neo4j.py"

try {
    ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget $syncCommand 2>&1
    Write-Host "`n同步完成！" -ForegroundColor Green
} catch {
    Write-Host "`n同步失败: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "同步操作完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan


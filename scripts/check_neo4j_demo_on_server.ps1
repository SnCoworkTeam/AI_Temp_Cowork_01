# 检查Neo4j演示数据需求脚本
# 上传检查脚本到服务器并执行

param(
    [string]$ServerHost = "43.143.139.197",
    [string]$ServerUser = "ubuntu",
    [string]$ServerKey = "E:\enterprise-ai-platform\Neo4j.pem",
    [string]$RemotePath = "/opt/enterprise-ai-platform"
)

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Neo4j演示数据需求检查" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查密钥文件
if (-not (Test-Path $ServerKey)) {
    Write-Host "[ERROR] 密钥文件不存在: $ServerKey" -ForegroundColor Red
    exit 1
}

# 上传检查脚本
Write-Host "[INFO] 上传检查脚本到服务器..." -ForegroundColor Yellow
$localScript = "E:\enterprise-ai-platform\scripts\check_neo4j_on_server.py"
$remoteScript = "$RemotePath/scripts/check_neo4j_on_server.py"

scp -i $ServerKey -o StrictHostKeyChecking=no "$localScript" "${ServerUser}@${ServerHost}:${remoteScript}" 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] 脚本上传成功" -ForegroundColor Green
} else {
    Write-Host "[ERROR] 脚本上传失败" -ForegroundColor Red
    exit 1
}

# 在服务器上执行检查
Write-Host "[INFO] 在服务器上执行Neo4j数据检查..." -ForegroundColor Yellow
Write-Host ""

$command = "cd $RemotePath; source .env 2>/dev/null; python3 scripts/check_neo4j_on_server.py"
$output = ssh -i $ServerKey -o StrictHostKeyChecking=no "$ServerUser@$ServerHost" $command 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] 检查完成" -ForegroundColor Green
    Write-Host ""
    Write-Host "检查结果:" -ForegroundColor Cyan
    Write-Host $output
    $output | Out-File -FilePath "neo4j_check_result.json" -Encoding UTF8
    Write-Host ""
    Write-Host "[INFO] 结果已保存到: neo4j_check_result.json" -ForegroundColor Green
} else {
    Write-Host "[ERROR] 检查失败" -ForegroundColor Red
    Write-Host $output
    exit 1
}


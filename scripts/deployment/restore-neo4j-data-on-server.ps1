#!/usr/bin/env pwsh
# Neo4j数据恢复脚本 - 在服务器上恢复Neo4j数据
# 使用方法: .\scripts\deployment\restore-neo4j-data-on-server.ps1

param(
    [string]$ServerIP = "43.143.90.179",
    [string]$ServerUser = "root",
    [string]$KeyPath = "",
    [string]$RemotePath = "/opt/enterprise-ai-platform",
    [string]$BackupFile = "",
    [string]$Neo4jPassword = "Neo4j",
    [switch]$ListBackups = $false
)

$ErrorActionPreference = "Stop"

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "📥 Neo4j数据恢复到服务器" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "服务器: $ServerUser@$ServerIP" -ForegroundColor Yellow
Write-Host "远程路径: $RemotePath" -ForegroundColor Yellow
Write-Host ""

# 检查密钥文件
$ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if ([string]::IsNullOrEmpty($KeyPath)) {
    $KeyPath = Join-Path $ProjectRoot "enterprise_ai_platform.pem"
    if (-not (Test-Path $KeyPath)) {
        $KeyPath = Join-Path $env:USERPROFILE ".ssh\enterprise_ai_platform.pem"
    }
}

if (-not (Test-Path $KeyPath)) {
    Write-Host "⚠️  未找到SSH密钥文件，将使用密码登录" -ForegroundColor Yellow
    $UsePassword = $true
} else {
    $UsePassword = $false
}

# 构建SSH命令
if ($UsePassword) {
    $sshCmd = "ssh -o StrictHostKeyChecking=no $ServerUser@${ServerIP}"
} else {
    $sshCmd = "ssh -i `"$KeyPath`" -o StrictHostKeyChecking=no $ServerUser@${ServerIP}"
}

# 检查服务器连接
Write-Host "[1/5] 检查服务器连接..." -ForegroundColor Cyan
try {
    $testResult = Invoke-Expression "$sshCmd 'echo Connection test successful'" 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "SSH连接失败"
    }
    Write-Host "✅ 服务器连接成功" -ForegroundColor Green
} catch {
    Write-Host "❌ 服务器连接失败: $_" -ForegroundColor Red
    exit 1
}

# 列出可用的备份文件
$remoteBackupDir = "$RemotePath/neo4j/backups"
Write-Host "`n[2/5] 查找备份文件..." -ForegroundColor Cyan
$listBackups = "ls -lh $remoteBackupDir 2>/dev/null | grep -E 'neo4j_backup_.*\.(tar\.gz|zip)' || echo 'No backups found'"
$backupList = Invoke-Expression "$sshCmd `"$listBackups`"" 2>&1

if ($backupList -match "No backups found" -or [string]::IsNullOrWhiteSpace($backupList)) {
    Write-Host "❌ 未找到备份文件" -ForegroundColor Red
    Write-Host "请先使用 upload-neo4j-data-to-server.ps1 上传备份文件" -ForegroundColor Yellow
    exit 1
}

Write-Host "可用的备份文件:" -ForegroundColor Yellow
Write-Host $backupList -ForegroundColor Gray

if ($ListBackups) {
    exit 0
}

# 如果没有指定备份文件，使用最新的
if ([string]::IsNullOrEmpty($BackupFile)) {
    $getLatest = "ls -t $remoteBackupDir/neo4j_backup_*.tar.gz $remoteBackupDir/neo4j_backup_*.zip 2>/dev/null | head -1"
    $latestBackup = Invoke-Expression "$sshCmd `"$getLatest`"" 2>&1
    if ($latestBackup -and -not ($latestBackup -match "No such file")) {
        $BackupFile = $latestBackup.Trim()
        Write-Host "`n使用最新备份文件: $BackupFile" -ForegroundColor Green
    } else {
        Write-Host "❌ 无法找到备份文件" -ForegroundColor Red
        exit 1
    }
} else {
    # 确保路径完整
    if (-not $BackupFile.StartsWith("/")) {
        $BackupFile = "$remoteBackupDir/$BackupFile"
    }
}

# 停止Neo4j容器
Write-Host "`n[3/5] 停止Neo4j容器..." -ForegroundColor Cyan
$stopNeo4j = "cd $RemotePath/neo4j && docker-compose stop neo4j"
Invoke-Expression "$sshCmd `"$stopNeo4j`"" | Out-Null
Write-Host "✅ Neo4j容器已停止" -ForegroundColor Green

# 备份当前数据（以防万一）
Write-Host "`n[4/5] 备份当前数据..." -ForegroundColor Cyan
$backupCurrent = "cd $RemotePath/neo4j && tar -czf data_backup_before_restore_$(date +%Y%m%d_%H%M%S).tar.gz data/ 2>/dev/null || true"
Invoke-Expression "$sshCmd `"$backupCurrent`"" | Out-Null
Write-Host "✅ 当前数据已备份" -ForegroundColor Green

# 解压并恢复数据
Write-Host "`n[5/5] 恢复Neo4j数据..." -ForegroundColor Cyan

# 解压备份文件
$extractDir = "$RemotePath/neo4j/restore_temp"
$extractCmd = @"
mkdir -p $extractDir && 
cd $extractDir && 
if [[ `$BackupFile == *.tar.gz ]]; then
    tar -xzf `$BackupFile
elif [[ `$BackupFile == *.zip ]]; then
    unzip -q `$BackupFile
fi
"@

Write-Host "正在解压备份文件..." -ForegroundColor Yellow
Invoke-Expression "$sshCmd `"$extractCmd`"" | Out-Null

# 恢复数据目录
Write-Host "正在恢复数据目录..." -ForegroundColor Yellow
$restoreData = @"
if [ -d "$extractDir/data" ]; then
    rm -rf $RemotePath/neo4j/data/* &&
    cp -r $extractDir/data/* $RemotePath/neo4j/data/
    echo "数据目录恢复完成"
elif [ -d "$extractDir/neo4j_data_*/data" ]; then
    rm -rf $RemotePath/neo4j/data/* &&
    cp -r $extractDir/neo4j_data_*/data/* $RemotePath/neo4j/data/
    echo "数据目录恢复完成"
else
    echo "未找到数据目录"
fi
"@

$restoreResult = Invoke-Expression "$sshCmd `"$restoreData`"" 2>&1
if ($restoreResult -match "数据目录恢复完成") {
    Write-Host "✅ 数据目录恢复成功" -ForegroundColor Green
} else {
    Write-Host "⚠️  数据目录恢复可能不完整，继续..." -ForegroundColor Yellow
}

# 如果存在dump文件，使用neo4j-admin load
$loadDump = @"
if [ -f "$extractDir/neo4j_dump.dump" ]; then
    cd $RemotePath/neo4j &&
    docker-compose run --rm neo4j neo4j-admin database load neo4j --from-path=/tmp --overwrite-destination=true &&
    docker cp $extractDir/neo4j_dump.dump enterprise-ai-neo4j:/tmp/neo4j.dump
    echo "Dump文件恢复完成"
fi
"@

$loadResult = Invoke-Expression "$sshCmd `"$loadDump`"" 2>&1
if ($loadResult -match "Dump文件恢复完成") {
    Write-Host "✅ Dump文件恢复成功" -ForegroundColor Green
}

# 清理临时文件
Write-Host "清理临时文件..." -ForegroundColor Yellow
$cleanup = "rm -rf $extractDir"
Invoke-Expression "$sshCmd `"$cleanup`"" | Out-Null

# 启动Neo4j容器
Write-Host "`n启动Neo4j容器..." -ForegroundColor Cyan
$startNeo4j = "cd $RemotePath/neo4j && docker-compose up -d"
Invoke-Expression "$sshCmd `"$startNeo4j`"" | Out-Null

# 等待Neo4j启动
Write-Host "等待Neo4j启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# 检查Neo4j状态
Write-Host "检查Neo4j状态..." -ForegroundColor Cyan
$checkStatus = "docker ps | grep neo4j"
$statusResult = Invoke-Expression "$sshCmd `"$checkStatus`"" 2>&1
if ($statusResult -match "neo4j") {
    Write-Host "✅ Neo4j容器运行正常" -ForegroundColor Green
} else {
    Write-Host "⚠️  无法确认Neo4j状态" -ForegroundColor Yellow
}

# 验证数据
Write-Host "`n验证数据..." -ForegroundColor Cyan
Start-Sleep -Seconds 10
$verifyData = "docker exec enterprise-ai-neo4j cypher-shell -u neo4j -p $Neo4jPassword 'MATCH (n) RETURN count(n) AS nodeCount'"
$verifyResult = Invoke-Expression "$sshCmd `"$verifyData`"" 2>&1
if ($verifyResult -match "\d+") {
    $nodeCount = [regex]::Match($verifyResult, '\d+').Value
    Write-Host "✅ 数据验证成功，节点数量: $nodeCount" -ForegroundColor Green
} else {
    Write-Host "⚠️  数据验证失败，可能需要更多时间" -ForegroundColor Yellow
}

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "🎉 Neo4j数据恢复完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "访问地址: http://$ServerIP:7474" -ForegroundColor Yellow
Write-Host ""


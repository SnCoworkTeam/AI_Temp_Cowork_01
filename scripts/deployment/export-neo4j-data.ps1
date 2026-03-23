#!/usr/bin/env pwsh
# Neo4j数据导出脚本
# 导出本地Neo4j数据库的所有数据

param(
    [string]$OutputDir = "backups\neo4j",
    [string]$ContainerName = "enterprise-ai-neo4j",
    [string]$Neo4jUser = "neo4j",
    [string]$Neo4jPassword = "neo4j_password"
)

$ErrorActionPreference = "Stop"

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "📦 Neo4j数据导出" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Neo4j容器
Write-Host "[1/4] 检查Neo4j容器..." -ForegroundColor Cyan
$containerExists = docker ps -a --filter "name=$ContainerName" --format "{{.Names}}"
if (-not $containerExists -or $containerExists -ne $ContainerName) {
    Write-Host "❌ Neo4j容器 '$ContainerName' 未找到" -ForegroundColor Red
    Write-Host "请确保Neo4j容器正在运行" -ForegroundColor Yellow
    exit 1
}

$containerRunning = docker ps --filter "name=$ContainerName" --format "{{.Names}}"
if (-not $containerRunning) {
    Write-Host "⚠️  Neo4j容器未运行，尝试启动..." -ForegroundColor Yellow
    docker start $ContainerName | Out-Null
    Start-Sleep -Seconds 5
}

Write-Host "✅ Neo4j容器检查通过" -ForegroundColor Green

# 创建输出目录
Write-Host "`n[2/4] 创建输出目录..." -ForegroundColor Cyan
$ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$OutputPath = Join-Path $ProjectRoot $OutputDir
New-Item -ItemType Directory -Force -Path $OutputPath | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Write-Host "✅ 输出目录: $OutputPath" -ForegroundColor Green

# 导出数据目录
Write-Host "`n[3/4] 导出Neo4j数据目录..." -ForegroundColor Cyan
$DataBackupDir = Join-Path $OutputPath "neo4j_data_$Timestamp"
New-Item -ItemType Directory -Force -Path $DataBackupDir | Out-Null

# 导出数据目录
Write-Host "正在导出数据目录..." -ForegroundColor Yellow
docker cp "${ContainerName}:/data" "$DataBackupDir\data" 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 数据目录导出成功" -ForegroundColor Green
} else {
    Write-Host "⚠️  数据目录导出可能失败，继续..." -ForegroundColor Yellow
}

# 使用cypher-shell导出数据（CSV格式）
Write-Host "`n[4/4] 使用Cypher导出数据..." -ForegroundColor Cyan

# 导出所有节点
Write-Host "正在导出节点数据..." -ForegroundColor Yellow
$exportNodesQuery = @"
MATCH (n)
RETURN labels(n) AS labels, properties(n) AS properties
"@

$nodesFile = Join-Path $DataBackupDir "nodes_export.cypher"
$exportNodesCmd = "docker exec $ContainerName cypher-shell -u $Neo4jUser -p $Neo4jPassword --format plain"
$exportNodesQuery | & $exportNodesCmd.Split(' ') | Out-File -FilePath $nodesFile -Encoding utf8

# 导出所有关系
Write-Host "正在导出关系数据..." -ForegroundColor Yellow
$exportRelationsQuery = @"
MATCH (a)-[r]->(b)
RETURN type(r) AS type, properties(r) AS properties, 
       labels(a) AS sourceLabels, properties(a) AS sourceProps,
       labels(b) AS targetLabels, properties(b) AS targetProps
"@

$relationsFile = Join-Path $DataBackupDir "relations_export.cypher"
$exportRelationsQuery | & $exportNodesCmd.Split(' ') | Out-File -FilePath $relationsFile -Encoding utf8

# 使用neo4j-admin dump导出完整数据库（如果可用）
Write-Host "正在尝试使用neo4j-admin导出完整数据库..." -ForegroundColor Yellow
$dumpFile = Join-Path $DataBackupDir "neo4j_dump.dump"
$dumpCmd = "docker exec $ContainerName neo4j-admin database dump neo4j --to-path=/tmp"
$dumpResult = Invoke-Expression $dumpCmd 2>&1
if ($LASTEXITCODE -eq 0) {
    docker cp "${ContainerName}:/tmp/neo4j.dump" $dumpFile 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 完整数据库导出成功" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️  neo4j-admin导出失败（可能需要停止数据库），使用数据目录备份" -ForegroundColor Yellow
}

# 压缩备份文件
Write-Host "`n压缩备份文件..." -ForegroundColor Cyan
$backupArchive = Join-Path $OutputPath "neo4j_backup_$Timestamp.tar.gz"
$compressCmd = "tar -czf `"$backupArchive`" -C `"$DataBackupDir`" ."
if (Get-Command tar -ErrorAction SilentlyContinue) {
    Invoke-Expression $compressCmd | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 备份文件压缩成功" -ForegroundColor Green
        $archiveSize = [math]::Round((Get-Item $backupArchive).Length / 1MB, 2)
        Write-Host "   文件大小: $archiveSize MB" -ForegroundColor Gray
    }
} else {
    # 使用PowerShell压缩
    $backupZip = Join-Path $OutputPath "neo4j_backup_$Timestamp.zip"
    Compress-Archive -Path "$DataBackupDir\*" -DestinationPath $backupZip -Force
    Write-Host "✅ 备份文件压缩成功 (ZIP格式)" -ForegroundColor Green
    $archiveSize = [math]::Round((Get-Item $backupZip).Length / 1MB, 2)
    Write-Host "   文件大小: $archiveSize MB" -ForegroundColor Gray
}

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "🎉 Neo4j数据导出完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "备份位置: $OutputPath" -ForegroundColor Yellow
Write-Host ""


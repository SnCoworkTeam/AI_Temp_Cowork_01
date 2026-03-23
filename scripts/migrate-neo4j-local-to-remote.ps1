#!/usr/bin/env pwsh
<#
.SYNOPSIS
将本地Docker中的Neo4j数据迁移到远程服务器

.DESCRIPTION
1. 从本地Neo4j容器导出数据
2. 将数据文件传输到远程服务器
3. 在远程服务器上导入数据
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$LocalContainerName = "enterprise-ai-neo4j",
    
    [Parameter(Mandatory=$true)]
    [string]$RemoteHost = "43.143.90.179",
    
    [Parameter(Mandatory=$false)]
    [string]$RemoteUser = "root",
    
    [Parameter(Mandatory=$false)]
    [string]$SshKeyPath = "Neo4j.pem",
    
    [Parameter(Mandatory=$false)]
    [string]$LocalNeo4jPassword = "neo4j_password",
    
    [Parameter(Mandatory=$false)]
    [string]$RemoteNeo4jPassword = "Neo4j@2024"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Neo4j数据迁移：本地 -> 远程" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查本地容器
Write-Host "[1] 检查本地Neo4j容器..." -ForegroundColor Yellow
$localContainer = docker ps --filter "name=$LocalContainerName" --format "{{.Names}}" | Select-Object -First 1
if (-not $localContainer) {
    Write-Host "❌ 本地Neo4j容器 '$LocalContainerName' 未运行" -ForegroundColor Red
    Write-Host "请先启动本地Neo4j容器" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ 找到本地容器: $localContainer" -ForegroundColor Green

# 检查本地数据
Write-Host ""
Write-Host "[2] 检查本地Neo4j数据..." -ForegroundColor Yellow
$nodeCount = docker exec $LocalContainerName cypher-shell -u neo4j -p $LocalNeo4jPassword "MATCH (n) RETURN count(n) AS count;" --format plain 2>&1 | Select-String -Pattern "\d+" | ForEach-Object { $_.Matches.Value } | Select-Object -First 1
if ($nodeCount) {
    Write-Host "✅ 本地节点数量: $nodeCount" -ForegroundColor Green
} else {
    Write-Host "⚠️  无法获取节点数量，继续执行..." -ForegroundColor Yellow
}

# 方法1: 使用neo4j-admin dump（推荐）
Write-Host ""
Write-Host "[3] 导出Neo4j数据（使用neo4j-admin dump）..." -ForegroundColor Yellow
$dumpFile = "neo4j-dump-$(Get-Date -Format 'yyyyMMdd-HHmmss').dump"
$dumpPath = "/tmp/$dumpFile"

try {
    # 在容器内执行dump
    docker exec $LocalContainerName neo4j-admin database dump neo4j --to-path=/tmp 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        # 从容器复制dump文件到本地
        docker cp "${LocalContainerName}:/tmp/neo4j.dump" "./$dumpFile"
        Write-Host "✅ 数据导出成功: $dumpFile" -ForegroundColor Green
    } else {
        throw "导出失败"
    }
} catch {
    Write-Host "⚠️  neo4j-admin dump失败，尝试使用Cypher导出..." -ForegroundColor Yellow
    
    # 方法2: 使用Cypher导出（备用方案）
    Write-Host "[3b] 使用Cypher导出数据..." -ForegroundColor Yellow
    $cypherFile = "neo4j-export-$(Get-Date -Format 'yyyyMMdd-HHmmss').cypher"
    
    # 导出所有节点和关系
    $cypherExport = @"
CALL apoc.export.cypher.all('$cypherFile', {
    format: 'cypher-shell',
    useOptimizations: {type: 'UNWIND_BATCH', unwindBatchSize: 20}
})
YIELD file, nodes, relationships, properties, time, rows, batchSize, batches, done, data
RETURN file, nodes, relationships, time, done;
"@
    
    docker exec $LocalContainerName cypher-shell -u neo4j -p $LocalNeo4jPassword $cypherExport 2>&1 | Out-Null
    
    # 从容器复制cypher文件
    docker cp "${LocalContainerName}:/var/lib/neo4j/import/$cypherFile" "./$cypherFile"
    $dumpFile = $cypherFile
    Write-Host "✅ Cypher导出成功: $cypherFile" -ForegroundColor Green
}

# 传输到远程服务器
Write-Host ""
Write-Host "[4] 传输数据文件到远程服务器..." -ForegroundColor Yellow
if (Test-Path $SshKeyPath) {
    $sshKeyArg = "-i $SshKeyPath"
} else {
    $sshKeyArg = ""
    Write-Host "⚠️  SSH密钥文件不存在，使用密码认证" -ForegroundColor Yellow
}

scp $sshKeyArg "$dumpFile" "${RemoteUser}@${RemoteHost}:/tmp/$dumpFile" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 文件传输成功" -ForegroundColor Green
} else {
    Write-Host "❌ 文件传输失败" -ForegroundColor Red
    exit 1
}

# 在远程服务器上导入
Write-Host ""
Write-Host "[5] 在远程服务器上导入数据..." -ForegroundColor Yellow

if ($dumpFile -like "*.dump") {
    # 使用neo4j-admin load
    $importCmd = @"
docker exec enterprise-ai-neo4j neo4j-admin database load neo4j --from-path=/tmp --overwrite-destination=true
"@
} else {
    # 使用cypher-shell执行Cypher文件
    $importCmd = @"
docker cp /tmp/$dumpFile enterprise-ai-neo4j:/var/lib/neo4j/import/$dumpFile
docker exec enterprise-ai-neo4j cypher-shell -u neo4j -p '$RemoteNeo4jPassword' < /var/lib/neo4j/import/$dumpFile
"@
}

ssh $sshKeyArg "${RemoteUser}@${RemoteHost}" $importCmd 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 数据导入成功" -ForegroundColor Green
} else {
    Write-Host "⚠️  导入可能有问题，请检查远程服务器日志" -ForegroundColor Yellow
}

# 验证
Write-Host ""
Write-Host "[6] 验证远程数据..." -ForegroundColor Yellow
$remoteCount = ssh $sshKeyArg "${RemoteUser}@${RemoteHost}" "docker exec enterprise-ai-neo4j cypher-shell -u neo4j -p '$RemoteNeo4jPassword' 'MATCH (n) RETURN count(n) AS count;' --format plain" 2>&1 | Select-String -Pattern "\d+" | ForEach-Object { $_.Matches.Value } | Select-Object -First 1

if ($remoteCount) {
    Write-Host "✅ 远程节点数量: $remoteCount" -ForegroundColor Green
    if ($nodeCount -and $remoteCount -eq $nodeCount) {
        Write-Host "✅ 数据迁移成功！节点数量匹配" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️  无法验证远程数据" -ForegroundColor Yellow
}

# 清理
Write-Host ""
Write-Host "[7] 清理临时文件..." -ForegroundColor Yellow
Remove-Item "./$dumpFile" -ErrorAction SilentlyContinue
ssh $sshKeyArg "${RemoteUser}@${RemoteHost}" "rm -f /tmp/$dumpFile" 2>&1 | Out-Null
Write-Host "✅ 清理完成" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "迁移完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan




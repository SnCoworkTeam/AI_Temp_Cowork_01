#!/usr/bin/env pwsh
# 数据同步脚本 - 将本地数据同步到服务器
# 包括：PostgreSQL数据库、Redis缓存、ChromaDB向量数据库、知识库文档、元数据

param(
    [string]$ServerIP = "43.143.139.197",
    [string]$ServerUser = "ubuntu",
    [string]$KeyPath = "enterprise_ai_platform.pem",
    [string]$RemotePath = "/opt/enterprise-ai-platform",
    [switch]$SkipDatabase = $false,
    [switch]$SkipRedis = $false,
    [switch]$SkipChroma = $false,
    [switch]$SkipDocuments = $false
)

$ErrorActionPreference = "Stop"

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "📦 企业AI平台 - 数据同步到服务器" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "服务器: $ServerIP" -ForegroundColor Yellow
Write-Host "远程路径: $RemotePath" -ForegroundColor Yellow
Write-Host ""

# 创建临时目录
$TempDir = "$env:TEMP\enterprise-ai-data-sync-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
Write-Host "📁 临时目录: $TempDir" -ForegroundColor Green

try {
    # 1. 导出PostgreSQL数据库
    if (-not $SkipDatabase) {
        Write-Host "`n=== 1. 导出PostgreSQL数据库 ===" -ForegroundColor Cyan
        $DbBackupFile = "$TempDir\postgres_backup.sql"
        
        Write-Host "正在导出数据库..." -ForegroundColor Yellow
        $dbName = $env:DB_NAME ?? "ai_platform"
        $dbUser = $env:DB_USER ?? "ai_user"
        $dbPassword = $env:DB_PASSWORD ?? "ai_password"
        
        # 使用docker exec导出数据库
        $exportCmd = "docker exec enterprise-ai-postgres pg_dump -U $dbUser -d $dbName --clean --if-exists --format=plain > $DbBackupFile"
        Write-Host "执行命令: $exportCmd" -ForegroundColor Gray
        
        # 在PowerShell中执行docker命令
        $env:PGPASSWORD = $dbPassword
        docker exec enterprise-ai-postgres pg_dump -U $dbUser -d $dbName --clean --if-exists --format=plain | Out-File -FilePath $DbBackupFile -Encoding utf8
        
        if (Test-Path $DbBackupFile -ErrorAction SilentlyContinue) {
            $fileSize = (Get-Item $DbBackupFile).Length / 1MB
            Write-Host "✅ 数据库导出成功: $DbBackupFile ($([math]::Round($fileSize, 2)) MB)" -ForegroundColor Green
        } else {
            Write-Host "❌ 数据库导出失败" -ForegroundColor Red
            throw "数据库导出失败"
        }
    } else {
        Write-Host "`n⏭️  跳过PostgreSQL数据库导出" -ForegroundColor Yellow
    }

    # 2. 导出Redis数据
    if (-not $SkipRedis) {
        Write-Host "`n=== 2. 导出Redis数据 ===" -ForegroundColor Cyan
        $RedisBackupFile = "$TempDir\redis_backup.rdb"
        
        Write-Host "正在导出Redis数据..." -ForegroundColor Yellow
        
        # Redis数据通常存储在volume中，我们需要从容器中复制
        # 首先触发Redis保存
        docker exec enterprise-ai-redis redis-cli BGSAVE | Out-Null
        Start-Sleep -Seconds 2
        
        # 复制RDB文件
        docker cp enterprise-ai-redis:/data/dump.rdb $RedisBackupFile 2>&1 | Out-Null
        
        if (Test-Path $RedisBackupFile -ErrorAction SilentlyContinue) {
            $fileSize = (Get-Item $RedisBackupFile).Length / 1KB
            Write-Host "✅ Redis数据导出成功: $RedisBackupFile ($([math]::Round($fileSize, 2)) KB)" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Redis数据导出失败（可能没有数据）" -ForegroundColor Yellow
        }
    } else {
        Write-Host "`n⏭️  跳过Redis数据导出" -ForegroundColor Yellow
    }

    # 3. 导出ChromaDB向量数据库
    if (-not $SkipChroma) {
        Write-Host "`n=== 3. 导出ChromaDB向量数据库 ===" -ForegroundColor Cyan
        $ChromaBackupFile = "$TempDir\chroma_backup.tar.gz"
        
        Write-Host "正在导出ChromaDB数据..." -ForegroundColor Yellow
        
        # 从容器中复制ChromaDB数据目录
        $ChromaTempDir = "$TempDir\chroma_db"
        New-Item -ItemType Directory -Path $ChromaTempDir -Force | Out-Null
        
        docker cp enterprise-ai-knowledge-base:/app/chroma_db/. $ChromaTempDir 2>&1 | Out-Null
        
        if (Test-Path $ChromaTempDir -ErrorAction SilentlyContinue -And (Get-ChildItem $ChromaTempDir -ErrorAction SilentlyContinue)) {
            # 压缩ChromaDB数据
            Compress-Archive -Path "$ChromaTempDir\*" -DestinationPath $ChromaBackupFile -Force
            $fileSize = (Get-Item $ChromaBackupFile).Length / 1MB
            Write-Host "✅ ChromaDB数据导出成功: $ChromaBackupFile ($([math]::Round($fileSize, 2)) MB)" -ForegroundColor Green
        } else {
            Write-Host "⚠️  ChromaDB数据导出失败（可能没有数据）" -ForegroundColor Yellow
        }
    } else {
        Write-Host "`n⏭️  跳过ChromaDB数据导出" -ForegroundColor Yellow
    }

    # 4. 导出知识库文档
    if (-not $SkipDocuments) {
        Write-Host "`n=== 4. 导出知识库文档 ===" -ForegroundColor Cyan
        $DocumentsBackupFile = "$TempDir\documents_backup.tar.gz"
        
        Write-Host "正在导出知识库文档..." -ForegroundColor Yellow
        
        # 从容器中复制文档目录
        $DocumentsTempDir = "$TempDir\documents"
        New-Item -ItemType Directory -Path $DocumentsTempDir -Force | Out-Null
        
        docker cp enterprise-ai-knowledge-base:/app/documents/. $DocumentsTempDir 2>&1 | Out-Null
        
        if (Test-Path $DocumentsTempDir -ErrorAction SilentlyContinue -And (Get-ChildItem $DocumentsTempDir -ErrorAction SilentlyContinue)) {
            # 压缩文档
            Compress-Archive -Path "$DocumentsTempDir\*" -DestinationPath $DocumentsBackupFile -Force
            $fileSize = (Get-Item $DocumentsBackupFile).Length / 1MB
            Write-Host "✅ 知识库文档导出成功: $DocumentsBackupFile ($([math]::Round($fileSize, 2)) MB)" -ForegroundColor Green
        } else {
            Write-Host "⚠️  知识库文档导出失败（可能没有文档）" -ForegroundColor Yellow
        }
    } else {
        Write-Host "`n⏭️  跳过知识库文档导出" -ForegroundColor Yellow
    }

    # 5. 上传数据到服务器
    Write-Host "`n=== 5. 上传数据到服务器 ===" -ForegroundColor Cyan
    
    $RemoteDataDir = "$RemotePath/data-backup"
    ssh -i $KeyPath -o StrictHostKeyChecking=no $ServerUser@${ServerIP} "mkdir -p $RemoteDataDir" 2>&1 | Out-Null
    
    $filesToUpload = @()
    if (-not $SkipDatabase -And (Test-Path "$TempDir\postgres_backup.sql")) {
        $filesToUpload += "$TempDir\postgres_backup.sql"
    }
    if (-not $SkipRedis -And (Test-Path "$TempDir\redis_backup.rdb")) {
        $filesToUpload += "$TempDir\redis_backup.rdb"
    }
    if (-not $SkipChroma -And (Test-Path "$TempDir\chroma_backup.tar.gz")) {
        $filesToUpload += "$TempDir\chroma_backup.tar.gz"
    }
    if (-not $SkipDocuments -And (Test-Path "$TempDir\documents_backup.tar.gz")) {
        $filesToUpload += "$TempDir\documents_backup.tar.gz"
    }
    
    foreach ($file in $filesToUpload) {
        $fileName = Split-Path $file -Leaf
        Write-Host "上传 $fileName..." -ForegroundColor Yellow
        scp -i $KeyPath -o StrictHostKeyChecking=no $file "${ServerUser}@${ServerIP}:$RemoteDataDir/" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $fileName 上传成功" -ForegroundColor Green
        } else {
            Write-Host "❌ $fileName 上传失败" -ForegroundColor Red
        }
    }

    # 6. 在服务器上恢复数据
    Write-Host "`n=== 6. 在服务器上恢复数据 ===" -ForegroundColor Cyan
    
    $restoreScript = @"
#!/bin/bash
set -e

cd $RemotePath
REMOTE_DATA_DIR="$RemoteDataDir"

echo "=== 恢复PostgreSQL数据库 ==="
if [ -f "\$REMOTE_DATA_DIR/postgres_backup.sql" ]; then
    echo "正在恢复数据库..."
    docker exec -i enterprise-ai-postgres psql -U \${DB_USER:-ai_user} -d \${DB_NAME:-ai_platform} < "\$REMOTE_DATA_DIR/postgres_backup.sql" || echo "⚠️  数据库恢复可能有问题，请检查"
    echo "✅ 数据库恢复完成"
else
    echo "⏭️  跳过数据库恢复（备份文件不存在）"
fi

echo ""
echo "=== 恢复Redis数据 ==="
if [ -f "\$REMOTE_DATA_DIR/redis_backup.rdb" ]; then
    echo "正在恢复Redis数据..."
    docker cp "\$REMOTE_DATA_DIR/redis_backup.rdb" enterprise-ai-redis:/data/dump.rdb
    docker restart enterprise-ai-redis
    echo "✅ Redis数据恢复完成"
else
    echo "⏭️  跳过Redis恢复（备份文件不存在）"
fi

echo ""
echo "=== 恢复ChromaDB向量数据库 ==="
if [ -f "\$REMOTE_DATA_DIR/chroma_backup.tar.gz" ]; then
    echo "正在恢复ChromaDB数据..."
    docker exec enterprise-ai-knowledge-base sh -c "rm -rf /app/chroma_db/*" || true
    docker cp "\$REMOTE_DATA_DIR/chroma_backup.tar.gz" enterprise-ai-knowledge-base:/tmp/chroma_backup.tar.gz
    docker exec enterprise-ai-knowledge-base sh -c "cd /app && tar -xzf /tmp/chroma_backup.tar.gz -C chroma_db && rm /tmp/chroma_backup.tar.gz" || echo "⚠️  ChromaDB恢复可能有问题"
    docker restart enterprise-ai-knowledge-base
    echo "✅ ChromaDB数据恢复完成"
else
    echo "⏭️  跳过ChromaDB恢复（备份文件不存在）"
fi

echo ""
echo "=== 恢复知识库文档 ==="
if [ -f "\$REMOTE_DATA_DIR/documents_backup.tar.gz" ]; then
    echo "正在恢复知识库文档..."
    docker exec enterprise-ai-knowledge-base sh -c "rm -rf /app/documents/*" || true
    docker cp "\$REMOTE_DATA_DIR/documents_backup.tar.gz" enterprise-ai-knowledge-base:/tmp/documents_backup.tar.gz
    docker exec enterprise-ai-knowledge-base sh -c "cd /app && tar -xzf /tmp/documents_backup.tar.gz -C documents && rm /tmp/documents_backup.tar.gz" || echo "⚠️  文档恢复可能有问题"
    docker restart enterprise-ai-knowledge-base
    echo "✅ 知识库文档恢复完成"
else
    echo "⏭️  跳过文档恢复（备份文件不存在）"
fi

echo ""
echo "✅ 所有数据恢复完成！"
"@
    
    $restoreScriptFile = "$TempDir\restore_data.sh"
    $restoreScript | Out-File -FilePath $restoreScriptFile -Encoding utf8 -NoNewline
    
    Write-Host "上传恢复脚本..." -ForegroundColor Yellow
    scp -i $KeyPath -o StrictHostKeyChecking=no $restoreScriptFile "${ServerUser}@${ServerIP}:$RemoteDataDir/restore_data.sh" 2>&1 | Out-Null
    
    Write-Host "执行恢复脚本..." -ForegroundColor Yellow
    ssh -i $KeyPath -o StrictHostKeyChecking=no $ServerUser@${ServerIP} "chmod +x $RemoteDataDir/restore_data.sh && bash $RemoteDataDir/restore_data.sh" 2>&1
    
    Write-Host "`n✅ 数据同步完成！" -ForegroundColor Green
    Write-Host "`n📊 同步摘要:" -ForegroundColor Cyan
    Write-Host "  - PostgreSQL数据库: $($filesToUpload | Where-Object { $_ -like '*postgres*' } | Measure-Object | Select-Object -ExpandProperty Count) 文件" -ForegroundColor White
    Write-Host "  - Redis数据: $($filesToUpload | Where-Object { $_ -like '*redis*' } | Measure-Object | Select-Object -ExpandProperty Count) 文件" -ForegroundColor White
    Write-Host "  - ChromaDB数据: $($filesToUpload | Where-Object { $_ -like '*chroma*' } | Measure-Object | Select-Object -ExpandProperty Count) 文件" -ForegroundColor White
    Write-Host "  - 知识库文档: $($filesToUpload | Where-Object { $_ -like '*documents*' } | Measure-Object | Select-Object -ExpandProperty Count) 文件" -ForegroundColor White

} catch {
    Write-Host "`n❌ 数据同步失败: $_" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
} finally {
    # 清理临时目录
    Write-Host "`n🧹 清理临时文件..." -ForegroundColor Yellow
    Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "✅ 清理完成" -ForegroundColor Green
}


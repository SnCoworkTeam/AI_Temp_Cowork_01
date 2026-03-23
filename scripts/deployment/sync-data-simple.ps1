#!/usr/bin/env pwsh
# 简化版数据同步脚本 - 分步执行

param(
    [string]$ServerIP = "43.143.139.197",
    [string]$ServerUser = "ubuntu",
    [string]$KeyPath = "enterprise_ai_platform.pem",
    [string]$RemotePath = "/opt/enterprise-ai-platform"
)

$ErrorActionPreference = "Continue"

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "📦 数据同步到服务器" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 创建临时目录
$TempDir = "$env:TEMP\enterprise-ai-sync-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
Write-Host "📁 临时目录: $TempDir" -ForegroundColor Green

try {
    # 1. 导出PostgreSQL数据库
    Write-Host "`n=== 1. 导出PostgreSQL数据库 ===" -ForegroundColor Cyan
    $DbBackupFile = "$TempDir\postgres_backup.sql"
    
    $dbName = "ai_platform"
    $dbUser = "ai_user"
    $dbPassword = "ai_password"
    
    Write-Host "正在导出数据库..." -ForegroundColor Yellow
    $env:PGPASSWORD = $dbPassword
    docker exec enterprise-ai-postgres pg_dump -U $dbUser -d $dbName --clean --if-exists --format=plain 2>&1 | Out-File -FilePath $DbBackupFile -Encoding utf8
    
    if (Test-Path $DbBackupFile) {
        $fileSize = [math]::Round((Get-Item $DbBackupFile).Length / 1MB, 2)
        Write-Host "✅ 数据库导出成功: $fileSize MB" -ForegroundColor Green
    } else {
        Write-Host "❌ 数据库导出失败" -ForegroundColor Red
    }

    # 2. 导出ChromaDB数据
    Write-Host "`n=== 2. 导出ChromaDB向量数据库 ===" -ForegroundColor Cyan
    $ChromaTempDir = "$TempDir\chroma_db"
    New-Item -ItemType Directory -Path $ChromaTempDir -Force | Out-Null
    
    Write-Host "正在复制ChromaDB数据..." -ForegroundColor Yellow
    docker cp enterprise-ai-knowledge-base:/app/chroma_db/. $ChromaTempDir 2>&1 | Out-Null
    
    if ((Test-Path $ChromaTempDir) -and (Get-ChildItem $ChromaTempDir -ErrorAction SilentlyContinue)) {
        $ChromaBackupFile = "$TempDir\chroma_backup.tar.gz"
        Compress-Archive -Path "$ChromaTempDir\*" -DestinationPath $ChromaBackupFile -Force
        $fileSize = [math]::Round((Get-Item $ChromaBackupFile).Length / 1MB, 2)
        Write-Host "✅ ChromaDB数据导出成功: $fileSize MB" -ForegroundColor Green
    } else {
        Write-Host "⚠️  ChromaDB数据为空或导出失败" -ForegroundColor Yellow
    }

    # 3. 导出知识库文档
    Write-Host "`n=== 3. 导出知识库文档 ===" -ForegroundColor Cyan
    $DocumentsTempDir = "$TempDir\documents"
    New-Item -ItemType Directory -Path $DocumentsTempDir -Force | Out-Null
    
    Write-Host "正在复制文档..." -ForegroundColor Yellow
    docker cp enterprise-ai-knowledge-base:/app/documents/. $DocumentsTempDir 2>&1 | Out-Null
    
    if ((Test-Path $DocumentsTempDir) -and (Get-ChildItem $DocumentsTempDir -ErrorAction SilentlyContinue)) {
        $DocumentsBackupFile = "$TempDir\documents_backup.tar.gz"
        Compress-Archive -Path "$DocumentsTempDir\*" -DestinationPath $DocumentsBackupFile -Force
        $fileSize = [math]::Round((Get-Item $DocumentsBackupFile).Length / 1MB, 2)
        Write-Host "✅ 文档导出成功: $fileSize MB" -ForegroundColor Green
    } else {
        Write-Host "⚠️  文档为空或导出失败" -ForegroundColor Yellow
    }

    # 4. 上传到服务器
    Write-Host "`n=== 4. 上传数据到服务器 ===" -ForegroundColor Cyan
    $RemoteDataDir = "$RemotePath/data-backup"
    ssh -i $KeyPath -o StrictHostKeyChecking=no $ServerUser@${ServerIP} "mkdir -p $RemoteDataDir" 2>&1 | Out-Null
    
    $files = @()
    if (Test-Path $DbBackupFile) { $files += $DbBackupFile }
    if (Test-Path "$TempDir\chroma_backup.tar.gz") { $files += "$TempDir\chroma_backup.tar.gz" }
    if (Test-Path "$TempDir\documents_backup.tar.gz") { $files += "$TempDir\documents_backup.tar.gz" }
    
    foreach ($file in $files) {
        $fileName = Split-Path $file -Leaf
        Write-Host "上传 $fileName..." -ForegroundColor Yellow
        scp -i $KeyPath -o StrictHostKeyChecking=no $file "${ServerUser}@${ServerIP}:$RemoteDataDir/" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $fileName 上传成功" -ForegroundColor Green
        } else {
            Write-Host "❌ $fileName 上传失败" -ForegroundColor Red
        }
    }

    # 5. 在服务器上恢复数据
    Write-Host "`n=== 5. 在服务器上恢复数据 ===" -ForegroundColor Cyan
    
    $restoreScript = @"
#!/bin/bash
set -e
cd $RemotePath
REMOTE_DATA_DIR="$RemoteDataDir"

echo "=== 恢复PostgreSQL数据库 ==="
if [ -f "\$REMOTE_DATA_DIR/postgres_backup.sql" ]; then
    echo "正在恢复数据库..."
    docker exec -i enterprise-ai-postgres psql -U ai_user -d ai_platform < "\$REMOTE_DATA_DIR/postgres_backup.sql" 2>&1 || echo "⚠️  数据库恢复可能有问题"
    echo "✅ 数据库恢复完成"
fi

echo ""
echo "=== 恢复ChromaDB数据 ==="
if [ -f "\$REMOTE_DATA_DIR/chroma_backup.tar.gz" ]; then
    echo "正在恢复ChromaDB..."
    docker exec enterprise-ai-knowledge-base sh -c "rm -rf /app/chroma_db/*" 2>&1 || true
    docker cp "\$REMOTE_DATA_DIR/chroma_backup.tar.gz" enterprise-ai-knowledge-base:/tmp/chroma_backup.tar.gz
    docker exec enterprise-ai-knowledge-base sh -c "cd /app && tar -xzf /tmp/chroma_backup.tar.gz -C chroma_db 2>&1 && rm /tmp/chroma_backup.tar.gz" || echo "⚠️  ChromaDB恢复可能有问题"
    docker restart enterprise-ai-knowledge-base
    echo "✅ ChromaDB恢复完成"
fi

echo ""
echo "=== 恢复知识库文档 ==="
if [ -f "\$REMOTE_DATA_DIR/documents_backup.tar.gz" ]; then
    echo "正在恢复文档..."
    docker exec enterprise-ai-knowledge-base sh -c "rm -rf /app/documents/*" 2>&1 || true
    docker cp "\$REMOTE_DATA_DIR/documents_backup.tar.gz" enterprise-ai-knowledge-base:/tmp/documents_backup.tar.gz
    docker exec enterprise-ai-knowledge-base sh -c "cd /app && tar -xzf /tmp/documents_backup.tar.gz -C documents 2>&1 && rm /tmp/documents_backup.tar.gz" || echo "⚠️  文档恢复可能有问题"
    docker restart enterprise-ai-knowledge-base
    echo "✅ 文档恢复完成"
fi

echo ""
echo "✅ 数据恢复完成！"
"@
    
    $restoreScriptFile = "$TempDir\restore_data.sh"
    # 使用Unix格式换行符
    $restoreScript = $restoreScript -replace "`r`n", "`n"
    [System.IO.File]::WriteAllText($restoreScriptFile, $restoreScript, [System.Text.Encoding]::UTF8)
    
    Write-Host "上传并执行恢复脚本..." -ForegroundColor Yellow
    scp -i $KeyPath -o StrictHostKeyChecking=no $restoreScriptFile "${ServerUser}@${ServerIP}:$RemoteDataDir/restore_data.sh" 2>&1 | Out-Null
    ssh -i $KeyPath -o StrictHostKeyChecking=no $ServerUser@${ServerIP} "chmod +x $RemoteDataDir/restore_data.sh && bash $RemoteDataDir/restore_data.sh" 2>&1
    
    Write-Host "`n✅ 数据同步完成！" -ForegroundColor Green

} catch {
    Write-Host "`n❌ 错误: $_" -ForegroundColor Red
} finally {
    Write-Host "`n🧹 清理临时文件..." -ForegroundColor Yellow
    Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
}


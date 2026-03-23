# 从同步包恢复元数据和知识库数据 (服务器端脚本)
# 在服务器上运行此脚本来恢复数据

param(
    [Parameter(Mandatory=$true)]
    [string]$SyncPackage,
    
    [string]$DbHost = "localhost",
    [string]$DbPort = "5432",
    [string]$DbName = "ai_platform",
    [string]$DbUser = "ai_user",
    [string]$DbPassword = "",
    
    [string]$ChromaVolume = "enterprise-ai-platform_knowledge_base_chroma",
    [string]$DocumentsVolume = "enterprise-ai-platform_knowledge_base_documents",
    
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  恢复元数据和知识库数据" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

if (-not (Test-Path $SyncPackage)) {
    Write-Host "[错误] 同步包不存在: $SyncPackage" -ForegroundColor Red
    exit 1
}

Write-Host "[解压] 解压同步包..." -ForegroundColor Cyan
$ExtractDir = Join-Path $env:TEMP "sync_restore_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Force -Path $ExtractDir | Out-Null

try {
    tar -xzf $SyncPackage -C $ExtractDir
    
    # 读取元数据
    $MetadataFile = Get-ChildItem -Path $ExtractDir -Filter "metadata_*.json" | Select-Object -First 1
    if (-not $MetadataFile) {
        Write-Host "[错误] 未找到元数据文件" -ForegroundColor Red
        exit 1
    }
    
    $Metadata = Get-Content $MetadataFile.FullName | ConvertFrom-Json
    Write-Host "  同步包时间戳: $($Metadata.timestamp)" -ForegroundColor Gray
    Write-Host "  包含数据:" -ForegroundColor Gray
    if ($Metadata.exports.postgres) { Write-Host "    - PostgreSQL数据" -ForegroundColor Gray }
    if ($Metadata.exports.chroma) { Write-Host "    - Chroma向量数据库" -ForegroundColor Gray }
    if ($Metadata.exports.documents) { Write-Host "    - 文档文件" -ForegroundColor Gray }
    Write-Host ""
    
    if ($DryRun) {
        Write-Host "[DRY RUN] 仅显示操作，不执行恢复" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "将执行以下操作:" -ForegroundColor Cyan
        Write-Host "  1. 恢复PostgreSQL数据" -ForegroundColor Yellow
        Write-Host "  2. 恢复Chroma向量数据库" -ForegroundColor Yellow
        Write-Host "  3. 恢复文档文件" -ForegroundColor Yellow
        exit 0
    }
    
    # 1. 恢复PostgreSQL数据
    if ($Metadata.exports.postgres) {
        Write-Host "[1/3] 恢复PostgreSQL数据..." -ForegroundColor Yellow
        $PostgresFile = Join-Path $ExtractDir $Metadata.exports.postgres
        
        if (Test-Path $PostgresFile) {
            # 解压
            $SqlFile = $PostgresFile -replace "\.gz$", ""
            gunzip -c $PostgresFile > $SqlFile
            
            # 恢复数据库
            $env:PGPASSWORD = $DbPassword
            psql -h $DbHost -p $DbPort -U $DbUser -d $DbName -f $SqlFile
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  [OK] PostgreSQL数据恢复完成" -ForegroundColor Green
            } else {
                Write-Host "  [错误] PostgreSQL数据恢复失败" -ForegroundColor Red
            }
        } else {
            Write-Host "  [警告] PostgreSQL备份文件不存在" -ForegroundColor Yellow
        }
        Write-Host ""
    }
    
    # 2. 恢复Chroma向量数据库
    if ($Metadata.exports.chroma) {
        Write-Host "[2/3] 恢复Chroma向量数据库..." -ForegroundColor Yellow
        $ChromaFile = Join-Path $ExtractDir $Metadata.exports.chroma
        
        if (Test-Path $ChromaFile) {
            # 创建临时容器
            $TempContainer = "chroma_restore_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
            docker run --rm -d --name $TempContainer -v "${ChromaVolume}:/data" alpine sleep 3600 | Out-Null
            
            try {
                # 清空现有数据
                docker exec $TempContainer sh -c "rm -rf /data/*"
                
                # 恢复数据
                gunzip -c $ChromaFile | docker exec -i $TempContainer tar -xzf - -C /data
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  [OK] Chroma数据恢复完成" -ForegroundColor Green
                } else {
                    Write-Host "  [错误] Chroma数据恢复失败" -ForegroundColor Red
                }
            } finally {
                docker rm -f $TempContainer 2>&1 | Out-Null
            }
        } else {
            Write-Host "  [警告] Chroma备份文件不存在" -ForegroundColor Yellow
        }
        Write-Host ""
    }
    
    # 3. 恢复文档文件
    if ($Metadata.exports.documents) {
        Write-Host "[3/3] 恢复文档文件..." -ForegroundColor Yellow
        $DocumentsFile = Join-Path $ExtractDir $Metadata.exports.documents
        
        if (Test-Path $DocumentsFile) {
            $TempContainer = "docs_restore_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
            docker run --rm -d --name $TempContainer -v "${DocumentsVolume}:/data" alpine sleep 3600 | Out-Null
            
            try {
                docker exec $TempContainer sh -c "rm -rf /data/*"
                gunzip -c $DocumentsFile | docker exec -i $TempContainer tar -xzf - -C /data
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  [OK] 文档文件恢复完成" -ForegroundColor Green
                } else {
                    Write-Host "  [错误] 文档文件恢复失败" -ForegroundColor Red
                }
            } finally {
                docker rm -f $TempContainer 2>&1 | Out-Null
            }
        } else {
            Write-Host "  [警告] 文档备份文件不存在" -ForegroundColor Yellow
        }
        Write-Host ""
    }
    
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  数据恢复完成！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "建议重启相关服务:" -ForegroundColor Cyan
    Write-Host "  docker-compose restart metadata-service knowledge-base" -ForegroundColor Yellow
    Write-Host ""
    
} finally {
    Remove-Item -Recurse -Force $ExtractDir -ErrorAction SilentlyContinue
}



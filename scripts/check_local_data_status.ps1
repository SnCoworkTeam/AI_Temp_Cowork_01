# 检查本地Docker中的元数据和知识库数据状态

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  检查本地数据状态" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 检查Docker
Write-Host "[检查] Docker状态..." -ForegroundColor Cyan
try {
    docker ps | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[错误] Docker未运行" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "[错误] Docker未安装或未运行" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Docker is running" -ForegroundColor Green
Write-Host ""

# 1. 检查PostgreSQL数据
Write-Host "[1/3] 检查PostgreSQL数据..." -ForegroundColor Yellow
$PostgresContainer = docker-compose -f docker-compose.yml ps -q postgres 2>&1

if ($PostgresContainer -and $PostgresContainer -notmatch "Error") {
    Write-Host "  PostgreSQL容器: 运行中" -ForegroundColor Green
    
    # 检查表数量
    $TableCount = docker exec $PostgresContainer.PostgresContainer psql -U ai_user -d ai_platform -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>&1
    if ($TableCount -match "^\s*(\d+)") {
        $Count = $Matches[1].Trim()
        Write-Host "  表数量: $Count" -ForegroundColor Gray
    }
    
    # 检查关键表的数据量
    $Tables = @("data_assets", "business_activities", "capability_units", "documents", "knowledge_base_entries")
    foreach ($Table in $Tables) {
        $Count = docker exec $PostgresContainer.PostgresContainer psql -U ai_user -d ai_platform -t -c "SELECT COUNT(*) FROM $Table;" 2>&1
        if ($Count -match "^\s*(\d+)") {
            $RowCount = $Matches[1].Trim()
            if ([int]$RowCount -gt 0) {
                Write-Host "    $Table`: $RowCount 条记录" -ForegroundColor Gray
            }
        }
    }
} else {
    Write-Host "  PostgreSQL容器: 未运行" -ForegroundColor Yellow
}
Write-Host ""

# 2. 检查Chroma向量数据库
Write-Host "[2/3] 检查Chroma向量数据库..." -ForegroundColor Yellow
$ChromaVolume = "enterprise-ai-platform_knowledge_base_chroma"
$VolumeInfo = docker volume inspect $ChromaVolume 2>&1

if ($LASTEXITCODE -eq 0) {
    $VolumePath = ($VolumeInfo | ConvertFrom-Json)[0].Mountpoint
    $VolumeSize = (docker system df -v | Select-String -Pattern $ChromaVolume -Context 5 | Select-String -Pattern "SIZE" | ForEach-Object { ($_ -split '\s+')[2] })
    
    Write-Host "  Chroma volume: 存在" -ForegroundColor Green
    Write-Host "  路径: $VolumePath" -ForegroundColor Gray
    
    # 检查是否有数据
    $TempContainer = "chroma_check_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    docker run --rm -d --name $TempContainer -v "${ChromaVolume}:/data" alpine sleep 10 | Out-Null
    
    try {
        $FileCount = docker exec $TempContainer find /data -type f | Measure-Object -Line
        if ($FileCount.Lines -gt 0) {
            Write-Host "  文件数量: $($FileCount.Lines)" -ForegroundColor Gray
            Write-Host "  [OK] Chroma有数据" -ForegroundColor Green
        } else {
            Write-Host "  [警告] Chroma为空" -ForegroundColor Yellow
        }
    } finally {
        docker rm -f $TempContainer 2>&1 | Out-Null
    }
} else {
    Write-Host "  Chroma volume: 不存在" -ForegroundColor Yellow
}
Write-Host ""

# 3. 检查文档文件
Write-Host "[3/3] 检查文档文件..." -ForegroundColor Yellow
$DocumentsVolume = "enterprise-ai-platform_knowledge_base_documents"
$VolumeInfo = docker volume inspect $DocumentsVolume 2>&1

if ($LASTEXITCODE -eq 0) {
    $VolumePath = ($VolumeInfo | ConvertFrom-Json)[0].Mountpoint
    
    Write-Host "  文档volume: 存在" -ForegroundColor Green
    Write-Host "  路径: $VolumePath" -ForegroundColor Gray
    
    $TempContainer = "docs_check_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    docker run --rm -d --name $TempContainer -v "${DocumentsVolume}:/data" alpine sleep 10 | Out-Null
    
    try {
        $FileCount = docker exec $TempContainer find /data -type f | Measure-Object -Line
        $DirCount = docker exec $TempContainer find /data -type d | Measure-Object -Line
        
        if ($FileCount.Lines -gt 0) {
            Write-Host "  文件数量: $($FileCount.Lines)" -ForegroundColor Gray
            Write-Host "  目录数量: $($DirCount.Lines)" -ForegroundColor Gray
            Write-Host "  [OK] 文档有数据" -ForegroundColor Green
        } else {
            Write-Host "  [警告] 文档目录为空" -ForegroundColor Yellow
        }
    } finally {
        docker rm -f $TempContainer 2>&1 | Out-Null
    }
} else {
    Write-Host "  文档volume: 不存在" -ForegroundColor Yellow
}
Write-Host ""

# 总结
Write-Host "========================================" -ForegroundColor Green
Write-Host "  检查完成" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "To sync data to server, run:" -ForegroundColor Cyan
Write-Host "  .\scripts\sync_metadata_knowledge_to_server.ps1 -ServerHost user@server" -ForegroundColor Yellow
Write-Host ""


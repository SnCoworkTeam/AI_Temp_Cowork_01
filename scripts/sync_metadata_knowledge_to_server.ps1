# 元数据和知识库数据同步脚本 (PowerShell版本)
# 将本地Docker中的元数据和知识库数据同步到服务器

param(
    [string]$ServerHost = "",
    [string]$ServerPath = "/opt/enterprise-ai-platform/backups",
    [switch]$NoUpload = $false,
    [string]$OutputDir = "backups\sync"
)

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  元数据和知识库数据同步" -ForegroundColor Green
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
Write-Host "[OK] Docker运行正常" -ForegroundColor Green
Write-Host ""

# 创建输出目录
$OutputDirPath = Join-Path $PSScriptRoot ".." $OutputDir
$OutputDirPath = [System.IO.Path]::GetFullPath($OutputDirPath)
New-Item -ItemType Directory -Force -Path $OutputDirPath | Out-Null

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Date = Get-Date -Format "yyyyMMdd"

Write-Host "[导出] 开始导出数据..." -ForegroundColor Cyan

# 1. 导出PostgreSQL数据
Write-Host "[1/3] 导出PostgreSQL数据..." -ForegroundColor Yellow
$PostgresFile = Join-Path $OutputDirPath "postgres_$Timestamp.sql.gz"

$DbHost = $env:DB_HOST
if (-not $DbHost) { $DbHost = "localhost" }
$DbPort = $env:DB_PORT
if (-not $DbPort) { $DbPort = "5432" }
$DbName = $env:DB_NAME
if (-not $DbName) { $DbName = "ai_platform" }
$DbUser = $env:DB_USER
if (-not $DbUser) { $DbUser = "ai_user" }
$DbPassword = $env:DB_PASSWORD
if (-not $DbPassword) { $DbPassword = "ai_password" }

# 检查PostgreSQL容器
$PostgresContainer = docker-compose -f docker-compose.yml ps -q postgres 2>&1
if ($PostgresContainer -and $PostgresContainer -notmatch "Error") {
    Write-Host "  使用PostgreSQL容器: $($PostgresContainer.Substring(0, 12))" -ForegroundColor Gray
    
    # 使用docker exec导出
    $env:PGPASSWORD = $DbPassword
    docker exec $PostgresContainer.PostgresContainer pg_dump -U $DbUser -d $DbName --clean --if-exists | gzip > $PostgresFile
    
    if ($LASTEXITCODE -eq 0) {
        $PostgresSize = (Get-Item $PostgresFile).Length / 1MB
        Write-Host "  [OK] PostgreSQL导出完成: $PostgresFile ($([math]::Round($PostgresSize, 2)) MB)" -ForegroundColor Green
        $PostgresExported = $true
    } else {
        Write-Host "  [警告] PostgreSQL导出失败" -ForegroundColor Yellow
        $PostgresExported = $false
    }
} else {
    Write-Host "  [警告] PostgreSQL容器未运行，跳过导出" -ForegroundColor Yellow
    $PostgresExported = $false
}

# 2. 导出Chroma向量数据库
Write-Host "[2/3] 导出Chroma向量数据库..." -ForegroundColor Yellow
$ChromaFile = Join-Path $OutputDirPath "chroma_$Timestamp.tar.gz"

$ChromaVolume = "enterprise-ai-platform_knowledge_base_chroma"
$VolumeInfo = docker volume inspect $ChromaVolume 2>&1

if ($LASTEXITCODE -eq 0) {
    $VolumePath = ($VolumeInfo | ConvertFrom-Json)[0].Mountpoint
    Write-Host "  Chroma数据目录: $VolumePath" -ForegroundColor Gray
    
    # 创建临时容器来打包数据
    $TempContainer = "chroma_backup_$Timestamp"
    
    docker run --rm -d --name $TempContainer -v "${ChromaVolume}:/data" alpine sleep 3600 | Out-Null
    
    try {
        # 在容器内打包
        docker exec $TempContainer tar -czf - -C /data . | Set-Content -Path $ChromaFile -Encoding Byte
        
        if ($LASTEXITCODE -eq 0) {
            $ChromaSize = (Get-Item $ChromaFile).Length / 1MB
            Write-Host "  [OK] Chroma导出完成: $ChromaFile ($([math]::Round($ChromaSize, 2)) MB)" -ForegroundColor Green
            $ChromaExported = $true
        } else {
            Write-Host "  [警告] Chroma导出失败" -ForegroundColor Yellow
            $ChromaExported = $false
        }
    } finally {
        docker rm -f $TempContainer 2>&1 | Out-Null
    }
} else {
    Write-Host "  [警告] Chroma volume未找到，跳过导出" -ForegroundColor Yellow
    $ChromaExported = $false
}

# 3. 导出文档文件
Write-Host "[3/3] 导出文档文件..." -ForegroundColor Yellow
$DocumentsFile = Join-Path $OutputDirPath "documents_$Timestamp.tar.gz"

$DocumentsVolume = "enterprise-ai-platform_knowledge_base_documents"
$VolumeInfo = docker volume inspect $DocumentsVolume 2>&1

if ($LASTEXITCODE -eq 0) {
    $VolumePath = ($VolumeInfo | ConvertFrom-Json)[0].Mountpoint
    Write-Host "  文档目录: $VolumePath" -ForegroundColor Gray
    
    $TempContainer = "docs_backup_$Timestamp"
    docker run --rm -d --name $TempContainer -v "${DocumentsVolume}:/data" alpine sleep 3600 | Out-Null
    
    try {
        docker exec $TempContainer tar -czf - -C /data . | Set-Content -Path $DocumentsFile -Encoding Byte
        
        if ($LASTEXITCODE -eq 0) {
            $DocsSize = (Get-Item $DocumentsFile).Length / 1MB
            Write-Host "  [OK] 文档导出完成: $DocumentsFile ($([math]::Round($DocsSize, 2)) MB)" -ForegroundColor Green
            $DocsExported = $true
        } else {
            Write-Host "  [警告] 文档导出失败" -ForegroundColor Yellow
            $DocsExported = $false
        }
    } finally {
        docker rm -f $TempContainer 2>&1 | Out-Null
    }
} else {
    Write-Host "  [警告] 文档volume未找到，跳过导出" -ForegroundColor Yellow
    $DocsExported = $false
}

# 检查是否有数据导出
if (-not $PostgresExported -and -not $ChromaExported -and -not $DocsExported) {
    Write-Host "[错误] 没有成功导出任何数据" -ForegroundColor Red
    exit 1
}

# 创建元数据文件
Write-Host "[打包] 创建同步包..." -ForegroundColor Cyan
$Metadata = @{
    timestamp = $Timestamp
    date = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
    exports = @{
        postgres = if ($PostgresExported) { "postgres_$Timestamp.sql.gz" } else { $null }
        chroma = if ($ChromaExported) { "chroma_$Timestamp.tar.gz" } else { $null }
        documents = if ($DocsExported) { "documents_$Timestamp.tar.gz" } else { $null }
    }
    version = "1.0.0"
}

$MetadataFile = Join-Path $OutputDirPath "metadata_$Timestamp.json"
$Metadata | ConvertTo-Json -Depth 10 | Set-Content -Path $MetadataFile

# 创建同步包
$PackageName = "metadata_knowledge_sync_$Timestamp.tar.gz"
$PackagePath = Join-Path $OutputDirPath $PackageName

# 使用tar打包（Windows 10+支持）
$FilesToPackage = @()
if ($PostgresExported) { $FilesToPackage += $PostgresFile }
if ($ChromaExported) { $FilesToPackage += $ChromaFile }
if ($DocsExported) { $FilesToPackage += $DocumentsFile }
$FilesToPackage += $MetadataFile

Write-Host "  打包文件..." -ForegroundColor Gray
$FilesToPackage | ForEach-Object {
    Write-Host "    - $(Split-Path $_ -Leaf)" -ForegroundColor Gray
}

# 使用tar命令打包
$TempDir = Join-Path $env:TEMP "sync_package_$Timestamp"
New-Item -ItemType Directory -Force -Path $TempDir | Out-Null

try {
    Copy-Item $FilesToPackage -Destination $TempDir
    Push-Location $TempDir
    tar -czf $PackagePath *
    Pop-Location
} finally {
    Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue
}

if (Test-Path $PackagePath) {
    $PackageSize = (Get-Item $PackagePath).Length / 1MB
    Write-Host "  [OK] 同步包创建完成: $PackagePath ($([math]::Round($PackageSize, 2)) MB)" -ForegroundColor Green
} else {
    Write-Host "  [错误] 同步包创建失败" -ForegroundColor Red
    exit 1
}

# 上传到服务器
if (-not $NoUpload) {
    if ([string]::IsNullOrEmpty($ServerHost)) {
        Write-Host ""
        Write-Host "[跳过] 未指定服务器地址，跳过上传" -ForegroundColor Yellow
        Write-Host "同步包已保存到: $PackagePath" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "[上传] 上传到服务器..." -ForegroundColor Cyan
        Write-Host "  目标: $ServerHost`:$ServerPath" -ForegroundColor Yellow
        
        $RemotePath = "$ServerHost`:$ServerPath/$PackageName"
        
        try {
            scp $PackagePath $RemotePath
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  [OK] 上传成功: $RemotePath" -ForegroundColor Green
            } else {
                Write-Host "  [错误] 上传失败" -ForegroundColor Red
                exit 1
            }
        } catch {
            Write-Host "  [错误] 上传失败: $_" -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host ""
    Write-Host "[跳过] 已设置 --NoUpload，跳过上传" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  数据同步完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "同步包: $PackagePath" -ForegroundColor Cyan
if (-not [string]::IsNullOrEmpty($ServerHost) -and -not $NoUpload) {
    Write-Host "服务器路径: $ServerHost`:$ServerPath/$PackageName" -ForegroundColor Cyan
}
Write-Host ""



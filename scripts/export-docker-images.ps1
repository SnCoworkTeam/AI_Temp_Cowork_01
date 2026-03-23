# 将本机已构建/拉取的 Docker 镜像导出为 tar，便于在内网服务器加载
# 用法: .\scripts\export-docker-images.ps1 [导出目录]
# 仅导出 zhgj 19 个服务: $env:ZHGJ_19="1"; .\scripts\export-docker-images.ps1
# 默认导出到: docker-images-export\

$ErrorActionPreference = "Stop"
$root = if (Test-Path "docker-compose.yml") { $PWD } else { Split-Path -Parent (Split-Path -Parent $PSScriptRoot) }
Set-Location $root

$exportDir = $args[0]
if (-not $exportDir) { $exportDir = "docker-images-export" }
$exportDir = $root | Join-Path -ChildPath $exportDir

if (-not (Test-Path ".env")) {
    Write-Host "WARN: .env not found. Copy from .env.example or .env.backup if needed for config resolution." -ForegroundColor Yellow
}

$projName = (Get-Location).Path | Split-Path -Leaf
$imageList = @()

if ($env:ZHGJ_19 -eq "1") {
    # 仅导出 zhgj 19 个服务的镜像（不含 redis-commander, deployment-agent, sap-metadata-agent, project-management, vector-coordinator-service）
    Write-Host "Exporting only zhgj 19 services (ZHGJ_19=1)..." -ForegroundColor Cyan
    $baseImages = @("postgres:15", "redis:7-alpine", "qdrant/qdrant:latest", "neo4j:5-community")
    $appServices = @("registry-service", "api-gateway", "config-center", "mcp-gateway", "workflow-engine", "web-ui", "auth-service", "knowledge-base", "metadata-service", "chat-service", "dag-orchestrator", "agent-service", "agent-orchestrator", "agent-registry", "memory-service")
    $imageList = $baseImages + ($appServices | ForEach-Object { "${projName}-$_" + ":latest" })
} else {
    Write-Host "Resolving images from docker-compose.yml (project: $projName)..." -ForegroundColor Cyan
    $images = docker compose config --images 2>$null
    if (-not $images) {
        Write-Host "ERROR: 'docker compose config --images' failed. Ensure Docker and docker-compose are available." -ForegroundColor Red
        exit 1
    }
    $imageList = $images -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ -match ":" }
}

if ($imageList.Count -eq 0) {
    Write-Host "ERROR: No images to export. Check docker-compose.yml and .env." -ForegroundColor Red
    exit 1
}

New-Item -ItemType Directory -Force -Path $exportDir | Out-Null

$saved = 0
foreach ($img in $imageList) {
    $safeName = $img -replace "[/:]", "-"
    $tarPath = Join-Path $exportDir "$safeName.tar"
    if ((Test-Path $tarPath) -and $env:EXPORT_FORCE -ne "1") {
        Write-Host "Skip (exists): $img" -ForegroundColor Gray
        $saved++
        continue
    }
    Write-Host "Saving: $img -> $safeName.tar" -ForegroundColor Cyan
    docker save -o $tarPath $img
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to save $img" -ForegroundColor Red
        exit 1
    }
    $saved++
}

# 复制部署所需文件到导出目录，便于整包拷到服务器
@("docker-compose.yml", ".env") | ForEach-Object {
    $f = Join-Path $root $_
    if (Test-Path $f) {
        Copy-Item $f -Destination (Join-Path $exportDir $_) -Force
        Write-Host "Copied: $_" -ForegroundColor Green
    }
}

# 仅 19 服务时：确保服务器上 compose 使用的项目名与镜像名一致（便于直接运行）
if ($env:ZHGJ_19 -eq "1") {
    $envDest = Join-Path $exportDir ".env"
    $envContent = Get-Content $envDest -Raw -ErrorAction SilentlyContinue
    if ($envContent -notmatch "COMPOSE_PROJECT_NAME") {
        Add-Content -Path $envDest -Value "`n# 与导出镜像名一致，服务器上直接 docker compose up 即可`nCOMPOSE_PROJECT_NAME=enterprise-ai-platform"
        Write-Host "Added COMPOSE_PROJECT_NAME to .env for server" -ForegroundColor Green
    }
    $readme = @"
========================================
zhgj 19 服务 - 服务器直接运行说明
========================================
请将本文件夹内所有文件上传到服务器目录：/opt/enterprise-ai-platform/
（若上传整个 docker-images-export 文件夹，则部署目录为 /opt/enterprise-ai-platform/docker-images-export/）

在服务器上执行（部署目录统一为 /opt/enterprise-ai-platform 或其子目录）：

1. 进入部署目录：
   cd /opt/enterprise-ai-platform

2. 加载所有镜像：
   for f in *.tar; do [ -f "\$f" ] && docker load -i "\$f"; done

3. 启动 19 个服务（无需重新构建）：
   docker compose up -d --no-build

4. 查看状态：
   docker compose ps

或使用脚本（在部署目录下）：
   chmod +x load-and-run.sh && ./load-and-run.sh

说明：.env 已设 COMPOSE_PROJECT_NAME=enterprise-ai-platform，与镜像名一致。
      docker-compose.yml 中 5 个可选服务已设 profile，默认只启动 19 个服务。
"@
    Set-Content -Path (Join-Path $exportDir "服务器启动说明.txt") -Value $readme -Encoding UTF8
    Write-Host "Created: 服务器启动说明.txt" -ForegroundColor Green
}

# 可选：复制 database/init-scripts 以便服务器初始化数据库
$initScripts = Join-Path $root "database\init-scripts"
if (Test-Path $initScripts) {
    $destInit = Join-Path $exportDir "database\init-scripts"
    New-Item -ItemType Directory -Force -Path (Split-Path $destInit) | Out-Null
    Copy-Item -Path "$initScripts\*" -Destination $destInit -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Copied: database/init-scripts" -ForegroundColor Green
}

# 复制加载脚本到导出目录，服务器拷过去后可直接执行
$loadPs1 = Join-Path (Split-Path $PSScriptRoot) "scripts\load-and-run.ps1"
$loadSh  = Join-Path (Split-Path $PSScriptRoot) "scripts\load-and-run.sh"
if (Test-Path $loadPs1) { Copy-Item $loadPs1 $exportDir -Force; Write-Host "Copied: load-and-run.ps1" -ForegroundColor Green }
if (Test-Path $loadSh)  { Copy-Item $loadSh  $exportDir -Force; Write-Host "Copied: load-and-run.sh"  -ForegroundColor Green }

Write-Host "`nDone. Exported $saved images to: $exportDir" -ForegroundColor Green
Write-Host "Next: copy entire folder to server (U disk / SCP / shared storage), then on server run:" -ForegroundColor Yellow
Write-Host "  .\load-and-run.ps1   (Windows)  or   ./load-and-run.sh   (Linux)" -ForegroundColor Yellow

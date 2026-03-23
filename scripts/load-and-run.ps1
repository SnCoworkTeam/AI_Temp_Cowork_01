# 在内网服务器上：加载导出的镜像并启动
# 用法: 将 docker-images-export 整包拷到服务器后，在该目录执行:
#   .\load-and-run.ps1
# 或指定导出目录: .\load-and-run.ps1 -ExportDir "E:\docker-images-export"

param([string]$ExportDir = "docker-images-export")

$ErrorActionPreference = "Stop"
if (-not (Test-Path $ExportDir)) {
    Write-Host "ERROR: Directory not found: $ExportDir" -ForegroundColor Red
    exit 1
}
Set-Location $ExportDir

$tars = Get-ChildItem -Path $ExportDir -Filter "*.tar" -File
if ($tars.Count -eq 0) {
    Write-Host "ERROR: No .tar files in $ExportDir" -ForegroundColor Red
    exit 1
}

Write-Host "Loading $($tars.Count) images..." -ForegroundColor Cyan
foreach ($f in $tars) {
    Write-Host "  Load: $($f.Name)" -ForegroundColor Gray
    docker load -i $f.FullName
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to load $($f.Name)" -ForegroundColor Red
        exit 1
    }
}

if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "WARN: docker-compose.yml not in $ExportDir. Start manually with: docker compose -f <path>/docker-compose.yml up -d" -ForegroundColor Yellow
    exit 0
}

# 若 .env 中未设置，使用 enterprise-ai-platform 以匹配导出的镜像名
if (-not $env:COMPOSE_PROJECT_NAME) { $env:COMPOSE_PROJECT_NAME = "enterprise-ai-platform" }
Write-Host "`nStarting stack (--no-build, use loaded images only)..." -ForegroundColor Cyan
docker compose up -d --no-build
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: docker compose up failed." -ForegroundColor Red
    exit 1
}
Write-Host "Done. Use 'docker compose ps' to check status." -ForegroundColor Green

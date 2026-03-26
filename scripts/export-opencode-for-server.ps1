# 在本地构建 OpenCode 镜像、打包并导出到 opencode-server-export 文件夹，供上传内网服务器
# 用法: 在项目根目录执行 .\scripts\export-opencode-for-server.ps1
# 输出: opencode-server-export/ 下含镜像 .tar 及部署所需全部文件

$ErrorActionPreference = "Stop"
$Root = if (Test-Path "docker-compose.yml") { $PWD } else { Split-Path -Parent (Split-Path -Parent $PSScriptRoot) }
Set-Location $Root

$ExportDir = Join-Path $Root "opencode-server-export"
$ImageName = "enterprise-ai-opencode:latest"
$TarName = "enterprise-ai-opencode.tar"

Write-Host "========== 1/3 构建 OpenCode 镜像 ==========" -ForegroundColor Cyan
docker compose build opencode
if ($LASTEXITCODE -ne 0) {
    Write-Host "构建失败。" -ForegroundColor Red
    exit 1
}

Write-Host "`n========== 2/3 导出镜像为 .tar ==========" -ForegroundColor Cyan
if (-not (Test-Path $ExportDir)) { New-Item -ItemType Directory -Path $ExportDir | Out-Null }
$TarPath = Join-Path $ExportDir $TarName
docker save -o $TarPath $ImageName
if ($LASTEXITCODE -ne 0) {
    Write-Host "导出镜像失败。" -ForegroundColor Red
    exit 1
}
Write-Host "已保存: $TarPath" -ForegroundColor Green

Write-Host "`n========== 3/3 检查导出文件夹 ==========" -ForegroundColor Cyan
$Required = @(
    "docker-compose.opencode.yml",
    ".env.example",
    "服务器启动说明.txt",
    "load-and-run.sh",
    "load-and-run.ps1"
)
foreach ($f in $Required) {
    $p = Join-Path $ExportDir $f
    if (Test-Path $p) { Write-Host "  OK $f" -ForegroundColor Green } else { Write-Host "  缺失 $f" -ForegroundColor Yellow }
}

Write-Host "`n完成。请将整个 opencode-server-export 文件夹上传到内网服务器，按 服务器启动说明.txt 操作。" -ForegroundColor Green

# zhgj 19 服务：导出镜像并 SCP 上传到 DMZ 内网服务器（10.24.20.56）
# 在能访问 10.24.20.56 的本机执行，上传后需在服务器上执行 load-and-run
# 用法: .\scripts\deployment\zhgj-export-and-upload-to-dmz.ps1
# 注意：请勿在脚本或代码中写入密码，SCP 时会提示输入密码

param(
    [string]$Server = "10.24.20.56",
    [string]$User = "lijingwei",
    [string]$RemotePath = "/opt/enterprise-ai-platform",
    [switch]$SkipExport
)

$ErrorActionPreference = "Stop"
$root = if (Test-Path "docker-compose.yml") { $PWD } else { Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) }
Set-Location $root

$exportDir = "docker-images-export"
$exportFullPath = Join-Path $root $exportDir

# Step 1: 导出 19 个服务镜像
if (-not $SkipExport) {
    Write-Host "========== Step 1: 导出 zhgj 19 服务镜像 ==========" -ForegroundColor Cyan
    $env:ZHGJ_19 = "1"
    & (Join-Path $root "scripts\export-docker-images.ps1") $exportDir
    if ($LASTEXITCODE -ne 0) { Write-Host "Export failed." -ForegroundColor Red; exit 1 }
} else {
    if (-not (Test-Path $exportFullPath)) {
        Write-Host "ERROR: $exportDir not found. Run without -SkipExport first." -ForegroundColor Red
        exit 1
    }
    Write-Host "Skip export, using existing $exportDir" -ForegroundColor Yellow
}

# Step 2: SCP 上传到服务器（会提示输入密码，请勿在脚本中写密码）
Write-Host "`n========== Step 2: SCP 上传到 ${User}@${Server}:${RemotePath} ==========" -ForegroundColor Cyan
Write-Host "请在提示时输入服务器密码。" -ForegroundColor Yellow
$dest = "${User}@${Server}:${RemotePath}"
# 确保远程目录存在
ssh -o StrictHostKeyChecking=no "${User}@${Server}" "mkdir -p $RemotePath"
if ($LASTEXITCODE -ne 0) {
    Write-Host "SSH 连接失败，请确认: 1) 本机可访问 $Server  2) 用户名 $User  3) 密码正确" -ForegroundColor Red
    exit 1
}
scp -o StrictHostKeyChecking=no -r "$exportFullPath" "${User}@${Server}:$RemotePath/"
if ($LASTEXITCODE -ne 0) {
    Write-Host "SCP 上传失败。" -ForegroundColor Red
    exit 1
}
$serverExportPath = "$RemotePath/$exportDir"
Write-Host "`nUpload done. On server run:" -ForegroundColor Green
Write-Host "  ssh ${User}@${Server}" -ForegroundColor White
Write-Host "  cd $serverExportPath" -ForegroundColor White
Write-Host "  docker load -i *.tar   # or run load-and-run.sh" -ForegroundColor White
Write-Host "  docker compose up -d --no-build" -ForegroundColor White

# zhgj 分支：只构建并启动 zhgj 下的服务（不含 joyagent-adapter、sap-mcp-server）
# 用法: .\scripts\zhgj-build-and-up.ps1
# 先构建除 joyagent 外的服务，再 docker compose up（默认不包含 profile joyagent/sap）

$ErrorActionPreference = "Stop"
$root = if (Test-Path "docker-compose.yml") { $PWD } else { Split-Path -Parent (Split-Path -Parent $PSScriptRoot) }
Set-Location $root

Write-Host "========== zhgj 分支：构建（跳过 joyagent-adapter）==========" -ForegroundColor Cyan
$env:SKIP_SERVICES = "joyagent-adapter"
& "$PSScriptRoot\build-services-one-by-one.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "构建未全部成功，可忽略失败服务后继续启动。" -ForegroundColor Yellow
    $cont = Read-Host "是否仍要启动已构建的服务？(y/N)"
    if ($cont -ne "y" -and $cont -ne "Y") { exit 1 }
}

Write-Host "`n========== 启动 zhgj 服务（不含 joyagent、sap-mcp）==========" -ForegroundColor Cyan
docker compose up -d --no-build
if ($LASTEXITCODE -ne 0) {
    Write-Host "启动失败。" -ForegroundColor Red
    exit 1
}
Write-Host "`nDone. 查看状态: docker compose ps" -ForegroundColor Green

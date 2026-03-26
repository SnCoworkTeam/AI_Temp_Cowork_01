# OpenCode 本地 Web：本机构建并把需上传的文件放到一个文件夹
# 在仓库根目录执行: .\opencode-server-export\build-and-pack-local-web.ps1
# 完成后所有要上传的文件在 opencode-upload 目录下

$ErrorActionPreference = "Stop"
$RepoRoot = $PSScriptRoot | Split-Path -Parent
$ExportDir = Join-Path $RepoRoot "opencode-server-export"
$UploadDir = Join-Path $RepoRoot "opencode-upload"

Set-Location $RepoRoot

Write-Host "=== 1/3 构建镜像 ===" -ForegroundColor Cyan
docker build -f opencode-src/Dockerfile.local-web -t enterprise-ai-opencode-local-web:latest opencode-src
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n=== 2/3 导出镜像为 tar ===" -ForegroundColor Cyan
docker save -o (Join-Path $ExportDir "enterprise-ai-opencode-local-web.tar") enterprise-ai-opencode-local-web:latest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n=== 3/3 整理上传包到 opencode-upload ===" -ForegroundColor Cyan
if (Test-Path $UploadDir) { Remove-Item -Recurse -Force $UploadDir }
New-Item -ItemType Directory -Path $UploadDir -Force | Out-Null

$files = @(
    @{ src = "enterprise-ai-opencode-local-web.tar"; from = $ExportDir }
    @{ src = "docker-compose.opencode.local-web.yml"; from = $ExportDir }
    @{ src = ".env.example"; from = $ExportDir }
)
foreach ($f in $files) {
    $fromPath = Join-Path $f.from $f.src
    if (Test-Path $fromPath) {
        Copy-Item $fromPath (Join-Path $UploadDir $f.src)
        Write-Host "  已复制: $($f.src)"
    } else {
        Write-Host "  跳过(不存在): $($f.src)" -ForegroundColor Yellow
    }
}
if (Test-Path (Join-Path $ExportDir ".env")) {
    Copy-Item (Join-Path $ExportDir ".env") (Join-Path $UploadDir ".env")
    Write-Host "  已复制: .env"
}

Write-Host "`n完成. 上传目录: $UploadDir" -ForegroundColor Green
Write-Host "单步上传命令见: opencode-server-export\单步上传命令.md"

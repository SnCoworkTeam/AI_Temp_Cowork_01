# ============================================================
# 企业AI平台 - 快速同步脚本（简化版）
# ============================================================
# 这是 complete-sync.ps1 的简化包装脚本
# 使用方法: .\sync-all.ps1
# ============================================================

param(
    [switch]$ImagesOnly = $false,      # 仅同步镜像
    [switch]$NoMigration = $false,      # 跳过迁移
    [switch]$DryRun = $false           # 干运行
)

$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "企业AI平台 - 快速同步" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 构建参数
$params = @()
if ($ImagesOnly) { $params += "-BuildImagesOnly" }
if ($NoMigration) { $params += "-SkipMigration" }
if ($DryRun) { $params += "-DryRun" }
$params += "-SkipDataSync"  # 默认跳过数据同步

# 调用完整同步脚本
$scriptPath = Join-Path $PSScriptRoot "scripts\deployment\complete-sync.ps1"
if (-not (Test-Path $scriptPath)) {
    Write-Host "❌ 找不到同步脚本: $scriptPath" -ForegroundColor Red
    exit 1
}

Write-Host "执行完整同步脚本..." -ForegroundColor Yellow
Write-Host "参数: $($params -join ' ')" -ForegroundColor Gray
Write-Host ""

& $scriptPath @params

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ 同步完成！" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ 同步失败，退出码: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}







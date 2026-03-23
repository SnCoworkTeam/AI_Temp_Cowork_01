# 检查.env文件配置脚本
# 用于验证.env文件是否包含必要的配置项

$envFile = ".env"
$requiredConfigs = @(
    "DB_HOST",
    "DB_PORT", 
    "DB_USER",
    "DB_PASSWORD",
    "DB_NAME",
    "METADATA_SERVICE_PORT"
)

Write-Host "检查 .env 文件配置..." -ForegroundColor Cyan

if (-not (Test-Path $envFile)) {
    Write-Host "❌ .env 文件不存在！" -ForegroundColor Red
    Write-Host "请从 env.example 复制创建: cp env.example .env" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ .env 文件存在" -ForegroundColor Green

# 读取.env文件
$envContent = Get-Content $envFile -Raw
$missingConfigs = @()

foreach ($config in $requiredConfigs) {
    if ($envContent -notmatch "$config\s*=") {
        $missingConfigs += $config
    }
}

if ($missingConfigs.Count -eq 0) {
    Write-Host "✅ 所有必需配置项都已存在" -ForegroundColor Green
} else {
    Write-Host "⚠️  缺少以下配置项:" -ForegroundColor Yellow
    foreach ($config in $missingConfigs) {
        Write-Host "   - $config" -ForegroundColor Yellow
    }
    Write-Host "`n请在 .env 文件中添加这些配置项" -ForegroundColor Yellow
}

# 检查PostgreSQL配置
Write-Host "`n检查PostgreSQL配置..." -ForegroundColor Cyan
if ($envContent -match "DB_NAME\s*=\s*enterprise_ai_platform") {
    Write-Host "✅ DB_NAME 配置正确" -ForegroundColor Green
} else {
    Write-Host "⚠️  DB_NAME 建议设置为: enterprise_ai_platform" -ForegroundColor Yellow
}

# 检查metadata-service配置
Write-Host "`n检查Metadata Service配置..." -ForegroundColor Cyan
if ($envContent -match "METADATA_SERVICE_PORT\s*=\s*8005") {
    Write-Host "✅ METADATA_SERVICE_PORT 配置正确" -ForegroundColor Green
} else {
    Write-Host "⚠️  建议添加: METADATA_SERVICE_PORT=8005" -ForegroundColor Yellow
}

Write-Host "`n检查完成！" -ForegroundColor Cyan


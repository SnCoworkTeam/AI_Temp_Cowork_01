# SAP元数据语义分析构建脚本 (PowerShell)
# 用于快速启动语义分析构建

param(
    [int]$BatchSize = 50,
    [int]$AssetsOffset = 0,
    [int]$EntitiesOffset = 0,
    [switch]$Resume,
    [switch]$NoResume
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SAP元数据语义分析构建" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python环境
Write-Host "检查Python环境..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python未安装或不在PATH中" -ForegroundColor Red
    exit 1
}
Write-Host "✅ $pythonVersion" -ForegroundColor Green
Write-Host ""

# 检查服务连接
Write-Host "检查服务连接..." -ForegroundColor Yellow

# 检查元数据服务
$metadataUrl = $env:METADATA_SERVICE_URL
if (-not $metadataUrl) {
    $metadataUrl = "http://localhost:8005"
}
Write-Host "  元数据服务: $metadataUrl" -ForegroundColor Gray

try {
    $response = Invoke-WebRequest -Uri "$metadataUrl/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  ✅ 元数据服务连接正常" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  元数据服务连接失败: $_" -ForegroundColor Yellow
    Write-Host "     请确保元数据服务正在运行" -ForegroundColor Yellow
}

# 检查知识库服务
$kbUrl = $env:KNOWLEDGE_BASE_URL
if (-not $kbUrl) {
    $kbUrl = "http://localhost:8004"
}
Write-Host "  知识库服务: $kbUrl" -ForegroundColor Gray

try {
    $response = Invoke-WebRequest -Uri "$kbUrl/api/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  ✅ 知识库服务连接正常" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  知识库服务连接失败: $_" -ForegroundColor Yellow
    Write-Host "     请确保知识库服务正在运行" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "是否继续? (Y/N)" -ForegroundColor Yellow
    $continue = Read-Host
    if ($continue -ne "Y" -and $continue -ne "y") {
        exit 1
    }
}

Write-Host ""

# 构建参数
$args = @()
if ($BatchSize) {
    $args += "--batch-size", $BatchSize
}
if ($AssetsOffset) {
    $args += "--assets-offset", $AssetsOffset
}
if ($EntitiesOffset) {
    $args += "--entities-offset", $EntitiesOffset
}
if ($Resume) {
    $args += "--resume"
}
if ($NoResume) {
    $args += "--no-resume"
}

# 显示构建参数
Write-Host "构建参数:" -ForegroundColor Yellow
Write-Host "  批次大小: $BatchSize" -ForegroundColor Gray
Write-Host "  数据资产偏移: $AssetsOffset" -ForegroundColor Gray
Write-Host "  业务实体偏移: $EntitiesOffset" -ForegroundColor Gray
if ($Resume) {
    Write-Host "  从进度文件恢复: 是" -ForegroundColor Gray
}
Write-Host ""

# 执行构建
Write-Host "开始构建..." -ForegroundColor Cyan
Write-Host ""

python build_semantic_analysis.py $args

$exitCode = $LASTEXITCODE

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "✅ 构建完成" -ForegroundColor Green
} else {
    Write-Host "❌ 构建失败 (退出码: $exitCode)" -ForegroundColor Red
    Write-Host ""
    Write-Host "提示:" -ForegroundColor Yellow
    Write-Host "  - 检查服务是否正常运行" -ForegroundColor Gray
    Write-Host "  - 查看错误日志" -ForegroundColor Gray
    Write-Host "  - 使用 --resume 参数继续构建" -ForegroundColor Gray
}

exit $exitCode


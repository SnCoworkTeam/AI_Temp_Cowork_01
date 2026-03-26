# 测试启动workflow-engine
$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "测试启动 Workflow Engine" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 激活虚拟环境
Write-Host "[1/4] 激活虚拟环境..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 虚拟环境激活失败" -ForegroundColor Red
    exit 1
}
Write-Host "✅ 虚拟环境已激活" -ForegroundColor Green
Write-Host ""

# 设置PYTHONPATH
Write-Host "[2/4] 设置PYTHONPATH..." -ForegroundColor Yellow
$projectRoot = Split-Path -Parent $PSScriptRoot
$sharedLibsPath = Join-Path $projectRoot "shared_libs"
$env:PYTHONPATH = "$sharedLibsPath;$env:PYTHONPATH"
Write-Host "PYTHONPATH: $env:PYTHONPATH" -ForegroundColor Gray
Write-Host ""

# 测试导入
Write-Host "[3/4] 测试模块导入..." -ForegroundColor Yellow
try {
    python -c "import sys; sys.path.insert(0, r'$sharedLibsPath'); from shared_libs.common.logger import setup_logger; print('✅ shared_libs导入成功')"
    if ($LASTEXITCODE -ne 0) { throw "导入失败" }
} catch {
    Write-Host "❌ shared_libs导入失败: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 设置环境变量
Write-Host "[4/4] 设置环境变量..." -ForegroundColor Yellow
$env:REDIS_HOST = "localhost"
$env:PORT = "8002"
$env:HOST = "127.0.0.1"
Write-Host "✅ 环境变量已设置" -ForegroundColor Green
Write-Host ""

# 启动服务
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "启动服务..." -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

python -m uvicorn src.main:app --host $env:HOST --port $env:PORT --reload


# 在venv虚拟环境中运行workflow-engine进行调试

$ErrorActionPreference = "Continue"

# 激活虚拟环境
Write-Host "激活虚拟环境..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"

# 设置PYTHONPATH，确保能找到shared_libs
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
# 将项目根目录添加到PYTHONPATH，这样Python可以找到shared_libs包
$env:PYTHONPATH = "$projectRoot;$env:PYTHONPATH"

Write-Host "PYTHONPATH: $env:PYTHONPATH" -ForegroundColor Gray
Write-Host ""

# 设置环境变量（如果需要）
if (-not $env:OPENAI_API_KEY) {
    Write-Host "提示: 未设置OPENAI_API_KEY环境变量" -ForegroundColor Yellow
}

if (-not $env:REDIS_HOST) {
    $env:REDIS_HOST = "localhost"
    Write-Host "设置REDIS_HOST=localhost" -ForegroundColor Gray
}

if (-not $env:PORT) {
    $env:PORT = "8002"
    Write-Host "设置PORT=8002" -ForegroundColor Gray
}

if (-not $env:HOST) {
    $env:HOST = "0.0.0.0"
    Write-Host "设置HOST=0.0.0.0" -ForegroundColor Gray
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "启动 Workflow Engine (调试模式)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 保持在workflow-engine目录，使用src.main作为模块路径
Write-Host "工作目录: $(Get-Location)" -ForegroundColor Gray
Write-Host ""

# 使用uvicorn运行（从workflow-engine目录运行，使用src.main作为模块）
python -m uvicorn src.main:app --host $env:HOST --port $env:PORT --reload


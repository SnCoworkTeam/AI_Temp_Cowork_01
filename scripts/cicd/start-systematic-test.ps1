# 系统性服务测试器启动脚本
# 用于启动逐个服务的自动化测试闭环

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("layer", "service", "all")]
    [string]$Mode = "layer",

    [Parameter(Mandatory=$false)]
    [switch]$Resume,

    [Parameter(Mandatory=$false)]
    [switch]$Reset
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "系统性服务测试器" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "❌ 未找到 Python，请确保已安装 Python 3.11+" -ForegroundColor Red
    exit 1
}

$pythonVersion = & python --version 2>&1
Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green

# 检查 GitHub CLI
$ghCmd = Get-Command gh -ErrorAction SilentlyContinue
if (-not $ghCmd) {
    Write-Host "❌ 未找到 GitHub CLI (gh)，请先安装" -ForegroundColor Red
    Write-Host "   安装方法: winget install --id GitHub.cli" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ GitHub CLI: 已安装" -ForegroundColor Green

# 检查 Git
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    Write-Host "❌ 未找到 Git，请先安装" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Git: 已安装" -ForegroundColor Green
Write-Host ""

# 进度文件路径
$progressFile = Join-Path $env:TEMP "service-test-logs\test_progress.json"

# 重置进度
if ($Reset) {
    if (Test-Path $progressFile) {
        Write-Host "🔄 重置测试进度..." -ForegroundColor Yellow
        Remove-Item $progressFile -Force
        Write-Host "✅ 进度已重置" -ForegroundColor Green
        Write-Host ""
    }
}

# 显示当前进度
if ($Resume -and (Test-Path $progressFile)) {
    Write-Host "📊 当前测试进度:" -ForegroundColor Cyan
    $progress = Get-Content $progressFile | ConvertFrom-Json

    Write-Host "   当前层级: $($progress.current_layer)" -ForegroundColor Gray
    Write-Host "   当前服务: $($progress.current_service)" -ForegroundColor Gray
    Write-Host "   已完成: $($progress.completed_services.Count) 个服务" -ForegroundColor Green
    Write-Host "   已失败: $($progress.failed_services.Count) 个服务" -ForegroundColor Red

    if ($progress.completed_services.Count -gt 0) {
        Write-Host "   ✅ 通过的服务:" -ForegroundColor Green
        foreach ($service in $progress.completed_services) {
            Write-Host "      - $service" -ForegroundColor Gray
        }
    }

    if ($progress.failed_services.Count -gt 0) {
        Write-Host "   ❌ 失败的服务:" -ForegroundColor Red
        foreach ($service in $progress.failed_services) {
            Write-Host "      - $service" -ForegroundColor Gray
        }
    }

    Write-Host ""
}

# 显示测试模式说明
Write-Host "测试模式说明:" -ForegroundColor Cyan
switch ($Mode) {
    "layer" {
        Write-Host "  📊 按层测试 (推荐)" -ForegroundColor Green
        Write-Host "     - Layer 1: 基础设施服务 (postgres, redis, registry, config)" -ForegroundColor Gray
        Write-Host "     - Layer 2: 认证与网关 (auth, api-gateway)" -ForegroundColor Gray
        Write-Host "     - Layer 3: 核心业务服务 (metadata, knowledge-base, workflow, chat, mcp)" -ForegroundColor Gray
        Write-Host "     - Layer 4: 智能编排服务 (agent, orchestrator, dag, memory)" -ForegroundColor Gray
        Write-Host "     - Layer 5: 扩展与适配 (adapters, coordinators)" -ForegroundColor Gray
        Write-Host "     - Layer 6: 前端服务 (web-ui)" -ForegroundColor Gray
    }
    "service" {
        Write-Host "  🔄 逐个服务测试" -ForegroundColor Yellow
        Write-Host "     - 按照服务列表顺序，逐个测试" -ForegroundColor Gray
        Write-Host "     - 每个服务最多重试 3 次" -ForegroundColor Gray
    }
    "all" {
        Write-Host "  🚀 全部服务一起测试" -ForegroundColor Cyan
        Write-Host "     - 所有服务同时测试" -ForegroundColor Gray
        Write-Host "     - 适合快速验证" -ForegroundColor Gray
    }
}

Write-Host ""

# 确认启动
Write-Host "准备启动测试..." -ForegroundColor Yellow
Write-Host "按 Ctrl+C 可随时中断测试" -ForegroundColor Gray
Write-Host ""

$confirm = Read-Host "确认启动？(y/n)"
if ($confirm -ne "y") {
    Write-Host "已取消" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "开始测试" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 启动测试器
$scriptPath = Join-Path $PSScriptRoot "systematic-service-tester.py"

try {
    & python $scriptPath --mode $Mode

    $exitCode = $LASTEXITCODE

    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    if ($exitCode -eq 0) {
        Write-Host "✅ 测试完成" -ForegroundColor Green
    } else {
        Write-Host "⚠️ 测试结束 (退出码: $exitCode)" -ForegroundColor Yellow
    }
    Write-Host "==========================================" -ForegroundColor Cyan

    # 显示最终报告
    if (Test-Path $progressFile) {
        Write-Host ""
        Write-Host "📊 最终报告:" -ForegroundColor Cyan
        $finalProgress = Get-Content $progressFile | ConvertFrom-Json

        $totalServices = $finalProgress.completed_services.Count + $finalProgress.failed_services.Count
        Write-Host "   总服务数: $totalServices" -ForegroundColor Gray
        Write-Host "   ✅ 通过: $($finalProgress.completed_services.Count)" -ForegroundColor Green
        Write-Host "   ❌ 失败: $($finalProgress.failed_services.Count)" -ForegroundColor Red

        Write-Host ""
        Write-Host "查看详细日志:" -ForegroundColor Cyan
        Write-Host "   $env:TEMP\service-test-logs\" -ForegroundColor Gray
        Write-Host ""
        Write-Host "查看进度文件:" -ForegroundColor Cyan
        Write-Host "   $progressFile" -ForegroundColor Gray
    }

} catch {
    Write-Host ""
    Write-Host "❌ 测试异常: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "提示: 使用 -Resume 参数可以恢复上次的测试进度" -ForegroundColor Gray
Write-Host "提示: 使用 -Reset 参数可以重置测试进度" -ForegroundColor Gray
Write-Host ""

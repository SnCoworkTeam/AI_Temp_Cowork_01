# 测试Cursor监控脚本
# 快速验证脚本是否正常工作

$ErrorActionPreference = "Continue"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptRoot)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "测试Cursor监控脚本" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查Python
Write-Host "[1/4] 检查Python..." -ForegroundColor Yellow
$pythonPath = $null
$pythonCommands = @("python", "python3", "py")

foreach ($cmd in $pythonCommands) {
    try {
        $result = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($result) {
            $pythonPath = $result.Source
            $pythonVersion = & $cmd --version 2>&1
            Write-Host "✓ 找到Python: $pythonVersion" -ForegroundColor Green
            Write-Host "  路径: $pythonPath" -ForegroundColor Gray
            break
        }
    } catch {
        continue
    }
}

if (-not $pythonPath) {
    Write-Host "✗ 未找到Python" -ForegroundColor Red
    Write-Host "请先安装Python 3.7+" -ForegroundColor Yellow
    exit 1
}

# 2. 检查监控脚本
Write-Host ""
Write-Host "[2/4] 检查监控脚本..." -ForegroundColor Yellow
$monitorScript = Join-Path $ScriptRoot "cursor-monitor.py"

if (Test-Path $monitorScript) {
    Write-Host "✓ 监控脚本存在: $monitorScript" -ForegroundColor Green
} else {
    Write-Host "✗ 监控脚本不存在: $monitorScript" -ForegroundColor Red
    exit 1
}

# 3. 测试单次运行
Write-Host ""
Write-Host "[3/4] 测试单次运行..." -ForegroundColor Yellow
try {
    $output = & $pythonPath $monitorScript --once 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ 单次运行测试成功" -ForegroundColor Green
    } else {
        Write-Host "⚠ 单次运行返回非零退出码: $LASTEXITCODE" -ForegroundColor Yellow
        Write-Host "输出: $output" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ 单次运行失败: $_" -ForegroundColor Red
}

# 4. 检查输出文件
Write-Host ""
Write-Host "[4/4] 检查输出文件..." -ForegroundColor Yellow

$instructionFile = Join-Path $ProjectRoot "continue-coverage-improvement.txt"
$activityFile = Join-Path $ProjectRoot ".cursor-activity.log"

if (Test-Path $instructionFile) {
    Write-Host "✓ 指令文件已创建: $instructionFile" -ForegroundColor Green
    $content = Get-Content $instructionFile -Raw
    Write-Host "  内容预览: $($content.Substring(0, [Math]::Min(50, $content.Length)))..." -ForegroundColor Gray
} else {
    Write-Host "⚠ 指令文件未创建（可能需要触发超时）" -ForegroundColor Yellow
}

if (Test-Path $activityFile) {
    Write-Host "✓ 活动日志已创建: $activityFile" -ForegroundColor Green
    $logLines = Get-Content $activityFile | Select-Object -Last 3
    Write-Host "  最近日志:" -ForegroundColor Gray
    $logLines | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
} else {
    Write-Host "⚠ 活动日志未创建" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "测试完成" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步:" -ForegroundColor Yellow
Write-Host "1. 运行持续监控: .\start-cursor-monitor.ps1" -ForegroundColor White
Write-Host "2. 安装定时任务: .\start-cursor-monitor.ps1 -InstallTask" -ForegroundColor White
Write-Host "3. 查看文档: CURSOR_MONITOR_README.md" -ForegroundColor White


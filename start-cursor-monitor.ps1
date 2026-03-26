# 启动Cursor监控脚本
# 检测Cursor是否卡住，如果卡住则自动发送继续执行指令

param(
    [int]$Interval = 30,
    [int]$Timeout = 300,
    [switch]$InstallTask = $false,
    [switch]$Once = $false
)

$ErrorActionPreference = "Continue"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Cursor任务监控" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

if ($InstallTask) {
    # 安装Windows定时任务
    Write-Host "安装Windows定时任务..." -ForegroundColor Yellow
    & "$ScriptRoot\scripts\test-coverage\install-cursor-monitor.ps1" -Install
    Write-Host ""
    Write-Host "✓ 定时任务已安装" -ForegroundColor Green
    Write-Host "任务将每5分钟自动检查一次" -ForegroundColor Gray
} else {
    # 直接运行监控脚本
    $monitorScript = Join-Path $ScriptRoot "scripts\test-coverage\cursor-monitor.py"
    
    if (-not (Test-Path $monitorScript)) {
        Write-Host "错误: 监控脚本不存在: $monitorScript" -ForegroundColor Red
        exit 1
    }
    
    # 检查Python（支持python、python3、py启动器）
    $pythonCmd = $null
    $pythonCommands = @("python", "python3", "py")
    
    foreach ($cmd in $pythonCommands) {
        try {
            $result = Get-Command $cmd -ErrorAction SilentlyContinue
            if ($result) {
                $pythonCmd = $cmd
                $pythonVersion = & $cmd --version 2>&1
                Write-Host "Python版本: $pythonVersion" -ForegroundColor Green
                Write-Host "使用命令: $cmd" -ForegroundColor Gray
                break
            }
        } catch {
            continue
        }
    }
    
    if (-not $pythonCmd) {
        Write-Host "错误: 未找到Python，请先安装Python" -ForegroundColor Red
        Write-Host "提示: 可以尝试安装Python 3.7+或使用py启动器" -ForegroundColor Yellow
        exit 1
    }
    
    # 构建参数
    $scriptArgs = @($monitorScript)
    
    if ($Once) {
        $scriptArgs += "--once"
    } else {
        $scriptArgs += "--interval", $Interval
        $scriptArgs += "--timeout", $Timeout
    }
    
    Write-Host "启动监控脚本..." -ForegroundColor Yellow
    Write-Host ""
    
    & $pythonCmd $scriptArgs
}

Write-Host ""
Write-Host "提示: 当检测到Cursor卡住时，会自动创建继续执行指令文件" -ForegroundColor Cyan
Write-Host "文件路径: continue-coverage-improvement.txt" -ForegroundColor Gray


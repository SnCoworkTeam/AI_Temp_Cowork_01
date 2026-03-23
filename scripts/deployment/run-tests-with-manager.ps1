# 使用连接管理器运行测试
# 自动处理连接健康检查和重建

param(
    [string]$Service = "workflow-engine",
    [int]$Timeout = 300
)

$ErrorActionPreference = "Continue"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ManagerScript = Join-Path $ScriptRoot "ssh-connection-manager.ps1"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "运行测试 (使用连接管理器)" -ForegroundColor Cyan
Write-Host "服务: $Service" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 先测试连接
Write-Host "[1/4] 测试连接..." -ForegroundColor Blue
$testResult = & powershell -ExecutionPolicy Bypass -File $ManagerScript -Action test
if ($LASTEXITCODE -ne 0) {
    Write-Host "连接不健康，清理旧连接..." -ForegroundColor Yellow
    & powershell -ExecutionPolicy Bypass -File $ManagerScript -Action cleanup | Out-Null
}

# 执行测试
Write-Host "[2/4] 运行测试..." -ForegroundColor Blue
$testCommand = "sudo docker exec enterprise-ai-$Service python3 -m pytest /app/tests/unit/ --cov=/app/src --cov-report=term-missing -q 2>&1 | tail -60"

$output = & powershell -ExecutionPolicy Bypass -File $ManagerScript -Action execute -Command $testCommand

Write-Host "[3/4] 测试完成" -ForegroundColor Green
Write-Host ""
Write-Host "测试输出:" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host $output
Write-Host "----------------------------------------" -ForegroundColor Gray

# 提取覆盖率
if ($output -match "TOTAL\s+(\d+)\s+(\d+)\s+(\d+)%") {
    $total = $matches[1]
    $missed = $matches[2]
    $coverage = $matches[3]
    
    Write-Host ""
    Write-Host "覆盖率: $coverage%" -ForegroundColor $(if ([int]$coverage -ge 80) { "Green" } else { "Yellow" })
    Write-Host "总行数: $total, 未覆盖: $missed" -ForegroundColor Gray
    
    if ([int]$coverage -lt 80) {
        Write-Host ""
        Write-Host "需要继续提升覆盖率到80%+" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "[4/4] 完成" -ForegroundColor Green


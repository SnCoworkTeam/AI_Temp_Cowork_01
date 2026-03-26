# 使用持久化连接运行测试
# 避免每次执行命令都重新登录

param(
    [string]$Service = "workflow-engine",
    [string]$ConfigFile = "remote.ssh",
    [switch]$Coverage = $true,
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Continue"

# 获取脚本目录
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptRoot
$ConfigPath = Join-Path $ProjectRoot $ConfigFile

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "运行测试 (使用持久化连接)" -ForegroundColor Cyan
Write-Host "服务: $Service" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 确保ControlMaster连接已建立
Write-Host "[1/3] 建立持久化连接..." -ForegroundColor Blue
$testCmd = "echo 'connection_test'"
$testResult = ssh -F $ConfigPath -o ConnectTimeout=5 enterprise-ai-server $testCmd 2>&1

if ($LASTEXITCODE -ne 0 -or $testResult -notmatch "connection_test") {
    Write-Host "正在建立ControlMaster连接..." -ForegroundColor Yellow
    # 建立后台连接
    $null = Start-Process -FilePath "ssh" -ArgumentList @(
        "-F", $ConfigPath,
        "-N",  # 不执行命令，只建立连接
        "enterprise-ai-server"
    ) -WindowStyle Hidden -PassThru
    Start-Sleep -Seconds 2
}

Write-Host "✓ 连接已就绪" -ForegroundColor Green
Write-Host ""

# 执行测试
Write-Host "[2/3] 运行测试..." -ForegroundColor Blue

$testCommand = "sudo docker exec enterprise-ai-$Service python3 -m pytest /app/tests/unit/ --cov=/app/src --cov-report=term-missing -q 2>&1 | tail -100"

Write-Host "执行命令: $testCommand" -ForegroundColor Gray
Write-Host ""

# 使用持久化连接执行命令
$output = ssh -F $ConfigPath enterprise-ai-server $testCommand 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "[3/3] 测试完成" -ForegroundColor Green
    Write-Host ""
    Write-Host "测试输出:" -ForegroundColor Cyan
    Write-Host "----------------------------------------" -ForegroundColor Gray
    Write-Host $output
    Write-Host "----------------------------------------" -ForegroundColor Gray
} else {
    Write-Host "[3/3] 测试执行出错" -ForegroundColor Red
    Write-Host ""
    Write-Host "错误输出:" -ForegroundColor Red
    Write-Host "----------------------------------------" -ForegroundColor Gray
    Write-Host $output
    Write-Host "----------------------------------------" -ForegroundColor Gray
    exit $LASTEXITCODE
}


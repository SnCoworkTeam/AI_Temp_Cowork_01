# PowerShell 版本的测试运行脚本
# 运行所有模块的测试

param(
    [Parameter(Position=0)]
    [ValidateSet("unit", "integration", "performance", "security", "service", "all")]
    [string]$TestType = "all",
    
    [Parameter(Position=1)]
    [switch]$Coverage = $false,
    
    [Parameter(Position=2)]
    [switch]$Verbose = $false,
    
    [Parameter(Position=3)]
    [string]$ServiceName = "all"
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

# 颜色输出函数
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    $colorMap = @{
        "Red" = "Red"
        "Green" = "Green"
        "Yellow" = "Yellow"
        "Blue" = "Cyan"
    }
    
    $colorCode = $colorMap[$Color]
    if ($colorCode) {
        Write-Host $Message -ForegroundColor $colorCode
    } else {
        Write-Host $Message
    }
}

# 测试结果统计
$script:TotalTests = 0
$script:PassedTests = 0
$script:FailedTests = 0
$script:SkippedTests = 0

Write-ColorOutput "==========================================" "Blue"
Write-ColorOutput "企业AI平台 - 完整测试套件" "Blue"
Write-ColorOutput "==========================================" "Blue"
Write-Host ""

# 检查pytest是否安装
try {
    $null = Get-Command pytest -ErrorAction Stop
} catch {
    Write-ColorOutput "错误: pytest 未安装" "Red"
    Write-ColorOutput "请运行: pip install -r tests/requirements.txt" "Yellow"
    exit 1
}

# 构建pytest命令
$PytestCmd = "pytest"
if ($Verbose) {
    $PytestCmd += " -v"
} else {
    $PytestCmd += " -q"
}

if ($Coverage) {
    $PytestCmd += " --cov=. --cov-report=html --cov-report=term-missing --cov-report=json"
}

# 测试函数
function Run-TestSuite {
    param(
        [string]$SuiteName,
        [string]$TestPath,
        [string]$Marker = ""
    )
    
    Write-ColorOutput "========================================" "Blue"
    Write-ColorOutput "测试: $SuiteName" "Blue"
    Write-ColorOutput "========================================" "Blue"
    
    if (-not (Test-Path $TestPath)) {
        Write-ColorOutput "跳过: $TestPath 不存在" "Yellow"
        $script:SkippedTests++
        return
    }
    
    $cmd = $PytestCmd
    if ($Marker) {
        $cmd += " -m $Marker"
    }
    $cmd += " $TestPath"
    
    try {
        Invoke-Expression $cmd
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✓ $SuiteName 测试通过" "Green"
            $script:PassedTests++
        } else {
            Write-ColorOutput "✗ $SuiteName 测试失败" "Red"
            $script:FailedTests++
        }
    } catch {
        Write-ColorOutput "✗ $SuiteName 测试失败: $_" "Red"
        $script:FailedTests++
    }
    Write-Host ""
}

# 根据测试类型运行
switch ($TestType) {
    "unit" {
        Write-ColorOutput "运行单元测试..." "Blue"
        Write-Host ""
        
        Run-TestSuite "MCP Gateway 单元测试" "mcp-gateway/tests/unit" "unit"
        Run-TestSuite "Workflow Engine 单元测试" "workflow-engine/tests/unit" "unit"
        Run-TestSuite "Auth Service 单元测试" "auth-service/tests/unit" "unit"
        Run-TestSuite "Knowledge Base 单元测试" "knowledge-base/tests/unit" "unit"
        Run-TestSuite "Metadata Service 单元测试" "metadata-service/tests/unit" "unit"
        Run-TestSuite "架构测试" "tests/test-architecture" "unit"
    }
    
    "integration" {
        Write-ColorOutput "运行集成测试..." "Blue"
        Write-Host ""
        
        Run-TestSuite "MCP Gateway 集成测试" "mcp-gateway/tests/integration" "integration"
        Run-TestSuite "Workflow Engine 集成测试" "workflow-engine/tests/integration" "integration"
        Run-TestSuite "Auth Service 集成测试" "auth-service/tests/integration" "integration"
        Run-TestSuite "Knowledge Base 集成测试" "knowledge-base/tests/integration" "integration"
        Run-TestSuite "全局集成测试" "tests/test-integration" "integration"
    }
    
    "performance" {
        Write-ColorOutput "运行性能测试..." "Blue"
        Write-Host ""
        
        Run-TestSuite "性能测试" "tests/test-performance" "performance"
    }
    
    "security" {
        Write-ColorOutput "运行安全测试..." "Blue"
        Write-Host ""
        
        Run-TestSuite "安全测试" "tests/test-security" "security"
    }
    
    "service" {
        Write-ColorOutput "运行服务测试..." "Blue"
        Write-Host ""
        
        if ($ServiceName -eq "all") {
            Run-TestSuite "MCP Gateway" "mcp-gateway/tests" ""
            Run-TestSuite "Workflow Engine" "workflow-engine/tests" ""
            Run-TestSuite "Auth Service" "auth-service/tests" ""
            Run-TestSuite "Knowledge Base" "knowledge-base/tests" ""
            Run-TestSuite "Metadata Service" "metadata-service/tests" ""
        } else {
            Run-TestSuite $ServiceName "$ServiceName/tests" ""
        }
    }
    
    "all" {
        Write-ColorOutput "运行所有测试..." "Blue"
        Write-Host ""
        
        # 1. 架构测试
        Run-TestSuite "架构测试" "tests/test-architecture" "unit"
        
        # 2. 单元测试
        Write-ColorOutput "--- 单元测试 ---" "Yellow"
        Run-TestSuite "MCP Gateway 单元测试" "mcp-gateway/tests/unit" "unit"
        Run-TestSuite "Workflow Engine 单元测试" "workflow-engine/tests/unit" "unit"
        Run-TestSuite "Auth Service 单元测试" "auth-service/tests/unit" "unit"
        Run-TestSuite "Knowledge Base 单元测试" "knowledge-base/tests/unit" "unit"
        Run-TestSuite "Metadata Service 单元测试" "metadata-service/tests/unit" "unit"
        
        # 3. 集成测试
        Write-ColorOutput "--- 集成测试 ---" "Yellow"
        Run-TestSuite "MCP Gateway 集成测试" "mcp-gateway/tests/integration" "integration"
        Run-TestSuite "Workflow Engine 集成测试" "workflow-engine/tests/integration" "integration"
        Run-TestSuite "Auth Service 集成测试" "auth-service/tests/integration" "integration"
        Run-TestSuite "Knowledge Base 集成测试" "knowledge-base/tests/integration" "integration"
        Run-TestSuite "全局集成测试" "tests/test-integration" "integration"
        
        # 4. 安全测试
        Write-ColorOutput "--- 安全测试 ---" "Yellow"
        Run-TestSuite "安全测试" "tests/test-security" "security"
        
        # 5. 性能测试（可选）
        Write-ColorOutput "--- 性能测试（跳过，使用 performance 参数单独运行）---" "Yellow"
    }
}

# 输出测试总结
Write-Host ""
Write-ColorOutput "==========================================" "Blue"
Write-ColorOutput "测试总结" "Blue"
Write-ColorOutput "==========================================" "Blue"
Write-ColorOutput "通过: $script:PassedTests" "Green"
Write-ColorOutput "失败: $script:FailedTests" "Red"
Write-ColorOutput "跳过: $script:SkippedTests" "Yellow"
Write-Host ""

if ($Coverage) {
    Write-ColorOutput "覆盖率报告已生成: htmlcov/index.html" "Blue"
    Write-Host ""
}

if ($script:FailedTests -eq 0) {
    Write-ColorOutput "✓ 所有测试通过！" "Green"
    exit 0
} else {
    Write-ColorOutput "✗ 有 $script:FailedTests 个测试套件失败" "Red"
    exit 1
}


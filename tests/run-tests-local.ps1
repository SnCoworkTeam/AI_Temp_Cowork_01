# 本地测试运行脚本（PowerShell）
# 用于在本地环境运行测试并检查覆盖率

param(
    [Parameter(Position=0)]
    [ValidateSet("all", "unit", "integration", "metadata-service", "database", "workflow-engine", "auth-service", "knowledge-base", "mcp-gateway")]
    [string]$TestType = "all",
    
    [switch]$Coverage = $false,
    [switch]$Verbose = $false
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "本地测试运行" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查pytest是否安装
try {
    $pytestVersion = pytest --version 2>&1
    Write-Host "✓ pytest已安装: $pytestVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ pytest未安装，正在安装..." -ForegroundColor Yellow
    pip install pytest pytest-asyncio pytest-cov pytest-mock httpx
}

# 构建pytest命令
$pytestArgs = @()

if ($Verbose) {
    $pytestArgs += "-v"
} else {
    $pytestArgs += "-q"
}

if ($Coverage) {
    $pytestArgs += "--cov=."
    $pytestArgs += "--cov-report=html"
    $pytestArgs += "--cov-report=term-missing"
    $pytestArgs += "--cov-report=json"
}

# 根据测试类型选择测试路径
switch ($TestType) {
    "unit" {
        Write-Host "运行单元测试..." -ForegroundColor Blue
        $pytestArgs += "-m"
        $pytestArgs += "unit"
    }
    "integration" {
        Write-Host "运行集成测试..." -ForegroundColor Blue
        $pytestArgs += "-m"
        $pytestArgs += "integration"
    }
    "metadata-service" {
        Write-Host "运行metadata-service测试..." -ForegroundColor Blue
        $pytestArgs += "metadata-service/tests"
    }
    "database" {
        Write-Host "运行database测试..." -ForegroundColor Blue
        $pytestArgs += "database/tests"
    }
    "workflow-engine" {
        Write-Host "运行workflow-engine测试..." -ForegroundColor Blue
        $pytestArgs += "workflow-engine/tests"
    }
    "auth-service" {
        Write-Host "运行auth-service测试..." -ForegroundColor Blue
        $pytestArgs += "auth-service/tests"
    }
    "knowledge-base" {
        Write-Host "运行knowledge-base测试..." -ForegroundColor Blue
        $pytestArgs += "knowledge-base/tests"
    }
    "mcp-gateway" {
        Write-Host "运行mcp-gateway测试..." -ForegroundColor Blue
        $pytestArgs += "mcp-gateway/tests"
    }
    "all" {
        Write-Host "运行所有测试..." -ForegroundColor Blue
        # 运行所有服务的测试
        $services = @("metadata-service", "database", "workflow-engine", "auth-service", "knowledge-base", "mcp-gateway")
        $failedServices = @()
        
        foreach ($service in $services) {
            Write-Host ""
            Write-Host "------------------------------------------" -ForegroundColor Yellow
            Write-Host "测试: $service" -ForegroundColor Yellow
            Write-Host "------------------------------------------" -ForegroundColor Yellow
            
            $serviceArgs = $pytestArgs.Clone()
            $serviceArgs += "$service/tests"
            
            $result = & pytest $serviceArgs
            
            if ($LASTEXITCODE -ne 0) {
                $failedServices += $service
                Write-Host "✗ $service 测试失败" -ForegroundColor Red
            } else {
                Write-Host "✓ $service 测试通过" -ForegroundColor Green
            }
        }
        
        Write-Host ""
        Write-Host "==========================================" -ForegroundColor Cyan
        Write-Host "测试总结" -ForegroundColor Cyan
        Write-Host "==========================================" -ForegroundColor Cyan
        
        if ($failedServices.Count -eq 0) {
            Write-Host "✓ 所有服务测试通过！" -ForegroundColor Green
        } else {
            Write-Host "✗ 以下服务测试失败:" -ForegroundColor Red
            $failedServices | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
        }
        
        if ($Coverage) {
            Write-Host ""
            Write-Host "覆盖率报告已生成: htmlcov/index.html" -ForegroundColor Cyan
        }
        
        exit 0
    }
}

# 运行测试
Write-Host ""
Write-Host "执行命令: pytest $($pytestArgs -join ' ')" -ForegroundColor Gray
Write-Host ""

$result = & pytest $pytestArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ 测试通过！" -ForegroundColor Green
    
    if ($Coverage) {
        Write-Host ""
        Write-Host "覆盖率报告已生成: htmlcov/index.html" -ForegroundColor Cyan
    }
} else {
    Write-Host ""
    Write-Host "✗ 测试失败" -ForegroundColor Red
    Write-Host ""
    Write-Host "提示:" -ForegroundColor Yellow
    Write-Host "1. 检查错误信息" -ForegroundColor White
    Write-Host "2. 验证导入路径是否正确" -ForegroundColor White
    Write-Host "3. 检查依赖是否安装" -ForegroundColor White
    Write-Host "4. 查看测试运行指南: docs/development-docs/TEST_RUNNING_GUIDE.md" -ForegroundColor White
}

exit $LASTEXITCODE



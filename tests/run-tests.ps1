# PowerShell测试运行脚本（Windows）

param(
    [Parameter(Position=0)]
    [ValidateSet("unit", "integration", "performance", "security", "all")]
    [string]$TestType = "all",
    
    [Parameter(Position=1)]
    [switch]$Coverage = $true
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "=========================================="
Write-Host "运行测试套件"
Write-Host "=========================================="

Set-Location $ProjectRoot

switch ($TestType) {
    "unit" {
        Write-Host "运行单元测试..."
        if ($Coverage) {
            pytest -m unit --cov=. --cov-report=html --cov-report=term
        } else {
            pytest -m unit
        }
    }
    "integration" {
        Write-Host "运行集成测试..."
        pytest -m integration -v
    }
    "performance" {
        Write-Host "运行性能测试..."
        pytest -m performance -v
    }
    "security" {
        Write-Host "运行安全测试..."
        pytest -m security -v
    }
    "all" {
        Write-Host "运行所有测试..."
        if ($Coverage) {
            pytest --cov=. --cov-report=html --cov-report=term --cov-report=json
        } else {
            pytest
        }
    }
}

Write-Host "=========================================="
Write-Host "测试完成"
Write-Host "=========================================="










# AI辅助CI/CD测试启动脚本
# 快速启动AI辅助的自动化测试闭环

param(
    [ValidateSet("layer", "service", "all")]
    [string]$Mode = "layer",

    [switch]$NoAIAssist,

    [switch]$CheckEnv
)

$ErrorActionPreference = "Stop"

# 颜色输出函数
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "✅ $Message" "Green"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "❌ $Message" "Red"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "⚠️  $Message" "Yellow"
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "ℹ️  $Message" "Cyan"
}

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "=" * 70 -ForegroundColor Cyan
    Write-ColorOutput $Message "Cyan"
    Write-Host "=" * 70 -ForegroundColor Cyan
    Write-Host ""
}

# 检查环境
function Test-Environment {
    Write-Header "检查运行环境"

    $allOk = $true

    # 检查GitHub CLI
    Write-Info "检查GitHub CLI (gh)..."
    $ghVersion = gh --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "GitHub CLI: $($ghVersion[0])"
    } else {
        Write-Error "GitHub CLI未安装"
        Write-Warning "安装命令: winget install --id GitHub.cli"
        $allOk = $false
    }

    # 检查Python
    Write-Info "检查Python..."
    $pythonVersion = python --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Python: $pythonVersion"

        # 检查版本是否>=3.11
        if ($pythonVersion -match "Python (\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
                Write-Warning "Python版本较低,建议3.11+"
            }
        }
    } else {
        Write-Error "Python未安装"
        Write-Warning "下载地址: https://www.python.org/downloads/"
        $allOk = $false
    }

    # 检查Node.js
    Write-Info "检查Node.js..."
    $nodeVersion = node --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Node.js: $nodeVersion"

        # 检查版本是否>=18
        if ($nodeVersion -match "v(\d+)") {
            $major = [int]$matches[1]
            if ($major -lt 18) {
                Write-Warning "Node.js版本较低,建议18+"
            }
        }
    } else {
        Write-Error "Node.js未安装"
        Write-Warning "下载地址: https://nodejs.org/"
        $allOk = $false
    }

    # 检查GitHub认证
    Write-Info "检查GitHub认证..."
    gh auth status 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "GitHub已认证"
    } else {
        Write-Error "GitHub未认证"
        Write-Warning "运行命令: gh auth login"
        $allOk = $false
    }

    # 检查脚本文件
    Write-Info "检查脚本文件..."
    $scriptPath = Join-Path $PSScriptRoot "cicd\ai_assisted_tester.py"
    if (Test-Path $scriptPath) {
        Write-Success "测试脚本: $scriptPath"
    } else {
        Write-Error "测试脚本不存在: $scriptPath"
        $allOk = $false
    }

    Write-Host ""
    if ($allOk) {
        Write-Success "环境检查通过,可以开始测试!"
        return $true
    } else {
        Write-Error "环境检查失败,请先安装缺失的工具"
        return $false
    }
}

# 显示使用说明
function Show-Usage {
    Write-Header "AI辅助CI/CD测试 - 使用说明"

    Write-Host "这个脚本会启动AI辅助的自动化测试闭环:"
    Write-Host ""
    Write-Host "工作流程:" -ForegroundColor Yellow
    Write-Host "  1. Python脚本触发GitHub Actions"
    Write-Host "  2. 等待测试完成并下载日志"
    Write-Host "  3. 自动分析错误"
    Write-Host "  4. 生成Claude Code错误报告"
    Write-Host "  5. 暂停等待你使用Claude Code修复"
    Write-Host "  6. 修复后继续下一轮测试"
    Write-Host "  7. 重复直到所有测试通过"
    Write-Host ""
    Write-Host "参数说明:" -ForegroundColor Yellow
    Write-Host "  -Mode <layer|service|all>  测试模式(默认:layer)"
    Write-Host "    - layer: 按服务层级逐层测试"
    Write-Host "    - service: 逐个服务测试"
    Write-Host "    - all: 所有服务一起测试"
    Write-Host ""
    Write-Host "  -NoAIAssist               禁用AI辅助(不等待人工)"
    Write-Host "  -CheckEnv                 只检查环境,不运行测试"
    Write-Host ""
    Write-Host "使用示例:" -ForegroundColor Yellow
    Write-Host "  .\start-ai-assisted-test.ps1                    # 按层级测试,启用AI辅助"
    Write-Host "  .\start-ai-assisted-test.ps1 -Mode service     # 逐个服务测试"
    Write-Host "  .\start-ai-assisted-test.ps1 -NoAIAssist       # 禁用AI辅助"
    Write-Host "  .\start-ai-assisted-test.ps1 -CheckEnv         # 只检查环境"
    Write-Host ""
}

# 主函数
function Main {
    Clear-Host

    Write-Header "AI辅助CI/CD自动化测试器"
    Write-Host "开始时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Host ""

    # 如果只是检查环境
    if ($CheckEnv) {
        $envOk = Test-Environment
        if ($envOk) {
            Write-Host ""
            Write-Success "环境检查完成,可以运行测试了!"
            Write-Host ""
            Write-Info "运行测试命令:"
            Write-Host "  .\start-ai-assisted-test.ps1" -ForegroundColor White
        }
        return
    }

    # 显示使用说明
    Show-Usage

    # 检查环境
    $envOk = Test-Environment
    if (-not $envOk) {
        Write-Host ""
        Write-Error "环境检查失败,无法继续"
        Write-Host ""
        Write-Info "你可以运行以下命令只检查环境:"
        Write-Host "  .\start-ai-assisted-test.ps1 -CheckEnv" -ForegroundColor White
        exit 1
    }

    # 确认开始
    Write-Host ""
    Write-Warning "即将启动AI辅助测试闭环"
    Write-Host ""
    Write-Host "测试模式: $Mode" -ForegroundColor Cyan
    Write-Host "AI辅助: $(if ($NoAIAssist) { '禁用' } else { '启用' })" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "注意事项:" -ForegroundColor Yellow
    Write-Host "  - 每次测试约15-20分钟"
    Write-Host "  - 测试失败时会生成错误报告"
    Write-Host "  - 需要在Claude Code中查看报告并修复"
    Write-Host "  - 修复后按Enter继续测试"
    Write-Host "  - 可以随时按Ctrl+C中断"
    Write-Host ""

    $confirm = Read-Host "确认开始? (Y/n)"
    if ($confirm -and $confirm -ne "Y" -and $confirm -ne "y") {
        Write-Warning "已取消"
        return
    }

    # 构建Python命令
    Write-Header "启动测试"

    $scriptPath = Join-Path $PSScriptRoot "cicd\ai_assisted_tester.py"
    $pythonArgs = @($scriptPath, "--mode", $Mode)

    if ($NoAIAssist) {
        $pythonArgs += "--no-ai-assist"
    }

    Write-Info "执行命令: python $($pythonArgs -join ' ')"
    Write-Host ""

    # 运行Python脚本
    try {
        & python $pythonArgs

        Write-Host ""
        if ($LASTEXITCODE -eq 0) {
            Write-Success "测试完成!"
        } else {
            Write-Warning "测试未完全通过,请查看详细日志"
        }
    }
    catch {
        Write-Host ""
        Write-Error "执行过程中出错: $_"
        exit 1
    }

    # 显示日志位置
    Write-Host ""
    Write-Header "测试结果"

    $logDir = Join-Path $env:TEMP "ai-assisted-test-logs"
    Write-Info "日志目录: $logDir"

    if (Test-Path $logDir) {
        Write-Info "进度文件: $(Join-Path $logDir 'test_progress.json')"

        # 显示最新的Claude报告
        $reports = Get-ChildItem -Path $logDir -Filter "claude_report_*.md" -ErrorAction SilentlyContinue |
                   Sort-Object LastWriteTime -Descending |
                   Select-Object -First 1

        if ($reports) {
            Write-Info "最新错误报告: $($reports.FullName)"
        }
    }

    Write-Host ""
    Write-Success "完成!"
}

# 运行主函数
Main

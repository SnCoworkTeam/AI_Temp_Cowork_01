# 本地测试报告监控脚本
# 定时从服务器拉取测试报告并分析

param(
    [string]$ServerIP = "43.143.139.197",
    [string]$ServerUser = "ubuntu",
    [string]$KeyPath = "enterprise_ai_platform.pem",
    [string]$RemotePath = "/opt/enterprise-ai-platform",
    [int]$IntervalMinutes = 30,  # 默认30分钟检查一次
    [switch]$RunOnce = $false,    # 只运行一次，不循环
    [switch]$RunTests = $false    # 是否在检查前先运行测试
)

$ErrorActionPreference = "Continue"

# 颜色输出函数
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

# 创建本地报告目录
$LocalReportDir = "test-reports-local"
if (-not (Test-Path $LocalReportDir)) {
    New-Item -ItemType Directory -Path $LocalReportDir | Out-Null
}

# 从服务器拉取测试报告
function Get-TestReports {
    Write-ColorOutput "`n=== 从服务器拉取测试报告 ===" "Cyan"
    
    try {
        # 拉取测试结果目录
        Write-ColorOutput "拉取测试结果..." "Yellow"
        scp -i $KeyPath -o StrictHostKeyChecking=no -r "${ServerUser}@${ServerIP}:$RemotePath/test-results" "$LocalReportDir/" 2>&1 | Out-Null
        
        # 拉取覆盖率报告
        Write-ColorOutput "拉取覆盖率报告..." "Yellow"
        scp -i $KeyPath -o StrictHostKeyChecking=no -r "${ServerUser}@${ServerIP}:$RemotePath/coverage-report" "$LocalReportDir/" 2>&1 | Out-Null
        
        # 拉取测试报告Markdown
        Write-ColorOutput "拉取测试报告..." "Yellow"
        scp -i $KeyPath -o StrictHostKeyChecking=no "${ServerUser}@${ServerIP}:$RemotePath/test-results/test-report.md" "$LocalReportDir/" 2>&1 | Out-Null
        
        Write-ColorOutput "✅ 测试报告已拉取到本地: $LocalReportDir" "Green"
        return $true
    }
    catch {
        Write-ColorOutput "❌ 拉取测试报告失败: $_" "Red"
        return $false
    }
}

# 分析测试结果
function Analyze-TestResults {
    Write-ColorOutput "`n=== 分析测试结果 ===" "Cyan"
    
    $results = @{
        Total = 0
        Passed = 0
        Failed = 0
        Errors = 0
        Skipped = 0
    }
    
    # 分析JUnit XML报告
    $xmlFiles = Get-ChildItem -Path "$LocalReportDir/test-results" -Filter "*-results.xml" -ErrorAction SilentlyContinue
    if ($xmlFiles) {
        foreach ($xmlFile in $xmlFiles) {
            Write-ColorOutput "分析: $($xmlFile.Name)" "Yellow"
            $xml = [xml](Get-Content $xmlFile.FullName)
            $testsuite = $xml.testsuite
            
            if ($testsuite) {
                $results.Total += [int]$testsuite.tests
                $results.Passed += [int]$testsuite.tests - [int]$testsuite.failures - [int]$testsuite.errors
                $results.Failed += [int]$testsuite.failures
                $results.Errors += [int]$testsuite.errors
            }
        }
    }
    
    # 显示统计
    Write-ColorOutput "`n📊 测试统计:" "Blue"
    Write-ColorOutput "  总计: $($results.Total)" "White"
    Write-ColorOutput "  通过: $($results.Passed)" "Green"
    Write-ColorOutput "  失败: $($results.Failed)" "Red"
    Write-ColorOutput "  错误: $($results.Errors)" "Red"
    Write-ColorOutput "  跳过: $($results.Skipped)" "Yellow"
    
    # 计算通过率
    if ($results.Total -gt 0) {
        $passRate = [math]::Round(($results.Passed / $results.Total) * 100, 2)
        Write-ColorOutput "  通过率: $passRate%" "Blue"
        
        if ($passRate -lt 80) {
            Write-ColorOutput "  ⚠️  通过率低于80%，需要关注！" "Yellow"
        }
    }
    
    # 检查失败
    if ($results.Failed -gt 0 -or $results.Errors -gt 0) {
        Write-ColorOutput "`n❌ 发现失败的测试！" "Red"
        Write-ColorOutput "查看详细日志: $LocalReportDir\test-results\" "Yellow"
        return $false
    }
    
    Write-ColorOutput "`n✅ 所有测试通过！" "Green"
    return $true
}

# 显示失败的测试详情
function Show-FailedTests {
    Write-ColorOutput "`n=== 失败的测试详情 ===" "Cyan"
    
    $xmlFiles = Get-ChildItem -Path "$LocalReportDir/test-results" -Filter "*-results.xml" -ErrorAction SilentlyContinue
    foreach ($xmlFile in $xmlFiles) {
        $xml = [xml](Get-Content $xmlFile.FullName)
        $failures = $xml.SelectNodes("//testcase[@status='failed' or failure or error]")
        
        if ($failures.Count -gt 0) {
            Write-ColorOutput "`n文件: $($xmlFile.Name)" "Yellow"
            foreach ($failure in $failures) {
                Write-ColorOutput "  ❌ $($failure.name)" "Red"
                if ($failure.failure) {
                    $message = $failure.failure.message
                    if ($message) {
                        Write-ColorOutput "     错误: $($message.Substring(0, [Math]::Min(100, $message.Length)))" "Red"
                    }
                }
            }
        }
    }
}

# 生成本地报告
function Generate-LocalReport {
    $reportFile = "$LocalReportDir\test-report-$(Get-Date -Format 'yyyyMMdd-HHmmss').md"
    
    $report = @"
# 测试报告监控结果

生成时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
服务器: $ServerIP

## 测试统计

"@
    
    # 读取测试报告
    if (Test-Path "$LocalReportDir\test-report.md") {
        $report += "`n" + (Get-Content "$LocalReportDir\test-report.md" -Raw)
    }
    
    # 分析结果
    $xmlFiles = Get-ChildItem -Path "$LocalReportDir/test-results" -Filter "*-results.xml" -ErrorAction SilentlyContinue
    if ($xmlFiles) {
        $report += "`n## 详细测试结果`n`n"
        foreach ($xmlFile in $xmlFiles) {
            $xml = [xml](Get-Content $xmlFile.FullName)
            $testsuite = $xml.testsuite
            if ($testsuite) {
                $report += "### $($xmlFile.BaseName)`n"
                $report += "- 总计: $($testsuite.tests)`n"
                $report += "- 通过: $([int]$testsuite.tests - [int]$testsuite.failures - [int]$testsuite.errors)`n"
                $report += "- 失败: $($testsuite.failures)`n"
                $report += "- 错误: $($testsuite.errors)`n`n"
            }
        }
    }
    
    $report | Out-File -FilePath $reportFile -Encoding UTF8
    Write-ColorOutput "`n📄 报告已生成: $reportFile" "Green"
}

# 在服务器上运行测试
function Run-TestsOnServer {
    Write-ColorOutput "`n=== 在服务器上运行测试 ===" "Cyan"
    
    try {
        ssh -i $KeyPath -o StrictHostKeyChecking=no $ServerUser@${ServerIP} "cd $RemotePath && bash scripts/test/run-tests-simple.sh > /tmp/test-run.log 2>&1 &" 2>&1 | Out-Null
        Write-ColorOutput "✅ 测试已在服务器后台启动" "Green"
        Write-ColorOutput "等待测试完成（60秒）..." "Yellow"
        Start-Sleep -Seconds 60
    }
    catch {
        Write-ColorOutput "❌ 启动测试失败: $_" "Red"
    }
}

# 主循环
function Main-Loop {
    Write-ColorOutput "==========================================" "Cyan"
    Write-ColorOutput "🧪 测试报告监控器" "Cyan"
    Write-ColorOutput "==========================================" "Cyan"
    Write-ColorOutput "服务器: $ServerIP" "White"
    Write-ColorOutput "检查间隔: $IntervalMinutes 分钟" "White"
    Write-ColorOutput "本地报告目录: $LocalReportDir" "White"
    Write-ColorOutput "==========================================" "Cyan"
    
    do {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Write-ColorOutput "`n[$timestamp] 开始检查..." "Cyan"
        
        # 如果需要，先运行测试
        if ($RunTests) {
            Run-TestsOnServer
        }
        
        # 拉取报告
        if (Get-TestReports) {
            # 分析结果
            $allPassed = Analyze-TestResults
            
            # 如果有失败，显示详情
            if (-not $allPassed) {
                Show-FailedTests
            }
            
            # 生成本地报告
            Generate-LocalReport
        }
        
        # 如果只运行一次，退出
        if ($RunOnce) {
            break
        }
        
        # 等待下次检查
        Write-ColorOutput "`n⏰ 等待 $IntervalMinutes 分钟后再次检查..." "Yellow"
        Start-Sleep -Seconds ($IntervalMinutes * 60)
        
    } while (-not $RunOnce)
}

# 运行主循环
Main-Loop


# 测试监控和自动修复脚本
# 监控测试报告，发现bug后自动分析并提供修复建议

param(
    [string]$ServerIP = "43.143.139.197",
    [string]$ServerUser = "ubuntu",
    [string]$KeyPath = "enterprise_ai_platform.pem",
    [string]$RemotePath = "/opt/enterprise-ai-platform",
    [int]$IntervalMinutes = 30,
    [switch]$AutoFix = $false,  # 是否自动修复（谨慎使用）
    [switch]$RunOnce = $false
)

$ErrorActionPreference = "Continue"

# 颜色输出
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

# 创建本地报告目录
$LocalReportDir = "test-reports-local"
$FixReportDir = "fix-reports"
if (-not (Test-Path $LocalReportDir)) {
    New-Item -ItemType Directory -Path $LocalReportDir | Out-Null
}
if (-not (Test-Path $FixReportDir)) {
    New-Item -ItemType Directory -Path $FixReportDir | Out-Null
}

# 从服务器拉取测试报告
function Get-TestReports {
    Write-ColorOutput "`n=== 从服务器拉取测试报告 ===" "Cyan"
    
    try {
        scp -i $KeyPath -o StrictHostKeyChecking=no -r "${ServerUser}@${ServerIP}:$RemotePath/test-results" "$LocalReportDir/" 2>&1 | Out-Null
        scp -i $KeyPath -o StrictHostKeyChecking=no -r "${ServerUser}@${ServerIP}:$RemotePath/coverage-report" "$LocalReportDir/" 2>&1 | Out-Null
        Write-ColorOutput "✅ 测试报告已拉取" "Green"
        return $true
    }
    catch {
        Write-ColorOutput "❌ 拉取失败: $_" "Red"
        return $false
    }
}

# 分析测试失败
function Analyze-Failures {
    Write-ColorOutput "`n=== 分析测试失败 ===" "Cyan"
    
    $failures = @()
    $xmlFiles = Get-ChildItem -Path "$LocalReportDir/test-results" -Filter "*-results.xml" -ErrorAction SilentlyContinue
    
    foreach ($xmlFile in $xmlFiles) {
        try {
            $xml = [xml](Get-Content $xmlFile.FullName)
            $testcases = $xml.SelectNodes("//testcase[failure or error]")
            
            foreach ($testcase in $testcases) {
                $failure = $testcase.SelectSingleNode("failure | error")
                if ($failure) {
                    $failures += @{
                        File = $xmlFile.Name
                        TestName = $testcase.name
                        ClassName = $testcase.classname
                        Message = $failure.message
                        Type = $failure.localName
                        StackTrace = $failure.'#text'
                    }
                }
            }
        }
        catch {
            Write-ColorOutput "⚠️  解析 $($xmlFile.Name) 失败: $_" "Yellow"
        }
    }
    
    return $failures
}

# 识别常见问题模式
function Identify-Issues {
    param([array]$Failures)
    
    $issues = @()
    
    foreach ($failure in $Failures) {
        $message = $failure.Message
        $stackTrace = $failure.StackTrace
        
        # 模式1: ModuleNotFoundError
        if ($message -match "ModuleNotFoundError.*No module named '(\w+)'") {
            $module = $matches[1]
            $issues += @{
                Type = "MissingModule"
                Severity = "High"
                Module = $module
                Failure = $failure
                Fix = "在requirements.txt中添加 $module，或在服务器上安装: pip install $module"
                AutoFixable = $true
            }
        }
        
        # 模式2: ImportError
        elseif ($message -match "ImportError.*cannot import name '(\w+)'") {
            $import = $matches[1]
            $issues += @{
                Type = "ImportError"
                Severity = "High"
                Import = $import
                Failure = $failure
                Fix = "检查导入路径和模块结构，确保 $import 正确导入"
                AutoFixable = $false
            }
        }
        
        # 模式3: 数据库连接错误
        elseif ($message -match ".*connection.*refused|.*database.*not.*found|.*authentication.*failed") {
            $issues += @{
                Type = "DatabaseConnection"
                Severity = "Critical"
                Failure = $failure
                Fix = "检查数据库服务是否运行，检查连接配置"
                AutoFixable = $false
            }
        }
        
        # 模式4: 文件不存在
        elseif ($message -match ".*No such file or directory.*|.*FileNotFoundError") {
            $issues += @{
                Type = "FileNotFound"
                Severity = "Medium"
                Failure = $failure
                Fix = "检查文件路径，确保文件已同步到服务器"
                AutoFixable = $false
            }
        }
        
        # 模式5: 断言失败
        elseif ($message -match "AssertionError|assert.*failed") {
            $issues += @{
                Type = "AssertionFailure"
                Severity = "Medium"
                Failure = $failure
                Fix = "检查测试逻辑和业务逻辑，修复断言条件"
                AutoFixable = $false
            }
        }
        
        # 模式6: 超时
        elseif ($message -match ".*timeout|.*timed.*out") {
            $issues += @{
                Type = "Timeout"
                Severity = "Medium"
                Failure = $failure
                Fix = "检查服务响应时间，可能需要优化性能或增加超时时间"
                AutoFixable = $false
            }
        }
        
        # 默认：未知问题
        else {
            $issues += @{
                Type = "Unknown"
                Severity = "Low"
                Failure = $failure
                Fix = "需要手动分析错误信息"
                AutoFixable = $false
            }
        }
    }
    
    return $issues
}

# 自动修复（仅限安全的问题）
function Auto-Fix {
    param([array]$Issues)
    
    if (-not $AutoFix) {
        Write-ColorOutput "`n⚠️  自动修复已禁用，使用 -AutoFix 参数启用" "Yellow"
        return $false
    }
    
    Write-ColorOutput "`n=== 尝试自动修复 ===" "Cyan"
    
    $fixed = 0
    $fixActions = @()
    
    foreach ($issue in $Issues) {
        if ($issue.AutoFixable) {
            switch ($issue.Type) {
                "MissingModule" {
                    Write-ColorOutput "修复: 添加缺失模块 $($issue.Module)" "Yellow"
                    
                    # 检查requirements.txt
                    $reqFile = "requirements.txt"
                    if (-not (Test-Path $reqFile)) {
                        $reqFile = "tests/requirements.txt"
                    }
                    
                    if (Test-Path $reqFile) {
                        $content = Get-Content $reqFile -Raw
                        if ($content -notmatch $issue.Module) {
                            Add-Content -Path $reqFile -Value "`n$($issue.Module)>=0.0.0  # 自动添加"
                            $fixActions += "在 $reqFile 中添加了 $($issue.Module)"
                            $fixed++
                        }
                    }
                }
            }
        }
    }
    
    if ($fixed -gt 0) {
        Write-ColorOutput "✅ 已修复 $fixed 个问题" "Green"
        $fixActions | ForEach-Object { Write-ColorOutput "  - $_" "Cyan" }
        return $true
    }
    else {
        Write-ColorOutput "ℹ️  没有可自动修复的问题" "Yellow"
        return $false
    }
}

# 生成修复报告
function Generate-FixReport {
    param([array]$Failures, [array]$Issues)
    
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $reportFile = "$FixReportDir/fix-report-$timestamp.md"
    
    $report = @"
# Bug修复报告

生成时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
服务器: $ServerIP

## 📊 失败统计

- **总失败数**: $($Failures.Count)
- **可自动修复**: $(($Issues | Where-Object { $_.AutoFixable }).Count)
- **需要手动修复**: $(($Issues | Where-Object { -not $_.AutoFixable }).Count)

## 🐛 问题详情

"@
    
    # 按严重程度分组
    $critical = $Issues | Where-Object { $_.Severity -eq "Critical" }
    $high = $Issues | Where-Object { $_.Severity -eq "High" }
    $medium = $Issues | Where-Object { $_.Severity -eq "Medium" }
    $low = $Issues | Where-Object { $_.Severity -eq "Low" }
    
    if ($critical.Count -gt 0) {
        $report += "`n### 🔴 严重问题 (Critical)`n`n"
        foreach ($issue in $critical) {
            $report += "#### $($issue.Failure.TestName)`n"
            $report += "- **类型**: $($issue.Type)`n"
            $report += "- **测试**: $($issue.Failure.ClassName)::$($issue.Failure.TestName)`n"
            $report += "- **错误**: $($issue.Failure.Message.Substring(0, [Math]::Min(200, $issue.Failure.Message.Length)))`n"
            $report += "- **修复建议**: $($issue.Fix)`n"
            $report += "- **自动修复**: $($issue.AutoFixable)`n`n"
        }
    }
    
    if ($high.Count -gt 0) {
        $report += "`n### 🟠 高优先级问题 (High)`n`n"
        foreach ($issue in $high) {
            $report += "#### $($issue.Failure.TestName)`n"
            $report += "- **类型**: $($issue.Type)`n"
            $report += "- **修复建议**: $($issue.Fix)`n"
            $report += "- **自动修复**: $($issue.AutoFixable)`n`n"
        }
    }
    
    if ($medium.Count -gt 0) {
        $report += "`n### 🟡 中优先级问题 (Medium)`n`n"
        foreach ($issue in $medium) {
            $report += "- **$($issue.Failure.TestName)**: $($issue.Fix)`n"
        }
    }
    
    $report += @"

## 🔧 修复操作

"@
    
    if ($AutoFix) {
        $report += "已尝试自动修复部分问题。`n`n"
    }
    else {
        $report += "自动修复未启用。请手动修复上述问题。`n`n"
    }
    
    $report += @"
## 📋 下一步

1. 查看详细错误信息: `test-reports-local/test-results/`
2. 根据修复建议修复问题
3. 同步代码到服务器
4. 重新运行测试验证修复

---
报告生成时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
"@
    
    $report | Out-File -FilePath $reportFile -Encoding UTF8
    Write-ColorOutput "`n📄 修复报告已生成: $reportFile" "Green"
    
    return $reportFile
}

# 发送通知（可选）
function Send-Notification {
    param([array]$Issues)
    
    if ($Issues.Count -eq 0) {
        return
    }
    
    $criticalCount = ($Issues | Where-Object { $_.Severity -eq "Critical" }).Count
    $highCount = ($Issues | Where-Object { $_.Severity -eq "High" }).Count
    
    Write-ColorOutput "`n🔔 发现 $($Issues.Count) 个问题需要修复！" "Red"
    if ($criticalCount -gt 0) {
        Write-ColorOutput "  🔴 严重问题: $criticalCount" "Red"
    }
    if ($highCount -gt 0) {
        Write-ColorOutput "  🟠 高优先级: $highCount" "Yellow"
    }
    
    # 可以在这里添加邮件、Slack等通知
}

# 主循环
function Main-Loop {
    Write-ColorOutput "==========================================" "Cyan"
    Write-ColorOutput "🐛 Bug监控和修复系统" "Cyan"
    Write-ColorOutput "==========================================" "Cyan"
    Write-ColorOutput "服务器: $ServerIP" "White"
    Write-ColorOutput "检查间隔: $IntervalMinutes 分钟" "White"
    Write-ColorOutput "自动修复: $AutoFix" "White"
    Write-ColorOutput "==========================================" "Cyan"
    
    do {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Write-ColorOutput "`n[$timestamp] 开始检查..." "Cyan"
        
        # 拉取报告
        if (Get-TestReports) {
            # 分析失败
            $failures = Analyze-Failures
            
            if ($failures.Count -gt 0) {
                Write-ColorOutput "`n❌ 发现 $($failures.Count) 个失败的测试" "Red"
                
                # 识别问题
                $issues = Identify-Issues -Failures $failures
                
                # 显示问题摘要
                Write-ColorOutput "`n=== 问题摘要 ===" "Cyan"
                $issues | Group-Object Type | ForEach-Object {
                    Write-ColorOutput "  $($_.Name): $($_.Count) 个" "Yellow"
                }
                
                # 尝试自动修复
                if ($AutoFix) {
                    Auto-Fix -Issues $issues
                }
                
                # 生成修复报告
                $reportFile = Generate-FixReport -Failures $failures -Issues $issues
                
                # 发送通知
                Send-Notification -Issues $issues
                
                Write-ColorOutput "`n📋 请查看修复报告: $reportFile" "Yellow"
            }
            else {
                Write-ColorOutput "`n✅ 所有测试通过！" "Green"
            }
        }
        
        if ($RunOnce) {
            break
        }
        
        Write-ColorOutput "`n⏰ 等待 $IntervalMinutes 分钟后再次检查..." "Yellow"
        Start-Sleep -Seconds ($IntervalMinutes * 60)
        
    } while (-not $RunOnce)
}

# 运行主循环
Main-Loop


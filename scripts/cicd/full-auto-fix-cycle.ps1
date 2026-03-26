# 完整自动化修复循环
# 1. 启动工作流
# 2. 获取工作流ID
# 3. 查看日志
# 4. 分析错误
# 5. 修复bug
# 6. 上传代码
# 7. 循环

$ErrorActionPreference = "Continue"

$PROJECT_DIR = $PSScriptRoot + "\..\.."
$REPO = "PMLiuyubin/enterprise-ai-platform"
$WORKFLOW = "deploy.yml"
$LOG_DIR = "$env:TEMP\github-errors"
$MAX_ITERATIONS = 5

Set-Location $PROJECT_DIR
New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "完整自动化修复循环" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 函数：启动工作流
function Start-Workflow {
    Write-Host "[步骤1] 启动工作流..." -ForegroundColor Yellow
    
    $result = gh workflow run $WORKFLOW --field environment=staging --repo=$REPO 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 工作流已启动" -ForegroundColor Green
        Start-Sleep -Seconds 5  # 等待工作流启动
        return $true
    } else {
        Write-Host "❌ 启动工作流失败: $result" -ForegroundColor Red
        return $false
    }
}

# 函数：获取最新运行ID
function Get-LatestRunId {
    Write-Host "[步骤2] 获取最新运行ID..." -ForegroundColor Yellow
    
    $runs = gh run list --workflow=$WORKFLOW --repo=$REPO --limit 1 --json databaseId,status,createdAt 2>&1 | ConvertFrom-Json
    
    if ($runs -and $runs.Count -gt 0) {
        $runId = $runs[0].databaseId
        $status = $runs[0].status
        $createdAt = $runs[0].createdAt
        
        Write-Host "运行ID: $runId" -ForegroundColor Green
        Write-Host "状态: $status" -ForegroundColor $(if ($status -eq "completed") { "Green" } else { "Yellow" })
        Write-Host "创建时间: $createdAt" -ForegroundColor Gray
        
        return $runId
    } else {
        Write-Host "❌ 未找到运行" -ForegroundColor Red
        return $null
    }
}

# 函数：等待运行完成
function Wait-ForRunCompletion {
    param($RunId, $MaxWait = 1800)  # 30分钟
    
    Write-Host "[步骤3] 等待运行完成..." -ForegroundColor Yellow
    Write-Host "运行ID: $RunId" -ForegroundColor Gray
    Write-Host "最大等待时间: $MaxWait 秒" -ForegroundColor Gray
    
    $elapsed = 0
    $checkInterval = 10
    
    while ($elapsed -lt $MaxWait) {
        $runInfo = gh run view $RunId --repo=$REPO --json status,conclusion 2>&1 | ConvertFrom-Json
        
        if ($runInfo.status -eq "completed") {
            $conclusion = $runInfo.conclusion
            Write-Host "运行完成，结果: $conclusion" -ForegroundColor $(if ($conclusion -eq "success") { "Green" } else { "Red" })
            return $conclusion
        }
        
        Write-Host "  状态: $($runInfo.status) (已等待 ${elapsed}s)" -ForegroundColor Gray
        Start-Sleep -Seconds $checkInterval
        $elapsed += $checkInterval
    }
    
    Write-Host "⚠️ 超时，继续处理..." -ForegroundColor Yellow
    return "timeout"
}

# 函数：下载日志
function Download-Logs {
    param($RunId)
    
    Write-Host "[步骤4] 下载日志..." -ForegroundColor Yellow
    
    $logDir = Join-Path $LOG_DIR "run-$RunId"
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    
    Write-Host "日志目录: $logDir" -ForegroundColor Gray
    
    # 获取所有作业
    $jobs = gh run view $RunId --repo=$REPO --json jobs --jq '.jobs[] | .name' 2>&1 | ConvertFrom-Json
    
    foreach ($job in $jobs) {
        if (-not $job) { continue }
        Write-Host "  下载: $job" -ForegroundColor Gray
        
        # 清理文件名
        $safeJobName = $job -replace '[<>:"/\\|?*$]', '_'
        $logFile = Join-Path $logDir "$safeJobName.log"
        
        gh run view $RunId --repo=$REPO --log --job=$job 2>&1 | Out-File -FilePath $logFile -Encoding UTF8
    }
    
    return $logDir
}

# 函数：分析错误
function Analyze-Errors {
    param($LogDir)
    
    Write-Host "[步骤5] 分析错误..." -ForegroundColor Yellow
    
    $errors = @()
    
    # 查找前端测试日志
    $frontendLogs = Get-ChildItem $LogDir -Filter "*frontend*.log" -ErrorAction SilentlyContinue
    $frontendLogs += Get-ChildItem $LogDir -Filter "*Frontend*.log" -ErrorAction SilentlyContinue
    
    foreach ($logFile in $frontendLogs) {
        Write-Host "分析: $($logFile.Name)" -ForegroundColor Gray
        $content = Get-Content $logFile.FullName -Raw -ErrorAction SilentlyContinue
        
        if (-not $content) { continue }
        
        # 提取TypeScript错误
        $pattern = '\./(src/[^:]+):(\d+):(\d+)\s+Type error:\s*(.+)'
        $matches = [regex]::Matches($content, $pattern)
        
        foreach ($match in $matches) {
            $errors += @{
                Type = "typescript"
                File = $match.Groups[1].Value
                Line = [int]$match.Groups[2].Value
                Column = [int]$match.Groups[3].Value
                Message = $match.Groups[4].Value.Trim()
                LogFile = $logFile.Name
            }
        }
        
        # 提取构建错误
        if ($content -match "Failed to compile") {
            $errors += @{
                Type = "build"
                Message = "前端构建失败"
                LogFile = $logFile.Name
            }
        }
    }
    
    if ($errors.Count -gt 0) {
        Write-Host "发现 $($errors.Count) 个错误:" -ForegroundColor Red
        foreach ($error in $errors) {
            if ($error.File) {
                Write-Host "  - $($error.File):$($error.Line) - $($error.Message)" -ForegroundColor Yellow
            } else {
                Write-Host "  - $($error.Message)" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "✅ 未发现错误" -ForegroundColor Green
    }
    
    return $errors
}

# 函数：自动修复
function Auto-FixErrors {
    param($Errors)
    
    Write-Host "[步骤6] 自动修复错误..." -ForegroundColor Yellow
    
    if ($Errors.Count -eq 0) {
        Write-Host "✅ 无需修复" -ForegroundColor Green
        return $false
    }
    
    $fixed = $false
    
    foreach ($error in $Errors) {
        if ($error.Type -ne "typescript") { continue }
        
        $filePath = Join-Path "web-ui" $error.File
        $fullPath = Join-Path $PROJECT_DIR $filePath
        
        if (-not (Test-Path $fullPath)) {
            Write-Host "⚠️ 文件不存在: $filePath" -ForegroundColor Yellow
            continue
        }
        
        Write-Host "修复: $($error.File):$($error.Line)" -ForegroundColor Cyan
        Write-Host "  错误: $($error.Message)" -ForegroundColor Gray
        
        $content = Get-Content $fullPath -Raw
        
        # 修复1: display_name
        if ($error.Message -match "display_name.*does not exist") {
            if ($error.File -eq "src/lib/api/auth.ts") {
                if ($content -notmatch "display_name") {
                    $content = $content -replace '(session_id\?: string)', "`$1`n  display_name?: string"
                    Set-Content -Path $fullPath -Value $content -NoNewline
                    Write-Host "  ✅ 已添加display_name" -ForegroundColor Green
                    $fixed = $true
                }
            }
        }
        
        # 修复2: 缺失导入
        if ($error.Message -match "Cannot find name '(\w+)'") {
            $missingName = $matches[1]
            if ($content -match "from ['\`"]lucide-react['\`"]") {
                if ($content -notmatch $missingName) {
                    # 查找导入行并添加
                    $importPattern = "(import\s*\{[^}]+)\}\s*from\s*['\`"]lucide-react['\`"]"
                    if ($content -match $importPattern) {
                        $importBlock = $matches[1]
                        $newImport = "$importBlock,`n  $missingName} from 'lucide-react'"
                        $content = $content -replace $importPattern, $newImport
                        Set-Content -Path $fullPath -Value $content -NoNewline
                        Write-Host "  ✅ 已添加导入: $missingName" -ForegroundColor Green
                        $fixed = $true
                    }
                }
            }
        }
        
        # 修复3: 类型不匹配
        if ($error.Message -match "is not assignable to type") {
            # 移除错误的else分支
            $lines = Get-Content $fullPath
            for ($i = 0; $i -lt $lines.Count; $i++) {
                if ($lines[$i] -match 'stat\.icon.*span') {
                    # 查找并修复if-else块
                    $newContent = $content -replace '(?s)\{IconComponent \? \(.*?\) : \(.*?<span.*?stat\.icon.*?</span>.*?\)\}', '{IconComponent && (`n                      <IconComponent className="w-12 h-12" />`n                    )}'
                    if ($newContent -ne $content) {
                        Set-Content -Path $fullPath -Value $newContent -NoNewline
                        Write-Host "  ✅ 已修复类型错误" -ForegroundColor Green
                        $fixed = $true
                        break
                    }
                }
            }
        }
    }
    
    return $fixed
}

# 函数：验证修复
function Verify-Fixes {
    Write-Host "[步骤7] 验证修复..." -ForegroundColor Yellow
    
    Push-Location (Join-Path $PROJECT_DIR "web-ui")
    
    try {
        $result = npx tsc --noEmit 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ 类型检查仍有错误" -ForegroundColor Red
            $result | Select-String -Pattern "error" | Select-Object -First 5 | ForEach-Object { Write-Host $_ -ForegroundColor Red }
            return $false
        }
        
        Write-Host "✅ 类型检查通过" -ForegroundColor Green
        return $true
    }
    finally {
        Pop-Location
    }
}

# 函数：提交并推送
function Commit-AndPush {
    Write-Host "[步骤8] 提交并推送..." -ForegroundColor Yellow
    
    # 检查是否有更改
    $status = git status --short
    if (-not $status) {
        Write-Host "⚠️ 没有更改需要提交" -ForegroundColor Yellow
        return $false
    }
    
    Write-Host "更改的文件:" -ForegroundColor Gray
    $status | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    
    git add -A
    
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $commitMessage = "fix: Auto-fix CI/CD errors`n`n- Auto-fixed from GitHub Actions`n- Fix time: $timestamp"
    
    git commit -m $commitMessage
    
    Write-Host "推送到远程..." -ForegroundColor Gray
    git push origin main
    
    Write-Host "✅ 已提交并推送" -ForegroundColor Green
    return $true
}

# 主循环
function Main {
    $iteration = 0
    
    while ($iteration -lt $MAX_ITERATIONS) {
        $iteration++
        
        Write-Host ""
        Write-Host "==========================================" -ForegroundColor Cyan
        Write-Host "迭代 $iteration / $MAX_ITERATIONS" -ForegroundColor Cyan
        Write-Host "==========================================" -ForegroundColor Cyan
        Write-Host ""
        
        # 步骤1: 启动工作流
        if (-not (Start-Workflow)) {
            Write-Host "跳过本次迭代" -ForegroundColor Yellow
            continue
        }
        
        # 步骤2: 获取运行ID
        $runId = Get-LatestRunId
        if (-not $runId) {
            Write-Host "跳过本次迭代" -ForegroundColor Yellow
            continue
        }
        
        # 步骤3: 等待完成
        $conclusion = Wait-ForRunCompletion $runId
        
        # 步骤4: 下载日志
        $logDir = Download-Logs $runId
        
        # 步骤5: 分析错误
        $errors = Analyze-Errors $logDir
        
        # 如果成功，退出循环
        if ($conclusion -eq "success" -and $errors.Count -eq 0) {
            Write-Host ""
            Write-Host "==========================================" -ForegroundColor Green
            Write-Host "✅ 所有测试通过！" -ForegroundColor Green
            Write-Host "==========================================" -ForegroundColor Green
            break
        }
        
        # 步骤6: 自动修复
        $fixed = Auto-FixErrors $errors
        
        if (-not $fixed) {
            Write-Host "⚠️ 无法自动修复，需要手动修复" -ForegroundColor Yellow
            Write-Host "日志目录: $logDir" -ForegroundColor Cyan
            break
        }
        
        # 步骤7: 验证修复
        if (-not (Verify-Fixes)) {
            Write-Host "❌ 修复验证失败" -ForegroundColor Red
            break
        }
        
        # 步骤8: 提交并推送
        if (Commit-AndPush) {
            Write-Host "等待新工作流启动..." -ForegroundColor Yellow
            Start-Sleep -Seconds 10
        } else {
            Write-Host "无需提交，继续下一轮" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "循环完成" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "总迭代次数: $iteration" -ForegroundColor Gray
    Write-Host "日志目录: $LOG_DIR" -ForegroundColor Gray
}

Main






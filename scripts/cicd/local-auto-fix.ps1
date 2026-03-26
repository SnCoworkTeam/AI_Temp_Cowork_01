# 本地自动修复系统（Windows PowerShell版本）
# 从GitHub Actions获取错误并自动修复

$ErrorActionPreference = "Stop"

$PROJECT_DIR = $PSScriptRoot + "\..\.."
$REPO = "PMLiuyubin/enterprise-ai-platform"
$WORKFLOW = "deploy.yml"
$LOG_DIR = "$env:TEMP\github-errors"

# 创建日志目录
New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null

Set-Location $PROJECT_DIR

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "本地自动修复系统" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 函数：获取最新失败运行
function Get-LatestFailedRun {
    $runs = gh run list --workflow=$WORKFLOW --repo=$REPO --limit 10 --json databaseId,status,conclusion | ConvertFrom-Json
    $failed = $runs | Where-Object { $_.conclusion -eq "failure" } | Select-Object -First 1
    return $failed.databaseId
}

# 函数：下载日志
function Download-Logs {
    param($RunId)
    
    $logDir = Join-Path $LOG_DIR "run-$RunId"
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    
    Write-Host "下载运行 $RunId 的日志..." -ForegroundColor Yellow
    
    # 获取所有作业
    $jobs = gh run view $RunId --repo=$REPO --json jobs --jq '.jobs[] | .name' | ConvertFrom-Json
    
    foreach ($job in $jobs) {
        Write-Host "  下载: $job" -ForegroundColor Gray
        gh run view $RunId --repo=$REPO --log --job=$job | Out-File -FilePath (Join-Path $logDir "$job.log") -Encoding UTF8
    }
    
    return $logDir
}

# 函数：提取TypeScript错误
function Extract-TypeScriptErrors {
    param($LogFile)
    
    $errors = @()
    $content = Get-Content $LogFile -Raw -ErrorAction SilentlyContinue
    
    if (-not $content) {
        return $errors
    }
    
    # 匹配TypeScript错误模式
    $pattern = '\./(src/[^:]+):(\d+):(\d+)\s+Type error:\s*(.+)'
    $matches = [regex]::Matches($content, $pattern)
    
    foreach ($match in $matches) {
        $errors += @{
            Type = "typescript"
            File = $match.Groups[1].Value
            Line = [int]$match.Groups[2].Value
            Column = [int]$match.Groups[3].Value
            Message = $match.Groups[4].Value.Trim()
        }
    }
    
    return $errors
}

# 函数：自动修复TypeScript错误
function Auto-FixTypeScript {
    param($Errors)
    
    $fixed = $false
    
    foreach ($error in $Errors) {
        $filePath = Join-Path "web-ui" $error.File
        $fullPath = Join-Path $PROJECT_DIR $filePath
        
        if (-not (Test-Path $fullPath)) {
            continue
        }
        
        Write-Host "修复: $($error.File):$($error.Line) - $($error.Message)" -ForegroundColor Yellow
        
        # 修复1: display_name不存在
        if ($error.Message -match "display_name.*does not exist") {
            if ($error.File -eq "src/lib/api/auth.ts") {
                $content = Get-Content $fullPath -Raw
                if ($content -notmatch "display_name") {
                    $content = $content -replace '(session_id\?: string)', "`$1`n  display_name?: string"
                    Set-Content -Path $fullPath -Value $content -NoNewline
                    Write-Host "  ✅ 已添加display_name" -ForegroundColor Green
                    $fixed = $true
                }
            }
        }
        
        # 修复2: 图标未导入
        if ($error.Message -match "Cannot find name '(\w+)'") {
            $missingName = $matches[1]
            $content = Get-Content $fullPath -Raw
            
            # 检查是否从lucide-react导入
            if ($content -match "from ['\`"]lucide-react['\`"]") {
                if ($content -notmatch $missingName) {
                    # 添加到导入列表
                    $importLine = $content | Select-String -Pattern "from ['\`"]lucide-react['\`"]" | Select-Object -First 1
                    if ($importLine) {
                        $newImport = $importLine.Line -replace "}", ",`n  $missingName}"
                        $content = $content -replace [regex]::Escape($importLine.Line), $newImport
                        Set-Content -Path $fullPath -Value $content -NoNewline
                        Write-Host "  ✅ 已添加导入: $missingName" -ForegroundColor Green
                        $fixed = $true
                    }
                }
            }
        }
        
        # 修复3: 类型不匹配（移除错误的else分支）
        if ($error.Message -match "is not assignable to type") {
            $content = Get-Content $fullPath -Raw
            $lines = Get-Content $fullPath
            
            # 查找包含 stat.icon 的span标签
            for ($i = 0; $i -lt $lines.Count; $i++) {
                if ($lines[$i] -match 'stat\.icon.*span') {
                    # 查找对应的if-else块并修复
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
    Write-Host "验证修复..." -ForegroundColor Yellow
    
    Push-Location (Join-Path $PROJECT_DIR "web-ui")
    
    try {
        # 类型检查
        $result = npx tsc --noEmit 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ 类型检查仍有错误" -ForegroundColor Red
            $result | Select-String -Pattern "error" | ForEach-Object { Write-Host $_ -ForegroundColor Red }
            return $false
        }
        
        Write-Host "✅ 类型检查通过" -ForegroundColor Green
        return $true
    }
    finally {
        Pop-Location
    }
}

# 函数：提交修复
function Commit-Fixes {
    Write-Host "提交修复..." -ForegroundColor Yellow
    
    # 检查是否有更改
    $status = git status --short
    if (-not $status) {
        Write-Host "⚠️ 没有更改需要提交" -ForegroundColor Yellow
        return $false
    }
    
    git add -A
    
    $runId = $script:CurrentRunId
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $commitMessage = "fix: Auto-fix CI/CD errors`n`n- Extract errors from GitHub Actions run $runId`n- Auto-apply fixes`n- Fix time: $timestamp"
    
    git commit -m $commitMessage
    
    Write-Host "Pushing to remote..." -ForegroundColor Yellow
    git push origin main
    
    Write-Host "Fixed and pushed successfully" -ForegroundColor Green
    return $true
}

# 主流程
function Main {
    # 1. 获取最新失败运行
    Write-Host "[1/5] 查找最新失败运行..." -ForegroundColor Cyan
    $runId = Get-LatestFailedRun
    
    if (-not $runId) {
        Write-Host "✅ 没有失败的运行" -ForegroundColor Green
        return
    }
    
    $script:CurrentRunId = $runId
    Write-Host "找到失败运行: $runId" -ForegroundColor Yellow
    
    # 2. 下载日志
    Write-Host "[2/5] 下载日志..." -ForegroundColor Cyan
    $logDir = Download-Logs $runId
    
    # 3. 提取错误
    Write-Host "[3/5] 提取并分析错误..." -ForegroundColor Cyan
    $frontendLog = Join-Path $logDir "frontend-test.log"
    $errors = @()
    
    if (Test-Path $frontendLog) {
        $errors = Extract-TypeScriptErrors $frontendLog
        Write-Host "发现 $($errors.Count) 个TypeScript错误" -ForegroundColor Yellow
    }
    
    if ($errors.Count -eq 0) {
        Write-Host "✅ 未发现可自动修复的错误" -ForegroundColor Green
        return
    }
    
    # 4. 应用修复
    Write-Host "[4/5] 应用自动修复..." -ForegroundColor Cyan
    if (-not (Auto-FixTypeScript $errors)) {
        Write-Host "⚠️ 无法自动修复所有错误" -ForegroundColor Yellow
        return
    }
    
    # 5. 验证修复
    Write-Host "[5/5] 验证修复..." -ForegroundColor Cyan
    if (-not (Verify-Fixes)) {
        Write-Host "❌ 修复验证失败" -ForegroundColor Red
        return
    }
    
    # 6. 提交
    if (Commit-Fixes) {
        Write-Host ""
        Write-Host "✅ 修复完成！" -ForegroundColor Green
        Write-Host "查看新运行: https://github.com/$REPO/actions" -ForegroundColor Cyan
    }
}

Main


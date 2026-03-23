# 简化版自动修复循环

$PROJECT_DIR = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$REPO = "PMLiuyubin/enterprise-ai-platform"
$WORKFLOW = "deploy.yml"
$LOG_DIR = "$env:TEMP\github-errors"

Set-Location $PROJECT_DIR
New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "自动修复循环" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤1: 启动工作流
Write-Host "[1/8] 启动工作流..." -ForegroundColor Yellow
gh workflow run $WORKFLOW --field environment=staging --repo=$REPO
if ($LASTEXITCODE -ne 0) {
    Write-Host "启动失败" -ForegroundColor Red
    exit 1
}
Write-Host "工作流已启动，等待5秒..." -ForegroundColor Green
Start-Sleep -Seconds 5

# 步骤2: 获取运行ID
Write-Host "[2/8] 获取最新运行ID..." -ForegroundColor Yellow
$runJson = gh run list --workflow=$WORKFLOW --repo=$REPO --limit 1 --json databaseId,status,conclusion | ConvertFrom-Json
$runId = $runJson.databaseId
$status = $runJson.status

Write-Host "运行ID: $runId" -ForegroundColor Green
Write-Host "状态: $status" -ForegroundColor $(if ($status -eq "completed") { "Green" } else { "Yellow" })

# 步骤3: 等待完成
Write-Host "[3/8] 等待运行完成..." -ForegroundColor Yellow
$maxWait = 1800
$elapsed = 0

while ($elapsed -lt $maxWait) {
    $runInfo = gh run view $runId --repo=$REPO --json status,conclusion | ConvertFrom-Json
    
    if ($runInfo.status -eq "completed") {
        Write-Host "运行完成，结果: $($runInfo.conclusion)" -ForegroundColor $(if ($runInfo.conclusion -eq "success") { "Green" } else { "Red" })
        break
    }
    
    Write-Host "  状态: $($runInfo.status) (${elapsed}s)" -ForegroundColor Gray
    Start-Sleep -Seconds 10
    $elapsed += 10
}

# 步骤4: 下载日志
Write-Host "[4/8] 下载日志..." -ForegroundColor Yellow
$logDir = Join-Path $LOG_DIR "run-$runId"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$jobs = gh run view $runId --repo=$REPO --json jobs --jq '.jobs[] | .name' | ConvertFrom-Json
foreach ($job in $jobs) {
    if ($job) {
        $safeName = $job -replace '[<>:"/\\|?*$]', '_'
        $logFile = Join-Path $logDir "$safeName.log"
        Write-Host "  下载: $job" -ForegroundColor Gray
        gh run view $runId --repo=$REPO --log --job=$job | Out-File -FilePath $logFile -Encoding UTF8
    }
}

# 步骤5: 分析错误
Write-Host "[5/8] 分析错误..." -ForegroundColor Yellow
$frontendLog = Get-ChildItem $logDir -Filter "*frontend*.log" -ErrorAction SilentlyContinue | Select-Object -First 1
$frontendLog += Get-ChildItem $logDir -Filter "*Frontend*.log" -ErrorAction SilentlyContinue | Select-Object -First 1

$hasErrors = $false
if ($frontendLog) {
    $content = Get-Content $frontendLog.FullName -Raw
    if ($content -match "Type error:") {
        Write-Host "发现TypeScript错误" -ForegroundColor Red
        $content | Select-String -Pattern "Type error:" -Context 3 | Select-Object -First 5 | ForEach-Object {
            Write-Host $_ -ForegroundColor Yellow
        }
        $hasErrors = $true
    }
}

# 步骤6: 自动修复
if ($hasErrors) {
    Write-Host "[6/8] 自动修复..." -ForegroundColor Yellow
    
    # 修复display_name
    $authFile = Join-Path $PROJECT_DIR "web-ui\src\lib\api\auth.ts"
    if (Test-Path $authFile) {
        $content = Get-Content $authFile -Raw
        if ($content -notmatch "display_name") {
            $content = $content -replace '(session_id\?: string)', '$1`n  display_name?: string'
            Set-Content -Path $authFile -Value $content -NoNewline
            Write-Host "已添加display_name" -ForegroundColor Green
        }
    }
    
    # 修复Table导入
    $dbFile = Join-Path $PROJECT_DIR "web-ui\src\app\admin\database\overview\page.tsx"
    if (Test-Path $dbFile) {
        $content = Get-Content $dbFile -Raw
        if ($content -match "from ['\`"]lucide-react['\`"]" -and $content -notmatch "Table") {
            $content = $content -replace "(import\s*\{[^}]+)\}\s*from\s*['\`"]lucide-react['\`"]", '$1,`n  Table} from ''lucide-react'''
            Set-Content -Path $dbFile -Value $content -NoNewline
            Write-Host "已添加Table导入" -ForegroundColor Green
        }
    }
    
    # 修复dashboard类型错误
    $dashboardFile = Join-Path $PROJECT_DIR "web-ui\src\app\admin\dashboard\page.tsx"
    if (Test-Path $dashboardFile) {
        $content = Get-Content $dashboardFile -Raw
        if ($content -match "stat\.icon.*span") {
            $lines = Get-Content $dashboardFile
            $newLines = @()
            $skipNext = $false
            
            for ($i = 0; $i -lt $lines.Count; $i++) {
                if ($lines[$i] -match "IconComponent \?") {
                    $newLines += $lines[$i] -replace "\?", "&&"
                    $skipNext = $true
                } elseif ($skipNext -and $lines[$i] -match "stat\.icon") {
                    # 跳过错误的else分支
                    continue
                } elseif ($skipNext -and $lines[$i] -match "</span>") {
                    $skipNext = $false
                    continue
                } else {
                    $newLines += $lines[$i]
                    $skipNext = $false
                }
            }
            Set-Content -Path $dashboardFile -Value ($newLines -join "`n")
            Write-Host "已修复dashboard类型错误" -ForegroundColor Green
        }
    }
} else {
    Write-Host "[6/8] 无需修复" -ForegroundColor Green
}

# 步骤7: 验证修复
Write-Host "[7/8] 验证修复..." -ForegroundColor Yellow
Push-Location (Join-Path $PROJECT_DIR "web-ui")
try {
    $tsResult = npx tsc --noEmit 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "类型检查通过" -ForegroundColor Green
    } else {
        Write-Host "类型检查仍有错误" -ForegroundColor Red
        $tsResult | Select-String -Pattern "error" | Select-Object -First 5
    }
} finally {
    Pop-Location
}

# 步骤8: 提交并推送
Write-Host "[8/8] 提交并推送..." -ForegroundColor Yellow
$gitStatus = git status --short
if ($gitStatus) {
    git add -A
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    git commit -m "fix: Auto-fix CI/CD errors - $timestamp"
    git push origin main
    Write-Host "已提交并推送" -ForegroundColor Green
} else {
    Write-Host "没有更改需要提交" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "完成" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "运行ID: $runId" -ForegroundColor Gray
Write-Host "日志目录: $logDir" -ForegroundColor Gray
$runUrl = "https://github.com/$REPO/actions/runs/$runId"
Write-Host "查看运行: $runUrl" -ForegroundColor Cyan


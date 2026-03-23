# 同步测试文件到服务器
# 通过git push推送到远程，然后在服务器上git pull

param(
    [string]$ConfigFile = "remote.ssh",
    [string]$RemotePath = "/opt/enterprise-ai-platform",
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Continue"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptRoot)
$ConfigPath = Join-Path $ProjectRoot $ConfigFile

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "同步测试文件到服务器" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Push-Location $ProjectRoot

try {
    # 步骤1: 检测测试文件变更
    Write-Host "[1/4] 检测测试文件变更..." -ForegroundColor Yellow
    
    $testFiles = @()
    
    # 获取所有测试相关的变更文件
    $changedFiles = git status --porcelain 2>&1 | ForEach-Object {
        if ($_ -match "^\s*[AM]+\s+(.+)$") {
            $file = $matches[1]
            if ($file -match "test.*\.py$" -or $file -match "tests/") {
                $testFiles += $file
            }
        }
    }
    
    # 获取未跟踪的测试文件
    $untrackedFiles = git ls-files --others --exclude-standard 2>&1 | Where-Object {
        $_ -match "test.*\.py$" -or $_ -match "tests/"
    }
    $testFiles += $untrackedFiles
    
    if ($testFiles.Count -eq 0) {
        Write-Host "没有测试文件需要同步" -ForegroundColor Yellow
        return
    }
    
    Write-Host "发现 $($testFiles.Count) 个测试文件需要同步:" -ForegroundColor Green
    $testFiles | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
    Write-Host ""
    
    if ($DryRun) {
        Write-Host "预览模式，不执行实际操作" -ForegroundColor Yellow
        return
    }
    
    # 步骤2: 添加并提交测试文件
    Write-Host "[2/4] 提交测试文件到Git..." -ForegroundColor Yellow
    
    # 添加所有测试文件
    foreach ($file in $testFiles) {
        git add $file 2>&1 | Out-Null
    }
    
    # 提交
    $commitMessage = "test: 添加/更新测试文件以提升覆盖率 [自动化]"
    $commitResult = git commit -m $commitMessage 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ 测试文件已提交" -ForegroundColor Green
    } else {
        if ($commitResult -match "nothing to commit") {
            Write-Host "没有需要提交的变更" -ForegroundColor Yellow
        } else {
            Write-Host "提交失败: $commitResult" -ForegroundColor Red
        }
    }
    Write-Host ""
    
    # 步骤3: 推送到远程仓库
    Write-Host "[3/4] 推送到远程仓库..." -ForegroundColor Yellow
    
    $currentBranch = git rev-parse --abbrev-ref HEAD
    $pushResult = git push origin $currentBranch 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ 已推送到远程仓库" -ForegroundColor Green
    } else {
        Write-Host "推送失败: $pushResult" -ForegroundColor Red
        Write-Host "继续尝试在服务器上拉取..." -ForegroundColor Yellow
    }
    Write-Host ""
    
    # 步骤4: 在服务器上拉取最新代码
    Write-Host "[4/4] 在服务器上拉取最新代码..." -ForegroundColor Yellow
    
    $SessionScript = Join-Path (Split-Path $ScriptRoot -Parent) "deployment\ssh-session-manager.ps1"
    
    if (-not (Test-Path $SessionScript)) {
        Write-Host "SSH会话管理器未找到，使用直接SSH连接" -ForegroundColor Yellow
        
        $pullCommand = "cd $RemotePath && git pull origin $currentBranch"
        $sshResult = ssh -F $ConfigPath enterprise-ai-server $pullCommand 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ 服务器代码已更新" -ForegroundColor Green
        } else {
            Write-Host "服务器更新失败: $sshResult" -ForegroundColor Red
        }
    } else {
        $pullCommand = "cd $RemotePath && git pull origin $currentBranch 2>&1"
        $output = & powershell -ExecutionPolicy Bypass -File $SessionScript -Action execute -Command $pullCommand
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ 服务器代码已更新" -ForegroundColor Green
            Write-Host $output
        } else {
            Write-Host "服务器更新失败" -ForegroundColor Red
            Write-Host $output
        }
    }
    
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "同步完成" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    
} catch {
    Write-Host "同步过程中出错: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}


# 测试-修复-上传循环自动化脚本
# 运行测试，发现问题，修复代码，上传到服务器，重复直到所有测试通过

param(
    [string]$ConfigFile = "remote.ssh",
    [string]$RemotePath = "/opt/enterprise-ai-platform",
    [switch]$SkipUpload = $false
)

# 导入SSH连接管理器
$sshManagerPath = Join-Path $PSScriptRoot "ssh-manager.ps1"
if (Test-Path $sshManagerPath) {
    . $sshManagerPath
}

# 导入同步脚本
$syncScriptPath = Join-Path $PSScriptRoot "sync-to-server.ps1"
if (Test-Path $syncScriptPath) {
    . $syncScriptPath
}

$ProjectRoot = (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent)
Push-Location $ProjectRoot

try {
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "测试-修复-上传循环自动化" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    
    $maxIterations = 10
    $iteration = 0
    $allTestsPassed = $false
    
    # 获取SSH连接
    $connection = Get-SSHConnection -ConfigFile $ConfigFile
    
    while (-not $allTestsPassed -and $iteration -lt $maxIterations) {
        $iteration++
        Write-Host "------------------------------------------" -ForegroundColor Yellow
        Write-Host "迭代 $iteration/$maxIterations" -ForegroundColor Yellow
        Write-Host "------------------------------------------" -ForegroundColor Yellow
        Write-Host ""
        
        # 步骤1: 运行测试
        Write-Host "[1/4] 在服务器上运行测试..." -ForegroundColor Blue
        
        $testCommand = "cd $RemotePath && bash tests/run-all-tests-server.sh 2>&1"
        $testResult = Invoke-SSHCommand -Connection $connection -Command $testCommand -Timeout 300
        
        if (-not $testResult.Success) {
            Write-Host "无法连接到服务器或执行测试命令" -ForegroundColor Red
            break
        }
        
        $testOutput = $testResult.Output -join "`n"
        
        # 步骤2: 分析测试结果
        Write-Host "[2/4] 分析测试结果..." -ForegroundColor Blue
        
        $failedTests = @()
        $errors = @()
        
        # 解析pytest输出，查找失败的测试
        if ($testOutput -match "FAILED|ERROR") {
            $lines = $testOutput -split "`n"
            foreach ($line in $lines) {
                if ($line -match "FAILED\s+(\S+::\S+)") {
                    $failedTests += $matches[1]
                }
                if ($line -match "ERROR\s+(\S+::\S+)") {
                    $errors += $matches[1]
                }
            }
        }
        
        # 检查是否有测试失败
        if ($testOutput -match "passed.*failed.*error" -or $testOutput -match "FAILED|ERROR") {
            Write-Host "发现测试失败或错误" -ForegroundColor Red
            Write-Host ""
            
            if ($failedTests.Count -gt 0) {
                Write-Host "失败的测试:" -ForegroundColor Yellow
                $failedTests | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
            }
            
            if ($errors.Count -gt 0) {
                Write-Host "错误的测试:" -ForegroundColor Yellow
                $errors | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
            }
            
            # 步骤3: 识别需要修复的文件
            Write-Host ""
            Write-Host "[3/4] 识别需要修复的文件..." -ForegroundColor Blue
            
            $filesToFix = @()
            
            # 从错误信息中提取文件路径
            if ($testOutput -match "File.*line\s+(\d+).*in\s+(\S+)") {
                $filesToFix += $matches[2]
            }
            
            # 从导入错误中提取模块路径
            if ($testOutput -match "ModuleNotFoundError.*No module named '(\S+)'") {
                $moduleName = $matches[1]
                Write-Host "缺少模块: $moduleName" -ForegroundColor Yellow
                # 这里可以添加自动修复逻辑
            }
            
            if ($testOutput -match "ImportError.*cannot import name '(\S+)'") {
                $importName = $matches[1]
                Write-Host "导入错误: $importName" -ForegroundColor Yellow
            }
            
            Write-Host ""
            Write-Host "需要手动修复以下问题:" -ForegroundColor Yellow
            Write-Host "1. 检查测试输出中的错误信息" -ForegroundColor White
            Write-Host "2. 修复代码中的问题" -ForegroundColor White
            Write-Host "3. 重新运行此脚本" -ForegroundColor White
            Write-Host ""
            
            if (-not $SkipUpload) {
                Write-Host "[4/4] 等待修复后上传..." -ForegroundColor Blue
                Write-Host "请修复代码后按任意键继续，或按Ctrl+C退出" -ForegroundColor Yellow
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                
                # 上传修复后的文件
                Write-Host "上传修复后的文件..." -ForegroundColor Blue
                & $syncScriptPath -ConfigFile $ConfigFile -RemotePath $RemotePath
            }
            
        } else {
            # 所有测试通过
            Write-Host "所有测试通过！" -ForegroundColor Green
            $allTestsPassed = $true
            
            # 检查覆盖率
            Write-Host ""
            Write-Host "[4/4] 检查测试覆盖率..." -ForegroundColor Blue
            $coverageCommand = "cd $RemotePath && bash tests/check-test-coverage.sh 2>&1"
            $coverageResult = Invoke-SSHCommand -Connection $connection -Command $coverageCommand -Timeout 60
            
            if ($coverageResult.Success) {
                $coverageOutput = $coverageResult.Output -join "`n"
                Write-Host $coverageOutput
            }
        }
        
        Write-Host ""
    }
    
    if ($allTestsPassed) {
        Write-Host "==========================================" -ForegroundColor Green
        Write-Host "所有测试通过，任务完成！" -ForegroundColor Green
        Write-Host "==========================================" -ForegroundColor Green
    } else {
        Write-Host "==========================================" -ForegroundColor Red
        Write-Host "达到最大迭代次数，仍有测试失败" -ForegroundColor Red
        Write-Host "请手动检查并修复问题" -ForegroundColor Red
        Write-Host "==========================================" -ForegroundColor Red
    }
    
} finally {
    Pop-Location
}


# 批量修复所有测试文件中的NameError问题
# 将func_name和class_name替换为硬编码的字符串常量

$ErrorActionPreference = "Stop"

Write-Host "=========================================="
Write-Host "批量修复测试文件NameError"
Write-Host "=========================================="
Write-Host ""

$projectRoot = "E:\enterprise-ai-platform"
$testDirs = @(
    "$projectRoot\knowledge-base\tests\unit",
    "$projectRoot\metadata-service\tests\unit",
    "$projectRoot\database\tests\unit"
)

$totalFixed = 0
$fixedFiles = @()

foreach ($testDir in $testDirs) {
    if (-not (Test-Path $testDir)) {
        Write-Host "跳过不存在的目录: $testDir" -ForegroundColor Yellow
        continue
    }
    
    $testFiles = Get-ChildItem -Path $testDir -Filter "test_*.py" -Recurse
    
    foreach ($file in $testFiles) {
        $content = Get-Content $file.FullName -Raw -Encoding UTF8
        $originalContent = $content
        $fileFixed = $false
        
        # 修复func_name（需要根据测试函数名推断）
        # 模式：pytest.skip(f"无法导入{func_name}: {e}")
        $funcNamePattern = 'pytest\.skip\(f"无法导入\{func_name\}: \{e\}"\)'
        
        # 查找所有func_name使用
        $matches = [regex]::Matches($content, $funcNamePattern)
        
        foreach ($match in $matches) {
            # 获取上下文，查找测试函数名
            $start = [Math]::Max(0, $match.Index - 500)
            $end = [Math]::Min($content.Length, $match.Index + $match.Length + 100)
            $context = $content.Substring($start, $end - $start)
            
            # 查找测试函数定义
            if ($context -match 'def\s+(test_\w+)') {
                $testName = $matches[0].Groups[1].Value
                # 从test_name提取函数名
                if ($testName -match '^test_(.+)$') {
                    $funcName = $matches[0].Groups[1].Value
                    # 移除_initialization后缀
                    if ($funcName -match '^(.+)_initialization$') {
                        $funcName = $matches[0].Groups[1].Value
                    }
                    
                    # 替换
                    $oldStr = $match.Value
                    $newStr = "pytest.skip(f`"无法导入$funcName: {e}`")"
                    $content = $content -replace [regex]::Escape($oldStr), $newStr
                    $fileFixed = $true
                }
            }
        }
        
        # 修复class_name
        $classNamePattern = 'pytest\.skip\(f"无法导入或初始化\{class_name\}: \{e\}"\)'
        $matches = [regex]::Matches($content, $classNamePattern)
        
        foreach ($match in $matches) {
            $start = [Math]::Max(0, $match.Index - 500)
            $end = [Math]::Min($content.Length, $match.Index + $match.Length + 100)
            $context = $content.Substring($start, $end - $start)
            
            if ($context -match 'def\s+(test_\w+)') {
                $testName = $matches[0].Groups[1].Value
                if ($testName -match '^test_(.+)_initialization$') {
                    $className = $matches[0].Groups[1].Value
                    # 转换为类名（首字母大写，驼峰命名）
                    $className = ($className -split '_' | ForEach-Object { 
                        $_.Substring(0,1).ToUpper() + $_.Substring(1).ToLower() 
                    }) -join ''
                    
                    $oldStr = $match.Value
                    $newStr = "pytest.skip(f`"无法导入或初始化$className: {e}`")"
                    $content = $content -replace [regex]::Escape($oldStr), $newStr
                    $fileFixed = $true
                } elseif ($context -match 'from\s+[\w.]+\s+import\s+(\w+)') {
                    $className = $matches[0].Groups[1].Value
                    $oldStr = $match.Value
                    $newStr = "pytest.skip(f`"无法导入或初始化$className: {e}`")"
                    $content = $content -replace [regex]::Escape($oldStr), $newStr
                    $fileFixed = $true
                }
            }
        }
        
        # 修复转义序列
        $content = $content -replace 'src\\', 'src/'
        $content = $content -replace 'src\\core\\', 'src/core/'
        $content = $content -replace 'src\\models\\', 'src/models/'
        $content = $content -replace 'src\\repositories\\', 'src/repositories/'
        
        if ($content -ne $originalContent) {
            Set-Content -Path $file.FullName -Value $content -Encoding UTF8 -NoNewline
            $totalFixed++
            $fixedFiles += $file.Name
            Write-Host "✅ 修复: $($file.Name)" -ForegroundColor Green
        }
    }
}

Write-Host ""
Write-Host "=========================================="
Write-Host "修复完成！"
Write-Host "=========================================="
Write-Host "修复了 $totalFixed 个文件"
Write-Host ""





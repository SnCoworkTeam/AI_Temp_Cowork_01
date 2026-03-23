# 分析 dev、main、test 三个分支的差异，找出最大和最新的文件

Write-Host "=== 分析三个分支的差异 ===" -ForegroundColor Cyan

# 获取所有分支中的文件列表
$branches = @("dev", "main", "test")
$fileInfo = @{}

foreach ($branch in $branches) {
    Write-Host "`n检查分支: $branch" -ForegroundColor Yellow
    git checkout $branch --quiet 2>&1 | Out-Null
    
    # 获取所有文件及其大小和修改时间
    $files = git ls-tree -r --name-only $branch
    foreach ($file in $files) {
        if (Test-Path $file) {
            $fileObj = Get-Item $file -ErrorAction SilentlyContinue
            if ($fileObj) {
                if (-not $fileInfo.ContainsKey($file)) {
                    $fileInfo[$file] = @{
                        Size = 0
                        LastModified = [DateTime]::MinValue
                        Branch = ""
                        Path = $file
                    }
                }
                
                $currentSize = $fileObj.Length
                $currentModified = $fileObj.LastWriteTime
                
                # 保留最大和最新的文件
                $shouldUpdate = $false
                if ($currentSize -gt $fileInfo[$file].Size) {
                    $shouldUpdate = $true
                } elseif ($currentSize -eq $fileInfo[$file].Size -and $currentModified -gt $fileInfo[$file].LastModified) {
                    $shouldUpdate = $true
                }
                
                if ($shouldUpdate) {
                    $fileInfo[$file].Size = $currentSize
                    $fileInfo[$file].LastModified = $currentModified
                    $fileInfo[$file].Branch = $branch
                }
            }
        }
    }
}

# 切换回原分支
git checkout test --quiet 2>&1 | Out-Null

Write-Host "`n=== 文件差异统计 ===" -ForegroundColor Cyan

# 按大小排序，显示最大的文件
Write-Host "`n最大的 20 个文件:" -ForegroundColor Green
$fileInfo.GetEnumerator() | 
    Sort-Object { $_.Value.Size } -Descending | 
    Select-Object -First 20 | 
    ForEach-Object {
        $sizeKB = [math]::Round($_.Value.Size / 1KB, 2)
        $sizeMB = [math]::Round($_.Value.Size / 1MB, 2)
        $sizeStr = if ($sizeMB -gt 1) { "$sizeMB MB" } else { "$sizeKB KB" }
        Write-Host "  [$($_.Value.Branch)] $($_.Key) - $sizeStr" -ForegroundColor White
    }

# 按修改时间排序，显示最新的文件
Write-Host "`n最新的 20 个文件:" -ForegroundColor Green
$fileInfo.GetEnumerator() | 
    Sort-Object { $_.Value.LastModified } -Descending | 
    Select-Object -First 20 | 
    ForEach-Object {
        Write-Host "  [$($_.Value.Branch)] $($_.Key) - $($_.Value.LastModified)" -ForegroundColor White
    }

# 统计每个分支的文件数量
Write-Host "`n=== 分支文件统计 ===" -ForegroundColor Cyan
$branchStats = @{}
foreach ($file in $fileInfo.Values) {
    if (-not $branchStats.ContainsKey($file.Branch)) {
        $branchStats[$file.Branch] = 0
    }
    $branchStats[$file.Branch]++
}

foreach ($branch in $branchStats.Keys) {
    Write-Host "  $branch : $($branchStats[$branch]) 个文件" -ForegroundColor Yellow
}

# 找出三个分支中不同的文件
Write-Host "`n=== 分支差异文件 ===" -ForegroundColor Cyan

# 比较 dev 和 main
Write-Host "`ndev vs main:" -ForegroundColor Yellow
$devMainDiff = git diff --name-status dev main
if ($devMainDiff) {
    $devMainDiff | Select-Object -First 10 | ForEach-Object { Write-Host "  $_" -ForegroundColor White }
} else {
    Write-Host "  无差异" -ForegroundColor Gray
}

# 比较 main 和 test
Write-Host "`nmain vs test:" -ForegroundColor Yellow
$mainTestDiff = git diff --name-status main test
if ($mainTestDiff) {
    $mainTestDiff | Select-Object -First 10 | ForEach-Object { Write-Host "  $_" -ForegroundColor White }
} else {
    Write-Host "  无差异" -ForegroundColor Gray
}

# 比较 dev 和 test
Write-Host "`ndev vs test:" -ForegroundColor Yellow
$devTestDiff = git diff --name-status dev test
if ($devTestDiff) {
    $devTestDiff | Select-Object -First 10 | ForEach-Object { Write-Host "  $_" -ForegroundColor White }
} else {
    Write-Host "  无差异" -ForegroundColor Gray
}

Write-Host "`n=== 分析完成 ===" -ForegroundColor Cyan


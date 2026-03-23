# 比较 dev、main、test 三个分支的差异，保留最大和最新的文件

Write-Host "=== 分析三个分支的差异 ===" -ForegroundColor Cyan

# 保存当前分支
$currentBranch = git branch --show-current
Write-Host "当前分支: $currentBranch" -ForegroundColor Yellow

# 获取所有分支中的文件及其大小和修改时间
$branches = @("dev", "main", "test")
$fileInfo = @{}

foreach ($branch in $branches) {
    Write-Host "`n检查分支: $branch" -ForegroundColor Yellow
    
    # 使用 git show 获取文件信息，避免切换分支
    $files = git ls-tree -r --name-only $branch
    
    foreach ($file in $files) {
        # 跳过 .next 缓存文件
        if ($file -like "web-ui/.next/*") {
            continue
        }
        
        # 获取文件在分支中的大小
        $blobInfo = git ls-tree -r -l $branch -- "$file" | Select-Object -First 1
        if ($blobInfo) {
            $parts = $blobInfo -split '\s+'
            $size = [long]$parts[3]
            
            # 获取文件的最后提交时间
            $lastCommit = git log -1 --format="%ct" $branch -- "$file" 2>$null
            if ($lastCommit) {
                $lastModified = [DateTimeOffset]::FromUnixTimeSeconds([long]$lastCommit).DateTime
            } else {
                $lastModified = [DateTime]::MinValue
            }
            
            if (-not $fileInfo.ContainsKey($file)) {
                $fileInfo[$file] = @{
                    Size = 0
                    LastModified = [DateTime]::MinValue
                    Branch = ""
                    Path = $file
                }
            }
            
            # 保留最大和最新的文件
            $shouldUpdate = $false
            if ($size -gt $fileInfo[$file].Size) {
                $shouldUpdate = $true
            } elseif ($size -eq $fileInfo[$file].Size -and $lastModified -gt $fileInfo[$file].LastModified) {
                $shouldUpdate = $true
            }
            
            if ($shouldUpdate) {
                $fileInfo[$file].Size = $size
                $fileInfo[$file].LastModified = $lastModified
                $fileInfo[$file].Branch = $branch
            }
        }
    }
}

Write-Host "`n=== 文件差异统计 ===" -ForegroundColor Cyan

# 按大小排序，显示最大的文件
Write-Host "`n最大的 30 个文件:" -ForegroundColor Green
$fileInfo.GetEnumerator() | 
    Sort-Object { $_.Value.Size } -Descending | 
    Select-Object -First 30 | 
    ForEach-Object {
        $sizeKB = [math]::Round($_.Value.Size / 1KB, 2)
        $sizeMB = [math]::Round($_.Value.Size / 1MB, 2)
        $sizeStr = if ($sizeMB -gt 1) { "$sizeMB MB" } else { "$sizeKB KB" }
        Write-Host "  [$($_.Value.Branch)] $($_.Key) - $sizeStr" -ForegroundColor White
    }

# 按修改时间排序，显示最新的文件
Write-Host "`n最新的 30 个文件:" -ForegroundColor Green
$fileInfo.GetEnumerator() | 
    Sort-Object { $_.Value.LastModified } -Descending | 
    Select-Object -First 30 | 
    ForEach-Object {
        Write-Host "  [$($_.Value.Branch)] $($_.Key) - $($_.Value.LastModified.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor White
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

# 比较分支差异
Write-Host "`n=== 分支差异文件 ===" -ForegroundColor Cyan

Write-Host "`ndev vs main:" -ForegroundColor Yellow
$devMainDiff = git diff --name-status dev main 2>$null
if ($devMainDiff) {
    $devMainDiff | Select-Object -First 20 | ForEach-Object { Write-Host "  $_" -ForegroundColor White }
    $devMainCount = ($devMainDiff | Measure-Object).Count
    Write-Host "  总计: $devMainCount 个差异文件" -ForegroundColor Gray
} else {
    Write-Host "  无差异" -ForegroundColor Gray
}

Write-Host "`nmain vs test:" -ForegroundColor Yellow
$mainTestDiff = git diff --name-status main test 2>$null
if ($mainTestDiff) {
    $mainTestDiff | Select-Object -First 20 | ForEach-Object { Write-Host "  $_" -ForegroundColor White }
    $mainTestCount = ($mainTestDiff | Measure-Object).Count
    Write-Host "  总计: $mainTestCount 个差异文件" -ForegroundColor Gray
} else {
    Write-Host "  无差异" -ForegroundColor Gray
}

Write-Host "`ndev vs test:" -ForegroundColor Yellow
$devTestDiff = git diff --name-status dev test 2>$null
if ($devTestDiff) {
    $devTestDiff | Select-Object -First 20 | ForEach-Object { Write-Host "  $_" -ForegroundColor White }
    $devTestCount = ($devTestDiff | Measure-Object).Count
    Write-Host "  总计: $devTestCount 个差异文件" -ForegroundColor Gray
} else {
    Write-Host "  无差异" -ForegroundColor Gray
}

# 生成保留文件列表
Write-Host "`n=== 生成保留文件报告 ===" -ForegroundColor Cyan
$reportFile = "branch_analysis_report.txt"
$report = "Branch Analysis Report`r`n"
$report += "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`r`n`r`n"
$report += "=== Branch File Statistics ===`r`n"

foreach ($branch in $branchStats.Keys) {
    $report += "`r`n$branch : $($branchStats[$branch]) files"
}

$report += "`r`n=== Top 50 Largest Files ===`r`n"

$fileInfo.GetEnumerator() | 
    Sort-Object { $_.Value.Size } -Descending | 
    Select-Object -First 50 | 
    ForEach-Object {
        $sizeKB = [math]::Round($_.Value.Size / 1KB, 2)
        $sizeMB = [math]::Round($_.Value.Size / 1MB, 2)
        $sizeStr = if ($sizeMB -gt 1) { "$sizeMB MB" } else { "$sizeKB KB" }
        $report += "`r`n[$($_.Value.Branch)] $($_.Key) - $sizeStr"
    }

$report += "`r`n=== Top 50 Latest Files ===`r`n"

$fileInfo.GetEnumerator() | 
    Sort-Object { $_.Value.LastModified } -Descending | 
    Select-Object -First 50 | 
    ForEach-Object {
        $report += "`r`n[$($_.Value.Branch)] $($_.Key) - $($_.Value.LastModified.ToString('yyyy-MM-dd HH:mm:ss'))"
    }

$report | Out-File -FilePath $reportFile -Encoding UTF8
Write-Host "报告已保存到: $reportFile" -ForegroundColor Green

Write-Host "`n=== 分析完成 ===" -ForegroundColor Cyan


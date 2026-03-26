# Compare dev, main, test branches and find largest and newest files

Write-Host "=== Analyzing branch differences ===" -ForegroundColor Cyan

$currentBranch = git branch --show-current
Write-Host "Current branch: $currentBranch" -ForegroundColor Yellow

$branches = @("dev", "main", "test")
$fileInfo = @{}

foreach ($branch in $branches) {
    Write-Host "`nChecking branch: $branch" -ForegroundColor Yellow
    
    $files = git ls-tree -r --name-only $branch
    
    foreach ($file in $files) {
        # Skip .next cache files
        if ($file -like "web-ui/.next/*") {
            continue
        }
        
        $blobInfo = git ls-tree -r -l $branch -- "$file" | Select-Object -First 1
        if ($blobInfo) {
            $parts = $blobInfo -split '\s+'
            $size = [long]$parts[3]
            
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

Write-Host "`n=== File Statistics ===" -ForegroundColor Cyan

Write-Host "`nTop 30 Largest Files:" -ForegroundColor Green
$fileInfo.GetEnumerator() | 
    Sort-Object { $_.Value.Size } -Descending | 
    Select-Object -First 30 | 
    ForEach-Object {
        $sizeKB = [math]::Round($_.Value.Size / 1KB, 2)
        $sizeMB = [math]::Round($_.Value.Size / 1MB, 2)
        $sizeStr = if ($sizeMB -gt 1) { "$sizeMB MB" } else { "$sizeKB KB" }
        Write-Host "  [$($_.Value.Branch)] $($_.Key) - $sizeStr" -ForegroundColor White
    }

Write-Host "`nTop 30 Latest Files:" -ForegroundColor Green
$fileInfo.GetEnumerator() | 
    Sort-Object { $_.Value.LastModified } -Descending | 
    Select-Object -First 30 | 
    ForEach-Object {
        Write-Host "  [$($_.Value.Branch)] $($_.Key) - $($_.Value.LastModified.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor White
    }

Write-Host "`n=== Branch File Count ===" -ForegroundColor Cyan
$branchStats = @{}
foreach ($file in $fileInfo.Values) {
    if (-not $branchStats.ContainsKey($file.Branch)) {
        $branchStats[$file.Branch] = 0
    }
    $branchStats[$file.Branch]++
}

foreach ($branch in $branchStats.Keys) {
    Write-Host "  $branch : $($branchStats[$branch]) files" -ForegroundColor Yellow
}

Write-Host "`n=== Branch Differences ===" -ForegroundColor Cyan

Write-Host "`ndev vs main:" -ForegroundColor Yellow
$devMainDiff = git diff --name-status dev main 2>$null
if ($devMainDiff) {
    $devMainDiff | Select-Object -First 20 | ForEach-Object { Write-Host "  $_" -ForegroundColor White }
    $devMainCount = ($devMainDiff | Measure-Object).Count
    Write-Host "  Total: $devMainCount different files" -ForegroundColor Gray
} else {
    Write-Host "  No differences" -ForegroundColor Gray
}

Write-Host "`nmain vs test:" -ForegroundColor Yellow
$mainTestDiff = git diff --name-status main test 2>$null
if ($mainTestDiff) {
    $mainTestDiff | Select-Object -First 20 | ForEach-Object { Write-Host "  $_" -ForegroundColor White }
    $mainTestCount = ($mainTestDiff | Measure-Object).Count
    Write-Host "  Total: $mainTestCount different files" -ForegroundColor Gray
} else {
    Write-Host "  No differences" -ForegroundColor Gray
}

Write-Host "`ndev vs test:" -ForegroundColor Yellow
$devTestDiff = git diff --name-status dev test 2>$null
if ($devTestDiff) {
    $devTestDiff | Select-Object -First 20 | ForEach-Object { Write-Host "  $_" -ForegroundColor White }
    $devTestCount = ($devTestDiff | Measure-Object).Count
    Write-Host "  Total: $devTestCount different files" -ForegroundColor Gray
} else {
    Write-Host "  No differences" -ForegroundColor Gray
}

# Generate report
Write-Host "`n=== Generating Report ===" -ForegroundColor Cyan
$reportFile = "branch_analysis_report.txt"
$report = "Branch Analysis Report`r`n"
$report += "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`r`n`r`n"
$report += "=== Branch File Statistics ===`r`n"

foreach ($branch in $branchStats.Keys) {
    $report += "`r`n$branch : $($branchStats[$branch]) files"
}

$report += "`r`n`r`n=== Top 50 Largest Files ===`r`n"

$fileInfo.GetEnumerator() | 
    Sort-Object { $_.Value.Size } -Descending | 
    Select-Object -First 50 | 
    ForEach-Object {
        $sizeKB = [math]::Round($_.Value.Size / 1KB, 2)
        $sizeMB = [math]::Round($_.Value.Size / 1MB, 2)
        $sizeStr = if ($sizeMB -gt 1) { "$sizeMB MB" } else { "$sizeKB KB" }
        $report += "`r`n[$($_.Value.Branch)] $($_.Key) - $sizeStr"
    }

$report += "`r`n`r`n=== Top 50 Latest Files ===`r`n"

$fileInfo.GetEnumerator() | 
    Sort-Object { $_.Value.LastModified } -Descending | 
    Select-Object -First 50 | 
    ForEach-Object {
        $report += "`r`n[$($_.Value.Branch)] $($_.Key) - $($_.Value.LastModified.ToString('yyyy-MM-dd HH:mm:ss'))"
    }

$report | Out-File -FilePath $reportFile -Encoding UTF8
Write-Host "Report saved to: $reportFile" -ForegroundColor Green

Write-Host "`n=== Analysis Complete ===" -ForegroundColor Cyan


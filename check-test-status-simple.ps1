# Check continuous testing system status

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Continuous Testing System Status" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python processes
$pythonProcs = Get-Process python -ErrorAction SilentlyContinue
if ($pythonProcs) {
    Write-Host "[OK] Python process is running" -ForegroundColor Green
    $pythonProcs | ForEach-Object {
        Write-Host "  PID: $($_.Id) | Start Time: $($_.StartTime)" -ForegroundColor Gray
    }
} else {
    Write-Host "[WARN] No Python process detected" -ForegroundColor Yellow
}

Write-Host ""

# Check latest workflow runs
Write-Host "Latest workflow runs:" -ForegroundColor Cyan
try {
    $runs = gh run list --workflow=deploy.yml --limit 3 --json databaseId,status,conclusion,createdAt | ConvertFrom-Json
    
    if ($runs) {
        $runs | ForEach-Object {
            $statusColor = switch ($_.status) {
                "completed" { if ($_.conclusion -eq "success") { "Green" } else { "Red" } }
                "in_progress" { "Yellow" }
                default { "Gray" }
            }
            
            $icon = switch ($_.conclusion) {
                "success" { "[OK]" }
                "failure" { "[FAIL]" }
                "cancelled" { "[CANCEL]" }
                default { "[...]" }
            }
            
            Write-Host "$icon Run ID: $($_.databaseId) | Status: $($_.status) | Result: $($_.conclusion) | Time: $($_.createdAt)" -ForegroundColor $statusColor
        }
    } else {
        Write-Host "[WARN] No runs found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[ERROR] Failed to get runs: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "View detailed logs:" -ForegroundColor Cyan
Write-Host "  gh run view {runId} --log" -ForegroundColor Gray
Write-Host ""
Write-Host "View run list:" -ForegroundColor Cyan
Write-Host "  gh run list --workflow=deploy.yml" -ForegroundColor Gray






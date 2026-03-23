# 修复所有工作流文件中的 upload-artifact@v3

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "修复所有 upload-artifact@v3" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$workflowFiles = @(
    ".github/workflows/test-suite.yml",
    ".github/workflows/feedback.yml",
    ".github/workflows/code-health.yml",
    ".github/workflows/release.yml",
    ".github/workflows/dependency-scan.yml"
)

$fixedFiles = @()

foreach ($file in $workflowFiles) {
    if (Test-Path $file) {
        Write-Host "检查: $file" -ForegroundColor Yellow
        $content = Get-Content $file -Raw
        
        if ($content -match "upload-artifact@v3") {
            Write-Host "  找到 v3，正在修复..." -ForegroundColor Yellow
            $newContent = $content -replace "upload-artifact@v3", "upload-artifact@v4"
            Set-Content -Path $file -Value $newContent -NoNewline
            $fixedFiles += $file
            Write-Host "  ✅ 已修复" -ForegroundColor Green
        } else {
            Write-Host "  ✅ 已经是 v4 或未使用" -ForegroundColor Green
        }
    } else {
        Write-Host "  ⚠️ 文件不存在: $file" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "修复完成" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

if ($fixedFiles.Count -gt 0) {
    Write-Host "已修复的文件:" -ForegroundColor Green
    $fixedFiles | ForEach-Object { Write-Host "  - $_" -ForegroundColor White }
    Write-Host ""
    Write-Host "提交修复:" -ForegroundColor Yellow
    Write-Host "  git add .github/workflows/*.yml" -ForegroundColor White
    Write-Host "  git commit -m 'fix: 更新所有工作流的 upload-artifact 从 v3 到 v4'" -ForegroundColor White
    Write-Host "  git push origin main" -ForegroundColor White
} else {
    Write-Host "✅ 所有文件都已是最新版本" -ForegroundColor Green
}






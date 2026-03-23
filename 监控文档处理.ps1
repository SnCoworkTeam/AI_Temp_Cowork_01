# 监控文档处理进度
param(
    [Parameter(Mandatory=$true)]
    [string]$DocumentId,
    [int]$MaxWaitTime = 600,
    [int]$CheckInterval = 3
)

$BASE_URL = "http://localhost:8004/api"
$startTime = Get-Date

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "监控文档处理进度" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "文档ID: $DocumentId" -ForegroundColor Yellow
Write-Host ""

while ($true) {
    $elapsed = (Get-Date) - $startTime
    
    if ($elapsed.TotalSeconds -gt $MaxWaitTime) {
        Write-Host "`n已达到最大等待时间（$MaxWaitTime秒）" -ForegroundColor Yellow
        break
    }
    
    try {
        # 获取进度
        $progress = Invoke-RestMethod -Uri "$BASE_URL/documents/$DocumentId/progress" -Method Get -TimeoutSec 5
        $stage = $progress.stage
        $progressPercent = $progress.progress_percentage
        $currentStep = $progress.current_step
        $completedSteps = $progress.completed_steps
        $totalSteps = $progress.total_steps
        
        # 获取文档状态
        try {
            $doc = Invoke-RestMethod -Uri "$BASE_URL/documents/$DocumentId" -Method Get -TimeoutSec 5
            $status = $doc.status
            $chunkCount = $doc.total_chunks
        } catch {
            $status = "unknown"
            $chunkCount = 0
        }
        
        Write-Host "[$([math]::Round($elapsed.TotalSeconds, 0))秒] " -NoNewline -ForegroundColor Gray
        Write-Host "阶段: $stage " -NoNewline -ForegroundColor Cyan
        Write-Host "进度: $([math]::Round($progressPercent, 1))% " -NoNewline -ForegroundColor Yellow
        Write-Host "状态: $status " -NoNewline -ForegroundColor Green
        if ($totalSteps -gt 0) {
            Write-Host "($completedSteps/$totalSteps) " -NoNewline -ForegroundColor Gray
        }
        Write-Host "块数: $chunkCount" -ForegroundColor Magenta
        
        if ($status -eq "completed") {
            Write-Host "`n✓ 文档处理完成！" -ForegroundColor Green
            Write-Host "总耗时: $([math]::Round($elapsed.TotalSeconds, 2))秒" -ForegroundColor Green
            break
        } elseif ($status -eq "failed") {
            Write-Host "`n✗ 文档处理失败！" -ForegroundColor Red
            if ($doc.error_message) {
                Write-Host "错误: $($doc.error_message)" -ForegroundColor Red
            }
            break
        }
        
    } catch {
        Write-Host "[$([math]::Round($elapsed.TotalSeconds, 0))秒] 无法获取进度信息" -ForegroundColor Yellow
    }
    
    Start-Sleep -Seconds $CheckInterval
}

Write-Host "`n查看最新日志:" -ForegroundColor Yellow
docker logs enterprise-ai-knowledge-base --tail 50



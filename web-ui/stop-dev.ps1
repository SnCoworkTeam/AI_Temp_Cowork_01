# 停止所有Next.js开发服务器

$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "停止 Web UI 开发服务器" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 查找所有监听3000和3001端口的Node进程
Write-Host "查找运行中的Next.js服务..." -ForegroundColor Yellow

$ports = @(3000, 3001)
$stoppedCount = 0

foreach ($port in $ports) {
    $connections = netstat -ano | findstr ":$port" | findstr "LISTENING"
    
    if ($connections) {
        foreach ($line in $connections) {
            $parts = $line -split '\s+'
            $processId = $parts[-1]
            
            if ($processId -and $processId -ne "0") {
                try {
                    $process = Get-Process -Id $processId -ErrorAction Stop
                    Write-Host "停止进程 $processId (端口 $port) - $($process.ProcessName)" -ForegroundColor Yellow
                    Stop-Process -Id $processId -Force
                    $stoppedCount++
                    Start-Sleep -Milliseconds 500
                } catch {
                    Write-Host "无法停止进程 $processId" -ForegroundColor Red
                }
            }
        }
    }
}

if ($stoppedCount -eq 0) {
    Write-Host "未找到运行中的Next.js服务" -ForegroundColor Gray
} else {
    Write-Host "✅ 已停止 $stoppedCount 个服务实例" -ForegroundColor Green
}

Write-Host ""
Write-Host "等待端口释放..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

# 验证端口是否已释放
$allFree = $true
foreach ($port in $ports) {
    $stillListening = netstat -ano | findstr ":$port" | findstr "LISTENING"
    if ($stillListening) {
        Write-Host "⚠️  端口 $port 仍在监听" -ForegroundColor Yellow
        $allFree = $false
    } else {
        Write-Host "✅ 端口 $port 已释放" -ForegroundColor Green
    }
}

Write-Host ""
if ($allFree) {
    Write-Host "✅ 所有服务已停止" -ForegroundColor Green
} else {
    Write-Host "⚠️  部分端口可能仍在占用，请手动检查" -ForegroundColor Yellow
}


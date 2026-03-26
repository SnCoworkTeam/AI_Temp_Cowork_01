# 快速检查服务状态
$key = "E:\enterprise-ai-platform\enterprise_ai_platform.pem"
$host = "ubuntu@43.143.139.197"

Write-Host "正在连接服务器检查服务状态..." -ForegroundColor Yellow

# 检查所有容器
$result = ssh -i $key -o StrictHostKeyChecking=no -o ConnectTimeout=10 $host "sudo docker ps -a --format '{{.Names}}|{{.Status}}' | grep enterprise" 2>&1

if ($LASTEXITCODE -eq 0 -and $result) {
    Write-Host "`n=== 服务状态 ===" -ForegroundColor Cyan
    $result | ForEach-Object {
        $parts = $_ -split '\|'
        $name = $parts[0]
        $status = $parts[1]
        if ($status -match "Up") {
            Write-Host "✅ $name - $status" -ForegroundColor Green
        } else {
            Write-Host "❌ $name - $status" -ForegroundColor Red
        }
    }
    
    # 统计
    $running = ($result | Select-String "Up").Count
    $total = ($result -split "`n").Count
    Write-Host "`n运行中: $running / $total" -ForegroundColor $(if ($running -eq $total) { "Green" } else { "Yellow" })
} else {
    Write-Host "无法连接到服务器或获取服务状态" -ForegroundColor Red
    Write-Host "错误: $result" -ForegroundColor Red
}


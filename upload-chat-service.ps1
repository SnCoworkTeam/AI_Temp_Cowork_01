# Chat Service 代码上传脚本
# 使用方法: .\upload-chat-service.ps1

$server = "root@43.143.139.197"
$keyPath = "enterprise_ai_platform.pem"
$remoteBase = "/root/enterprise-ai-platform"

# 需要上传的文件列表
$files = @(
    "chat-service/src/main.py",
    "chat-service/src/routes/chat.py",
    "chat-service/src/routes/server_assistant.py",
    "chat-service/src/services/ai_service.py",
    "chat-service/src/services/server_assistant_service.py",
    "chat-service/src/config.py",
    "chat-service/static/index.html"
)

Write-Host "开始上传 Chat Service 代码..." -ForegroundColor Green

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "上传: $file" -ForegroundColor Yellow
        $remotePath = "$remoteBase/$file"
        $remoteDir = Split-Path $remotePath -Parent
        
        # 创建远程目录
        ssh -i $keyPath $server "mkdir -p $remoteDir"
        
        # 上传文件
        scp -i $keyPath $file "$server`:$remotePath"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ 成功" -ForegroundColor Green
        } else {
            Write-Host "  ✗ 失败" -ForegroundColor Red
        }
    } else {
        Write-Host "文件不存在: $file" -ForegroundColor Red
    }
}

Write-Host "`n上传完成！正在重启服务..." -ForegroundColor Green
ssh -i $keyPath $server "cd $remoteBase && docker compose restart chat-service"

Write-Host "完成！" -ForegroundColor Green



# 快速上传修复后的菜单文件
$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"
$SERVER_PATH = "/opt/enterprise-ai-platform"

Write-Host "上传修复后的菜单文件..." -ForegroundColor Green

# 检查密钥
if (-not (Test-Path $SSH_KEY)) {
    $SSH_KEY = "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem"
}

# 上传Sidebar.tsx
Write-Host "`n上传 Sidebar.tsx..." -ForegroundColor Cyan
scp -i $SSH_KEY -o StrictHostKeyChecking=no "web-ui/src/components/Layout/Sidebar.tsx" "${SERVER}:${SERVER_PATH}/web-ui/src/components/Layout/" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  OK" -ForegroundColor Green
} else {
    Write-Host "  失败" -ForegroundColor Red
}

Write-Host "`n完成！" -ForegroundColor Green


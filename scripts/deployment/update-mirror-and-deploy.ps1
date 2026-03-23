# PowerShell 脚本：更新镜像源为腾讯云并部署服务
# 使用方法: 在服务器上执行此脚本

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "步骤1: 修改镜像源为腾讯云" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

Set-Location /opt/enterprise-ai-platform

# 修改所有 Dockerfile 中的镜像源
Write-Host "正在更新 mcp-gateway/Dockerfile..." -ForegroundColor Yellow
(Get-Content mcp-gateway/Dockerfile) -replace 'pypi.tuna.tsinghua.edu.cn', 'mirrors.cloud.tencent.com' | Set-Content mcp-gateway/Dockerfile

Write-Host "正在更新 workflow-engine/Dockerfile..." -ForegroundColor Yellow
(Get-Content workflow-engine/Dockerfile) -replace 'pypi.tuna.tsinghua.edu.cn', 'mirrors.cloud.tencent.com' | Set-Content workflow-engine/Dockerfile

Write-Host "正在更新 auth-service/Dockerfile..." -ForegroundColor Yellow
(Get-Content auth-service/Dockerfile) -replace 'pypi.tuna.tsinghua.edu.cn', 'mirrors.cloud.tencent.com' | Set-Content auth-service/Dockerfile

Write-Host "正在更新 knowledge-base/Dockerfile..." -ForegroundColor Yellow
(Get-Content knowledge-base/Dockerfile) -replace 'pypi.tuna.tsinghua.edu.cn', 'mirrors.cloud.tencent.com' | Set-Content knowledge-base/Dockerfile

Write-Host "正在更新 metadata-service/Dockerfile..." -ForegroundColor Yellow
(Get-Content metadata-service/Dockerfile) -replace 'pypi.tuna.tsinghua.edu.cn', 'mirrors.cloud.tencent.com' | Set-Content metadata-service/Dockerfile

# 验证修改
Write-Host ""
Write-Host "验证修改结果:" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Gray
$result = Select-String -Path mcp-gateway/Dockerfile -Pattern "mirrors.cloud.tencent.com" | Select-Object -First 1
if ($result) {
    Write-Host $result.Line
} else {
    Write-Host "未找到腾讯云镜像源配置" -ForegroundColor Yellow
}
Write-Host "----------------------------------------" -ForegroundColor Gray

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "步骤2: 构建并启动所有服务" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 构建并启动服务
docker compose -f docker-compose.prod.yml up -d --build

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "部署完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "使用以下命令查看服务状态:" -ForegroundColor Cyan
Write-Host "  docker compose -f docker-compose.prod.yml ps" -ForegroundColor White
Write-Host "使用以下命令查看日志:" -ForegroundColor Cyan
Write-Host "  docker compose -f docker-compose.prod.yml logs -f" -ForegroundColor White
Write-Host "==========================================" -ForegroundColor Green


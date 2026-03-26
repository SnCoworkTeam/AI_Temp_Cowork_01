# 上传内存优化修复
$ErrorActionPreference = "Stop"

Write-Host "正在上传文档处理内存优化修复..." -ForegroundColor Green

# 上传修复的文件
scp -i enterprise_ai_platform.pem `
    knowledge-base/src/services/document_service.py `
    ubuntu@43.143.139.197:/opt/enterprise-ai-platform/knowledge-base/src/services/

Write-Host "文件上传完成" -ForegroundColor Green

# 重启知识库服务
Write-Host "正在重启知识库服务..." -ForegroundColor Yellow
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197 "cd /opt/enterprise-ai-platform && sudo docker restart enterprise-ai-knowledge-base"

Write-Host "等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# 检查服务状态
Write-Host "检查服务状态..." -ForegroundColor Yellow
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197 "cd /opt/enterprise-ai-platform && sudo docker ps --filter name=enterprise-ai-knowledge-base"

# 检查内存使用
Write-Host "`n检查内存使用..." -ForegroundColor Yellow
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197 "free -h"

Write-Host "`n内存优化部署完成!" -ForegroundColor Green
Write-Host "批处理大小: 50 chunks per batch" -ForegroundColor Cyan
Write-Host "预计内存节省: 70-80%" -ForegroundColor Cyan

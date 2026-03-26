# 上传搜索功能修复到服务器
$ErrorActionPreference = "Stop"

Write-Host "正在上传知识库搜索功能修复..." -ForegroundColor Green

# 上传修复的文件
scp -i enterprise_ai_platform.pem `
    knowledge-base/src/models/document_models.py `
    ubuntu@43.143.139.197:/opt/enterprise-ai-platform/knowledge-base/src/models/

scp -i enterprise_ai_platform.pem `
    knowledge-base/src/routes/search.py `
    ubuntu@43.143.139.197:/opt/enterprise-ai-platform/knowledge-base/src/routes/

Write-Host "文件上传完成" -ForegroundColor Green

# 重启知识库服务
Write-Host "正在重启知识库服务..." -ForegroundColor Yellow
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197 "cd /opt/enterprise-ai-platform && sudo docker restart enterprise-ai-knowledge-base"

Write-Host "等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 检查服务状态
Write-Host "检查服务状态..." -ForegroundColor Yellow
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197 "cd /opt/enterprise-ai-platform && sudo docker ps --filter name=enterprise-ai-knowledge-base"

Write-Host "`n修复部署完成!" -ForegroundColor Green

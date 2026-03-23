@echo off
chcp 65001 >nul
echo 正在查看知识库服务日志...
echo.

ssh -i enterprise_ai_platform.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@43.143.139.197 "docker logs enterprise-ai-knowledge-base --tail 200"

echo.
echo 按任意键退出...
pause >nul


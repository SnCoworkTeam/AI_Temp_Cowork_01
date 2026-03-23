@echo off
chcp 65001 >nul
echo ==========================================
echo 测试覆盖率提升 - 命令执行助手
echo ==========================================
echo.
echo 注意: 这些命令需要在原生PowerShell中执行
echo 请按照 COMMAND_EXECUTION_LIST.md 中的步骤执行
echo.
echo 当前步骤: 提交auth-service测试文件
echo.
pause

cd /d "%~dp0"

echo 执行git add...
git add auth-service/tests/unit/test_*.py

echo 执行git commit...
git commit -m "test: 添加auth-service测试文件以提升覆盖率"

echo 执行git push...
git push origin main

echo.
echo ==========================================
echo 下一步: 在服务器上拉取代码
echo 执行命令:
echo ssh -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server "cd /opt/enterprise-ai-platform; timeout 10 git pull origin main"
echo ==========================================
pause


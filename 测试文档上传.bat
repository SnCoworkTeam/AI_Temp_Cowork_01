@echo off
chcp 65001 >nul
echo 正在启动文档上传测试...
echo.

powershell -ExecutionPolicy Bypass -File "测试文档上传.ps1"

pause


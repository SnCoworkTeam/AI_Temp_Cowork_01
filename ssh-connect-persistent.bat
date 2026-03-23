@echo off
REM SSH持久化连接启动脚本 (Windows批处理)
powershell.exe -ExecutionPolicy Bypass -File "%~dp0ssh-connect-persistent.ps1"
pause


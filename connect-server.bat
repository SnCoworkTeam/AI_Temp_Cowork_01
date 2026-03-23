@echo off
REM 使用 remote.ssh 配置连接服务器
REM 使用方法: connect-server.bat

powershell.exe -ExecutionPolicy Bypass -File "%~dp0connect-server.ps1" %*


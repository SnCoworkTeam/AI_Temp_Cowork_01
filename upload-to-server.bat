@echo off
REM 直接上传文件到服务器
REM 使用方法: upload-to-server.bat

powershell.exe -ExecutionPolicy Bypass -File "%~dp0upload-to-server.ps1" %*


@echo off
REM 快速同步脚本 - Windows 批处理版本
REM 使用方法: sync.bat
REM 优先使用 PowerShell 7，如果不存在则使用 PowerShell 5.1

REM 检查 PowerShell 7 是否存在
if exist "%ProgramFiles%\PowerShell\7\pwsh.exe" (
    "%ProgramFiles%\PowerShell\7\pwsh.exe" -ExecutionPolicy Bypass -File "%~dp0scripts\deployment\sync-to-server.ps1" %*
) else if exist "%ProgramFiles(x86)%\PowerShell\7\pwsh.exe" (
    "%ProgramFiles(x86)%\PowerShell\7\pwsh.exe" -ExecutionPolicy Bypass -File "%~dp0scripts\deployment\sync-to-server.ps1" %*
) else (
    REM 使用 Windows PowerShell 5.1
    powershell.exe -ExecutionPolicy Bypass -File "%~dp0scripts\deployment\sync-to-server.ps1" %*
)


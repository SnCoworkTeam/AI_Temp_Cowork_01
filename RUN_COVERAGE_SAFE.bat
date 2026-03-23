@echo off
chcp 65001 >nul
REM 安全运行覆盖率提升循环，带超时保护

cd /d "%~dp0"

echo ==========================================
echo 启动测试覆盖率提升循环（安全模式）
echo ==========================================
echo.

REM 使用PowerShell执行，设置超时
pwsh -ExecutionPolicy Bypass -Command ^
"$job = Start-Job -ScriptBlock { & pwsh -ExecutionPolicy Bypass -File '%~dp0scripts\test-coverage\coverage-improvement-loop.ps1' }; ^
$result = Wait-Job $job -Timeout 300; ^
if ($result) { Receive-Job $job | Write-Host; Remove-Job $job } else { Write-Host '警告: 脚本超时，可能卡住' -ForegroundColor Yellow; Stop-Job $job; Remove-Job $job }"

pause


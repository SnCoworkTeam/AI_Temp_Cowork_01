# SSH持久化连接启动脚本
# 快速启动交互式SSH连接管理器

$ScriptPath = Join-Path $PSScriptRoot "scripts\deployment\ssh-persistent.ps1"

if (Test-Path $ScriptPath) {
    & $ScriptPath -Action connect -Interactive
} else {
    Write-Host "错误: 找不到 ssh-persistent.ps1 脚本" -ForegroundColor Red
    Write-Host "路径: $ScriptPath" -ForegroundColor Yellow
    exit 1
}


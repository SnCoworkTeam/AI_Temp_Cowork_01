# 从 Git 拉取 OpenCode 源码到本地
# 用法: .\scripts\clone-opencode.ps1 [目标目录]
# 默认克隆到项目根目录下的 opencode-src

$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/anomalyco/opencode.git"
$Branch = if ($env:OPENCODE_BRANCH) { $env:OPENCODE_BRANCH } else { "dev" }

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDir
$Dest = if ($args[0]) { $args[0] } else { Join-Path $Root "opencode-src" }

if (Test-Path $Dest) {
    Write-Host "目录已存在: $Dest"
    Write-Host "进入目录并执行 git pull..."
    Set-Location $Dest
    git fetch origin
    git checkout $Branch 2>$null; if (-not $?) { }
    git pull origin $Branch
    Write-Host "已更新。"
    exit 0
}

Write-Host "正在克隆 OpenCode 到: $Dest"
git clone --depth 1 --branch $Branch $RepoUrl $Dest
Write-Host "克隆完成。进入目录: cd $Dest"

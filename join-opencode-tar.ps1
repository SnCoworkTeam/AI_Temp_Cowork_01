# 在服务器上将拆分的两个包合并为一个 .tar（本文件夹内执行）
# 用法: .\join-opencode-tar.ps1
# 合并后再执行 load-and-run.ps1 加载镜像

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$Part1 = "enterprise-ai-opencode.tar.part1"
$Part2 = "enterprise-ai-opencode.tar.part2"
$Out = "enterprise-ai-opencode.tar"

if (-not (Test-Path $Part1) -or -not (Test-Path $Part2)) {
    Write-Host "ERROR: 未找到 $Part1 或 $Part2，请先上传两个分卷到本目录。" -ForegroundColor Red
    exit 1
}

Write-Host "正在合并为 $Out ..."
[System.IO.File]::WriteAllBytes($Out, [System.IO.File]::ReadAllBytes($Part1) + [System.IO.File]::ReadAllBytes($Part2))
Write-Host "合并完成。可执行 .\load-and-run.ps1 加载镜像并启动。" -ForegroundColor Green

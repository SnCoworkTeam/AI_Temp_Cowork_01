# 将 enterprise-ai-opencode.tar 拆成两个包，便于上传（如 U 盘/大小限制）
# 用法: 在项目根目录执行 .\scripts\split-opencode-tar.ps1
# 输出: opencode-server-export/ 下 enterprise-ai-opencode.tar.part1 与 .part2
# 服务器上先运行该文件夹内的 join-opencode-tar 再 docker load

$ErrorActionPreference = "Stop"
$Root = if (Test-Path "opencode-server-export") { $PWD } else { Split-Path -Parent (Split-Path -Parent $PSScriptRoot) }
Set-Location $Root

$ExportDir = Join-Path $Root "opencode-server-export"
$TarPath = Join-Path $ExportDir "enterprise-ai-opencode.tar"

if (-not (Test-Path $TarPath)) {
    Write-Host "ERROR: 未找到 $TarPath，请先执行导出镜像（或 export-opencode-for-server.ps1）。" -ForegroundColor Red
    exit 1
}

$len = (Get-Item $TarPath).Length
$half = [math]::Floor($len / 2)
Write-Host "文件大小: $([math]::Round($len/1MB, 2)) MB，拆成两卷各约 $([math]::Round($half/1MB, 2)) MB"

$part1 = Join-Path $ExportDir "enterprise-ai-opencode.tar.part1"
$part2 = Join-Path $ExportDir "enterprise-ai-opencode.tar.part2"

$fs = [System.IO.File]::OpenRead($TarPath)
try {
    $buf = New-Object byte[] $half
    [void]$fs.Read($buf, 0, $half)
    [System.IO.File]::WriteAllBytes($part1, $buf)
    Write-Host "已生成: enterprise-ai-opencode.tar.part1"

    $remain = $len - $half
    $buf2 = New-Object byte[] $remain
    [void]$fs.Read($buf2, 0, $remain)
    [System.IO.File]::WriteAllBytes($part2, $buf2)
    Write-Host "已生成: enterprise-ai-opencode.tar.part2"
} finally {
    $fs.Close()
}

# 可选：删除原 tar 以节省空间（如需保留原包可注释下一行）
# Remove-Item $TarPath -Force
Write-Host "`n完成。请将 opencode-server-export 文件夹上传到服务器，在服务器上先执行 join-opencode-tar 再 load-and-run。" -ForegroundColor Green

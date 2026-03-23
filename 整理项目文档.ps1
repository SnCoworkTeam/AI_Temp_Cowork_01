# 整理项目文档脚本
# 将文档文件分类移动到docs目录下

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "整理项目文档文件" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 创建目录结构
$dirs = @(
    "docs\troubleshooting",
    "docs\deployment\scripts",
    "docs\deployment\commands",
    "docs\quick-start"
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Host "Created: $dir" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Moving files..." -ForegroundColor Yellow

# 移动故障排查文档
$troubleshootingPatterns = @(
    "修复*.txt",
    "排查*.txt",
    "检查*.txt",
    "验证*.txt",
    "问题*.md",
    "Docker网络问题解决方案.md",
    "依赖版本修复说明.md"
)

foreach ($pattern in $troubleshootingPatterns) {
    Get-ChildItem -Path . -Filter $pattern -File -ErrorAction SilentlyContinue | ForEach-Object {
        Move-Item -Path $_.FullName -Destination "docs\troubleshooting\" -Force -ErrorAction SilentlyContinue
        Write-Host "  Moved: $($_.Name) -> troubleshooting\" -ForegroundColor Gray
    }
}

# 移动部署命令文档
$deploymentCommandPatterns = @(
    "启动*.txt",
    "快速*.txt",
    "正确*.txt",
    "强制*.txt",
    "创建*.txt",
    "解决*.txt",
    "绕过*.txt",
    "直接*.txt",
    "分步*.txt",
    "永久*.txt",
    "服务器启动命令*.txt",
    "服务器启动命令.md",
    "服务器修复命令.txt",
    "所有服务名称*.txt",
    "测试*.txt",
    "简化*.txt",
    "深度*.txt"
)

foreach ($pattern in $deploymentCommandPatterns) {
    Get-ChildItem -Path . -Filter $pattern -File -ErrorAction SilentlyContinue | ForEach-Object {
        Move-Item -Path $_.FullName -Destination "docs\deployment\commands\" -Force -ErrorAction SilentlyContinue
        Write-Host "  Moved: $($_.Name) -> deployment\commands\" -ForegroundColor Gray
    }
}

# 移动部署脚本
$deploymentScriptPatterns = @(
    "上传*.ps1",
    "上传*.txt"
)

foreach ($pattern in $deploymentScriptPatterns) {
    Get-ChildItem -Path . -Filter $pattern -File -ErrorAction SilentlyContinue | ForEach-Object {
        Move-Item -Path $_.FullName -Destination "docs\deployment\scripts\" -Force -ErrorAction SilentlyContinue
        Write-Host "  Moved: $($_.Name) -> deployment\scripts\" -ForegroundColor Gray
    }
}

# 移动其他PowerShell脚本（排除根目录需要的）
$ps1Files = Get-ChildItem -Path . -Filter "*.ps1" -File -ErrorAction SilentlyContinue | 
    Where-Object { $_.Name -notin @("check-env.ps1", "check-services.ps1", "update-env.ps1", "start-all.sh") }

foreach ($file in $ps1Files) {
    Move-Item -Path $file.FullName -Destination "docs\deployment\scripts\" -Force -ErrorAction SilentlyContinue
    Write-Host "  Moved: $($file.Name) -> deployment\scripts\" -ForegroundColor Gray
}

# 移动部署文档
$deploymentDocs = @(
    "DEPLOYMENT-*.md",
    "GITHUB_*.md",
    "PLATFORM_INTRODUCTION.md",
    "文件差异检查报告.md",
    "服务器文件检查报告.md"
)

foreach ($pattern in $deploymentDocs) {
    Get-ChildItem -Path . -Filter $pattern -File -ErrorAction SilentlyContinue | ForEach-Object {
        Move-Item -Path $_.FullName -Destination "docs\deployment\" -Force -ErrorAction SilentlyContinue
        Write-Host "  Moved: $($_.Name) -> deployment\" -ForegroundColor Gray
    }
}

# 移动剩余的txt文件（排除requirements.txt等）
Get-ChildItem -Path . -Filter "*.txt" -File -ErrorAction SilentlyContinue | 
    Where-Object { $_.Name -notlike "requirements.txt" -and $_.Name -notlike "*requirements*.txt" } | 
    ForEach-Object {
        Move-Item -Path $_.FullName -Destination "docs\deployment\commands\" -Force -ErrorAction SilentlyContinue
        Write-Host "  Moved: $($_.Name) -> deployment\commands\" -ForegroundColor Gray
    }

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "整理完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "文档已分类整理到以下目录：" -ForegroundColor Yellow
Write-Host "  - docs\troubleshooting\    故障排查文档" -ForegroundColor White
Write-Host "  - docs\deployment\commands\ 部署命令文档" -ForegroundColor White
Write-Host "  - docs\deployment\scripts\  部署脚本" -ForegroundColor White
Write-Host "  - docs\deployment\          部署文档" -ForegroundColor White
Write-Host ""


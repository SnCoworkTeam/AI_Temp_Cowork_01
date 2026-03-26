# PlantUML架构图生成脚本
# 用于批量生成系统架构图

param(
    [string]$OutputDir = "docs/images/architecture",
    [string]$Format = "png",  # png, svg, pdf
    [string]$SourceDir = "docs/architecture-docs"
)

Write-Host "=========================================="
Write-Host "PlantUML 架构图生成工具"
Write-Host "=========================================="
Write-Host ""

# 检查PlantUML是否安装
$plantumlCmd = Get-Command plantuml -ErrorAction SilentlyContinue
if (-not $plantumlCmd) {
    Write-Host "错误: 未找到PlantUML命令" -ForegroundColor Red
    Write-Host ""
    Write-Host "请先安装PlantUML:" -ForegroundColor Yellow
    Write-Host "  choco install plantuml" -ForegroundColor Cyan
    Write-Host "  或" -ForegroundColor Yellow
    Write-Host "  brew install plantuml" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}

Write-Host "✓ PlantUML已安装: $($plantumlCmd.Source)" -ForegroundColor Green
Write-Host ""

# 创建输出目录
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    Write-Host "✓ 创建输出目录: $OutputDir" -ForegroundColor Green
}

# 查找所有.puml文件
$pumlFiles = Get-ChildItem -Path $SourceDir -Filter "*.puml" -Recurse

if ($pumlFiles.Count -eq 0) {
    Write-Host "错误: 未找到.puml文件" -ForegroundColor Red
    exit 1
}

Write-Host "找到 $($pumlFiles.Count) 个PlantUML文件:" -ForegroundColor Cyan
foreach ($file in $pumlFiles) {
    Write-Host "  - $($file.Name)" -ForegroundColor Gray
}
Write-Host ""

# 生成图片
Write-Host "开始生成图片..." -ForegroundColor Cyan
Write-Host ""

$successCount = 0
$failCount = 0

foreach ($file in $pumlFiles) {
    try {
        $fileName = $file.BaseName
        $outputPath = Join-Path $OutputDir "$fileName.$Format"
        
        Write-Host "生成: $($file.Name) -> $outputPath" -ForegroundColor Yellow
        
        # 构建PlantUML命令
        $formatFlag = switch ($Format) {
            "svg" { "-tsvg" }
            "pdf" { "-tpdf" }
            default { "-tpng" }
        }
        
        $command = "plantuml $formatFlag -o `"$OutputDir`" `"$($file.FullName)`""
        
        # 执行命令
        $result = Invoke-Expression $command 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ 成功" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "  ✗ 失败: $result" -ForegroundColor Red
            $failCount++
        }
    } catch {
        Write-Host "  ✗ 错误: $_" -ForegroundColor Red
        $failCount++
    }
}

Write-Host ""
Write-Host "=========================================="
Write-Host "生成完成"
Write-Host "=========================================="
Write-Host "成功: $successCount" -ForegroundColor Green
Write-Host "失败: $failCount" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })
Write-Host "输出目录: $OutputDir" -ForegroundColor Cyan
Write-Host ""





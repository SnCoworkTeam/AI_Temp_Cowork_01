# 快速测试数据同步脚本
# 只导出数据，不上传到服务器

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  快速测试数据同步" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 运行同步脚本（只导出，不上传）
Write-Host "[测试] 运行数据同步脚本（仅导出）..." -ForegroundColor Cyan
Write-Host ""

try {
    & "$PSScriptRoot\sync_metadata_knowledge_to_server.ps1" -NoUpload
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[成功] 数据导出测试完成！" -ForegroundColor Green
        Write-Host ""
        Write-Host "导出的文件保存在: backups\sync\" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "下一步:" -ForegroundColor Yellow
        Write-Host "  1. 检查导出的文件" -ForegroundColor Gray
        Write-Host "  2. 使用完整命令上传到服务器:" -ForegroundColor Gray
        Write-Host "     .\scripts\sync_metadata_knowledge_to_server.ps1 -ServerHost user@server" -ForegroundColor Yellow
    } else {
        Write-Host ""
        Write-Host "[失败] 数据导出测试失败" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "[错误] 测试失败: $_" -ForegroundColor Red
    exit 1
}



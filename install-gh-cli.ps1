# GitHub CLI 自动安装脚本

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "GitHub CLI 安装工具" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否已安装
if (Get-Command gh -ErrorAction SilentlyContinue) {
    Write-Host "✅ GitHub CLI已安装" -ForegroundColor Green
    gh --version
    exit 0
}

Write-Host "开始安装GitHub CLI..." -ForegroundColor Yellow
Write-Host ""

# 获取最新版本下载URL
$latestUrl = "https://api.github.com/repos/cli/cli/releases/latest"
Write-Host "获取最新版本信息..." -ForegroundColor Yellow

try {
    $release = Invoke-RestMethod -Uri $latestUrl -UseBasicParsing
    $asset = $release.assets | Where-Object { $_.name -like "*windows_amd64.msi" } | Select-Object -First 1
    
    if ($asset) {
        $downloadUrl = $asset.browser_download_url
        $installer = "$env:TEMP\gh_installer.msi"
        
        Write-Host "下载版本: $($release.tag_name)" -ForegroundColor Cyan
        Write-Host "下载地址: $downloadUrl" -ForegroundColor Gray
        Write-Host "保存到: $installer" -ForegroundColor Gray
        Write-Host ""
        
        # 下载安装包
        Write-Host "下载安装包..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri $downloadUrl -OutFile $installer -UseBasicParsing
        
        if (Test-Path $installer) {
            Write-Host "✅ 下载完成" -ForegroundColor Green
            Write-Host ""
            
            # 安装
            Write-Host "安装GitHub CLI..." -ForegroundColor Yellow
            $process = Start-Process msiexec.exe -ArgumentList "/i `"$installer`" /quiet /norestart" -Wait -PassThru -NoNewWindow
            
            if ($process.ExitCode -eq 0) {
                Write-Host "✅ 安装完成！" -ForegroundColor Green
                Write-Host ""
                Write-Host "⚠️  重要: 请重启PowerShell终端以使命令生效" -ForegroundColor Yellow
                Write-Host ""
                Write-Host "重启后运行以下命令验证:" -ForegroundColor Cyan
                Write-Host "  gh --version" -ForegroundColor White
                Write-Host "  gh auth login" -ForegroundColor White
            } else {
                Write-Host "❌ 安装失败，退出代码: $($process.ExitCode)" -ForegroundColor Red
                Write-Host "请手动运行安装程序: $installer" -ForegroundColor Yellow
            }
        } else {
            Write-Host "❌ 下载失败" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ 未找到Windows安装包" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ 安装失败: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "请手动安装:" -ForegroundColor Yellow
    Write-Host "  1. 访问: https://cli.github.com/" -ForegroundColor White
    Write-Host "  2. 下载Windows安装包" -ForegroundColor White
    Write-Host "  3. 运行安装程序" -ForegroundColor White
}

# 配置SSH_PRIVATE_KEY Secret

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "配置SSH_PRIVATE_KEY Secret" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 可能的密钥文件位置
$possiblePaths = @(
    "enterprise_ai_platform.pem",
    "$env:USERPROFILE\.ssh\enterprise_ai_platform.pem",
    "E:\enterprise-ai-platform\enterprise_ai_platform.pem"
)

$keyFile = $null

# 查找密钥文件
Write-Host "查找SSH密钥文件..." -ForegroundColor Yellow
foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $keyFile = $path
        Write-Host "找到密钥文件: $path" -ForegroundColor Green
        break
    }
}

if (-not $keyFile) {
    Write-Host ""
    Write-Host "未找到密钥文件，请手动指定路径" -ForegroundColor Red
    Write-Host ""
    Write-Host "可能的解决方案:" -ForegroundColor Yellow
    Write-Host "1. 如果密钥文件在其他位置，请提供完整路径" -ForegroundColor Gray
    Write-Host "2. 或者从服务器管理员获取密钥文件" -ForegroundColor Gray
    Write-Host ""
    $keyFile = Read-Host "请输入密钥文件路径（或按Enter跳过）"
    
    if ([string]::IsNullOrEmpty($keyFile) -or -not (Test-Path $keyFile)) {
        Write-Host "未找到密钥文件，无法配置SSH_PRIVATE_KEY" -ForegroundColor Red
        Write-Host ""
        Write-Host "请使用GitHub Web界面手动配置:" -ForegroundColor Yellow
        Write-Host "1. 访问: https://github.com/PMLiuyubin/enterprise-ai-platform/settings/secrets/actions" -ForegroundColor Cyan
        Write-Host "2. 点击 'New repository secret'" -ForegroundColor Gray
        Write-Host "3. Name: SSH_PRIVATE_KEY" -ForegroundColor Gray
        Write-Host "4. Secret: 粘贴密钥文件内容" -ForegroundColor Gray
        exit 1
    }
}

# 读取密钥内容
Write-Host ""
Write-Host "读取密钥文件..." -ForegroundColor Yellow
$keyContent = Get-Content $keyFile -Raw

# 验证密钥格式
if ($keyContent -notmatch "BEGIN.*PRIVATE KEY") {
    Write-Host "警告: 密钥文件格式可能不正确" -ForegroundColor Yellow
    $confirm = Read-Host "是否继续? (y/n)"
    if ($confirm -ne "y") {
        exit 0
    }
}

# 配置Secret
Write-Host ""
Write-Host "配置SSH_PRIVATE_KEY Secret..." -ForegroundColor Yellow
$keyContent | gh secret set SSH_PRIVATE_KEY

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "SSH_PRIVATE_KEY 配置成功！" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "验证配置:" -ForegroundColor Yellow
    gh secret list | Select-String "SSH_PRIVATE_KEY"
} else {
    Write-Host ""
    Write-Host "配置失败，请检查:" -ForegroundColor Red
    Write-Host "1. GitHub CLI是否已登录: gh auth status" -ForegroundColor Yellow
    Write-Host "2. 是否有仓库权限" -ForegroundColor Yellow
    Write-Host "3. 或使用Web界面手动配置" -ForegroundColor Yellow
}






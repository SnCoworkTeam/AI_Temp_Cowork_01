#!/usr/bin/env pwsh
# 上传代码到服务器4的脚本

$ErrorActionPreference = "Stop"

# 服务器配置
$serverHost = "43.143.139.197"
$serverUser = "ubuntu"
$serverPath = "/home/ubuntu/enterprise-ai-platform"
$keyFile = "enterprise_ai_platform.pem"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "开始上传代码到服务器4" -ForegroundColor Cyan
Write-Host "服务器: $serverUser@$serverHost" -ForegroundColor Cyan
Write-Host "目标路径: $serverPath" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# 检查密钥文件
if (-not (Test-Path $keyFile)) {
    Write-Host "错误: 找不到密钥文件 $keyFile" -ForegroundColor Red
    exit 1
}

# 设置密钥文件权限（Linux/Unix需要）
Write-Host "设置密钥文件权限..." -ForegroundColor Yellow
icacls $keyFile /inheritance:r /grant:r "$($env:USERNAME):(R)" | Out-Null

# 测试SSH连接
Write-Host "测试SSH连接..." -ForegroundColor Yellow
$testConnection = ssh -i $keyFile -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$serverUser@$serverHost" "echo '连接成功'" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "SSH连接失败: $testConnection" -ForegroundColor Red
    exit 1
}
Write-Host "SSH连接成功" -ForegroundColor Green
Write-Host ""

# 需要上传的目录和文件
$uploadItems = @(
    "web-ui/src/app/projects",
    "web-ui/src/app/admin/projects",
    "web-ui/src/components/ProjectPhaseProgress.tsx"
)

Write-Host "准备上传以下内容:" -ForegroundColor Yellow
foreach ($item in $uploadItems) {
    if (Test-Path $item) {
        Write-Host "  ✓ $item" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $item (不存在)" -ForegroundColor Red
    }
}
Write-Host ""

# 创建目标目录
Write-Host "在服务器上创建目标目录..." -ForegroundColor Yellow
ssh -i $keyFile -o StrictHostKeyChecking=no "$serverUser@$serverHost" "mkdir -p $serverPath/web-ui/src/app/projects $serverPath/web-ui/src/app/admin/projects $serverPath/web-ui/src/components" 2>&1 | Out-Null

# 上传文件
Write-Host "开始上传文件..." -ForegroundColor Yellow
Write-Host ""

# 上传项目相关页面
Write-Host "[1/3] 上传用户端项目页面..." -ForegroundColor Cyan
$remotePath1 = "${serverUser}@${serverHost}:${serverPath}/web-ui/src/app/"
scp -i $keyFile -o StrictHostKeyChecking=no -r "web-ui/src/app/projects" $remotePath1 2>&1 | ForEach-Object {
    if ($_ -match "error|Error|ERROR|failed|Failed|FAILED") {
        Write-Host $_ -ForegroundColor Red
    } else {
        Write-Host $_
    }
}

Write-Host "[2/3] 上传管理端项目页面..." -ForegroundColor Cyan
$remotePath2 = "${serverUser}@${serverHost}:${serverPath}/web-ui/src/app/admin/"
scp -i $keyFile -o StrictHostKeyChecking=no -r "web-ui/src/app/admin/projects" $remotePath2 2>&1 | ForEach-Object {
    if ($_ -match "error|Error|ERROR|failed|Failed|FAILED") {
        Write-Host $_ -ForegroundColor Red
    } else {
        Write-Host $_
    }
}

Write-Host "[3/3] 上传阶段进度组件..." -ForegroundColor Cyan
$remotePath3 = "${serverUser}@${serverHost}:${serverPath}/web-ui/src/components/"
scp -i $keyFile -o StrictHostKeyChecking=no "web-ui/src/components/ProjectPhaseProgress.tsx" $remotePath3 2>&1 | ForEach-Object {
    if ($_ -match "error|Error|ERROR|failed|Failed|FAILED") {
        Write-Host $_ -ForegroundColor Red
    } else {
        Write-Host $_
    }
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "文件上传完成!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# 验证上传
Write-Host "验证上传的文件..." -ForegroundColor Yellow
ssh -i $keyFile -o StrictHostKeyChecking=no "$serverUser@$serverHost" "ls -la $serverPath/web-ui/src/components/ProjectPhaseProgress.tsx" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 阶段进度组件上传成功" -ForegroundColor Green
} else {
    Write-Host "✗ 阶段进度组件上传失败" -ForegroundColor Red
}

Write-Host ""
Write-Host "上传完成! 请在服务器上重启web-ui服务以应用更改。" -ForegroundColor Green


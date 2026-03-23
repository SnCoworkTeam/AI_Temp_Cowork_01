# 快速部署脚本 - 需要提供服务器地址作为参数

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerHost,
    
    [Parameter(Mandatory=$false)]
    [string]$ServerUser = "root",
    
    [Parameter(Mandatory=$false)]
    [string]$ServerPath = "/opt/enterprise-ai-platform"
)

Write-Host "==========================================" -ForegroundColor Green
Write-Host "快速部署到服务器: $ServerHost" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# 检查部署脚本是否存在
if (-not (Test-Path ".\scripts\deploy_all_to_server.ps1")) {
    Write-Host "错误: 部署脚本不存在" -ForegroundColor Red
    exit 1
}

# 执行部署
& ".\scripts\deploy_all_to_server.ps1" -ServerHost $ServerHost -ServerUser $ServerUser -ServerPath $ServerPath




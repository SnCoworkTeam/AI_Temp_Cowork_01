#!/usr/bin/env pwsh
# Neo4j完整部署脚本 - 一键部署Neo4j并上传数据
# 使用方法: .\scripts\deployment\deploy-neo4j-complete.ps1

param(
    [string]$ServerIP = "43.143.90.179",
    [string]$ServerUser = "root",
    [string]$KeyPath = "",
    [string]$RemotePath = "/opt/enterprise-ai-platform",
    [string]$Neo4jPassword = "Neo4j",
    [switch]$SkipDeploy = $false,
    [switch]$SkipDataUpload = $false
)

$ErrorActionPreference = "Stop"

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "🚀 Neo4j完整部署流程" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "服务器: $ServerUser@$ServerIP" -ForegroundColor Yellow
Write-Host "Neo4j密码: $Neo4jPassword" -ForegroundColor Yellow
Write-Host ""

$ScriptDir = $PSScriptRoot

# 步骤1: 部署Neo4j
if (-not $SkipDeploy) {
    Write-Host "`n==========================================" -ForegroundColor Green
    Write-Host "步骤 1/3: 部署Neo4j到服务器" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    
    $deployScript = Join-Path $ScriptDir "deploy-neo4j-to-server.ps1"
    if (Test-Path $deployScript) {
        & $deployScript -ServerIP $ServerIP -ServerUser $ServerUser -KeyPath $KeyPath -RemotePath $RemotePath -Neo4jPassword $Neo4jPassword
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Neo4j部署失败" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "❌ 部署脚本未找到: $deployScript" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "`n⏭️  跳过Neo4j部署步骤" -ForegroundColor Yellow
}

# 步骤2: 导出本地数据
if (-not $SkipDataUpload) {
    Write-Host "`n==========================================" -ForegroundColor Green
    Write-Host "步骤 2/3: 导出本地Neo4j数据" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    
    $exportScript = Join-Path $ScriptDir "export-neo4j-data.ps1"
    if (Test-Path $exportScript) {
        & $exportScript
        if ($LASTEXITCODE -ne 0) {
            Write-Host "⚠️  数据导出失败，但继续上传步骤" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️  导出脚本未找到，跳过导出" -ForegroundColor Yellow
    }
    
    # 步骤3: 上传数据到服务器
    Write-Host "`n==========================================" -ForegroundColor Green
    Write-Host "步骤 3/3: 上传数据到服务器" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    
    $uploadScript = Join-Path $ScriptDir "upload-neo4j-data-to-server.ps1"
    if (Test-Path $uploadScript) {
        & $uploadScript -ServerIP $ServerIP -ServerUser $ServerUser -KeyPath $KeyPath -RemotePath $RemotePath -ExportFirst:$false
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ 数据上传失败" -ForegroundColor Red
            exit 1
        }
        
        # 步骤4: 在服务器上恢复数据
        Write-Host "`n==========================================" -ForegroundColor Green
        Write-Host "步骤 4/4: 在服务器上恢复数据" -ForegroundColor Green
        Write-Host "==========================================" -ForegroundColor Green
        
        $restoreScript = Join-Path $ScriptDir "restore-neo4j-data-on-server.ps1"
        if (Test-Path $restoreScript) {
            & $restoreScript -ServerIP $ServerIP -ServerUser $ServerUser -KeyPath $KeyPath -RemotePath $RemotePath -Neo4jPassword $Neo4jPassword
            if ($LASTEXITCODE -ne 0) {
                Write-Host "❌ 数据恢复失败" -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host "❌ 恢复脚本未找到: $restoreScript" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "❌ 上传脚本未找到: $uploadScript" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "`n⏭️  跳过数据上传步骤" -ForegroundColor Yellow
}

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "🎉 Neo4j完整部署流程完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "访问信息:" -ForegroundColor Yellow
Write-Host "  HTTP界面: http://$ServerIP:7474" -ForegroundColor White
Write-Host "  Bolt连接: bolt://$ServerIP:7687" -ForegroundColor White
Write-Host "  用户名: neo4j" -ForegroundColor White
Write-Host "  密码: $Neo4jPassword" -ForegroundColor White
Write-Host ""


# PowerShell 脚本：一键部署到测试服务器
# 使用方法: .\scripts\deployment\deploy-test-server.ps1 [-ServiceName <service>] [-SkipImages] [-SkipCode]
#
# 功能：
# 1. 构建Docker镜像
# 2. 上传Docker镜像到服务器
# 3. 同步代码文件到服务器
# 4. 在服务器上重启服务

param(
    [string]$ConfigFile = "remote.ssh",
    [string]$KeyFile = "enterprise_ai_platform.pem",
    [string]$RemotePath = "/opt/enterprise-ai-platform",
    [string]$ServiceName = "",  # 如果指定，只部署该服务
    [switch]$SkipImages = $false,  # 跳过镜像上传
    [switch]$SkipCode = $false,  # 跳过代码同步
    [switch]$BuildOnly = $false,  # 只构建，不部署
    [switch]$Restart = $true  # 是否重启服务
)

# 颜色输出函数
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Cyan "=========================================="
Write-ColorOutput Cyan "一键部署到测试服务器"
Write-ColorOutput Cyan "=========================================="
Write-Output ""

# 获取项目根目录
$ProjectRoot = if ($PSScriptRoot) {
    Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
} else {
    $PWD
}

Push-Location $ProjectRoot

try {
    # ==========================================
    # 步骤1: 读取服务器配置
    # ==========================================
    Write-ColorOutput Blue "[1/5] 读取服务器配置..."
    
    $ServerIP = ""
    $ServerUser = "ubuntu"
    $KeyPath = ""
    
    $configPath = Join-Path $ProjectRoot $ConfigFile
    if (Test-Path $configPath) {
        $configContent = Get-Content $configPath -Raw
        
        if ($configContent -match "HostName\s+(\S+)") {
            $ServerIP = $matches[1]
        }
        if ($configContent -match "User\s+(\S+)") {
            $ServerUser = $matches[1]
        }
        if ($configContent -match "IdentityFile\s+(\S+)") {
            $KeyPath = $matches[1].Trim('"')
            if (-not [System.IO.Path]::IsPathRooted($KeyPath)) {
                $KeyPath = Join-Path $ProjectRoot $KeyPath
            }
        }
    } else {
        $ServerIP = "43.143.139.197"
    }
    
    # 查找密钥文件
    if ([string]::IsNullOrEmpty($KeyPath) -or -not (Test-Path $KeyPath)) {
        $possibleKeyPaths = @(
            Join-Path $ProjectRoot $KeyFile,
            Join-Path $env:USERPROFILE ".ssh\$KeyFile"
        )
        
        foreach ($path in $possibleKeyPaths) {
            if (Test-Path $path) {
                $KeyPath = $path
                break
            }
        }
        
        if ([string]::IsNullOrEmpty($KeyPath) -or -not (Test-Path $KeyPath)) {
            Write-ColorOutput Red "❌ 未找到密钥文件: $KeyFile"
            exit 1
        }
    }
    
    Write-Output "服务器: $ServerUser@$ServerIP"
    Write-Output "远程路径: $RemotePath"
    Write-Output ""
    
    # ==========================================
    # 步骤2: 构建Docker镜像
    # ==========================================
    if (-not $SkipImages) {
        Write-ColorOutput Blue "[2/5] 构建Docker镜像..."
        
        $uploadImagesScript = Join-Path $PSScriptRoot "upload-docker-images.ps1"
        if (Test-Path $uploadImagesScript) {
            $buildArgs = @{
                ConfigFile = $ConfigFile
                KeyFile = $KeyFile
                RemotePath = $RemotePath
            }
            
            if (-not [string]::IsNullOrEmpty($ServiceName)) {
                $buildArgs.ServiceName = $ServiceName
            }
            
            if ($BuildOnly) {
                $buildArgs.BuildOnly = $true
            }
            
            & $uploadImagesScript @buildArgs
            
            if ($LASTEXITCODE -ne 0) {
                Write-ColorOutput Red "❌ 镜像构建/上传失败"
                exit 1
            }
        } else {
            Write-ColorOutput Yellow "⚠️  镜像上传脚本不存在，跳过镜像上传"
        }
        Write-Output ""
    } else {
        Write-ColorOutput Yellow "[2/5] 跳过镜像构建和上传"
        Write-Output ""
    }
    
    if ($BuildOnly) {
        Write-ColorOutput Green "✅ 构建完成"
        exit 0
    }
    
    # ==========================================
    # 步骤3: 同步代码文件
    # ==========================================
    if (-not $SkipCode) {
        Write-ColorOutput Blue "[3/5] 同步代码文件..."
        
        $syncScript = Join-Path $PSScriptRoot "sync-to-server.ps1"
        if (Test-Path $syncScript) {
            $syncArgs = @{
                ConfigFile = $ConfigFile
                KeyFile = $KeyFile
                RemotePath = $RemotePath
            }
            
            if (-not [string]::IsNullOrEmpty($ServiceName)) {
                # 如果指定了服务，只同步该服务的文件
                Write-Output "同步服务文件: $ServiceName"
            }
            
            & $syncScript @syncArgs
            
            if ($LASTEXITCODE -ne 0) {
                Write-ColorOutput Yellow "⚠️  代码同步失败，继续部署..."
            }
        } else {
            Write-ColorOutput Yellow "⚠️  代码同步脚本不存在，跳过代码同步"
        }
        Write-Output ""
    } else {
        Write-ColorOutput Yellow "[3/5] 跳过代码同步"
        Write-Output ""
    }
    
    # ==========================================
    # 步骤4: 在服务器上重启服务
    # ==========================================
    if ($Restart) {
        Write-ColorOutput Blue "[4/5] 重启服务器上的服务..."
        
        if (-not [string]::IsNullOrEmpty($ServiceName)) {
            Write-Output "重启服务: $ServiceName"
            $restartCmd = "cd $RemotePath && docker compose restart $ServiceName"
        } else {
            Write-Output "重启所有服务..."
            $restartCmd = "cd $RemotePath && docker compose restart"
        }
        
        & ssh -i "`"$KeyPath`" -o StrictHostKeyChecking=no -o ConnectTimeout=30 $ServerUser@${ServerIP} $restartCmd 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput Green "✅ 服务重启成功"
        } else {
            Write-ColorOutput Yellow "⚠️  服务重启失败，请手动检查"
        }
        Write-Output ""
    } else {
        Write-ColorOutput Yellow "[4/5] 跳过服务重启"
        Write-Output ""
    }
    
    # ==========================================
    # 步骤5: 验证部署
    # ==========================================
    Write-ColorOutput Blue "[5/5] 验证部署..."
    
    Write-Output "检查服务状态..."
    $statusCmd = "cd $RemotePath && docker compose ps"
    $statusOutput = & ssh -i "`"$KeyPath`" -o StrictHostKeyChecking=no -o ConnectTimeout=10 $ServerUser@${ServerIP} $statusCmd 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Output $statusOutput
        Write-ColorOutput Green "✅ 部署验证完成"
    } else {
        Write-ColorOutput Yellow "⚠️  无法验证部署状态"
    }
    
    # ==========================================
    # 总结
    # ==========================================
    Write-Output ""
    Write-ColorOutput Green "=========================================="
    Write-ColorOutput Green "✅ 部署完成！"
    Write-ColorOutput Green "=========================================="
    Write-Output ""
    Write-Output "服务器信息："
    Write-Output "  - 地址: $ServerUser@$ServerIP"
    Write-Output "  - 路径: $RemotePath"
    Write-Output ""
    Write-Output "下一步操作："
    Write-Output "  1. SSH 连接: ssh -i `"$KeyPath`" $ServerUser@${ServerIP}"
    Write-Output "  2. 查看日志: cd $RemotePath && docker compose logs -f [service-name]"
    Write-Output "  3. 查看状态: cd $RemotePath && docker compose ps"
    Write-Output ""
    
} catch {
    Write-ColorOutput Red "❌ 发生错误: $_"
    Write-Output $_.ScriptStackTrace
    exit 1
} finally {
    Pop-Location
}


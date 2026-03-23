# PowerShell 脚本：导出并上传Docker镜像到测试服务器
# 使用方法: .\scripts\deployment\upload-docker-images.ps1 [-ServiceName <service>] [-Compress] [-SkipBuild]
#
# 功能：
# 1. 从 remote.ssh 配置文件读取服务器信息
# 2. 导出本地Docker镜像
# 3. 压缩镜像（可选）
# 4. 上传到服务器
# 5. 在服务器上加载镜像

param(
    [string]$ConfigFile = "remote.ssh",
    [string]$KeyFile = "enterprise_ai_platform.pem",
    [string]$RemotePath = "/opt/enterprise-ai-platform",
    [string]$ServiceName = "",  # 如果指定，只上传该服务的镜像
    [switch]$Compress = $true,  # 是否压缩镜像
    [switch]$SkipBuild = $false,  # 是否跳过构建，直接上传已有镜像
    [switch]$BuildOnly = $false,  # 只构建，不上传
    [switch]$All = $false  # 上传所有服务的镜像
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
Write-ColorOutput Cyan "Docker镜像上传工具"
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
    Write-ColorOutput Blue "[1/6] 读取服务器配置..."
    
    $ServerIP = ""
    $ServerUser = "ubuntu"
    $KeyPath = ""
    
    # 尝试从 remote.ssh 读取配置
    $configPath = Join-Path $ProjectRoot $ConfigFile
    if (Test-Path $configPath) {
        Write-ColorOutput Green "✅ 找到配置文件: $configPath"
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
        Write-ColorOutput Yellow "⚠️  配置文件不存在: $configPath"
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
    # 步骤2: 获取需要上传的服务列表
    # ==========================================
    Write-ColorOutput Blue "[2/6] 获取服务列表..."
    
    # 从docker-compose.yml读取服务列表（排除基础服务）
    $baseServices = @("postgres", "redis", "redis-commander", "qdrant")
    $services = @()
    
    if (-not [string]::IsNullOrEmpty($ServiceName)) {
        $services = @($ServiceName)
    } elseif ($All) {
        # 获取所有服务
        $composeContent = Get-Content "docker-compose.yml" -Raw
        $serviceMatches = [regex]::Matches($composeContent, "^\s+(\w+):\s*$", [System.Text.RegularExpressions.RegexOptions]::Multiline)
        $services = $serviceMatches | ForEach-Object { $_.Groups[1].Value } | Where-Object { $baseServices -notcontains $_ }
    } else {
        # 默认上传主要服务
        $services = @(
            "registry-service",
            "api-gateway",
            "config-center",
            "mcp-gateway",
            "workflow-engine",
            "auth-service",
            "knowledge-base",
            "metadata-service",
            "chat-service",
            "agent-service",
            "agent-orchestrator",
            "memory-service"
        )
    }
    
    Write-ColorOutput Green "✅ 将上传 $($services.Count) 个服务的镜像"
    Write-Output ""
    
    # ==========================================
    # 步骤3: 构建Docker镜像（如果需要）
    # ==========================================
    if (-not $SkipBuild) {
        Write-ColorOutput Blue "[3/6] 构建Docker镜像..."
        
        if (-not [string]::IsNullOrEmpty($ServiceName)) {
            Write-Output "构建服务: $ServiceName"
            docker compose build $ServiceName
            if ($LASTEXITCODE -ne 0) {
                Write-ColorOutput Red "❌ 镜像构建失败: $ServiceName"
                exit 1
            }
        } else {
            Write-Output "构建所有服务镜像..."
            $buildServices = $services -join " "
            docker compose build $buildServices
            if ($LASTEXITCODE -ne 0) {
                Write-ColorOutput Yellow "⚠️  部分镜像构建失败，继续上传已构建的镜像..."
            }
        }
        
        Write-ColorOutput Green "✅ 镜像构建完成"
        Write-Output ""
    } else {
        Write-ColorOutput Yellow "[3/6] 跳过构建步骤"
        Write-Output ""
    }
    
    if ($BuildOnly) {
        Write-ColorOutput Green "✅ 构建完成（跳过上传）"
        exit 0
    }
    
    # ==========================================
    # 步骤4: 导出镜像
    # ==========================================
    Write-ColorOutput Blue "[4/6] 导出Docker镜像..."
    
    $tempDir = Join-Path $env:TEMP "docker-images-$(Get-Date -Format 'yyyyMMddHHmmss')"
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    Write-Output "临时目录: $tempDir"
    
    $exportedImages = @()
    
    foreach ($service in $services) {
        $imageName = "enterprise-ai-platform-${service}"
        $imageFile = Join-Path $tempDir "${service}.tar"
        
        Write-Output "导出镜像: $imageName"
        
        # 检查镜像是否存在
        $imageExists = docker images --format "{{.Repository}}:{{.Tag}}" | Select-String -Pattern "^${imageName}:latest$|^${imageName}:\w+$"
        if (-not $imageExists) {
            Write-ColorOutput Yellow "⚠️  镜像 $imageName 不存在，跳过..."
            continue
        }
        
        # 导出镜像
        docker save "${imageName}:latest" -o $imageFile
        if ($LASTEXITCODE -eq 0) {
            $fileSize = (Get-Item $imageFile).Length / 1MB
            Write-ColorOutput Green "✅ 镜像导出成功: $([math]::Round($fileSize, 2)) MB"
            $exportedImages += @{
                Service = $service
                ImageFile = $imageFile
                Size = $fileSize
            }
        } else {
            Write-ColorOutput Red "❌ 镜像导出失败: $service"
        }
    }
    
    if ($exportedImages.Count -eq 0) {
        Write-ColorOutput Red "❌ 没有成功导出的镜像"
        exit 1
    }
    
    Write-ColorOutput Green "✅ 成功导出 $($exportedImages.Count) 个镜像"
    Write-Output ""
    
    # ==========================================
    # 步骤5: 压缩镜像（可选）
    # ==========================================
    if ($Compress) {
        Write-ColorOutput Blue "[5/6] 压缩镜像文件..."
        
        foreach ($img in $exportedImages) {
            $originalFile = $img.ImageFile
            $compressedFile = "${originalFile}.gz"
            
            Write-Output "压缩: $($img.Service)..."
            
            # 使用gzip压缩（如果可用）
            if (Get-Command gzip -ErrorAction SilentlyContinue) {
                gzip -f $originalFile
                if ($LASTEXITCODE -eq 0) {
                    $compressedSize = (Get-Item $compressedFile).Length / 1MB
                    $ratio = [math]::Round((1 - $compressedSize / $img.Size) * 100, 1)
                    Write-ColorOutput Green "✅ 压缩完成: $([math]::Round($compressedSize, 2)) MB (压缩率: $ratio%)"
                    $img.ImageFile = $compressedFile
                    $img.Compressed = $true
                } else {
                    Write-ColorOutput Yellow "⚠️  压缩失败，使用未压缩文件"
                    $img.Compressed = $false
                }
            } else {
                Write-ColorOutput Yellow "⚠️  gzip未安装，跳过压缩"
                $img.Compressed = $false
            }
        }
        Write-Output ""
    }
    
    # ==========================================
    # 步骤6: 上传到服务器
    # ==========================================
    Write-ColorOutput Blue "[6/6] 上传镜像到服务器..."
    
    # 在服务器上创建目录
    $sshCmd = "mkdir -p $RemotePath/docker-images"
    & ssh -i "`"$KeyPath`" -o StrictHostKeyChecking=no -o ConnectTimeout=10 $ServerUser@${ServerIP} $sshCmd 2>&1 | Out-Null
    
    $uploadSuccess = 0
    $uploadFailed = 0
    
    foreach ($img in $exportedImages) {
        $imageFile = $img.ImageFile
        $service = $img.Service
        $fileName = Split-Path $imageFile -Leaf
        
        Write-Output "上传: $service ($fileName)..."
        
        # 上传文件
        $scpArgs = @(
            "-i", "`"$KeyPath`"",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=30",
            $imageFile,
            "$ServerUser@${ServerIP}:$RemotePath/docker-images/$fileName"
        )
        
        & scp @scpArgs 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput Green "✅ 上传成功: $service"
            $uploadSuccess++
            
            # 在服务器上加载镜像
            Write-Output "  加载镜像到Docker..."
            if ($img.Compressed) {
                $loadCmd = "cd $RemotePath; gunzip -c docker-images/$fileName | docker load; rm -f docker-images/$fileName"
            } else {
                $loadCmd = "cd $RemotePath; docker load -i docker-images/$fileName; rm -f docker-images/$fileName"
            }
            
            & ssh -i "`"$KeyPath`" -o StrictHostKeyChecking=no -o ConnectTimeout=30 $ServerUser@${ServerIP} $loadCmd 2>&1 | Out-Null
            
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput Green "✅ 镜像加载成功: $service"
            } else {
                Write-ColorOutput Yellow "⚠️  镜像加载失败: $service（文件已上传）"
            }
        } else {
            Write-ColorOutput Red "❌ 上传失败: $service"
            $uploadFailed++
        }
    }
    
    # 清理临时文件
    Write-Output ""
    Write-Output "清理临时文件..."
    if (Test-Path $tempDir) {
        Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    # ==========================================
    # 总结
    # ==========================================
    Write-Output ""
    Write-ColorOutput Green "=========================================="
    Write-ColorOutput Green "✅ 上传完成！"
    Write-ColorOutput Green "=========================================="
    Write-Output ""
    Write-Output "统计信息："
    Write-Output "  - 成功上传: $uploadSuccess"
    Write-Output "  - 上传失败: $uploadFailed"
    Write-Output ""
    Write-Output "下一步操作："
    Write-Output "  1. SSH 连接: ssh -i `"$KeyPath`" $ServerUser@${ServerIP}"
    Write-Output "  2. 进入目录: cd $RemotePath"
    Write-Output "  3. 重启服务: docker compose restart [service-name]"
    Write-Output ""
    
} catch {
    Write-Host "发生错误: $_" -ForegroundColor Red
    Write-Output $_.ScriptStackTrace
    exit 1
} finally {
    Pop-Location
}


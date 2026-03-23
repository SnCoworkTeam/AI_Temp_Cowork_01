# ============================================================
# 企业AI平台 - 完整自动同步脚本
# ============================================================
# 功能：
# 1. 代码同步（通过rsync/scp）
# 2. Docker镜像构建和同步
# 3. 数据库迁移文件同步和执行
# 4. 数据库数据备份和同步（可选）
# 5. 服务部署和重启
#
# 使用方法：
#   .\scripts\deployment\complete-sync.ps1
#   .\scripts\deployment\complete-sync.ps1 -SkipDataSync
#   .\scripts\deployment\complete-sync.ps1 -BuildImagesOnly
# ============================================================

param(
    [string]$ConfigFile = "remote.ssh",
    [string]$KeyFile = "enterprise_ai_platform.pem",
    [string]$RemotePath = "/opt/enterprise-ai-platform",
    [switch]$SkipDataSync = $false,        # 跳过数据同步
    [switch]$BuildImagesOnly = $false,     # 仅构建镜像，不同步代码
    [switch]$SkipMigration = $false,       # 跳过数据库迁移
    [switch]$DryRun = $false,              # 干运行模式（仅显示将要执行的操作）
    [string]$Services = ""                 # 指定要同步的服务（逗号分隔），为空则同步所有
)

$ErrorActionPreference = "Continue"

# 颜色输出函数
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Step($Step, $Message) {
    Write-ColorOutput Cyan "=========================================="
    Write-ColorOutput Cyan "[$Step] $Message"
    Write-ColorOutput Cyan "=========================================="
    Write-Output ""
}

function Write-Success($Message) {
    Write-ColorOutput Green "✅ $Message"
}

function Write-Error($Message) {
    Write-ColorOutput Red "❌ $Message"
}

function Write-Warning($Message) {
    Write-ColorOutput Yellow "⚠️  $Message"
}

function Write-Info($Message) {
    Write-ColorOutput Gray "ℹ️  $Message"
}

# 获取项目根目录
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptRoot
if ($ProjectRoot -is [System.Array]) {
    $ProjectRoot = $ProjectRoot[0]
}

# 确保项目根目录是正确的（修复路径问题）
# 如果配置文件不在计算出的根目录，尝试使用脚本目录的上级目录
$testConfigPath = Join-Path $ProjectRoot $ConfigFile
if (-not (Test-Path $testConfigPath)) {
    # 尝试从脚本路径向上查找项目根目录
    $currentPath = $ScriptRoot
    while ($currentPath -and $currentPath -ne (Split-Path $currentPath)) {
        $parentPath = Split-Path $currentPath
        $testPath = Join-Path $parentPath $ConfigFile
        if (Test-Path $testPath) {
            $ProjectRoot = $parentPath
            break
        }
        $currentPath = $parentPath
    }
}

Push-Location $ProjectRoot

Write-ColorOutput Cyan "=========================================="
Write-ColorOutput Cyan "企业AI平台 - 完整自动同步脚本"
Write-ColorOutput Cyan "=========================================="
Write-Output ""
Write-Info "项目根目录: $ProjectRoot"
Write-Info "远程路径: $RemotePath"
Write-Output ""

# ============================================================
# 1. 读取SSH配置
# ============================================================
Write-Step "1/7" "读取SSH配置"

$ConfigPath = Join-Path $ProjectRoot $ConfigFile
if (-not (Test-Path $ConfigPath)) {
    Write-Error "SSH配置文件不存在: $ConfigPath"
    exit 1
}

$sshConfig = @{
    HostName = ""
    User = "ubuntu"
    IdentityFile = ""
    Port = 22
}

$content = Get-Content $ConfigPath -Raw
if ($content -match "HostName\s+(\S+)") {
    $sshConfig.HostName = $matches[1]
}
if ($content -match "User\s+(\S+)") {
    $sshConfig.User = $matches[1]
}
if ($content -match "IdentityFile\s+(\S+)") {
    $keyFile = $matches[1]
    $keyPath = Join-Path $ProjectRoot $keyFile
    if (Test-Path $keyPath) {
        $sshConfig.IdentityFile = $keyPath
    } else {
        Write-Error "密钥文件不存在: $keyPath"
        exit 1
    }
}
if ($content -match "Port\s+(\d+)") {
    $sshConfig.Port = [int]$matches[1]
}

Write-Success "SSH配置读取成功"
Write-Info "  服务器: $($sshConfig.User)@$($sshConfig.HostName):$($sshConfig.Port)"
Write-Info "  密钥文件: $($sshConfig.IdentityFile)"
Write-Output ""

# 构建SSH命令前缀
$sshOptions = "-i `"$($sshConfig.IdentityFile)`" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p $($sshConfig.Port)"

# ============================================================
# 2. 测试SSH连接
# ============================================================
Write-Step "2/7" "测试SSH连接"

if (-not $DryRun) {
    $testResult = & ssh $sshOptions -o ConnectTimeout=10 "$($sshConfig.User)@$($sshConfig.HostName)" "echo 'connection_test'" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "SSH连接失败: $testResult"
        exit 1
    }
    Write-Success "SSH连接成功"
} else {
    Write-Info "[干运行] 跳过SSH连接测试"
}
Write-Output ""

# ============================================================
# 3. 代码同步（通过rsync/scp）
# ============================================================
if (-not $BuildImagesOnly) {
    Write-Step "3/7" "同步代码文件到服务器"
    
    # 需要同步的目录和文件
    $syncItems = @(
        @{Path = "database"; Exclude = @("__pycache__", "*.pyc", "venv", ".pytest_cache")},
        @{Path = "shared_libs"; Exclude = @("__pycache__", "*.pyc")},
        @{Path = "docker-compose.yml"; Exclude = @()},
        @{Path = "docker-compose.prod.yml"; Exclude = @()},
        @{Path = ".env.example"; Exclude = @()},
        @{Path = "scripts"; Exclude = @("__pycache__", "*.pyc")}
    )
    
    # 如果指定了服务，只同步相关服务
    if ($Services) {
        $serviceList = $Services -split ","
        foreach ($service in $serviceList) {
            $servicePath = $service.Trim()
            if (Test-Path $servicePath) {
                $syncItems += @{Path = $servicePath; Exclude = @("__pycache__", "*.pyc", "venv", "node_modules", ".next")}
            }
        }
    } else {
        # 同步所有服务目录
        $serviceDirs = Get-ChildItem -Directory | Where-Object {
            $_.Name -match "^(api-gateway|auth-service|mcp-gateway|workflow-engine|web-ui|knowledge-base|metadata-service|chat-service|agent-service|agent-orchestrator|agent-registry|memory-service|vector-coordinator|dag-orchestrator|sap-metadata-agent|project-management|config-center|registry-service)$"
        }
        foreach ($dir in $serviceDirs) {
            $syncItems += @{Path = $dir.Name; Exclude = @("__pycache__", "*.pyc", "venv", "node_modules", ".next", ".pytest_cache")}
        }
    }
    
    foreach ($item in $syncItems) {
        $localPath = Join-Path $ProjectRoot $item.Path
        if (-not (Test-Path $localPath)) {
            Write-Warning "跳过不存在的路径: $($item.Path)"
            continue
        }
        
        $remoteItemPath = "$RemotePath/$($item.Path)"
        
        if ($DryRun) {
            Write-Info "[干运行] 将同步: $($item.Path) -> $remoteItemPath"
        } else {
            Write-Info "同步: $($item.Path)"
            
            # 构建rsync排除选项
            $excludeArgs = ""
            foreach ($exclude in $item.Exclude) {
                $excludeArgs += " --exclude='$exclude'"
            }
            
            # 使用rsync同步（如果可用），否则使用scp
            if (Get-Command rsync -ErrorAction SilentlyContinue) {
                $rsyncCmd = "rsync -avz --delete $excludeArgs -e `"ssh $sshOptions`" `"$localPath`" $($sshConfig.User)@$($sshConfig.HostName):`"$remoteItemPath`""
                Invoke-Expression $rsyncCmd
            } else {
                # 使用scp（递归复制目录）
                if (Test-Path $localPath -PathType Container) {
                    # 创建远程目录
                    & ssh $sshOptions "$($sshConfig.User)@$($sshConfig.HostName)" "mkdir -p `"$remoteItemPath`""
                    # 使用scp递归复制
                    & scp $sshOptions -r "$localPath\*" "$($sshConfig.User)@$($sshConfig.HostName):`"$remoteItemPath`""
                } else {
                    # 复制单个文件
                    $remoteDir = Split-Path -Parent $remoteItemPath
                    & ssh $sshOptions "$($sshConfig.User)@$($sshConfig.HostName)" "mkdir -p `"$remoteDir`""
                    & scp $sshOptions "$localPath" "$($sshConfig.User)@$($sshConfig.HostName):`"$remoteItemPath`""
                }
            }
            
            if ($LASTEXITCODE -eq 0) {
                Write-Success "  $($item.Path) 同步完成"
            } else {
                Write-Error "  $($item.Path) 同步失败"
            }
        }
    }
    Write-Output ""
} else {
    Write-Info "跳过代码同步（仅构建镜像模式）"
    Write-Output ""
}

# ============================================================
# 4. Docker镜像构建和同步
# ============================================================
Write-Step "4/7" "构建和同步Docker镜像"

# 需要构建的服务镜像
$servicesToBuild = @()
if ($Services) {
    $serviceList = $Services -split ","
    foreach ($service in $serviceList) {
        $serviceName = $service.Trim()
        if (Test-Path (Join-Path $ProjectRoot $serviceName)) {
            $servicesToBuild += $serviceName
        }
    }
} else {
    # 构建所有服务的镜像
    $serviceDirs = Get-ChildItem -Directory | Where-Object {
        $_.Name -match "^(api-gateway|auth-service|mcp-gateway|workflow-engine|web-ui|knowledge-base|metadata-service|chat-service|agent-service|agent-orchestrator|agent-registry|memory-service|vector-coordinator-service|dag-orchestrator|sap-metadata-agent|project-management|config-center|registry-service)$"
    }
    $servicesToBuild = $serviceDirs | ForEach-Object { $_.Name }
}

Write-Info "将构建以下服务的镜像: $($servicesToBuild -join ', ')"

foreach ($service in $servicesToBuild) {
    $servicePath = Join-Path $ProjectRoot $service
    $dockerfile = Join-Path $servicePath "Dockerfile"
    $dockerfileDev = Join-Path $servicePath "Dockerfile.dev"
    
    # 优先使用Dockerfile，如果没有则使用Dockerfile.dev
    $dockerfileToUse = $null
    if (Test-Path $dockerfile) {
        $dockerfileToUse = $dockerfile
    } elseif (Test-Path $dockerfileDev) {
        $dockerfileToUse = $dockerfileDev
    }
    
    if (-not $dockerfileToUse) {
        Write-Warning "跳过 $service（未找到Dockerfile）"
        continue
    }
    
    $imageName = "enterprise-ai-$($service.ToLower())"
    $imageTag = "latest"
    $fullImageName = "${imageName}:${imageTag}"
    
    if ($DryRun) {
        Write-Info "[干运行] 将构建镜像: $fullImageName"
        Write-Info "  使用Dockerfile: $dockerfileToUse"
    } else {
        Write-Info "构建镜像: $fullImageName"
        
        # 构建镜像
        $buildContext = if ($dockerfileToUse -eq $dockerfile) { $servicePath } else { $ProjectRoot }
        
        docker build -t $fullImageName -f $dockerfileToUse $buildContext
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "  $fullImageName 构建成功"
            
            # 保存镜像为tar文件
            $tarFile = "$imageName-$imageTag.tar"
            Write-Info "  保存镜像为: $tarFile"
            docker save $fullImageName -o $tarFile
            
            if (Test-Path $tarFile) {
                # 上传到服务器
                Write-Info "  上传镜像到服务器..."
                & scp $sshOptions $tarFile "$($sshConfig.User)@$($sshConfig.HostName):/tmp/"
                
                if ($LASTEXITCODE -eq 0) {
                    # 在服务器上加载镜像
                    Write-Info "  在服务器上加载镜像..."
                    & ssh $sshOptions "$($sshConfig.User)@$($sshConfig.HostName)" "docker load -i /tmp/$tarFile && rm /tmp/$tarFile"
                    
                    if ($LASTEXITCODE -eq 0) {
                        Write-Success "  $fullImageName 已同步到服务器"
                    } else {
                        Write-Error "  在服务器上加载镜像失败"
                    }
                } else {
                    Write-Error "  上传镜像失败"
                }
                
                # 删除本地tar文件
                Remove-Item $tarFile -Force -ErrorAction SilentlyContinue
            } else {
                Write-Error "  保存镜像失败"
            }
        } else {
            Write-Error "  $fullImageName 构建失败"
        }
    }
}

Write-Output ""

# ============================================================
# 5. 数据库迁移文件同步和执行
# ============================================================
if (-not $SkipMigration) {
    Write-Step "5/7" "同步和执行数据库迁移"
    
    $migrationPath = Join-Path $ProjectRoot "database\src\migrations"
    if (Test-Path $migrationPath) {
        if ($DryRun) {
            Write-Info "[干运行] 将同步迁移文件: $migrationPath"
            Write-Info "[干运行] 将在服务器上执行: alembic upgrade head"
        } else {
            Write-Info "同步迁移文件..."
            
            # 同步迁移目录
            $remoteMigrationPath = "$RemotePath/database/src/migrations"
            if (Get-Command rsync -ErrorAction SilentlyContinue) {
                & rsync -avz -e "ssh $sshOptions" "$migrationPath\*" "$($sshConfig.User)@$($sshConfig.HostName):`"$remoteMigrationPath`""
            } else {
                & scp $sshOptions -r "$migrationPath\*" "$($sshConfig.User)@$($sshConfig.HostName):`"$remoteMigrationPath`""
            }
            
            if ($LASTEXITCODE -eq 0) {
                Write-Success "迁移文件同步完成"
                
                # 在服务器上执行迁移
                Write-Info "在服务器上执行数据库迁移..."
                $migrationCmd = @"
cd $RemotePath/database && \
export DB_HOST=localhost && \
export DB_PORT=5432 && \
export DB_USER=ai_user && \
export DB_PASSWORD=ai_password && \
export DB_NAME=ai_platform && \
python3 -m alembic upgrade head
"@
                
                $migrationResult = & ssh $sshOptions "$($sshConfig.User)@$($sshConfig.HostName)" $migrationCmd 2>&1
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Success "数据库迁移执行成功"
                    Write-Info $migrationResult
                } else {
                    Write-Error "数据库迁移执行失败"
                    Write-Error $migrationResult
                }
            } else {
                Write-Error "迁移文件同步失败"
            }
        }
    } else {
        Write-Warning "迁移目录不存在: $migrationPath"
    }
    Write-Output ""
} else {
    Write-Info "跳过数据库迁移"
    Write-Output ""
}

# ============================================================
# 6. 数据库数据备份和同步（可选）
# ============================================================
if (-not $SkipDataSync) {
    Write-Step "6/7" "数据库数据备份和同步"
    
    if ($DryRun) {
        Write-Info "[干运行] 将备份本地数据库"
        Write-Info "[干运行] 将同步数据到服务器"
    } else {
        # 备份本地数据库
        Write-Info "备份本地数据库..."
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $localBackupFile = "backup_local_$timestamp.sql"
        
        # 检查本地数据库容器
        $localDbContainer = docker ps --filter "name=enterprise-ai-postgres" --format "{{.Names}}"
        if ($localDbContainer) {
            docker exec enterprise-ai-postgres pg_dump -U ai_user -d ai_platform > $localBackupFile 2>&1
            
            if ($LASTEXITCODE -eq 0 -and (Test-Path $localBackupFile)) {
                Write-Success "本地数据库备份完成: $localBackupFile"
                
                # 上传备份文件到服务器
                Write-Info "上传备份文件到服务器..."
                & scp $sshOptions $localBackupFile "$($sshConfig.User)@$($sshConfig.HostName):/tmp/"
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Success "备份文件已上传到服务器"
                    Write-Info "  注意: 需要在服务器上手动恢复数据（如果需要）"
                    Write-Info "  恢复命令: docker exec -i enterprise-ai-postgres psql -U ai_user -d ai_platform < /tmp/$localBackupFile"
                } else {
                    Write-Warning "上传备份文件失败"
                }
                
                # 删除本地备份文件（可选，保留注释掉）
                # Remove-Item $localBackupFile -Force -ErrorAction SilentlyContinue
            } else {
                Write-Warning "本地数据库备份失败（可能数据库未运行）"
            }
        } else {
            Write-Warning "本地数据库容器未运行，跳过备份"
        }
    }
    Write-Output ""
} else {
    Write-Info "跳过数据同步"
    Write-Output ""
}

# ============================================================
# 7. 服务部署和重启
# ============================================================
Write-Step "7/7" "部署和重启服务"

if ($DryRun) {
    Write-Info "[干运行] 将在服务器上执行: docker compose up -d --build"
} else {
    Write-Info "在服务器上重启服务..."
    
    # 检测使用 docker-compose 还是 docker compose
    $composeCmd = "docker compose"
    $testCmd = "which docker-compose > /dev/null 2>&1 && echo 'docker-compose' || echo 'docker compose'"
    $composeTest = & ssh $sshOptions "$($sshConfig.User)@$($sshConfig.HostName)" $testCmd 2>&1
    if ($composeTest -match "docker-compose") {
        $composeCmd = "docker-compose"
    }
    
    # 构建重启命令
    if ($Services -and $Services -ne "") {
        # 只重启指定的服务
        $serviceList = $Services -split "," | ForEach-Object { $_.Trim() }
        $servicesStr = $serviceList -join " "
        Write-Info "重启指定服务: $servicesStr"
        
        $deployCmd = @"
cd $RemotePath && \
$composeCmd up -d --build $servicesStr && \
$composeCmd ps $servicesStr
"@
    } else {
        # 重启所有服务
        Write-Info "重启所有服务..."
        
        $deployCmd = @"
cd $RemotePath && \
$composeCmd up -d --build && \
$composeCmd ps
"@
    }
    
    Write-Info "执行命令: $deployCmd"
    Write-Output ""
    
    $deployResult = & ssh $sshOptions "$($sshConfig.User)@$($sshConfig.HostName)" $deployCmd 2>&1
    
    Write-Output $deployResult
    Write-Output ""
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "服务部署和重启完成"
        
        # 等待服务启动
        Write-Info "等待服务启动（10秒）..."
        Start-Sleep -Seconds 10
        
        # 检查服务状态
        $statusCmd = "cd $RemotePath && $composeCmd ps --format 'table {{.Name}}\t{{.Status}}' | head -20"
        $statusResult = & ssh $sshOptions "$($sshConfig.User)@$($sshConfig.HostName)" $statusCmd 2>&1
        Write-Output $statusResult
    } else {
        Write-Error "服务部署失败（退出码: $LASTEXITCODE）"
        Write-Warning "请手动检查服务器上的服务状态"
    }
}

Write-Output ""
Write-ColorOutput Cyan "=========================================="
Write-ColorOutput Cyan "同步完成！"
Write-ColorOutput Cyan "=========================================="
Write-Output ""
Write-Info "服务器地址: http://$($sshConfig.HostName)"
Write-Info "  前端: http://$($sshConfig.HostName):3000"
Write-Info "  API网关: http://$($sshConfig.HostName):8080"
Write-Output ""

Pop-Location







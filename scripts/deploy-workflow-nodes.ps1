# 部署工作流节点组件到服务器
# 用途：将美化后的工作流节点组件上传到服务器并重启web-ui服务

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "部署工作流节点组件到服务器" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 服务器配置
$SERVER = "ubuntu@43.143.139.197"
$KEY_FILE = "E:\enterprise-ai-platform\enterprise_ai_platform.pem"
$REMOTE_DIR = "/opt/enterprise-ai-platform"
$NODES_DIR = "web-ui/src/components/nodes"

# 检查密钥文件
if (-not (Test-Path $KEY_FILE)) {
    Write-Host "错误: 找不到密钥文件 $KEY_FILE" -ForegroundColor Red
    exit 1
}

# 检查本地节点目录
if (-not (Test-Path $NODES_DIR)) {
    Write-Host "错误: 找不到节点目录 $NODES_DIR" -ForegroundColor Red
    exit 1
}

Write-Host "`n步骤1: 上传所有节点组件文件..." -ForegroundColor Yellow

# 获取所有节点组件文件
$nodeFiles = Get-ChildItem -Path $NODES_DIR -Filter "*.tsx" | Where-Object { $_.Name -ne "index.ts" }

foreach ($file in $nodeFiles) {
    $fileName = $file.Name
    Write-Host "  上传: $fileName" -ForegroundColor Gray
    
    scp -i $KEY_FILE -o StrictHostKeyChecking=no `
        "$($file.FullName)" `
        "${SERVER}:${REMOTE_DIR}/${NODES_DIR}/"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  错误: 上传 $fileName 失败" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n✅ 所有节点组件文件上传成功" -ForegroundColor Green

Write-Host "`n步骤2: 在服务器上重启web-ui服务..." -ForegroundColor Yellow
ssh -i $KEY_FILE -o StrictHostKeyChecking=no $SERVER @"
cd $REMOTE_DIR
echo '检查web-ui容器状态...'
docker ps --filter 'name=web-ui' --format 'table {{.Names}}\t{{.Status}}'
echo ''
echo '重启web-ui容器...'
docker restart enterprise-ai-web-ui 2>&1
echo ''
echo '等待服务启动（Next.js需要重新编译）...'
sleep 10
echo ''
echo '检查服务状态...'
docker ps --filter 'name=web-ui' --format 'table {{.Names}}\t{{.Status}}'
echo ''
echo '查看最新日志（最后20行）...'
docker logs --tail 20 enterprise-ai-web-ui 2>&1 | tail -20
"@

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n⚠️  警告: 重启web-ui服务时出现问题，但文件已上传" -ForegroundColor Yellow
    Write-Host "请手动重启: docker restart enterprise-ai-web-ui" -ForegroundColor Yellow
} else {
    Write-Host "`n✅ web-ui服务重启成功" -ForegroundColor Green
}

Write-Host "`n==========================================" -ForegroundColor Green
Write-Host "部署完成！" -ForegroundColor Green
Write-Host "`n注意: Next.js需要一些时间来重新编译，请等待30-60秒后刷新浏览器页面" -ForegroundColor Yellow
Write-Host "如果看不到变化，请尝试硬刷新 (Ctrl+Shift+R)" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Green






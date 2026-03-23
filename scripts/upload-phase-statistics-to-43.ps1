# 上传阶段统计页面到43服务器
# 用途：将新开发的阶段统计页面和相关文件上传到43服务器

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "上传阶段统计页面到43服务器" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 服务器配置
$SERVER = "ubuntu@43.143.139.197"
$KEY_FILE = "enterprise_ai_platform.pem"
$REMOTE_DIR = "/opt/enterprise-ai-platform"

# 检查密钥文件
if (-not (Test-Path $KEY_FILE)) {
    Write-Host "错误: 找不到密钥文件 $KEY_FILE" -ForegroundColor Red
    exit 1
}

Write-Host "`n步骤1: 上传阶段统计页面..." -ForegroundColor Yellow
scp -i $KEY_FILE -o StrictHostKeyChecking=no `
    web-ui/src/app/admin/projects/phase-statistics/page.tsx `
    "${SERVER}:${REMOTE_DIR}/web-ui/src/app/admin/projects/phase-statistics/"

if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: 上传阶段统计页面失败" -ForegroundColor Red
    exit 1
}

Write-Host "步骤2: 上传更新的侧边栏组件..." -ForegroundColor Yellow
scp -i $KEY_FILE -o StrictHostKeyChecking=no `
    web-ui/src/components/Layout/Sidebar.tsx `
    "${SERVER}:${REMOTE_DIR}/web-ui/src/components/Layout/"

if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: 上传侧边栏组件失败" -ForegroundColor Red
    exit 1
}

Write-Host "`n步骤3: 在服务器上重启web-ui服务..." -ForegroundColor Yellow
ssh -i $KEY_FILE -o StrictHostKeyChecking=no $SERVER "cd $REMOTE_DIR && echo '检查web-ui容器状态...' && docker ps --filter 'name=web-ui' --format 'table {{.Names}}\t{{.Status}}' && echo '' && echo '重启web-ui容器...' && docker restart enterprise-ai-web-ui 2>&1 && echo '' && echo '等待服务启动...' && sleep 5 && echo '' && echo '检查服务状态...' && docker ps --filter 'name=web-ui' --format 'table {{.Names}}\t{{.Status}}'"

Write-Host "`n==========================================" -ForegroundColor Green
Write-Host "上传完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "`n访问地址: http://43.143.139.197:3000/admin/projects/phase-statistics" -ForegroundColor Cyan





# 测试SSH连接的各种方式
$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  SSH连接诊断" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 测试1: 基本连接（长超时）
Write-Host "测试1: 基本SSH连接（超时30秒）..." -ForegroundColor Cyan
$result1 = ssh -i $SSH_KEY -o ConnectTimeout=30 -o StrictHostKeyChecking=no -o LogLevel=ERROR $SERVER "echo 'Connection OK'" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 连接成功" -ForegroundColor Green
    Write-Host $result1
} else {
    Write-Host "✗ 连接失败" -ForegroundColor Red
    Write-Host $result1
}
Write-Host ""

# 测试2: 禁用Banner
Write-Host "测试2: 禁用Banner..." -ForegroundColor Cyan
$result2 = ssh -i $SSH_KEY -o ConnectTimeout=30 -o StrictHostKeyChecking=no -o LogLevel=ERROR -o SendEnv="" -o SetEnv="" $SERVER "echo 'Connection OK'" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 连接成功" -ForegroundColor Green
    Write-Host $result2
} else {
    Write-Host "✗ 连接失败" -ForegroundColor Red
    Write-Host $result2
}
Write-Host ""

# 测试3: 使用scp测试
Write-Host "测试3: 使用scp测试连接..." -ForegroundColor Cyan
$testFile = "test-ssh-connection.txt"
"test" | Out-File -FilePath $testFile -Encoding utf8
$result3 = scp -i $SSH_KEY -o ConnectTimeout=30 -o StrictHostKeyChecking=no -o LogLevel=ERROR $testFile "${SERVER}:/tmp/" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ scp连接成功" -ForegroundColor Green
    Remove-Item $testFile -ErrorAction SilentlyContinue
} else {
    Write-Host "✗ scp连接失败" -ForegroundColor Red
    Write-Host $result3
    Remove-Item $testFile -ErrorAction SilentlyContinue
}
Write-Host ""

# 测试4: 检查SSH版本兼容性
Write-Host "测试4: 检查SSH版本..." -ForegroundColor Cyan
$sshVersion = ssh -V 2>&1
Write-Host "SSH版本: $sshVersion" -ForegroundColor Yellow
Write-Host ""

# 测试5: 使用rsync（如果可用）
Write-Host "测试5: 检查rsync..." -ForegroundColor Cyan
try {
    $null = Get-Command rsync -ErrorAction Stop
    Write-Host "rsync可用，尝试连接..." -ForegroundColor Green
    $result5 = rsync -avz --progress -e "ssh -i $SSH_KEY -o ConnectTimeout=30 -o StrictHostKeyChecking=no" test.txt enterprise-ai-server:/tmp/ 2>&1
    Write-Host $result5
} catch {
    Write-Host "rsync不可用" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "  诊断完成" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green


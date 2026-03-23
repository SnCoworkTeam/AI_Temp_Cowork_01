# GitHub仓库设置脚本
# 使用方法：执行此脚本后，按照提示操作

Write-Host "=========================================="
Write-Host "GitHub仓库设置向导"
Write-Host "=========================================="
Write-Host ""

# 检查Git配置
Write-Host "1. 检查Git配置..."
$userName = git config user.name
$userEmail = git config user.email

if (-not $userName) {
    Write-Host "  配置Git用户名称..."
    git config user.name "lyb-005"
    Write-Host "  ✓ 用户名称已设置"
} else {
    Write-Host "  ✓ 用户名称: $userName"
}

if (-not $userEmail) {
    Write-Host "  配置Git用户邮箱..."
    git config user.email "lyb-005@163.com"
    Write-Host "  ✓ 用户邮箱已设置"
} else {
    Write-Host "  ✓ 用户邮箱: $userEmail"
}

Write-Host ""

# 检查是否有未提交的更改
Write-Host "2. 检查工作区状态..."
$status = git status --porcelain
if ($status) {
    Write-Host "  发现未提交的更改，准备添加到暂存区..."
    git add .
    Write-Host "  ✓ 文件已添加到暂存区"
    
    # 检查是否有提交
    $hasCommits = git rev-parse --verify HEAD 2>$null
    if (-not $hasCommits) {
        Write-Host "  创建初始提交..."
        git commit -m "Initial commit: Enterprise AI Platform"
        Write-Host "  ✓ 初始提交已创建"
    } else {
        Write-Host "  创建提交..."
        git commit -m "Update: Add project files"
        Write-Host "  ✓ 提交已创建"
    }
} else {
    Write-Host "  ✓ 工作区干净，无需提交"
}

Write-Host ""

# 检查远程仓库
Write-Host "3. 检查远程仓库配置..."
$remote = git remote -v
if (-not $remote) {
    Write-Host "  未配置远程仓库"
    Write-Host ""
    Write-Host "  请选择认证方式："
    Write-Host "  1. HTTPS (使用个人访问令牌)"
    Write-Host "  2. SSH (使用SSH密钥)"
    Write-Host ""
    $choice = Read-Host "请输入选择 (1 或 2)"
    
    if ($choice -eq "1") {
        $remoteUrl = "https://github.com/lyb-005/enterprise-ai-platform.git"
        Write-Host "  使用HTTPS URL: $remoteUrl"
    } elseif ($choice -eq "2") {
        $remoteUrl = "git@github.com:lyb-005/enterprise-ai-platform.git"
        Write-Host "  使用SSH URL: $remoteUrl"
    } else {
        Write-Host "  无效选择，使用HTTPS"
        $remoteUrl = "https://github.com/lyb-005/enterprise-ai-platform.git"
    }
    
    git remote add origin $remoteUrl
    Write-Host "  ✓ 远程仓库已添加"
} else {
    Write-Host "  ✓ 远程仓库已配置"
    Write-Host $remote
}

Write-Host ""

# 设置主分支
Write-Host "4. 设置主分支..."
git branch -M main 2>$null
Write-Host "  ✓ 主分支已设置为 main"

Write-Host ""
Write-Host "=========================================="
Write-Host "设置完成！"
Write-Host "=========================================="
Write-Host ""
Write-Host "下一步操作："
Write-Host ""
Write-Host "1. 在GitHub上创建私有仓库："
Write-Host "   https://github.com/new"
Write-Host "   仓库名称: enterprise-ai-platform"
Write-Host "   选择: Private (私有)"
Write-Host ""
Write-Host "2. 如果使用HTTPS，需要创建个人访问令牌："
Write-Host "   https://github.com/settings/tokens"
Write-Host "   权限: repo (完整仓库访问)"
Write-Host ""
Write-Host "3. 推送代码到GitHub："
Write-Host "   git push -u origin main"
Write-Host ""
Write-Host "   当提示输入密码时，使用个人访问令牌"
Write-Host ""
Write-Host "详细说明请查看: GITHUB_UPLOAD_GUIDE.md"
Write-Host ""










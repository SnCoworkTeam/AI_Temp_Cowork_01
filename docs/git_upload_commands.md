# Git 上传和合并命令

## 📋 完整的上传和合并流程

### 1. 检查当前状态

```powershell
# 查看当前分支
git branch

# 查看更改状态
git status

# 查看更改的文件列表
git status --short
```

### 2. 添加所有更改的文件

```powershell
# 添加所有更改的文件
git add .

# 或者只添加特定目录
git add metadata-service/
git add database/src/migrations/versions/011_add_workflow_versions.py
```

### 3. 提交更改

```powershell
# 提交更改（带描述信息）
git commit -m "feat: 实现工作流版本管理功能

- 添加WorkflowVersion和WorkflowVersionTag数据模型
- 实现版本管理服务（VersionService）
- 实现版本管理API端点
- 创建数据库迁移脚本
- 添加完整的测试套件
- 更新文档和测试指南"
```

### 4. 推送到远程仓库

```powershell
# 推送到当前分支
git push

# 或者推送到指定分支
git push origin <当前分支名>
```

### 5. 切换到主分支并合并

```powershell
# 切换到主分支
git checkout main

# 或者如果主分支叫master
git checkout master

# 拉取最新代码
git pull origin main

# 合并功能分支（假设当前在功能分支）
git merge <功能分支名>

# 或者直接合并当前分支的更改
git merge <功能分支名> --no-ff -m "merge: 合并工作流版本管理功能"
```

### 6. 推送合并后的主分支

```powershell
# 推送合并后的主分支
git push origin main
```

## 🚀 一键执行脚本（推荐）

### 方式1：分步执行（安全）

```powershell
# 步骤1: 检查状态
git status

# 步骤2: 添加文件
git add .

# 步骤3: 提交
git commit -m "feat: 实现工作流版本管理功能"

# 步骤4: 获取当前分支名
$currentBranch = git branch --show-current
Write-Host "当前分支: $currentBranch"

# 步骤5: 推送到远程
git push origin $currentBranch

# 步骤6: 切换到主分支
git checkout main

# 步骤7: 拉取最新代码
git pull origin main

# 步骤8: 合并功能分支
git merge $currentBranch --no-ff -m "merge: 合并工作流版本管理功能到主分支"

# 步骤9: 推送主分支
git push origin main

# 步骤10: 切换回功能分支（可选）
git checkout $currentBranch
```

### 方式2：使用PowerShell脚本

创建 `upload_and_merge.ps1` 文件：

```powershell
# Git上传和合并脚本
param(
    [string]$CommitMessage = "feat: 实现工作流版本管理功能",
    [string]$MainBranch = "main"
)

Write-Host "=== Git上传和合并流程 ===" -ForegroundColor Green

# 1. 检查状态
Write-Host "`n1. 检查Git状态..." -ForegroundColor Yellow
git status

# 2. 添加文件
Write-Host "`n2. 添加所有更改的文件..." -ForegroundColor Yellow
git add .
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: 添加文件失败" -ForegroundColor Red
    exit 1
}

# 3. 提交
Write-Host "`n3. 提交更改..." -ForegroundColor Yellow
git commit -m $CommitMessage
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: 提交失败" -ForegroundColor Red
    exit 1
}

# 4. 获取当前分支
$currentBranch = git branch --show-current
Write-Host "`n4. 当前分支: $currentBranch" -ForegroundColor Cyan

# 5. 推送到远程
Write-Host "`n5. 推送到远程仓库..." -ForegroundColor Yellow
git push origin $currentBranch
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: 推送失败" -ForegroundColor Red
    exit 1
}

# 6. 切换到主分支
Write-Host "`n6. 切换到主分支 ($MainBranch)..." -ForegroundColor Yellow
git checkout $MainBranch
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: 切换分支失败" -ForegroundColor Red
    exit 1
}

# 7. 拉取最新代码
Write-Host "`n7. 拉取最新代码..." -ForegroundColor Yellow
git pull origin $MainBranch
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: 拉取失败" -ForegroundColor Red
    exit 1
}

# 8. 合并功能分支
Write-Host "`n8. 合并功能分支 ($currentBranch)..." -ForegroundColor Yellow
git merge $currentBranch --no-ff -m "merge: 合并工作流版本管理功能到主分支"
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: 合并失败，可能需要手动解决冲突" -ForegroundColor Red
    exit 1
}

# 9. 推送主分支
Write-Host "`n9. 推送主分支..." -ForegroundColor Yellow
git push origin $MainBranch
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: 推送主分支失败" -ForegroundColor Red
    exit 1
}

# 10. 切换回功能分支（可选）
Write-Host "`n10. 切换回功能分支 ($currentBranch)..." -ForegroundColor Yellow
git checkout $currentBranch

Write-Host "`n=== 完成 ===" -ForegroundColor Green
Write-Host "所有更改已成功上传并合并到主分支" -ForegroundColor Green
```

执行脚本：

```powershell
# 使用默认提交信息
.\upload_and_merge.ps1

# 或指定自定义提交信息
.\upload_and_merge.ps1 -CommitMessage "feat: 添加工作流版本管理功能" -MainBranch "main"
```

## ⚠️ 注意事项

### 1. 检查冲突

在合并前，确保没有冲突：

```powershell
# 检查是否有冲突
git status

# 如果有冲突，需要先解决
git merge --abort  # 取消合并
# 解决冲突后
git add .
git commit -m "resolve: 解决合并冲突"
```

### 2. 备份重要更改

```powershell
# 创建备份分支
git branch backup-$(Get-Date -Format "yyyyMMdd-HHmmss")

# 或者创建标签
git tag backup-v1.0
```

### 3. 查看提交历史

```powershell
# 查看提交历史
git log --oneline --graph --all

# 查看特定文件的更改
git log --oneline -- metadata-service/
```

## 🔍 常见问题处理

### 问题1: 推送被拒绝

```powershell
# 如果远程有新的提交，先拉取
git pull origin main --rebase

# 然后再推送
git push origin main
```

### 问题2: 合并冲突

```powershell
# 查看冲突文件
git status

# 手动解决冲突后
git add <冲突文件>
git commit -m "resolve: 解决合并冲突"
```

### 问题3: 撤销错误的提交

```powershell
# 撤销最后一次提交（保留更改）
git reset --soft HEAD~1

# 撤销最后一次提交（丢弃更改）
git reset --hard HEAD~1
```

## 📝 推荐的提交信息格式

```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 构建/工具相关
```

示例：
```
feat: 实现工作流版本管理功能

- 添加WorkflowVersion和WorkflowVersionTag数据模型
- 实现版本管理服务（VersionService）
- 实现版本管理API端点
- 创建数据库迁移脚本
- 添加完整的测试套件
- 更新文档和测试指南
```


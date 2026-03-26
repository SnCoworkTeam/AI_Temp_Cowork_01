# 分支管理

## 概述

本文档定义分支的命名规范、创建流程和管理策略。

## 分支命名规范

### 功能分支 (Feature)
```
feature/功能名称

示例:
- feature/user-authentication
- feature/workflow-designer
- feature/knowledge-base-search
```

### 缺陷修复分支 (Bugfix)
```
bugfix/问题描述

示例:
- bugfix/fix-api-timeout
- bugfix/fix-database-connection
- bugfix/fix-login-issue
```

### 紧急修复分支 (Hotfix)
```
hotfix/版本号

示例:
- hotfix/v1.0.1
- hotfix/v1.1.1
```

### 发布分支 (Release)
```
release/版本号

示例:
- release/v1.0.0
- release/v1.1.0
```

## 分支创建流程

### 创建功能分支
```bash
# 1. 确保develop是最新的
git checkout develop
git pull origin develop

# 2. 创建功能分支
git checkout -b feature/new-feature

# 3. 推送到远程
git push -u origin feature/new-feature
```

### 创建缺陷修复分支
```bash
# 1. 确保develop是最新的
git checkout develop
git pull origin develop

# 2. 创建bugfix分支
git checkout -b bugfix/fix-issue

# 3. 推送到远程
git push -u origin bugfix/fix-issue
```

### 创建发布分支
```bash
# 1. 确保develop是最新的
git checkout develop
git pull origin develop

# 2. 创建release分支
git checkout -b release/v1.0.0

# 3. 推送到远程
git push -u origin release/v1.0.0
```

### 创建紧急修复分支
```bash
# 1. 确保main是最新的
git checkout main
git pull origin main

# 2. 创建hotfix分支
git checkout -b hotfix/v1.0.1

# 3. 推送到远程
git push -u origin hotfix/v1.0.1
```

## 分支管理策略

### 分支生命周期

#### 功能分支
- **创建**: 功能开发开始时
- **合并**: 功能完成后合并到develop
- **删除**: 合并后立即删除

#### 缺陷修复分支
- **创建**: 发现缺陷时
- **合并**: 修复完成后合并到develop
- **删除**: 合并后立即删除

#### 发布分支
- **创建**: 准备发布时
- **合并**: 发布完成后合并到main和develop
- **删除**: 合并后立即删除

#### 紧急修复分支
- **创建**: 发现生产问题时
- **合并**: 修复完成后合并到main和develop
- **删除**: 合并后立即删除

### 分支同步

#### 定期同步develop
```bash
# 每周同步一次develop到功能分支
git checkout feature/my-feature
git merge develop
```

#### 发布前同步
```bash
# 发布前同步develop到release分支
git checkout release/v1.0.0
git merge develop
```

## 分支清理

### 删除本地分支
```bash
# 删除已合并分支
git branch -d feature/old-feature

# 强制删除分支
git branch -D feature/old-feature
```

### 删除远程分支
```bash
# 删除远程分支
git push origin --delete feature/old-feature
```

### 清理脚本
```bash
# 清理所有已合并分支
./scripts/release/cleanup-branches.sh
```

## 分支命名检查

### 自动检查
- Git钩子检查分支名称
- CI/CD检查分支名称
- 脚本验证分支名称

### 命名规则
- 使用小写字母
- 使用连字符分隔
- 避免特殊字符
- 保持简洁明了

## 分支权限

### 创建权限
- 所有团队成员可以创建feature/bugfix分支
- 只有维护者可以创建release/hotfix分支

### 合并权限
- feature/bugfix → develop: 需要审查
- release → main: 需要审查和批准
- hotfix → main: 需要审查和批准

## 分支统计

### 统计指标
- 活跃分支数量
- 已合并分支数量
- 待合并分支数量
- 分支平均生命周期

### 定期审查
- 每周审查活跃分支
- 每月清理过期分支
- 每季度评估分支策略










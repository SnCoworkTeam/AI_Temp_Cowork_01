# Git策略

## 概述

本文档定义项目的Git工作流和分支策略。

## 分支模型

### Git Flow模型

```
main (生产)
  │
  ├── develop (开发)
  │     │
  │     ├── feature/xxx (功能分支)
  │     ├── bugfix/xxx (缺陷修复)
  │     └── release/v1.0.0 (发布分支)
  │
  └── hotfix/v1.0.1 (紧急修复)
```

## 分支说明

### main分支
- **用途**: 生产环境代码
- **保护**: 禁止直接推送
- **合并**: 仅通过release或hotfix分支
- **标签**: 每次合并创建标签

### develop分支
- **用途**: 开发环境代码
- **保护**: 允许团队成员推送
- **合并**: 功能分支和bugfix分支
- **更新**: 定期同步main分支

### feature分支
- **命名**: `feature/功能名称`
- **来源**: develop分支
- **目标**: develop分支
- **生命周期**: 功能完成后删除

### bugfix分支
- **命名**: `bugfix/问题描述`
- **来源**: develop分支
- **目标**: develop分支
- **生命周期**: 修复完成后删除

### release分支
- **命名**: `release/版本号`
- **来源**: develop分支
- **目标**: main和develop分支
- **用途**: 发布准备和测试

### hotfix分支
- **命名**: `hotfix/版本号`
- **来源**: main分支
- **目标**: main和develop分支
- **用途**: 紧急修复生产问题

## 工作流程

### 功能开发流程

```
1. 从develop创建feature分支
   git checkout -b feature/new-feature develop

2. 开发功能
   git commit -m "feat: 添加新功能"

3. 推送到远程
   git push origin feature/new-feature

4. 创建Pull Request到develop

5. 代码审查和合并

6. 删除feature分支
```

### 缺陷修复流程

```
1. 从develop创建bugfix分支
   git checkout -b bugfix/fix-issue develop

2. 修复问题
   git commit -m "fix: 修复问题"

3. 推送到远程
   git push origin bugfix/fix-issue

4. 创建Pull Request到develop

5. 代码审查和合并

6. 删除bugfix分支
```

### 发布流程

```
1. 从develop创建release分支
   git checkout -b release/v1.0.0 develop

2. 更新版本号
   # 更新版本文件

3. 更新CHANGELOG
   # 更新发布说明

4. 测试和修复（在release分支）

5. 合并到main
   git checkout main
   git merge release/v1.0.0
   git tag v1.0.0

6. 合并到develop
   git checkout develop
   git merge release/v1.0.0

7. 删除release分支
```

### 紧急修复流程

```
1. 从main创建hotfix分支
   git checkout -b hotfix/v1.0.1 main

2. 修复问题
   git commit -m "fix: 紧急修复"

3. 合并到main
   git checkout main
   git merge hotfix/v1.0.1
   git tag v1.0.1

4. 合并到develop
   git checkout develop
   git merge hotfix/v1.0.1

5. 删除hotfix分支
```

## 分支保护规则

### main分支保护
- 禁止直接推送
- 需要Pull Request
- 需要代码审查（至少1人）
- 需要状态检查通过
- 禁止强制推送

### develop分支保护
- 允许团队成员推送
- 建议使用Pull Request
- 需要代码审查
- 需要状态检查通过

## 冲突解决

### 合并冲突
1. 更新本地分支
2. 解决冲突
3. 测试验证
4. 提交合并

### 变基冲突
1. 使用交互式变基
2. 解决每个冲突
3. 测试验证
4. 完成变基

## 最佳实践

### 提交规范
- 使用有意义的提交消息
- 每个提交只做一件事
- 频繁提交，少量提交

### 分支管理
- 及时删除已合并分支
- 保持分支名称清晰
- 定期同步develop分支

### 代码审查
- 及时审查
- 提供建设性反馈
- 确保测试覆盖

## 工具和脚本

### 自动化脚本
- `create-feature.sh` - 创建功能分支
- `create-release.sh` - 创建发布分支
- `merge-release.sh` - 合并发布分支

### Git钩子
- pre-commit: 代码检查
- commit-msg: 提交消息检查
- pre-push: 推送前检查










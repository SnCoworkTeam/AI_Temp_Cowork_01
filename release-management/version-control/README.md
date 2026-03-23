# 版本控制策略

## 概述

本文档定义项目的Git版本控制策略，包括分支管理、标签管理和发布流程。

## Git策略

### 分支策略
- **main**: 生产环境代码
- **develop**: 开发环境代码
- **feature/**: 功能分支
- **bugfix/**: 缺陷修复分支
- **hotfix/**: 紧急修复分支
- **release/**: 发布分支

参见 [git-strategy/README.md](./git-strategy/README.md)

## 分支管理

### 分支命名规范
- `feature/功能名称`
- `bugfix/问题描述`
- `hotfix/紧急修复`
- `release/版本号`

参见 [branch-management/README.md](./branch-management/README.md)

## 标签管理

### 标签格式
- 正式版本: `v1.0.0`
- 预发布版本: `v1.0.0-alpha.1`
- 构建版本: `v1.0.0+20240120`

参见 [tag-management/README.md](./tag-management/README.md)

## 提交规范

### 提交消息格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型 (type)
- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档
- `style`: 格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

### 示例
```
feat(workflow): 添加工作流执行功能

实现了基于LangGraph的工作流执行引擎，
支持条件分支和循环。

Closes #123
```

## 代码审查

### 审查要求
- 至少1人审查
- 审查通过后才能合并
- 重要变更需要2人审查

### 审查内容
- 代码质量
- 功能正确性
- 测试覆盖
- 文档完整性

## 合并策略

### 合并到develop
- 功能分支 → develop
- 缺陷修复 → develop
- 需要审查

### 合并到main
- develop → main（通过release分支）
- hotfix → main（直接合并）
- 需要审查和批准

## 版本发布

### 发布流程
1. 创建release分支
2. 更新版本号
3. 更新CHANGELOG
4. 创建Git标签
5. 合并到main和develop

参见 [release-pipeline/README.md](../release-pipeline/README.md)










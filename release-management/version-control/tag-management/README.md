# 标签管理

## 概述

本文档定义Git标签的创建、管理和使用策略。

## 标签格式

### 语义化版本标签
```
vMAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]

示例:
- v1.0.0          (正式版本)
- v1.0.0-alpha.1  (预发布版本)
- v1.0.0-beta.1   (测试版本)
- v1.0.0-rc.1     (发布候选版本)
- v1.0.0+20240120 (构建版本)
```

## 标签类型

### 正式版本标签
- **格式**: `v1.0.0`
- **创建时机**: 生产发布时
- **创建位置**: main分支
- **用途**: 标记生产版本

### 预发布版本标签
- **格式**: `v1.0.0-alpha.1`, `v1.0.0-beta.1`, `v1.0.0-rc.1`
- **创建时机**: 测试和验证阶段
- **创建位置**: release分支或develop分支
- **用途**: 标记测试版本

### 构建版本标签
- **格式**: `v1.0.0+20240120`
- **创建时机**: 每次构建时（可选）
- **创建位置**: 任意分支
- **用途**: 标记构建版本

## 标签创建流程

### 创建正式版本标签
```bash
# 1. 确保在main分支
git checkout main
git pull origin main

# 2. 创建带注释的标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 3. 推送标签
git push origin v1.0.0

# 或推送所有标签
git push origin --tags
```

### 创建预发布版本标签
```bash
# 1. 确保在release分支
git checkout release/v1.0.0

# 2. 创建预发布标签
git tag -a v1.0.0-rc.1 -m "Release candidate 1.0.0-rc.1"

# 3. 推送标签
git push origin v1.0.0-rc.1
```

## 标签管理

### 列出标签
```bash
# 列出所有标签
git tag

# 列出匹配模式的标签
git tag -l "v1.0.*"

# 列出标签详细信息
git tag -l -n1
```

### 查看标签
```bash
# 查看标签信息
git show v1.0.0

# 查看标签指向的提交
git log v1.0.0
```

### 删除标签
```bash
# 删除本地标签
git tag -d v1.0.0

# 删除远程标签
git push origin --delete v1.0.0
```

## 标签验证

### 验证标签格式
```bash
# 使用脚本验证
./scripts/release/validate-tag.sh v1.0.0
```

### 验证标签内容
- 标签指向正确的提交
- 标签消息完整
- 版本号符合规范

## 标签使用

### 检出标签
```bash
# 检出标签（只读）
git checkout v1.0.0

# 基于标签创建分支
git checkout -b release-v1.0.0 v1.0.0
```

### 构建特定版本
```bash
# 基于标签构建
git checkout v1.0.0
docker-compose build
```

### 发布特定版本
```bash
# 基于标签发布
git checkout v1.0.0
./scripts/release/deploy-production.sh
```

## 标签策略

### 标签命名
- 使用语义化版本
- 添加v前缀
- 避免使用特殊字符

### 标签消息
- 包含版本号
- 包含发布日期
- 包含主要变更（可选）

### 标签频率
- 正式版本: 每次生产发布
- 预发布版本: 根据需要
- 构建版本: 可选

## 自动化标签

### CI/CD自动标签
- 发布时自动创建标签
- 自动推送标签
- 自动生成标签消息

### 脚本自动标签
```bash
# 自动创建标签
./scripts/release/create-tag.sh 1.0.0

# 自动更新版本并创建标签
./scripts/release/release.sh --version 1.0.0
```

## 标签历史

### 查看标签历史
```bash
# 按时间排序
git tag --sort=-version:refname

# 查看标签和提交
git log --tags --simplify-by-decoration --pretty="format:%ai %d"
```

### 标签统计
- 总标签数量
- 正式版本数量
- 预发布版本数量
- 最新版本

## 标签最佳实践

### 创建标签
- 使用带注释的标签（-a）
- 提供有意义的标签消息
- 在正确的提交上创建标签

### 管理标签
- 定期清理过期标签
- 保持标签命名一致
- 记录标签创建原因

### 使用标签
- 基于标签构建和部署
- 使用标签进行回滚
- 使用标签追踪版本










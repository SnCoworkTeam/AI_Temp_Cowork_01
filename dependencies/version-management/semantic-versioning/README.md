# 语义化版本管理

## 版本格式

遵循 [Semantic Versioning 2.0.0](https://semver.org/) 规范：

```
MAJOR.MINOR.PATCH

例如: 1.2.3
- 1: MAJOR (主版本号)
- 2: MINOR (次版本号)
- 3: PATCH (补丁版本号)
```

## 版本号规则

### MAJOR (主版本号)
- **何时增加**: 不兼容的API变更
- **示例**: 1.0.0 → 2.0.0
- **影响**: 可能破坏现有功能

### MINOR (次版本号)
- **何时增加**: 向后兼容的功能添加
- **示例**: 1.0.0 → 1.1.0
- **影响**: 不影响现有功能

### PATCH (补丁版本号)
- **何时增加**: 向后兼容的问题修复
- **示例**: 1.0.0 → 1.0.1
- **影响**: 仅修复bug，不添加功能

## 预发布版本

### 格式
```
MAJOR.MINOR.PATCH-IDENTIFIER

例如:
- 1.0.0-alpha.1
- 1.0.0-beta.1
- 1.0.0-rc.1
```

### 标识符
- **alpha**: 内部测试版本
- **beta**: 公开测试版本
- **rc**: 发布候选版本

## 版本管理

### 服务版本
每个服务独立版本管理：

```
mcp-gateway: 1.2.3
workflow-engine: 1.5.0
auth-service: 1.0.5
knowledge-base: 1.1.0
web-ui: 1.3.2
```

### 项目版本
项目整体版本（用于发布）：

```
enterprise-ai-platform: 1.0.0
```

## 版本标记

### Git标签
```bash
# 创建版本标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 推送标签
git push origin v1.0.0
```

### 版本文件
每个服务维护版本信息：

```python
# src/__version__.py
__version__ = "1.0.0"
```

## 版本升级策略

### 自动升级
- **PATCH**: 安全补丁自动升级
- **MINOR**: 测试后升级

### 手动升级
- **MAJOR**: 需要完整评估和测试

## 依赖版本约束

### Python (requirements.txt)
```
# 精确版本
fastapi==0.104.0

# 兼容版本
fastapi>=0.100.0,<0.110.0

# 最新版本（不推荐生产）
fastapi>=0.104.0
```

### Node.js (package.json)
```json
{
  "dependencies": {
    "next": "^14.0.4",  // 兼容小版本
    "react": "~18.2.0"  // 兼容补丁版本
  }
}
```

## 版本发布流程

### 1. 准备发布
- 更新版本号
- 更新CHANGELOG
- 更新依赖版本

### 2. 测试
- 运行测试套件
- 安全扫描
- 性能测试

### 3. 创建标签
- 创建Git标签
- 推送标签

### 4. 发布
- 构建镜像
- 发布文档
- 发布公告

## 版本回滚

### 回滚策略
1. **PATCH回滚**: 直接回滚到上一个PATCH版本
2. **MINOR回滚**: 需要评估兼容性
3. **MAJOR回滚**: 需要完整评估

### 回滚步骤
```bash
# 1. 检出上一个版本
git checkout v1.0.0

# 2. 重新构建
docker-compose build

# 3. 重新部署
docker-compose up -d
```










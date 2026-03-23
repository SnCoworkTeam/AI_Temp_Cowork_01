# 发布脚本

## 脚本说明

### create-release.sh
创建发布版本，包括：
- 创建release分支
- 更新版本号
- 生成CHANGELOG

**使用方法**:
```bash
./scripts/release/create-release.sh --version 1.0.0
./scripts/release/create-release.sh --type minor  # 自动生成版本
```

### merge-release.sh
合并发布分支到main和develop，包括：
- 合并到main
- 创建Git标签
- 合并到develop
- 删除release分支

**使用方法**:
```bash
./scripts/release/merge-release.sh --version 1.0.0
```

### release.sh
完整发布流程，包括：
- 创建发布
- 运行测试
- 预发布部署
- 生产发布

**使用方法**:
```bash
./scripts/release/release.sh --version 1.0.0 --type minor
```

### deploy-staging.sh
部署到预发布环境。

**使用方法**:
```bash
./scripts/release/deploy-staging.sh
```

### deploy-production.sh
部署到生产环境。

**使用方法**:
```bash
./scripts/release/deploy-production.sh
```

### rollback-fast.sh
快速回滚到指定版本。

**使用方法**:
```bash
./scripts/release/rollback-fast.sh v1.0.0
```

### generate-changelog.sh
生成CHANGELOG。

**使用方法**:
```bash
./scripts/release/generate-changelog.sh 1.0.0
```

### verify-staging.sh
验证预发布环境。

**使用方法**:
```bash
./scripts/release/verify-staging.sh
```

### verify-production.sh
验证生产环境。

**使用方法**:
```bash
./scripts/release/verify-production.sh
```

### pre-release-check.sh
发布前检查。

**使用方法**:
```bash
./scripts/release/pre-release-check.sh
```

### cleanup-branches.sh
清理已合并的分支。

**使用方法**:
```bash
./scripts/release/cleanup-branches.sh
```

### validate-tag.sh
验证Git标签格式。

**使用方法**:
```bash
./scripts/release/validate-tag.sh v1.0.0
```

## 典型发布流程

### 标准发布
```bash
# 1. 创建发布
./scripts/release/create-release.sh --type minor

# 2. 测试和修复（在release分支）

# 3. 合并发布
./scripts/release/merge-release.sh --version 1.1.0

# 4. 部署到生产
./scripts/release/deploy-production.sh
```

### 快速发布
```bash
# 使用完整发布脚本
./scripts/release/release.sh --version 1.0.1 --type patch
```

## 注意事项

1. 发布前确保所有测试通过
2. 发布前运行安全扫描
3. 生产发布前备份数据
4. 准备好回滚方案










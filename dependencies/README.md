# 依赖管理和安全扫描系统

## 概述

本目录包含项目的依赖管理、安全扫描和版本管理配置。

## 目录结构

```
dependencies/
├── security-scan/           # 安全扫描
│   ├── snyk-config.yaml    # Snyk配置
│   ├── trivy-config.yaml   # Trivy配置
│   └── security-policies/  # 安全策略
├── dependency-graph/        # 依赖关系图
│   ├── service-dependencies/ # 服务间依赖
│   ├── external-dependencies/ # 外部依赖
│   └── dependency-conflicts/ # 依赖冲突
└── version-management/      # 版本管理
    ├── semantic-versioning/ # 语义化版本
    ├── release-notes/       # 发布说明
    └── upgrade-guides/      # 升级指南
```

## 依赖管理工具

### Python依赖
- **Poetry**: 推荐用于新项目（可选）
- **pip + requirements.txt**: 当前使用
- **Safety**: 安全漏洞扫描
- **pip-audit**: 依赖审计

### Node.js依赖
- **npm**: 包管理器
- **npm audit**: 安全漏洞扫描
- **npm-check-updates**: 依赖更新检查

### Docker依赖
- **Trivy**: 容器镜像漏洞扫描
- **Hadolint**: Dockerfile linting

### 系统级依赖
- **Snyk**: 多语言安全扫描
- **Grype**: 系统包漏洞扫描

## 安全扫描

### 扫描频率
- **每日**: 自动扫描（CI/CD）
- **每周**: 完整扫描报告
- **发布前**: 强制安全扫描

### 扫描范围
- Python依赖（requirements.txt）
- Node.js依赖（package.json）
- Docker镜像
- 系统依赖

## 使用指南

### 运行安全扫描
```bash
# 扫描所有依赖
./scripts/dependencies/scan-all.sh

# 扫描Python依赖
./scripts/dependencies/scan-python.sh

# 扫描Node.js依赖
./scripts/dependencies/scan-nodejs.sh

# 扫描Docker镜像
./scripts/dependencies/scan-docker.sh
```

### 查看依赖关系图
```bash
# 生成依赖关系图
./scripts/dependencies/generate-graph.sh

# 查看服务依赖
cat dependencies/dependency-graph/service-dependencies/graph.json
```

### 依赖更新
```bash
# 检查可更新依赖
./scripts/dependencies/check-updates.sh

# 更新依赖（交互式）
./scripts/dependencies/update-dependencies.sh
```

## 安全策略

参见 [security-policies/README.md](./security-scan/security-policies/README.md)










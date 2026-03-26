# 生产环境部署指南

## 前置要求

- Docker & Docker Compose
- Kubernetes集群（可选）
- 域名和SSL证书
- 数据库备份策略

## 部署步骤

### 1. 准备环境

```bash
# 克隆代码
git clone <repository-url>
cd enterprise-ai-platform

# 切换到生产分支
git checkout production
```

### 2. 配置环境变量

```bash
# 复制生产环境配置
cp .env.production .env

# 编辑配置
# - 数据库连接
# - Redis连接
# - JWT密钥
# - 加密密钥
# - 云存储配置
```

### 3. 构建镜像

```bash
# 构建所有服务镜像
docker-compose -f docker-compose.prod.yml build

# 或单独构建
docker build -t mcp-gateway:latest ./mcp-gateway
docker build -t workflow-engine:latest ./workflow-engine
docker build -t auth-service:latest ./auth-service
docker build -t knowledge-base:latest ./knowledge-base
```

### 4. 启动服务

```bash
# 使用Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# 或使用Kubernetes
kubectl apply -f k8s/
```

### 5. 运行数据库迁移

```bash
docker-compose exec mcp-gateway alembic upgrade head
```

### 6. 验证部署

```bash
# 检查服务健康状态
curl http://your-domain/api/health

# 检查日志
docker-compose logs -f
```

## 监控和日志

### 日志管理
- 使用统一日志格式
- 日志集中收集（ELK Stack）
- 日志轮转和清理

### 监控指标
- 服务健康状态
- API响应时间
- 错误率
- 资源使用情况

## 备份策略

参考 `scripts/backup/README.md` 配置自动备份。

## 安全配置

- 启用HTTPS
- 配置防火墙规则
- 定期更新依赖
- 监控安全漏洞

## 回滚方案

```bash
# 回滚到上一个版本
docker-compose -f docker-compose.prod.yml down
git checkout <previous-version>
docker-compose -f docker-compose.prod.yml up -d
```


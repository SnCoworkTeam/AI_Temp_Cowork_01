# 部署协调智能体服务

自动监控代码变更并协调部署任务的智能体服务。

## 功能特性

- ✅ **自动文件监控** - 监控代码变更（只读）
- ✅ **智能服务分析** - 分析变更影响的服务
- ✅ **依赖关系分析** - 自动分析服务依赖
- ✅ **部署协调** - 调用现有部署脚本
- ✅ **数据同步** - 支持数据库迁移和图数据库同步

## 快速开始

### 1. 启动服务

```bash
# 使用Docker Compose启动
docker-compose up -d deployment-agent

# 查看日志
docker-compose logs -f deployment-agent
```

### 2. 访问API文档

```
http://localhost:8007/docs
```

### 3. 健康检查

```bash
curl http://localhost:8007/health
```

## API端点

### 健康检查
- `GET /health` - 健康检查
- `GET /api/v1/status` - 获取智能体状态

### 部署操作
- `POST /api/v1/deploy` - 手动触发部署
- `POST /api/v1/deploy-full` - 完整部署（所有服务 + 数据同步）
- `POST /api/v1/analyze` - 分析代码变更影响

### 历史记录
- `GET /api/v1/history` - 获取部署历史

## 使用示例

### 手动触发部署

```bash
curl -X POST http://localhost:8007/api/v1/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "services": ["api-gateway", "workflow-engine"],
    "skip_data_sync": false,
    "skip_migration": false,
    "include_neo4j": true
  }'
```

### 完整部署（包含所有数据同步）

```bash
curl -X POST http://localhost:8007/api/v1/deploy-full \
  -H "Content-Type: application/json" \
  -d '{
    "skip_data_sync": false,
    "skip_migration": false,
    "include_neo4j": true
  }'
```

### 分析代码变更

```bash
curl -X POST http://localhost:8007/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "changed_files": [
      "api-gateway/src/main.py",
      "shared_libs/common.py"
    ]
  }'
```

## 配置说明

### 环境变量

- `WATCH_PATH` - 监控的代码路径（默认：`/workspace`）
- `WORKDIR` - 工作目录（默认：`/app/workdir`）
- `SCRIPTS_DIR` - 脚本目录（默认：`/workspace/scripts/deployment`）
- `LOG_LEVEL` - 日志级别（默认：`INFO`）

### 挂载说明

- `/workspace` - 代码目录（只读）
- `/app/workdir` - 工作目录（可写，用于日志和临时文件）
- `/app/keys/` - SSH密钥（只读）
- `/app/config/` - SSH配置（只读）
- `/workspace/scripts` - 脚本目录（只读）

## 工作原理

1. **文件监控** - 使用watchdog库监控代码变更
2. **服务分析** - 根据文件路径分析影响的服务
3. **依赖分析** - 分析服务依赖关系
4. **脚本调用** - 调用现有的部署脚本（`complete-sync.ps1`等）
5. **状态反馈** - 记录部署历史和状态

## 注意事项

- 服务启动后会自动监控代码变更
- 文件变更会触发自动部署（防抖延迟2秒）
- 部署任务在后台异步执行
- 所有部署历史保存在工作目录中





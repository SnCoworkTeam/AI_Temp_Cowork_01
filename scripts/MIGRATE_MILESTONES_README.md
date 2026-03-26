# 里程碑1-4代码和数据迁移指南

## 概述

此脚本用于将阶段1-4的代码和数据同步到服务器。

## 使用方法

### Windows PowerShell

```powershell
# 基本用法（干运行，不实际上传）
.\scripts\migrate_milestones_to_server.ps1 -DryRun

# 实际上传代码
.\scripts\migrate_milestones_to_server.ps1

# 只上传代码，跳过数据
.\scripts\migrate_milestones_to_server.ps1 -SkipData

# 只上传数据，跳过代码
.\scripts\migrate_milestones_to_server.ps1 -SkipCode

# 指定Neo4j服务器（如果Neo4j在独立服务器上）
.\scripts\migrate_milestones_to_server.ps1 -Neo4jServerHost "your-neo4j-server-ip"
```

### Linux/Mac Bash

```bash
# 设置执行权限
chmod +x scripts/migrate_milestones_to_server.sh

# 基本用法
./scripts/migrate_milestones_to_server.sh

# 设置环境变量
export APP_SERVER_HOST="43.143.139.197"
export NEO4j_SERVER_HOST="your-neo4j-server-ip"
export DRY_RUN="true"  # 干运行
./scripts/migrate_milestones_to_server.sh
```

## 配置参数

### PowerShell参数

- `-AppServerHost`: 应用服务器IP（默认: 43.143.139.197）
- `-AppServerUser`: 应用服务器用户名（默认: ubuntu）
- `-AppServerKey`: 应用服务器密钥文件路径（默认: E:\enterprise-ai-platform\enterprise_ai_platform.pem）
- `-Neo4jServerHost`: Neo4j服务器IP（如果Neo4j在独立服务器上）
- `-Neo4jServerUser`: Neo4j服务器用户名（默认: ubuntu）
- `-Neo4jServerKey`: Neo4j服务器密钥文件路径（默认: E:\enterprise-ai-platform\Neo4j.pem）
- `-RemotePath`: 远程服务器路径（默认: /opt/enterprise-ai-platform）
- `-SkipCode`: 跳过代码同步
- `-SkipData`: 跳过数据同步
- `-DryRun`: 干运行模式（不实际上传）

### Bash环境变量

- `APP_SERVER_HOST`: 应用服务器IP
- `APP_SERVER_USER`: 应用服务器用户名
- `APP_SERVER_KEY`: 应用服务器密钥文件路径
- `NEO4J_SERVER_HOST`: Neo4j服务器IP
- `NEO4J_SERVER_USER`: Neo4j服务器用户名
- `NEO4J_SERVER_KEY`: Neo4j服务器密钥文件路径
- `REMOTE_PATH`: 远程服务器路径
- `SKIP_CODE`: 跳过代码同步（true/false）
- `SKIP_DATA`: 跳过数据同步（true/false）
- `DRY_RUN`: 干运行模式（true/false）

## 同步内容

### 里程碑1: OS内核化
- `os-core/` - OS核心模块
- `services/unified_intent_service.py` - 统一意图服务

### 里程碑2: 企业蓝图驱动
- `metadata-service/src/services/ea_vectorization_service.py` - EA向量化服务
- `metadata-service/src/services/ea_knowledge_graph.py` - EA知识图谱服务
- `metadata-service/src/services/ea_hybrid_query.py` - EA混合查询引擎
- `services/enterprise_semantic_engine.py` - 企业语义引擎
- `metadata-service/src/scripts/ea_data_initializer.py` - EA数据初始化脚本

### 里程碑3: 策略与治理
- `os-core/policy_engine.py` - 策略引擎
- `os-core/audit_logger.py` - 审计日志
- `os-core/governance_dashboard.py` - 治理仪表板
- `api-gateway/src/routes/policy_management.py` - 策略管理API
- `config/policies.yaml` - 策略配置文件

### 里程碑4: 自演进AIOS
- `os-core/behavior_collector.py` - 行为数据收集器
- `os-core/optimization_engine.py` - 优化引擎
- `os-core/evolution_manager.py` - 自演进管理器
- `os-core/scenario_recommender.py` - 场景推荐引擎

### 测试文件
- `tests/os_core/` - OS核心测试
- `tests/milestone_integration_test.py` - 里程碑集成测试

### 配置文件
- `docker-compose.yml` - Docker Compose配置
- `os-core/__init__.py` - OS核心模块初始化

## 数据库数据迁移

### PostgreSQL数据迁移

1. **导出本地数据**:
   ```bash
   pg_dump -h localhost -U ai_user -d ai_platform > pg_dump.sql
   ```

2. **上传到服务器**（脚本会自动处理）:
   ```bash
   scp -i enterprise_ai_platform.pem pg_dump.sql ubuntu@43.143.139.197:/opt/enterprise-ai-platform/
   ```

3. **在服务器上导入**:
   ```bash
   ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197
   cd /opt/enterprise-ai-platform
   psql -h localhost -U ai_user -d ai_platform < pg_dump.sql
   ```

### Neo4j数据迁移

如果Neo4j在独立服务器上：

1. **导出本地Neo4j数据**:
   ```bash
   cypher-shell -u neo4j -p password "MATCH (n) RETURN n" > neo4j_export.cypher
   ```

2. **上传到Neo4j服务器**:
   ```bash
   scp -i Neo4j.pem neo4j_export.cypher ubuntu@neo4j-server:/opt/enterprise-ai-platform/
   ```

3. **在Neo4j服务器上导入**:
   ```bash
   ssh -i Neo4j.pem ubuntu@neo4j-server
   cypher-shell -u neo4j -p password < /opt/enterprise-ai-platform/neo4j_export.cypher
   ```

## 服务器端操作

迁移完成后，在服务器上执行：

```bash
# 1. 检查文件是否正确上传
cd /opt/enterprise-ai-platform
ls -la os-core/
ls -la services/
ls -la metadata-service/src/services/

# 2. 设置文件权限
find os-core -type f -name '*.py' -exec chmod 644 {} \;
find services -type f -name '*.py' -exec chmod 644 {} \;
find metadata-service -type f -name '*.py' -exec chmod 644 {} \;

# 3. 重启相关服务
docker-compose restart

# 4. 运行测试验证
pytest tests/milestone_integration_test.py -v
```

## 故障排除

### SSH连接失败

1. 检查密钥文件权限:
   ```powershell
   icacls enterprise_ai_platform.pem /inheritance:r /grant:r "%USERNAME%:R"
   ```

2. 测试SSH连接:
   ```powershell
   ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197 "echo 'Connection OK'"
   ```

### 文件上传失败

1. 检查远程目录权限:
   ```bash
   ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197 "ls -la /opt/enterprise-ai-platform"
   ```

2. 手动创建目录:
   ```bash
   ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197 "mkdir -p /opt/enterprise-ai-platform/os-core"
   ```

### 数据库导入失败

1. 检查数据库连接:
   ```bash
   ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197 "psql -h localhost -U ai_user -d ai_platform -c 'SELECT 1'"
   ```

2. 检查数据库用户权限:
   ```bash
   ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197 "psql -h localhost -U postgres -c '\du'"
   ```

## 注意事项

1. **备份**: 在迁移前，建议备份服务器上的现有代码和数据
2. **测试**: 使用 `-DryRun` 参数先测试，确认无误后再实际执行
3. **权限**: 确保密钥文件权限正确（Windows: 600, Linux: 600）
4. **网络**: 确保网络连接稳定，大文件上传可能需要较长时间
5. **数据库**: 数据库迁移可能需要较长时间，建议在低峰期执行

## 联系支持

如有问题，请检查：
- 服务器日志: `docker-compose logs`
- SSH连接: 测试密钥和网络连接
- 文件权限: 确保远程目录有写入权限


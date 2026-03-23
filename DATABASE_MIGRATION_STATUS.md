# 数据库迁移状态报告

生成时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

## 📊 数据库服务状态

### ✅ 本地数据库
- **状态**: 运行中 (healthy)
- **容器**: enterprise-ai-postgres
- **版本**: PostgreSQL 15.15
- **迁移版本**: **0023** (最新)
- **表数量**: 31

### ✅ 服务器数据库
- **状态**: 运行中 (healthy)
- **容器**: enterprise-ai-postgres
- **迁移版本**: **009_add_agent_tables** (旧版本，需要升级)
- **目标版本**: 0023

## 🔄 迁移文件列表

本地迁移文件（共24个）：
- 001_initial_migration.py
- 002_fix_document_chunk_vector.py
- 003_fix_knowledge_graph_node.py
- 004_fix_workflow_connection.py
- 005_add_performance_indexes.py
- 006_add_conversation_tables.py
- 007_fix_workflow_schema.py
- 009_add_agent_tables.py
- 010_add_token_blacklist.py
- 011_add_workflow_versions.py
- 012_add_workflow_metadata.py
- 013_fix_workflow_executions_schema.py
- 014_fix_mcp_tools_schema.py
- 015_add_metadata_tables.py
- 016_add_operational_metadata.py
- 017_add_processed_at_to_documents.py
- 018_add_knowledge_bases_table.py
- 019_add_prompt_templates.py
- 020_add_entity_mappings.py
- 0023_create_business_activity_tables.py
- 04f8c14d6b00_merge_014_and_020.py

## ⚠️ 需要执行的操作

### 服务器数据库迁移

服务器数据库当前版本是 `009_add_agent_tables`，需要升级到最新版本 `0023`。

### 迁移执行方法

#### 方法1：在服务器主机上运行（推荐）

```bash
cd /opt/enterprise-ai-platform/database
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=ai_user
export DB_PASSWORD=ai_password
export DB_NAME=ai_platform
python3 -m alembic upgrade head
```

#### 方法2：在容器内运行

```bash
docker exec -it enterprise-ai-postgres bash
cd /opt/enterprise-ai-platform/database
alembic upgrade head
```

#### 方法3：使用迁移脚本

如果存在 `run_migration.sh` 或 `run_migration.ps1`：

```bash
cd /opt/enterprise-ai-platform/database
./run_migration.sh
```

## ✅ 验证迁移结果

迁移完成后，验证：

```sql
-- 检查迁移版本
SELECT * FROM alembic_version;

-- 应该显示: 0023

-- 检查表数量
SELECT COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

-- 应该显示: 31
```

## 📋 迁移内容

从 009 到 0023 的主要迁移包括：

1. **010_add_token_blacklist.py** - 添加token黑名单表
2. **011_add_workflow_versions.py** - 添加工作流版本表
3. **012_add_workflow_metadata.py** - 添加工作流元数据表
4. **013_fix_workflow_executions_schema.py** - 修复工作流执行模式
5. **014_fix_mcp_tools_schema.py** - 修复MCP工具模式
6. **015_add_metadata_tables.py** - 添加元数据表
7. **016_add_operational_metadata.py** - 添加操作元数据表
8. **017_add_processed_at_to_documents.py** - 添加文档处理时间字段
9. **018_add_knowledge_bases_table.py** - 添加知识库表
10. **019_add_prompt_templates.py** - 添加提示模板表
11. **020_add_entity_mappings.py** - 添加实体映射表
12. **0023_create_business_activity_tables.py** - 创建业务活动表

## 🎯 下一步

1. ✅ 数据库服务已启动
2. ⏳ 运行服务器数据库迁移
3. ⏳ 验证迁移结果
4. ⏳ 检查所有表是否正确创建


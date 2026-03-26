# 数据库迁移执行指南

## 📋 迁移信息

**迁移文件**: `database/src/migrations/versions/020_add_entity_mappings.py`  
**迁移内容**: 创建 `entity_mappings` 表  
**Revision ID**: 020  
**基于版本**: 019

---

## 🚀 执行步骤

### 方法1: 使用PowerShell脚本（推荐）

```powershell
cd database
.\run_migration.ps1
```

**前提条件**:
- Docker数据库容器正在运行
- 虚拟环境已创建并激活

### 方法2: 手动执行

#### 步骤1: 确保数据库运行

**Docker方式**:
```bash
# 检查容器状态
docker ps --filter "name=enterprise-ai-postgres"

# 如果未运行，启动数据库
docker-compose -f docker-compose.db.yml up -d
```

**本地PostgreSQL方式**:
- 确保PostgreSQL服务正在运行
- 确保端口5432可访问

#### 步骤2: 设置环境变量

```powershell
# Windows PowerShell
$env:DB_HOST = "localhost"
$env:DB_PORT = "5432"
$env:DB_USER = "ai_user"
$env:DB_PASSWORD = "ai_password"
$env:DB_NAME = "ai_platform"
```

```bash
# Linux/Mac
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=ai_user
export DB_PASSWORD=ai_password
export DB_NAME=ai_platform
```

#### 步骤3: 安装依赖

```bash
cd database
pip install -r requirements.txt
```

#### 步骤4: 执行迁移

```bash
cd database
alembic upgrade head
```

---

## ✅ 验证迁移

### 检查当前版本

```bash
cd database
alembic current
```

**预期输出**: `020 (head)`

### 检查表结构

连接到数据库并执行：

```sql
-- 检查表是否存在
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name = 'entity_mappings';

-- 检查表结构
\d entity_mappings

-- 或者使用SQL
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'entity_mappings'
ORDER BY ordinal_position;
```

**预期表结构**:
- `id` (Integer, Primary Key)
- `source_uri` (String(500), Indexed)
- `source_type` (String(50))
- `source_id` (String(255))
- `target_uri` (String(500), Indexed)
- `target_type` (String(50))
- `target_id` (String(255))
- `mapping_type` (String(50), Default: 'auto')
- `confidence` (Float, Default: 0.0)
- `status` (String(20), Default: 'pending')
- `mapped_at` (DateTime)
- `created_at` (DateTime)
- `updated_at` (DateTime)

**预期索引**:
- `idx_source_uri`
- `idx_target_uri`
- `idx_source_target` (联合索引)
- `idx_status`
- `ix_entity_mappings_id`

---

## 🔄 回滚迁移（如果需要）

```bash
cd database
alembic downgrade 019
```

这将删除 `entity_mappings` 表。

---

## ❌ 常见问题

### 1. 连接被拒绝

**错误**: `Connection refused (0x0000274D/10061)`

**解决方案**:
- 确保数据库服务正在运行
- 检查端口是否正确（默认5432）
- 检查防火墙设置
- 如果使用Docker，确保容器正在运行

### 2. 认证失败

**错误**: `password authentication failed`

**解决方案**:
- 检查环境变量中的用户名和密码
- 确认数据库用户权限

### 3. 数据库不存在

**错误**: `database "ai_platform" does not exist`

**解决方案**:
```sql
CREATE DATABASE ai_platform;
```

### 4. 迁移文件未找到

**错误**: `Can't locate revision identified by '020'`

**解决方案**:
- 确认迁移文件存在于 `database/src/migrations/versions/`
- 检查 `down_revision` 是否正确（应该是 '019'）

---

## 📝 迁移后测试

### 1. 测试实体映射API

```bash
# 创建映射
curl -X POST http://localhost:8005/api/entity-mapping/mappings \
  -H "Content-Type: application/json" \
  -d '{
    "source_uri": "entity://knowledge/node/test-123",
    "source_type": "knowledge_graph_node",
    "source_id": "test-123",
    "target_uri": "entity://metadata/business_entity/456",
    "target_type": "business_entity",
    "target_id": "456",
    "mapping_type": "manual",
    "confidence": 0.9,
    "status": "pending"
  }'

# 查询映射
curl "http://localhost:8005/api/entity-mapping/mappings?limit=10"
```

### 2. 测试自动映射

```bash
curl -X POST http://localhost:8005/api/entity-mapping/auto-map \
  -H "Content-Type: application/json" \
  -d '{"similarity_threshold": 0.8}'
```

---

## 📚 相关文档

- [实施完成总结](../IMPLEMENTATION_COMPLETE_SUMMARY.md)
- [实施进度报告](../IMPLEMENTATION_PROGRESS_REPORT.md)

---

**最后更新**: 2025-11-28









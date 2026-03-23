# 数据库迁移问题排查指南

## 常见问题

### 问题1: 迁移版本冲突

**症状：**
```
alembic.util.exc.CommandError: Multiple heads are present
```

**原因：** 存在多个迁移分支，需要合并

**解决方案：**
```bash
# 在服务器上执行
cd /opt/enterprise-ai-platform/database/src/migrations

# 查看当前heads
alembic heads

# 合并heads（如果需要）
alembic merge -m "merge heads" heads

# 然后执行迁移
alembic upgrade head
```

### 问题2: down_revision不匹配

**症状：**
```
alembic.util.exc.CommandError: Can't locate revision identified by '027'
```

**原因：** 迁移文件的`down_revision`指向的版本不存在

**解决方案：**
```bash
# 1. 检查当前数据库版本
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT version_num FROM alembic_version;"

# 2. 查看所有迁移文件
ls -la /opt/enterprise-ai-platform/database/src/migrations/versions/

# 3. 修改028迁移文件的down_revision为实际存在的版本
# 例如：如果当前版本是8323deb6c345，则修改为：
# down_revision = '8323deb6c345'
```

### 问题3: JSONB索引创建失败

**症状：**
```
psycopg2.errors.SyntaxError: syntax error at or near "->"
```

**原因：** Alembic的`op.create_index`对JSONB表达式索引支持有限

**解决方案：**
使用`op.execute`直接执行SQL：
```python
op.execute("""
    CREATE INDEX IF NOT EXISTS idx_data_assets_business_domain 
    ON data_assets USING gin ((classification_dimensions->'business'->>'domain'));
""")
```

### 问题4: 字段已存在

**症状：**
```
psycopg2.errors.DuplicateColumn: column "classification_dimensions" of relation "data_assets" already exists
```

**原因：** 字段已经添加，可能是之前的迁移未完成

**解决方案：**
```bash
# 检查字段是否存在
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c \
  "SELECT column_name FROM information_schema.columns WHERE table_name = 'data_assets' AND column_name = 'classification_dimensions';"

# 如果字段已存在，可以：
# 1. 跳过迁移（如果字段和索引都已创建）
# 2. 或者修改迁移脚本，使用 IF NOT EXISTS
```

### 问题5: 迁移执行超时

**症状：** 迁移执行时间过长或超时

**原因：** 数据量大，索引创建耗时

**解决方案：**
```bash
# 1. 增加超时时间
docker-compose run --rm metadata-service sh -c "cd /database/src/migrations && timeout 300 alembic upgrade head"

# 2. 或者分批执行（先添加字段，再创建索引）
```

---

## 快速修复步骤

### 步骤1: 检查当前状态

```bash
ssh root@43.143.139.197
cd /opt/enterprise-ai-platform

# 检查当前版本
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT version_num FROM alembic_version;"

# 检查字段是否存在
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c \
  "SELECT table_name, column_name FROM information_schema.columns WHERE column_name IN ('classification_dimensions', 'standardized_tags');"
```

### 步骤2: 根据情况选择方案

**情况A: 字段不存在，需要执行迁移**
```bash
# 执行迁移
docker-compose run --rm \
  -e DB_HOST=postgres \
  -e DB_PORT=5432 \
  -e DB_USER=ai_user \
  -e DB_PASSWORD=ai_password \
  -e DB_NAME=ai_platform \
  metadata-service sh -c "cd /database/src/migrations && alembic upgrade head"
```

**情况B: 字段已存在，但迁移记录未更新**
```bash
# 手动更新alembic版本
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c \
  "UPDATE alembic_version SET version_num = '028';"
```

**情况C: 需要修复迁移文件**
```bash
# 1. 修改迁移文件的down_revision
# 2. 重新上传文件
# 3. 执行迁移
```

---

## 手动执行迁移SQL（紧急情况）

如果Alembic迁移失败，可以手动执行SQL：

```sql
-- 1. 添加字段
ALTER TABLE data_assets ADD COLUMN IF NOT EXISTS classification_dimensions JSONB;
ALTER TABLE data_assets ADD COLUMN IF NOT EXISTS standardized_tags JSONB;

ALTER TABLE ai_models ADD COLUMN IF NOT EXISTS classification_dimensions JSONB;
ALTER TABLE ai_models ADD COLUMN IF NOT EXISTS standardized_tags JSONB;

ALTER TABLE workflow_metadata ADD COLUMN IF NOT EXISTS classification_dimensions JSONB;
ALTER TABLE workflow_metadata ADD COLUMN IF NOT EXISTS standardized_tags JSONB;

ALTER TABLE business_entities ADD COLUMN IF NOT EXISTS classification_dimensions JSONB;
ALTER TABLE business_entities ADD COLUMN IF NOT EXISTS standardized_tags JSONB;

-- 2. 创建索引
CREATE INDEX IF NOT EXISTS idx_data_assets_business_domain ON data_assets USING gin ((classification_dimensions->'business'->>'domain'));
CREATE INDEX IF NOT EXISTS idx_data_assets_technical_source ON data_assets USING gin ((classification_dimensions->'technical'->>'source'));
CREATE INDEX IF NOT EXISTS idx_data_assets_standardized_tags ON data_assets USING gin (standardized_tags);

CREATE INDEX IF NOT EXISTS idx_ai_models_lifecycle_status ON ai_models USING gin ((classification_dimensions->'lifecycle'->>'status'));
CREATE INDEX IF NOT EXISTS idx_ai_models_standardized_tags ON ai_models USING gin (standardized_tags);

CREATE INDEX IF NOT EXISTS idx_workflow_business_domain ON workflow_metadata USING gin ((classification_dimensions->'business'->>'domain'));
CREATE INDEX IF NOT EXISTS idx_workflow_standardized_tags ON workflow_metadata USING gin (standardized_tags);

CREATE INDEX IF NOT EXISTS idx_business_entities_business_domain ON business_entities USING gin ((classification_dimensions->'business'->>'domain'));
CREATE INDEX IF NOT EXISTS idx_business_entities_standardized_tags ON business_entities USING gin (standardized_tags);

-- 3. 更新alembic版本
UPDATE alembic_version SET version_num = '028';
```

执行方式：
```bash
docker exec -i enterprise-ai-postgres psql -U ai_user -d ai_platform < migration_028_manual.sql
```









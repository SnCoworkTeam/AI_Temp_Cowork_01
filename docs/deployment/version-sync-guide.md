# 迁移版本同步指南

## 目标
确保本地和服务器上的数据库迁移版本完全一致。

## 问题诊断

### 1. 检查服务器当前版本
```bash
ssh root@43.143.139.197
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT version_num FROM alembic_version;"
```

### 2. 检查服务器heads
```bash
cd /opt/enterprise-ai-platform
docker-compose run --rm \
  -e DB_HOST=postgres \
  -e DB_PORT=5432 \
  -e DB_USER=ai_user \
  -e DB_PASSWORD=ai_password \
  -e DB_NAME=ai_platform \
  metadata-service sh -c 'cd /database/src/migrations && alembic heads'
```

### 3. 检查本地迁移文件
```powershell
# Windows
Get-ChildItem database\src\migrations\versions\028_*.py

# 查看down_revision
Select-String -Path database\src\migrations\versions\028_*.py -Pattern "down_revision"
```

## 常见问题及解决方案

### 问题1: 多个heads（版本分支）

**症状：**
```
alembic.util.exc.CommandError: Multiple heads are present for given argument 'head': 027, 156ed976eba1
```

**解决方案：**
```bash
# 在服务器上执行
cd /opt/enterprise-ai-platform
docker-compose run --rm \
  -e DB_HOST=postgres \
  -e DB_PORT=5432 \
  -e DB_USER=ai_user \
  -e DB_PASSWORD=ai_password \
  -e DB_NAME=ai_platform \
  metadata-service sh -c 'cd /database/src/migrations && alembic merge -m "merge_heads_before_028" heads'
```

### 问题2: down_revision不匹配

**症状：**
```
alembic.util.exc.CommandError: Can't locate revision identified by '027'
```

**可能原因：**
- 服务器上的迁移历史与本地不同
- 028迁移文件的`down_revision`指向了不存在的版本

**解决方案A: 修改down_revision**
如果服务器上存在合并点（如`156ed976eba1`或`8323deb6c345`），修改028文件的`down_revision`：

```python
# 在 database/src/migrations/versions/028_add_classification_dimensions.py
down_revision = '156ed976eba1'  # 或 '8323deb6c345'，根据实际情况
```

**解决方案B: 创建合并迁移**
如果服务器上有多个heads，先合并它们，然后028的down_revision指向合并后的版本。

### 问题3: 版本号不一致

**症状：**
- 服务器版本是`027`，但本地期望`028`
- 或者服务器版本是`156ed976eba1`，但本地期望`028`

**解决方案：**
```bash
# 如果字段已存在，只需更新版本号
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "UPDATE alembic_version SET version_num = '028';"

# 如果字段不存在，执行迁移
cd /opt/enterprise-ai-platform
docker-compose run --rm \
  -e DB_HOST=postgres \
  -e DB_PORT=5432 \
  -e DB_USER=ai_user \
  -e DB_PASSWORD=ai_password \
  -e DB_NAME=ai_platform \
  metadata-service sh -c 'cd /database/src/migrations && alembic upgrade head'
```

## 完整同步流程

### 使用自动化脚本（推荐）

```powershell
.\scripts\sync-migration-versions.ps1
```

### 手动同步步骤

#### 步骤1: 检查服务器状态
```bash
ssh root@43.143.139.197
cd /opt/enterprise-ai-platform

# 检查当前版本
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT version_num FROM alembic_version;"

# 检查heads
docker-compose run --rm \
  -e DB_HOST=postgres \
  -e DB_PORT=5432 \
  -e DB_USER=ai_user \
  -e DB_PASSWORD=ai_password \
  -e DB_NAME=ai_platform \
  metadata-service sh -c 'cd /database/src/migrations && alembic heads'
```

#### 步骤2: 解决版本冲突（如果有）
```bash
# 如果有多个heads，先合并
docker-compose run --rm \
  -e DB_HOST=postgres \
  -e DB_PORT=5432 \
  -e DB_USER=ai_user \
  -e DB_PASSWORD=ai_password \
  -e DB_NAME=ai_platform \
  metadata-service sh -c 'cd /database/src/migrations && alembic merge -m "merge_heads_before_028" heads'
```

#### 步骤3: 上传迁移文件
```powershell
# 从本地Windows机器执行
scp database\src\migrations\versions\028_add_classification_dimensions.py root@43.143.139.197:/opt/enterprise-ai-platform/database/src/migrations/versions/
```

#### 步骤4: 检查并修正down_revision（如果需要）
```bash
# 在服务器上检查028文件的down_revision
cat /opt/enterprise-ai-platform/database/src/migrations/versions/028_add_classification_dimensions.py | grep down_revision

# 如果与当前heads不匹配，需要修改
# 使用vi或nano编辑文件
vi /opt/enterprise-ai-platform/database/src/migrations/versions/028_add_classification_dimensions.py
```

#### 步骤5: 执行迁移
```bash
cd /opt/enterprise-ai-platform
docker-compose run --rm \
  -e DB_HOST=postgres \
  -e DB_PORT=5432 \
  -e DB_USER=ai_user \
  -e DB_PASSWORD=ai_password \
  -e DB_NAME=ai_platform \
  metadata-service sh -c 'cd /database/src/migrations && alembic upgrade head'
```

#### 步骤6: 验证
```bash
# 检查最终版本
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT version_num FROM alembic_version;"

# 检查字段是否存在
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'data_assets' AND column_name = 'classification_dimensions';"

# 检查heads（应该只有一个）
docker-compose run --rm \
  -e DB_HOST=postgres \
  -e DB_PORT=5432 \
  -e DB_USER=ai_user \
  -e DB_PASSWORD=ai_password \
  -e DB_NAME=ai_platform \
  metadata-service sh -c 'cd /database/src/migrations && alembic heads'
```

## 版本一致性检查清单

- [ ] 服务器数据库版本 = `028`
- [ ] 服务器heads数量 = `1`
- [ ] 服务器heads值 = `028`
- [ ] 字段`classification_dimensions`存在于所有元数据表
- [ ] 索引已创建（`idx_data_assets_business_domain`等）
- [ ] 本地迁移文件`028_add_classification_dimensions.py`已上传到服务器
- [ ] 本地和服务器上的028文件内容一致

## 紧急恢复方案

如果迁移失败，可以手动执行SQL：

```sql
-- 1. 添加字段（如果不存在）
ALTER TABLE data_assets ADD COLUMN IF NOT EXISTS classification_dimensions JSONB;
ALTER TABLE data_assets ADD COLUMN IF NOT EXISTS standardized_tags JSONB;
-- ... 其他表类似

-- 2. 创建索引（如果不存在）
CREATE INDEX IF NOT EXISTS idx_data_assets_business_domain ON data_assets USING gin ((classification_dimensions->'business'->>'domain'));
-- ... 其他索引类似

-- 3. 更新版本号
UPDATE alembic_version SET version_num = '028';
```

执行方式：
```bash
docker exec -i enterprise-ai-postgres psql -U ai_user -d ai_platform < migration_028_manual.sql
```









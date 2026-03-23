# 分类体系迁移部署指南

## 部署时间：2025-12-19

## 一、代码部署

### 1.1 上传代码到服务器

将所有修改的文件上传到服务器，主要文件包括：

#### 数据库迁移文件
- `database/src/migrations/versions/028_add_classification_dimensions.py`

#### 后端服务文件
- `metadata-service/src/models/data_asset.py`
- `metadata-service/src/models/ai_model.py`
- `metadata-service/src/models/workflow_metadata.py`
- `metadata-service/src/models/business_entity.py`
- `metadata-service/src/services/metadata_catalog.py`
- `metadata-service/src/api/data_assets.py`
- `metadata-service/src/api/ai_models.py`
- `metadata-service/src/api/workflows.py`
- `metadata-service/src/api/business_entities.py`
- `metadata-service/src/api/classification_migration.py` (新文件)
- `metadata-service/src/utils/classification_migration.py` (新文件)
- `metadata-service/src/main.py`

#### 前端文件
- `web-ui/src/lib/metadata-classification.ts`
- `web-ui/src/lib/classification-standards.ts` (新文件)
- `web-ui/src/components/metadata/ClassificationDimensionEditor.tsx` (新文件)
- `web-ui/src/components/metadata/index.ts`
- `web-ui/src/app/admin/metadata/page.tsx`

### 1.2 部署步骤

```bash
# 1. 进入项目目录
cd /path/to/enterprise-ai-platform

# 2. 拉取最新代码（如果使用Git）
git pull origin main
# 或者
git checkout main
git pull

# 3. 重启后端服务（如果使用Docker）
docker-compose restart metadata-service

# 或者如果直接运行Python服务
cd metadata-service
# 停止旧服务
pkill -f "uvicorn.*metadata"
# 启动新服务
source venv/bin/activate  # 如果使用虚拟环境
uvicorn src.main:app --host 0.0.0.0 --port 8000 &

# 4. 重启前端服务（如果使用Docker）
docker-compose restart web-ui

# 或者如果直接运行Next.js
cd web-ui
# 停止旧服务
pkill -f "next dev"
# 启动新服务
npm run dev &
```

## 二、数据库迁移

### 2.1 备份数据库（重要！）

在执行迁移之前，**必须备份数据库**：

```bash
# PostgreSQL备份
pg_dump -U postgres -d luminaos -F c -f backup_before_028_$(date +%Y%m%d_%H%M%S).dump

# 或者SQL格式备份
pg_dump -U postgres -d luminaos > backup_before_028_$(date +%Y%m%d_%H%M%S).sql
```

### 2.2 检查当前迁移版本

```bash
cd /path/to/enterprise-ai-platform/database

# 查看当前数据库版本
alembic current

# 查看迁移历史
alembic history
```

### 2.3 执行数据库迁移

```bash
# 进入数据库目录
cd /path/to/enterprise-ai-platform/database

# 执行迁移到最新版本
alembic upgrade head
```

**预期输出：**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 027 -> 028, 添加分类维度字段
==================================================
添加分类维度字段到元数据表
==================================================
为 data_assets 表添加分类维度字段...
为 ai_models 表添加分类维度字段...
为 workflow_metadata 表添加分类维度字段...
为 business_entities 表添加分类维度字段...
创建分类维度索引...
分类维度字段添加完成！
==================================================
```

### 2.4 验证迁移结果

```bash
# 连接到PostgreSQL
psql -U postgres -d luminaos

# 检查字段是否添加成功
\d data_assets
\d ai_models
\d workflow_metadata
\d business_entities

# 应该看到新字段：
# - classification_dimensions (jsonb)
# - standardized_tags (jsonb)

# 检查索引是否创建成功
\di idx_*classification*
\di idx_*standardized*

# 退出
\q
```

## 三、测试迁移工具

### 3.1 检查服务状态

```bash
# 检查metadata-service是否运行
curl http://localhost:8000/api/health

# 或者
curl http://your-server-ip:8000/api/health
```

### 3.2 预览迁移结果（试运行）

在正式迁移之前，先预览迁移结果：

```bash
# 预览迁移结果（不实际执行）
curl -X POST "http://localhost:8000/api/classification/migration/preview?limit=10" \
  -H "Content-Type: application/json"

# 或者使用服务器IP
curl -X POST "http://your-server-ip:8000/api/classification/migration/preview?limit=10" \
  -H "Content-Type: application/json"
```

**预期响应：**
```json
{
  "status": "success",
  "preview": {
    "data_assets": [...],
    "ai_models": [...],
    "workflows": [...],
    "business_entities": [...]
  },
  "message": "预览了 10 条记录"
}
```

### 3.3 执行试运行迁移

```bash
# 执行试运行（dry_run=true，不实际更新数据库）
curl -X POST "http://localhost:8000/api/classification/migrate" \
  -H "Content-Type: application/json" \
  -d '{
    "dry_run": true,
    "batch_size": 10
  }'
```

**预期响应：**
```json
{
  "status": "success",
  "dry_run": true,
  "stats": {
    "data_assets": {
      "total": 100,
      "migrated": 100,
      "errors": 0
    },
    "ai_models": {
      "total": 50,
      "migrated": 50,
      "errors": 0
    },
    "workflows": {
      "total": 30,
      "migrated": 30,
      "errors": 0
    },
    "business_entities": {
      "total": 20,
      "migrated": 20,
      "errors": 0
    }
  },
  "message": "试运行完成，未实际更新数据库"
}
```

### 3.4 执行实际迁移

确认试运行结果无误后，执行实际迁移：

```bash
# 执行实际迁移（dry_run=false，实际更新数据库）
curl -X POST "http://localhost:8000/api/classification/migrate" \
  -H "Content-Type: application/json" \
  -d '{
    "dry_run": false,
    "batch_size": 100
  }'
```

**预期响应：**
```json
{
  "status": "success",
  "dry_run": false,
  "stats": {
    "data_assets": {
      "total": 100,
      "migrated": 100,
      "errors": 0
    },
    ...
  },
  "message": "迁移完成"
}
```

### 3.5 验证迁移结果

```bash
# 连接到PostgreSQL
psql -U postgres -d luminaos

# 检查数据是否已迁移
SELECT 
  id, 
  name, 
  classification_dimensions, 
  standardized_tags 
FROM data_assets 
LIMIT 5;

SELECT 
  id, 
  name, 
  classification_dimensions, 
  standardized_tags 
FROM ai_models 
LIMIT 5;

# 退出
\q
```

## 四、测试API接口

### 4.1 测试维度分类查询

```bash
# 测试按业务领域查询数据资产
curl "http://localhost:8000/api/data-assets?business_domain=finance&limit=5"

# 测试按技术来源查询
curl "http://localhost:8000/api/data-assets?technical_source=sap&limit=5"

# 测试按生命周期阶段查询
curl "http://localhost:8000/api/data-assets?lifecycle_stage=production&limit=5"

# 测试按标准化标签查询
curl "http://localhost:8000/api/data-assets?standardized_tag=biz:critical&limit=5"

# 测试AI模型维度查询
curl "http://localhost:8000/api/ai-models?lifecycle_status=active&limit=5"

# 测试工作流维度查询
curl "http://localhost:8000/api/workflows?business_domain=data_integration&limit=5"
```

### 4.2 测试前端界面

1. 访问前端页面：
   ```
   http://your-server-ip:3000/admin/metadata
   ```

2. 测试步骤：
   - 切换到不同标签页（data-assets, workflows, ai-models, business-entities）
   - 点击任意元数据项查看详情
   - 检查"分类维度"部分是否正确显示
   - 验证分类维度编辑器是否正常工作

## 五、回滚方案（如果需要）

如果迁移出现问题，可以回滚：

### 5.1 回滚数据库迁移

```bash
cd /path/to/enterprise-ai-platform/database

# 回滚到上一个版本
alembic downgrade -1

# 或者回滚到特定版本
alembic downgrade 027
```

### 5.2 恢复数据库备份

```bash
# 如果使用dump格式备份
pg_restore -U postgres -d luminaos backup_before_028_YYYYMMDD_HHMMSS.dump

# 如果使用SQL格式备份
psql -U postgres -d luminaos < backup_before_028_YYYYMMDD_HHMMSS.sql
```

## 六、常见问题排查

### 6.1 迁移失败

**问题：** `alembic upgrade head` 失败

**排查步骤：**
1. 检查数据库连接是否正常
2. 检查当前数据库版本：`alembic current`
3. 查看迁移历史：`alembic history`
4. 检查迁移文件语法是否正确
5. 查看详细错误日志

### 6.2 API测试失败

**问题：** 迁移API返回错误

**排查步骤：**
1. 检查metadata-service是否正常运行
2. 检查数据库连接配置
3. 查看服务日志：`docker-compose logs metadata-service`
4. 检查API路由是否正确注册

### 6.3 前端显示异常

**问题：** 前端无法显示分类维度

**排查步骤：**
1. 检查前端服务是否正常运行
2. 检查浏览器控制台是否有错误
3. 检查API响应是否包含新字段
4. 清除浏览器缓存并刷新

## 七、性能优化建议

### 7.1 大批量数据迁移

如果数据量很大（>10万条），建议：

1. **分批迁移**：
   ```bash
   # 使用较小的batch_size
   curl -X POST "http://localhost:8000/api/classification/migrate" \
     -H "Content-Type: application/json" \
     -d '{"dry_run": false, "batch_size": 50}'
   ```

2. **在低峰期执行**：选择业务低峰期执行迁移

3. **监控资源使用**：监控数据库CPU、内存、磁盘IO

### 7.2 索引优化

迁移完成后，可以分析索引使用情况：

```sql
-- 分析索引使用情况
ANALYZE data_assets;
ANALYZE ai_models;
ANALYZE workflow_metadata;
ANALYZE business_entities;

-- 查看索引大小
SELECT 
  schemaname,
  tablename,
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE indexname LIKE 'idx_%classification%' OR indexname LIKE 'idx_%standardized%'
ORDER BY pg_relation_size(indexrelid) DESC;
```

## 八、检查清单

部署前检查：
- [ ] 数据库已备份
- [ ] 代码已上传到服务器
- [ ] 服务已重启
- [ ] 数据库连接正常

迁移前检查：
- [ ] 已执行预览迁移
- [ ] 已执行试运行迁移
- [ ] 试运行结果已审核
- [ ] 已选择合适的时间窗口

迁移后检查：
- [ ] 数据库迁移成功
- [ ] 字段和索引已创建
- [ ] 数据迁移成功
- [ ] API接口测试通过
- [ ] 前端界面显示正常
- [ ] 性能指标正常

## 九、联系支持

如果遇到问题，请提供以下信息：
1. 错误日志
2. 数据库版本信息
3. 迁移执行命令和输出
4. API测试结果
5. 前端控制台错误信息

---

**部署完成后，请更新部署记录并通知相关团队成员。**









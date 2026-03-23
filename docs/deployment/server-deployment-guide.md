# 分类体系迁移服务器部署指南

## 📋 部署目标

**服务器IP：** 43.143.139.197  
**部署路径：** /opt/enterprise-ai-platform  
**部署时间：** 2025-12-19

---

## 🚀 快速部署步骤

### 方法一：使用自动化脚本（推荐）

```powershell
# 在本地Windows环境执行
cd e:\enterprise-ai-platform
.\scripts\deploy-classification-migration-to-server.ps1
```

脚本会自动完成：
1. ✅ SSH连接检查
2. ✅ 代码文件上传
3. ✅ 数据库备份
4. ✅ 数据库迁移
5. ✅ 服务重启
6. ✅ 迁移工具测试

### 方法二：手动部署

#### 1. 上传代码文件

```powershell
# 方式1: 使用scp逐个上传
scp database\src\migrations\versions\028_add_classification_dimensions.py root@43.143.139.197:/opt/enterprise-ai-platform/database/src/migrations/versions/

scp metadata-service\src\models\data_asset.py root@43.143.139.197:/opt/enterprise-ai-platform/metadata-service/src/models/
scp metadata-service\src\models\ai_model.py root@43.143.139.197:/opt/enterprise-ai-platform/metadata-service/src/models/
scp metadata-service\src\models\workflow_metadata.py root@43.143.139.197:/opt/enterprise-ai-platform/metadata-service/src/models/
scp metadata-service\src\models\business_entity.py root@43.143.139.197:/opt/enterprise-ai-platform/metadata-service/src/models/

scp metadata-service\src\services\metadata_catalog.py root@43.143.139.197:/opt/enterprise-ai-platform/metadata-service/src/services/

scp metadata-service\src\api\data_assets.py root@43.143.139.197:/opt/enterprise-ai-platform/metadata-service/src/api/
scp metadata-service\src\api\ai_models.py root@43.143.139.197:/opt/enterprise-ai-platform/metadata-service/src/api/
scp metadata-service\src\api\workflows.py root@43.143.139.197:/opt/enterprise-ai-platform/metadata-service/src/api/
scp metadata-service\src\api\business_entities.py root@43.143.139.197:/opt/enterprise-ai-platform/metadata-service/src/api/
scp metadata-service\src\api\classification_migration.py root@43.143.139.197:/opt/enterprise-ai-platform/metadata-service/src/api/
scp metadata-service\src\utils\classification_migration.py root@43.143.139.197:/opt/enterprise-ai-platform/metadata-service/src/utils/
scp metadata-service\src\main.py root@43.143.139.197:/opt/enterprise-ai-platform/metadata-service/src/

scp web-ui\src\lib\metadata-classification.ts root@43.143.139.197:/opt/enterprise-ai-platform/web-ui/src/lib/
scp web-ui\src\lib\classification-standards.ts root@43.143.139.197:/opt/enterprise-ai-platform/web-ui/src/lib/
scp web-ui\src\components\metadata\ClassificationDimensionEditor.tsx root@43.143.139.197:/opt/enterprise-ai-platform/web-ui/src/components/metadata/
scp web-ui\src\components\metadata\index.ts root@43.143.139.197:/opt/enterprise-ai-platform/web-ui/src/components/metadata/
scp web-ui\src\app\admin\metadata\page.tsx root@43.143.139.197:/opt/enterprise-ai-platform/web-ui/src/app/admin/metadata/
```

```bash
# 方式2: 在服务器上使用git pull（如果使用Git）
ssh root@43.143.139.197
cd /opt/enterprise-ai-platform
git pull origin main
```

#### 2. 备份数据库

```bash
# SSH到服务器
ssh root@43.143.139.197

# 创建备份目录
mkdir -p /backup/database

# 执行备份
docker exec enterprise-ai-postgres pg_dump -U ai_user -d ai_platform -F c -f /tmp/backup_before_028_$(date +%Y%m%d_%H%M%S).dump

# 复制到备份目录
docker cp enterprise-ai-postgres:/tmp/backup_before_028_*.dump /backup/database/
```

#### 3. 执行数据库迁移

```bash
# 在服务器上执行
cd /opt/enterprise-ai-platform

# 检查当前版本
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT version_num FROM alembic_version;"

# 执行迁移
docker-compose run --rm \
  -e DB_HOST=postgres \
  -e DB_PORT=5432 \
  -e DB_USER=ai_user \
  -e DB_PASSWORD=ai_password \
  -e DB_NAME=ai_platform \
  metadata-service sh -c "cd /database/src/migrations && alembic upgrade head"

# 验证迁移结果
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c \
  "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'data_assets' AND column_name = 'classification_dimensions';"
```

#### 4. 重启服务

```bash
# 重启metadata-service
cd /opt/enterprise-ai-platform
docker-compose restart metadata-service

# 重启web-ui（如果需要）
docker-compose restart web-ui

# 查看服务状态
docker-compose ps metadata-service web-ui
```

#### 5. 测试迁移工具

```bash
# 预览迁移结果
curl -X GET "http://43.143.139.197:8005/api/classification/migration/preview?limit=10"

# 试运行迁移
curl -X POST "http://43.143.139.197:8005/api/classification/migrate" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true, "batch_size": 10}'

# 执行实际迁移
curl -X POST "http://43.143.139.197:8005/api/classification/migrate" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false, "batch_size": 100}'
```

#### 6. 测试API接口

```bash
# 测试维度分类查询
curl "http://43.143.139.197:8005/api/data-assets?business_domain=finance&limit=5"
curl "http://43.143.139.197:8005/api/data-assets?technical_source=sap&limit=5"
curl "http://43.143.139.197:8005/api/data-assets?standardized_tag=biz:critical&limit=5"
```

---

## 📝 详细部署步骤

### 步骤1: 准备部署环境

**本地环境：**
- ✅ 确保所有代码已提交
- ✅ 确保SSH密钥已配置
- ✅ 确保可以SSH连接到服务器

**服务器环境：**
- ✅ Docker和docker-compose已安装
- ✅ PostgreSQL容器运行正常
- ✅ metadata-service容器可以访问

### 步骤2: 上传代码

**推荐方式：使用自动化脚本**

```powershell
.\scripts\deploy-classification-migration-to-server.ps1
```

**手动方式：**

参考上面的"方法二：手动部署"部分

### 步骤3: 执行数据库迁移

**在服务器上执行：**

```bash
ssh root@43.143.139.197
cd /opt/enterprise-ai-platform

# 备份数据库
docker exec enterprise-ai-postgres pg_dump -U ai_user -d ai_platform -F c -f /tmp/backup_before_028_$(date +%Y%m%d_%H%M%S).dump
docker cp enterprise-ai-postgres:/tmp/backup_before_028_*.dump /backup/database/

# 执行迁移
docker-compose run --rm \
  -e DB_HOST=postgres \
  -e DB_PORT=5432 \
  -e DB_USER=ai_user \
  -e DB_PASSWORD=ai_password \
  -e DB_NAME=ai_platform \
  metadata-service sh -c "cd /database/src/migrations && alembic upgrade head"

# 验证
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c \
  "SELECT column_name FROM information_schema.columns WHERE table_name = 'data_assets' AND column_name IN ('classification_dimensions', 'standardized_tags');"
```

### 步骤4: 重启服务

```bash
cd /opt/enterprise-ai-platform
docker-compose restart metadata-service
docker-compose restart web-ui

# 等待服务启动
sleep 10

# 检查服务状态
docker-compose ps
curl http://localhost:8005/api/health
```

### 步骤5: 测试迁移工具

```bash
# 1. 预览迁移结果
curl -X GET "http://43.143.139.197:8005/api/classification/migration/preview?limit=10" | jq

# 2. 试运行迁移
curl -X POST "http://43.143.139.197:8005/api/classification/migrate" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true, "batch_size": 10}' | jq

# 3. 执行实际迁移（确认无误后）
curl -X POST "http://43.143.139.197:8005/api/classification/migrate" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false, "batch_size": 100}' | jq
```

### 步骤6: 验证前端

访问：`http://43.143.139.197:3000/admin/metadata`

检查：
- ✅ 分类维度是否正确显示
- ✅ 详情弹窗中是否有"分类维度"部分
- ✅ 维度查询功能是否正常

---

## 🔍 验证清单

### 数据库验证

```bash
# 检查字段是否存在
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c \
  "SELECT table_name, column_name, data_type 
   FROM information_schema.columns 
   WHERE column_name IN ('classification_dimensions', 'standardized_tags')
   ORDER BY table_name, column_name;"

# 检查索引是否存在
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c \
  "SELECT indexname FROM pg_indexes 
   WHERE indexname LIKE 'idx_%classification%' OR indexname LIKE 'idx_%standardized%';"
```

### API验证

```bash
# 健康检查
curl http://43.143.139.197:8005/api/health

# 测试维度查询
curl "http://43.143.139.197:8005/api/data-assets?business_domain=finance&limit=1"
curl "http://43.143.139.197:8005/api/ai-models?lifecycle_status=active&limit=1"
curl "http://43.143.139.197:8005/api/workflows?business_domain=data_integration&limit=1"
```

### 前端验证

1. 访问 `http://43.143.139.197:3000/admin/metadata`
2. 切换到不同标签页
3. 点击任意元数据项查看详情
4. 检查"分类维度"部分是否正确显示

---

## 🆘 问题排查

### 问题1: SSH连接失败

**症状：** 无法SSH连接到服务器

**解决方案：**
```bash
# 检查SSH配置
ssh -v root@43.143.139.197

# 检查网络连接
ping 43.143.139.197

# 检查SSH密钥
ssh-add -l
```

### 问题2: 文件上传失败

**症状：** scp上传文件失败

**解决方案：**
```bash
# 检查服务器磁盘空间
ssh root@43.143.139.197 "df -h"

# 检查文件权限
ssh root@43.143.139.197 "ls -la /opt/enterprise-ai-platform"

# 手动创建目录
ssh root@43.143.139.197 "mkdir -p /opt/enterprise-ai-platform/metadata-service/src/utils"
```

### 问题3: 数据库迁移失败

**症状：** alembic upgrade head 失败

**解决方案：**
```bash
# 查看详细错误
docker-compose run --rm metadata-service sh -c "cd /database/src/migrations && alembic upgrade head -v"

# 检查数据库连接
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT 1;"

# 检查迁移文件语法
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT version_num FROM alembic_version;"
```

### 问题4: 服务启动失败

**症状：** metadata-service无法启动

**解决方案：**
```bash
# 查看服务日志
docker-compose logs metadata-service

# 检查服务配置
docker-compose config

# 重启服务
docker-compose restart metadata-service

# 查看容器状态
docker ps -a | grep metadata
```

### 问题5: API测试失败

**症状：** API返回404或500错误

**解决方案：**
```bash
# 检查服务是否运行
curl http://43.143.139.197:8005/api/health

# 检查API路由
curl http://43.143.139.197:8005/api/docs

# 查看服务日志
docker-compose logs metadata-service | tail -50
```

---

## 📋 部署后检查清单

- [ ] 所有代码文件已上传
- [ ] 数据库已备份
- [ ] 数据库迁移成功
- [ ] 字段和索引已创建
- [ ] metadata-service已重启
- [ ] web-ui已重启（如果需要）
- [ ] 服务健康检查通过
- [ ] 预览迁移成功
- [ ] 试运行迁移成功
- [ ] 实际数据迁移成功（可选）
- [ ] API测试通过
- [ ] 前端显示正常

---

## 🔄 回滚方案

如果部署出现问题，可以回滚：

### 回滚数据库迁移

```bash
ssh root@43.143.139.197
cd /opt/enterprise-ai-platform

# 回滚到上一个版本
docker-compose run --rm \
  -e DB_HOST=postgres \
  -e DB_PORT=5432 \
  -e DB_USER=ai_user \
  -e DB_PASSWORD=ai_password \
  -e DB_NAME=ai_platform \
  metadata-service sh -c "cd /database/src/migrations && alembic downgrade -1"
```

### 恢复数据库备份

```bash
# 恢复备份
docker exec -i enterprise-ai-postgres pg_restore -U ai_user -d ai_platform -c < /backup/database/backup_before_028_YYYYMMDD_HHMMSS.dump
```

---

**部署完成后，请更新部署记录并通知相关团队成员。**









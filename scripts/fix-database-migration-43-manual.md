# 修复43服务器数据库迁移 - 手动执行命令

## 问题描述
- `workflow_metadata` 表不存在
- `data_assets` 表缺少 `classification_dimensions` 列
- 数据库迁移版本是 `999999`（占位符，未正确执行）

## 执行步骤

### 步骤1: 上传修复后的迁移文件

在本地 PowerShell 中执行：

```powershell
cd e:\enterprise-ai-platform

# 上传修复后的迁移文件
scp -i enterprise_ai_platform.pem -o StrictHostKeyChecking=no `
    database/src/migrations/versions/028_add_classification_dimensions.py `
    ubuntu@43.143.139.197:/opt/enterprise-ai-platform/database/src/migrations/versions/
```

### 步骤2: 连接到服务器

```powershell
ssh -i enterprise_ai_platform.pem -o StrictHostKeyChecking=no ubuntu@43.143.139.197
```

### 步骤3: 在服务器上执行以下命令

```bash
# 进入项目目录
cd /opt/enterprise-ai-platform

# 检查当前迁移状态
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT version_num FROM alembic_version;"

# 进入数据库目录
cd database

# 执行数据库迁移
docker exec -w /app/database enterprise-ai-postgres alembic upgrade head

# 验证迁移结果 - 检查 workflow_metadata 表是否存在
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name='workflow_metadata';"

# 验证迁移结果 - 检查 data_assets 表的 classification_dimensions 列
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT column_name FROM information_schema.columns WHERE table_name='data_assets' AND column_name='classification_dimensions';"

# 重启 metadata-service 容器
docker restart enterprise-ai-metadata-service

# 等待服务启动
sleep 5

# 测试 API
curl -s http://localhost:8005/api/data-assets?skip=0&limit=5 | head -20
```

## 预期结果

1. **迁移执行成功**：应该看到迁移日志，包括创建 `workflow_metadata` 表和添加 `classification_dimensions` 列
2. **workflow_metadata 表存在**：查询应该返回 1 行
3. **classification_dimensions 列存在**：查询应该返回该列名
4. **API 正常**：测试 API 应该返回 JSON 数据而不是 500 错误

## 如果遇到错误

### 错误1: 迁移版本冲突
如果提示迁移版本冲突，可以尝试：
```bash
# 查看迁移历史
docker exec -w /app/database enterprise-ai-postgres alembic history

# 如果需要，可以手动设置版本
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "UPDATE alembic_version SET version_num='027';"
```

### 错误2: 表已存在但结构不对
如果表已存在但缺少字段，迁移会自动添加缺失的字段。

### 错误3: 容器无法访问
确保容器正在运行：
```bash
docker ps | grep enterprise-ai-postgres
docker ps | grep enterprise-ai-metadata-service
```

## 验证清单

- [ ] 迁移文件已上传到服务器
- [ ] 迁移执行成功，无错误
- [ ] `workflow_metadata` 表存在
- [ ] `data_assets.classification_dimensions` 列存在
- [ ] metadata-service 容器已重启
- [ ] API 测试返回正常数据（非 500 错误）

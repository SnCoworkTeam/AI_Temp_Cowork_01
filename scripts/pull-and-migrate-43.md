# 从Git拉取并执行数据库迁移 - 43服务器

## 执行步骤

### 步骤1: 连接到服务器

```powershell
ssh -i enterprise_ai_platform.pem -o StrictHostKeyChecking=no ubuntu@43.143.139.197
```

### 步骤2: 在服务器上执行以下命令

```bash
# 1. 进入项目目录
cd /opt/enterprise-ai-platform

# 2. 拉取最新代码（包括修复后的迁移文件）
git pull origin main

# 3. 检查当前迁移状态
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT version_num FROM alembic_version;"

# 4. 进入数据库目录
cd database

# 5. 执行数据库迁移（关键步骤）
docker exec -w /app/database enterprise-ai-postgres alembic upgrade head

# 6. 验证迁移结果 - 检查 workflow_metadata 表是否存在
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name='workflow_metadata';"

# 7. 验证迁移结果 - 检查 data_assets 表的 classification_dimensions 列
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT column_name FROM information_schema.columns WHERE table_name='data_assets' AND column_name='classification_dimensions';"

# 8. 重启 metadata-service 容器
docker restart enterprise-ai-metadata-service

# 9. 等待服务启动
sleep 5

# 10. 测试 API（应该返回数据而不是500错误）
curl -s http://localhost:8005/api/data-assets?skip=0&limit=5 | head -20
```

## 预期结果

1. **Git pull 成功**：看到 "Updating..." 或 "Already up to date"
2. **迁移执行成功**：应该看到迁移日志，包括创建 `workflow_metadata` 表和添加 `classification_dimensions` 列
3. **workflow_metadata 表存在**：查询应该返回 1 行
4. **classification_dimensions 列存在**：查询应该返回该列名
5. **API 正常**：测试 API 应该返回 JSON 数据而不是 500 错误

## 如果遇到错误

### 错误1: Git pull 失败
如果 Git pull 失败，可能是网络问题或需要配置 Git：
```bash
# 检查 Git 远程仓库配置
git remote -v

# 如果需要，重新配置
git remote set-url origin https://github.com/PMLiuyubin/enterprise-ai-platform.git
```

### 错误2: 迁移版本冲突
如果提示迁移版本冲突，可以尝试：
```bash
# 查看迁移历史
docker exec -w /app/database enterprise-ai-postgres alembic history

# 如果需要，可以手动设置版本
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "UPDATE alembic_version SET version_num='027';"
```

### 错误3: 容器无法访问
确保容器正在运行：
```bash
docker ps | grep enterprise-ai-postgres
docker ps | grep enterprise-ai-metadata-service
```

## 验证清单

- [ ] Git pull 成功，代码已更新
- [ ] 迁移文件已更新（028_add_classification_dimensions.py）
- [ ] 迁移执行成功，无错误
- [ ] `workflow_metadata` 表存在
- [ ] `data_assets.classification_dimensions` 列存在
- [ ] metadata-service 容器已重启
- [ ] API 测试返回正常数据（非 500 错误）

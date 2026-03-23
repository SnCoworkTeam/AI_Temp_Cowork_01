# 分类体系迁移快速指南

## 📋 概述

本文档提供分类体系迁移的快速部署和测试指南。完整的部署文档请参考：`docs/deployment/classification-migration-deployment.md`

## 🚀 快速开始

### 1. 代码部署

确保所有修改的代码已上传到服务器，主要文件包括：
- 数据库迁移文件：`database/src/migrations/versions/028_add_classification_dimensions.py`
- 后端服务文件（models, services, api）
- 前端文件（components, lib）

### 2. 数据库迁移

```bash
# 1. 备份数据库（重要！）
pg_dump -U postgres -d luminaos -F c -f backup_before_028_$(date +%Y%m%d_%H%M%S).dump

# 2. 执行迁移
cd database
alembic upgrade head

# 3. 验证迁移
psql -U postgres -d luminaos -c "\d data_assets" | grep classification_dimensions
```

### 3. 测试迁移工具

```bash
# 预览迁移结果（不实际执行）
curl -X POST "http://localhost:8000/api/classification/migration/preview?limit=10" \
  -H "Content-Type: application/json"

# 试运行迁移（不更新数据库）
curl -X POST "http://localhost:8000/api/classification/migrate" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true, "batch_size": 10}'

# 执行实际迁移（更新数据库）
curl -X POST "http://localhost:8000/api/classification/migrate" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false, "batch_size": 100}'
```

### 4. 测试API接口

```bash
# 测试维度分类查询
curl "http://localhost:8000/api/data-assets?business_domain=finance&limit=5"
curl "http://localhost:8000/api/data-assets?technical_source=sap&limit=5"
curl "http://localhost:8000/api/data-assets?standardized_tag=biz:critical&limit=5"
```

### 5. 验证前端

访问 `http://your-server:3000/admin/metadata`，检查分类维度是否正确显示。

## 📝 自动化脚本

### Linux/Mac

```bash
# 使用自动化部署脚本
chmod +x scripts/deploy-classification-migration.sh
./scripts/deploy-classification-migration.sh
```

### Windows

```powershell
# 使用PowerShell测试脚本
.\scripts\test-classification-migration.ps1
```

## ⚠️ 注意事项

1. **必须备份数据库**：在执行迁移前，务必备份数据库
2. **先试运行**：在实际迁移前，先执行试运行（dry_run=true）验证结果
3. **低峰期执行**：大批量数据迁移建议在业务低峰期执行
4. **监控资源**：迁移过程中监控数据库CPU、内存使用情况

## 🔄 回滚方案

如果迁移出现问题，可以回滚：

```bash
# 回滚数据库迁移
cd database
alembic downgrade -1

# 恢复数据库备份
pg_restore -U postgres -d luminaos backup_before_028_YYYYMMDD_HHMMSS.dump
```

## 📚 相关文档

- 完整部署指南：`docs/deployment/classification-migration-deployment.md`
- 实施总结：`docs/implementation/phase1-phase2-implementation-summary.md`
- 可行性分析：`docs/analysis/metadata-classification-refactoring-feasibility.md`

## 🆘 问题排查

如果遇到问题，请检查：
1. 服务是否正常运行：`curl http://localhost:8000/api/health`
2. 数据库连接是否正常
3. 迁移文件语法是否正确
4. 查看服务日志：`docker-compose logs metadata-service`

## ✅ 检查清单

- [ ] 数据库已备份
- [ ] 代码已部署
- [ ] 数据库迁移成功
- [ ] 试运行迁移通过
- [ ] 实际迁移成功
- [ ] API测试通过
- [ ] 前端显示正常

---

**部署完成后，请更新部署记录并通知相关团队成员。**









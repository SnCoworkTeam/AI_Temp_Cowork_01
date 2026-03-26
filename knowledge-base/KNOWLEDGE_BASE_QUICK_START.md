# 知识库功能快速开始指南

## 🚀 快速执行步骤

### 1. 运行数据库迁移（必须）

**Windows:**
```powershell
cd database
.\run_migration_018.ps1
```

**Linux/Mac:**
```bash
cd database
alembic upgrade head
```

**验证迁移成功:**
```sql
-- 连接到数据库后执行
SELECT table_name FROM information_schema.tables 
WHERE table_name = 'knowledge_bases';

SELECT column_name FROM information_schema.columns 
WHERE table_name = 'documents' AND column_name = 'knowledge_base_id';
```

### 2. 重启服务（如果正在运行）

```bash
# 重启知识库服务
docker-compose restart knowledge-base

# 或重启所有服务
docker-compose restart
```

### 3. 测试API

**快速测试（使用测试脚本）:**
```bash
cd knowledge-base
python test_knowledge_bases_api.py
```

**手动测试（使用curl）:**
```bash
# 创建知识库
curl -X POST http://localhost:8080/api/knowledge/knowledge-bases \
  -H "Content-Type: application/json" \
  -d '{"name": "测试知识库", "description": "测试"}'

# 获取列表
curl http://localhost:8080/api/knowledge/knowledge-bases
```

### 4. 访问前端

1. 打开浏览器访问: `http://localhost:3000/knowledge-bases`
2. 点击"创建知识库"按钮
3. 填写知识库信息并创建
4. 验证知识库列表显示正常

---

## ✅ 验证清单

### 数据库
- [ ] `knowledge_bases` 表存在
- [ ] `documents.knowledge_base_id` 字段存在
- [ ] 外键约束已创建

### API
- [ ] 创建知识库: `POST /api/knowledge/knowledge-bases`
- [ ] 获取列表: `GET /api/knowledge/knowledge-bases`
- [ ] 获取详情: `GET /api/knowledge/knowledge-bases/{id}`
- [ ] 更新知识库: `PUT /api/knowledge/knowledge-bases/{id}`
- [ ] 删除知识库: `DELETE /api/knowledge/knowledge-bases/{id}`

### 前端
- [ ] 知识库列表页面正常显示
- [ ] 可以创建知识库
- [ ] 可以删除知识库
- [ ] 状态显示正确

---

## 📝 主要变更

### 数据库
- 新增 `knowledge_bases` 表
- `documents` 表新增 `knowledge_base_id` 字段

### API
- 知识库作为独立实体管理
- 支持完整的CRUD操作
- 支持配置管理（embedding_model, chunk_strategy等）
- 支持统计和文档查询

### 前端
- 使用新的API端点
- 支持新的状态类型（paused, archived）
- 改进的错误处理

---

## 🐛 常见问题

**Q: 迁移失败怎么办？**
A: 检查数据库连接配置，确认数据库容器正在运行，查看错误日志

**Q: API返回404？**
A: 确认API Gateway路由配置正确，检查服务是否启动

**Q: 前端显示错误？**
A: 检查浏览器控制台，验证API返回的数据格式

---

## 📚 详细文档

查看 `KNOWLEDGE_BASE_IMPLEMENTATION_GUIDE.md` 获取完整文档。




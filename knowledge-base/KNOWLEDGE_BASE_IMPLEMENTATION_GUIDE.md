# 知识库功能实现指南

## 📋 实现完成情况

### ✅ 已完成的高优先级功能

1. **知识库作为独立实体（数据库模型）**
   - ✅ 创建了 `KnowledgeBase` 数据库模型
   - ✅ 创建了数据库迁移脚本 `018_add_knowledge_bases_table.py`
   - ✅ 在 `Document` 表中添加了 `knowledge_base_id` 外键

2. **知识库更新功能（PUT/PATCH）**
   - ✅ 实现了 `PUT /api/knowledge-bases/{id}` - 完整更新
   - ✅ 实现了 `PATCH /api/knowledge-bases/{id}` - 部分更新

3. **文档与知识库的明确关联**
   - ✅ 文档表添加了 `knowledge_base_id` 字段
   - ✅ 文档上传和查询都支持按知识库过滤

4. **知识库配置管理**
   - ✅ 支持配置：embedding_model, chunk_strategy, chunk_size, chunk_overlap
   - ✅ 支持自定义设置（settings JSONB 字段）

5. **知识库API完善**
   - ✅ 所有CRUD端点已实现
   - ✅ 统计和文档管理端点已实现

---

## 🚀 执行步骤

### 步骤1: 运行数据库迁移

#### Windows (PowerShell)
```powershell
cd database
.\run_migration_018.ps1
```

#### Linux/Mac
```bash
cd database
# 确保数据库连接配置正确
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=ai_user
export DB_PASSWORD=ai_password
export DB_NAME=ai_platform

# 运行迁移
python3 -c "
import sys
import os
sys.path.insert(0, '..')
os.chdir('.')
from database.src.migrations.versions import 018_add_knowledge_bases_table as migration
from sqlalchemy import create_engine
from alembic import op

db_url = f'postgresql://{os.environ[\"DB_USER\"]}:{os.environ[\"DB_PASSWORD\"]}@{os.environ[\"DB_HOST\"]}:{os.environ[\"DB_PORT\"]}/{os.environ[\"DB_NAME\"]}'
engine = create_engine(db_url)

with engine.connect() as connection:
    op.connection = connection
    migration.upgrade()
    connection.commit()
print('✅ 迁移完成')
"
```

#### 使用 Alembic (推荐)
```bash
cd database
alembic upgrade head
```

### 步骤2: 测试API

#### 方法1: 使用测试脚本
```bash
cd knowledge-base
python test_knowledge_bases_api.py
```

#### 方法2: 使用 curl 手动测试

**创建知识库:**
```bash
curl -X POST http://localhost:8080/api/knowledge/knowledge-bases \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试知识库",
    "description": "这是一个测试知识库",
    "embedding_model": "default",
    "chunk_strategy": "fixed",
    "chunk_size": 1000,
    "chunk_overlap": 200
  }'
```

**获取知识库列表:**
```bash
curl http://localhost:8080/api/knowledge/knowledge-bases?page=1&page_size=10
```

**获取知识库详情:**
```bash
curl http://localhost:8080/api/knowledge/knowledge-bases/{kb_id}
```

**更新知识库:**
```bash
curl -X PUT http://localhost:8080/api/knowledge/knowledge-bases/{kb_id} \
  -H "Content-Type: application/json" \
  -d '{
    "description": "更新后的描述",
    "chunk_size": 1500
  }'
```

**部分更新知识库:**
```bash
curl -X PATCH http://localhost:8080/api/knowledge/knowledge-bases/{kb_id} \
  -H "Content-Type: application/json" \
  -d '{
    "description": "PATCH更新的描述"
  }'
```

**获取知识库统计:**
```bash
curl http://localhost:8080/api/knowledge/knowledge-bases/{kb_id}/stats
```

**获取知识库下的文档:**
```bash
curl http://localhost:8080/api/knowledge/knowledge-bases/{kb_id}/documents?page=1&page_size=10
```

**删除知识库:**
```bash
curl -X DELETE http://localhost:8080/api/knowledge/knowledge-bases/{kb_id}
```

### 步骤3: 更新前端UI

前端UI已经更新以支持新的API端点。主要更新包括：

1. **知识库列表页面** (`web-ui/src/app/knowledge-bases/page.tsx`)
   - ✅ 使用新的API端点获取知识库列表
   - ✅ 支持创建知识库
   - ✅ 支持删除知识库
   - ✅ 显示知识库状态（包括新增的 paused 和 archived 状态）

2. **API路由** (`web-ui/src/app/api/knowledge-bases/`)
   - ✅ 更新了 GET 和 POST 端点
   - ✅ 添加了 PUT 和 PATCH 支持
   - ✅ 添加了统计和文档列表端点

---

## 📝 API端点列表

### 知识库管理

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/knowledge/knowledge-bases` | 获取知识库列表（支持分页、搜索、过滤） |
| POST | `/api/knowledge/knowledge-bases` | 创建知识库 |
| GET | `/api/knowledge/knowledge-bases/{id}` | 获取知识库详情 |
| PUT | `/api/knowledge/knowledge-bases/{id}` | 完整更新知识库 |
| PATCH | `/api/knowledge/knowledge-bases/{id}` | 部分更新知识库 |
| DELETE | `/api/knowledge/knowledge-bases/{id}` | 删除知识库 |
| GET | `/api/knowledge/knowledge-bases/{id}/stats` | 获取知识库统计信息 |
| GET | `/api/knowledge/knowledge-bases/{id}/documents` | 获取知识库下的文档列表 |

### 查询参数

**GET /api/knowledge/knowledge-bases**
- `page` (int): 页码，默认1
- `page_size` (int): 每页大小，默认20，最大100
- `status` (string): 状态过滤 (active, indexing, paused, archived, failed)
- `created_by` (string): 创建者ID过滤
- `search` (string): 搜索关键词（名称或描述）

---

## 🔍 验证检查清单

### 数据库验证
- [ ] 确认 `knowledge_bases` 表已创建
- [ ] 确认 `documents.knowledge_base_id` 字段已添加
- [ ] 确认外键约束已创建
- [ ] 确认索引已创建

### API验证
- [ ] 创建知识库成功
- [ ] 获取知识库列表成功
- [ ] 获取知识库详情成功
- [ ] 更新知识库成功（PUT和PATCH）
- [ ] 获取统计信息成功
- [ ] 获取文档列表成功
- [ ] 删除知识库成功

### 前端验证
- [ ] 知识库列表页面正常显示
- [ ] 创建知识库功能正常
- [ ] 删除知识库功能正常
- [ ] 状态显示正确

---

## 🐛 故障排除

### 迁移失败
1. 检查数据库连接配置
2. 确认数据库容器正在运行
3. 检查迁移脚本语法
4. 查看数据库日志

### API测试失败
1. 确认API Gateway和知识库服务正在运行
2. 检查API Gateway路由配置
3. 查看服务日志
4. 验证数据库连接

### 前端显示异常
1. 检查浏览器控制台错误
2. 验证API端点返回的数据格式
3. 检查网络请求是否成功

---

## 📚 相关文件

### 后端
- `database/src/models/knowledge_models.py` - 数据库模型
- `database/src/migrations/versions/018_add_knowledge_bases_table.py` - 迁移脚本
- `knowledge-base/src/repositories/knowledge_base_repository.py` - Repository层
- `knowledge-base/src/services/knowledge_base_service.py` - Service层
- `knowledge-base/src/routes/knowledge_bases.py` - API路由

### 前端
- `web-ui/src/app/api/knowledge-bases/route.ts` - API路由
- `web-ui/src/app/api/knowledge-bases/[id]/route.ts` - 单个知识库API路由
- `web-ui/src/app/knowledge-bases/page.tsx` - 知识库列表页面

### 测试
- `knowledge-base/test_knowledge_bases_api.py` - API测试脚本
- `database/run_migration_018.ps1` - 迁移运行脚本

---

## 🎯 下一步计划

### 中优先级功能（P1）
- [ ] 知识库权限管理
- [ ] 知识库统计和分析增强
- [ ] 知识库搜索和过滤增强
- [ ] 知识库批量操作

### 低优先级功能（P2）
- [ ] 知识库导入/导出
- [ ] 知识库版本管理
- [ ] 知识库模板功能
- [ ] 知识库协作功能

---

## 📞 支持

如有问题，请检查：
1. 服务日志
2. 数据库连接
3. API Gateway配置
4. 前端控制台错误




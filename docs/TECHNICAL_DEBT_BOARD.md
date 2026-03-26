# LuminaOS 技术债看板

> **更新日期**: 2025-11-13
> **项目**: LuminaOS (Enterprise AI Platform)
> **总债务**: 95-121小时修复时间

---

## 📊 技术债务概览

### 总体统计

| 指标 | 数值 |
|------|------|
| **总债务项** | 23项 |
| **关键阻塞项** | 12项 (P0) |
| **高优先级项** | 8项 (P1) |
| **中优先级项** | 3项 (P2) |
| **预计修复时间** | 95-121小时 |
| **月度利息成本** | ~41小时/月 |

### 按类别分布

```
架构设计问题: ████████ 5项 (48-60h)
API规范问题:  ████████ 5项 (24-32h)
错误处理问题: █████    3项 (12-16h)
数据库问题:   ████     4项 (11h)
性能优化:     ███      6项 (2h)
```

---

## 🔴 P0 - 关键阻塞问题 (立即修复)

### 1. 安全: 敏感信息泄露 🔐

| 属性 | 值 |
|------|---|
| **ID** | TECH-DEBT-001 |
| **优先级** | 🔴 P0 - 紧急 |
| **影响** | 严重 (安全风险) |
| **受影响服务** | 所有5个服务 |
| **预计修复时间** | 8小时 |
| **月度成本** | 15小时 (故障排查) |
| **负责人** | Backend Team |

**问题描述**:
所有5个服务在全局异常处理中暴露敏感信息，可能泄露数据库凭证、SQL语句、系统架构。

**影响范围**:
- auth-service/src/main.py:83
- metadata-service/src/main.py:XX
- mcp-gateway/src/main.py:XX
- workflow-engine/src/main.py:XX
- knowledge-base/src/main.py:XX

**修复方案**:
```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    request_id = str(uuid.uuid4())
    logger.error(f"[{request_id}] {str(exc)}", exc_info=True)

    if os.getenv("ENV") == "production":
        return JSONResponse({
            "error": "Internal server error",
            "request_id": request_id
        }, status_code=500)
```

**验收标准**:
- [ ] 生产环境不返回敏感错误信息
- [ ] 所有错误都有唯一请求ID
- [ ] 错误详情记录到日志但不返回给客户端

---

### 2. 数据库: WorkflowConnection字段不一致 🗄️

| 属性 | 值 |
|------|---|
| **ID** | TECH-DEBT-002 |
| **优先级** | 🔴 P0 - 紧急 |
| **影响** | 高 (数据完整性) |
| **受影响服务** | workflow-engine |
| **预计修复时间** | 2小时 |
| **月度成本** | 5小时 (数据问题排查) |
| **负责人** | Database Team |

**问题描述**:
source_node_id 和 target_node_id 在模型中为 UUID，在迁移中为 String(100)，且没有外键约束。

**影响范围**:
- database/src/models/workflow_models.py:WorkflowConnection
- database/src/migrations/versions/001_initial_migration.py

**修复方案**:
```python
# 创建迁移 002_fix_workflow_connection_fk.py
def upgrade():
    # 修改字段类型
    op.alter_column('workflow_connections', 'source_node_id',
                    type_=UUID(as_uuid=True))
    op.alter_column('workflow_connections', 'target_node_id',
                    type_=UUID(as_uuid=True))

    # 添加外键约束
    op.create_foreign_key(
        'fk_workflow_connections_source',
        'workflow_connections', 'workflow_nodes',
        ['source_node_id'], ['id'],
        ondelete='CASCADE'
    )
```

**验收标准**:
- [ ] 字段类型为UUID
- [ ] 外键约束正确
- [ ] 无孤立连接记录

---

### 3. 数据库: KnowledgeGraphNode字段映射不一致 🗄️

| 属性 | 值 |
|------|---|
| **ID** | TECH-DEBT-003 |
| **优先级** | 🔴 P0 - 紧急 |
| **影响** | 高 (功能不可用) |
| **受影响服务** | knowledge-base |
| **预计修复时间** | 3小时 |
| **月度成本** | 8小时 |
| **负责人** | Database Team |

**问题描述**:
模型定义 (label, node_type, properties, document_id) vs 迁移定义 (concept, category, description) 字段完全不同。

**影响范围**:
- database/src/models/knowledge_models.py:KnowledgeGraphNode
- database/src/migrations/versions/001_initial_migration.py

**修复方案**:
```python
# 创建迁移 003_fix_knowledge_graph_nodes.py
def upgrade():
    op.add_column('knowledge_graph_nodes',
                  sa.Column('node_type', sa.String(50)))
    op.add_column('knowledge_graph_nodes',
                  sa.Column('properties', JSONB))
    op.add_column('knowledge_graph_nodes',
                  sa.Column('document_id', UUID(as_uuid=True),
                           sa.ForeignKey('documents.id')))
```

**验收标准**:
- [ ] 所有模型字段在数据库中存在
- [ ] 可以正确保存节点属性
- [ ] 可以关联源文档

---

### 4. 数据库: DocumentChunk向量字段不兼容 🗄️

| 属性 | 值 |
|------|---|
| **ID** | TECH-DEBT-004 |
| **优先级** | 🔴 P0 - 紧急 |
| **影响** | 高 (向量搜索不可用) |
| **受影响服务** | knowledge-base |
| **预计修复时间** | 3小时 |
| **月度成本** | 10小时 |
| **负责人** | Database Team |

**问题描述**:
模型定义 `embedding(JSONB)` vs 迁移定义 `vector_id(String)`，完全不兼容。

**影响范围**:
- database/src/models/knowledge_models.py:DocumentChunk
- database/src/migrations/versions/001_initial_migration.py

**修复方案**:
```python
# 创建迁移 004_fix_document_chunks.py
def upgrade():
    op.drop_column('document_chunks', 'vector_id')
    op.drop_column('document_chunks', 'metadata')

    op.add_column('document_chunks',
                  sa.Column('embedding', JSONB))
    op.add_column('document_chunks',
                  sa.Column('embedding_model', sa.String(100)))
    op.add_column('document_chunks',
                  sa.Column('start_char', sa.Integer))
    op.add_column('document_chunks',
                  sa.Column('end_char', sa.Integer))
```

**验收标准**:
- [ ] 可以存储嵌入向量
- [ ] 块位置信息完整
- [ ] 向量搜索功能正常

---

### 5. API: HTTP方法使用不当 🌐

| 属性 | 值 |
|------|---|
| **ID** | TECH-DEBT-005 |
| **优先级** | 🔴 P0 - 紧急 |
| **影响** | 高 (RESTful规范违反) |
| **受影响服务** | auth-service, knowledge-base |
| **预计修复时间** | 4小时 |
| **月度成本** | 3小时 (集成问题) |
| **负责人** | API Team |

**问题描述**:
- GET /auth/sso/login 产生副作用 (应为POST)
- /documents/upload 路径不规范

**影响范围**:
- auth-service/src/routes/auth.py
- knowledge-base/src/routes/documents.py

**修复方案**:
```python
# auth-service
@router.post("/auth/sso/login")  # 改为 POST
async def sso_login(request: SSOLoginRequest):
    ...

# knowledge-base
@router.post("/documents")  # 统一为 /documents
async def create_document(file: UploadFile):
    ...
```

**验收标准**:
- [ ] 所有修改操作使用POST/PUT/DELETE
- [ ] 路径符合RESTful命名规范
- [ ] 更新API文档

---

### 6. API: 版本控制完全缺失 🌐

| 属性 | 值 |
|------|---|
| **ID** | TECH-DEBT-006 |
| **优先级** | 🔴 P0 - 紧急 |
| **影响** | 高 (可维护性) |
| **受影响服务** | 所有服务 |
| **预计修复时间** | 12小时 |
| **月度成本** | 5小时 (版本兼容问题) |
| **负责人** | API Team |

**问题描述**:
无/api/v1, /api/v2前缀，无法维护向后兼容。

**影响范围**:
- 所有服务的 main.py 和路由文件

**修复方案**:
```python
# 各服务 main.py
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth-v1"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users-v1"])

# 添加版本检测中间件
@app.middleware("http")
async def version_middleware(request, call_next):
    if not request.url.path.startswith("/api/v"):
        return JSONResponse({"error": "API version required"}, 400)
    return await call_next(request)
```

**验收标准**:
- [ ] 所有API都有/api/v1前缀
- [ ] 旧路径重定向到新路径(临时兼容)
- [ ] 更新所有API文档

---

### 7. API: HTTP状态码使用不一致 🌐

| 属性 | 值 |
|------|---|
| **ID** | TECH-DEBT-007 |
| **优先级** | 🔴 P0 - 紧急 |
| **影响** | 中 (客户端处理复杂) |
| **受影响服务** | 所有服务 |
| **预计修复时间** | 8小时 |
| **月度成本** | 4小时 |
| **负责人** | API Team |

**问题描述**:
创建资源返回200/201混用，删除资源返回200/204混用，验证错误返回500。

**影响范围**:
- 所有服务的路由文件

**修复方案**:
```python
# 统一状态码
@router.post("/users", status_code=201)  # 创建
async def create_user(): ...

@router.delete("/users/{id}", status_code=204)  # 删除
async def delete_user(): ...

@app.exception_handler(ValidationError)
async def validation_error_handler(request, exc):
    return JSONResponse({"error": str(exc)}, status_code=422)  # 验证错误
```

**验收标准**:
- [ ] 创建资源统一返回201
- [ ] 删除资源统一返回204
- [ ] 验证错误返回422
- [ ] 权限错误返回403

---

### 8. 错误处理: 缺少统一错误代码体系 ⚠️

| 属性 | 值 |
|------|---|
| **ID** | TECH-DEBT-008 |
| **优先级** | 🔴 P0 - 紧急 |
| **影响** | 中 (可维护性) |
| **受影响服务** | 所有服务 |
| **预计修复时间** | 6小时 |
| **月度成本** | 8小时 |
| **负责人** | Backend Team |

**问题描述**:
无统一的错误代码，客户端无法程序化处理错误。

**影响范围**:
- shared_libs/common/error_handler.py

**修复方案**:
```python
# shared_libs/common/error_codes.py
class ErrorCode(Enum):
    VALIDATION_ERROR = "ERR_001"
    AUTHENTICATION_FAILED = "ERR_401"
    AUTHORIZATION_ERROR = "ERR_403"
    RESOURCE_NOT_FOUND = "ERR_404"
    CONFLICT_ERROR = "ERR_409"
    INTERNAL_ERROR = "ERR_500"

def create_error_response(code: ErrorCode, message: str, status_code: int):
    return JSONResponse({
        "error": message,
        "code": code.value,
        "timestamp": datetime.utcnow().isoformat()
    }, status_code=status_code)
```

**验收标准**:
- [ ] 所有错误都有唯一错误代码
- [ ] 错误代码文档完整
- [ ] 客户端可以根据代码处理错误

---

### 9. 架构: 启动时级联依赖 🏗️

| 属性 | 值 |
|------|---|
| **ID** | TECH-DEBT-009 |
| **优先级** | 🔴 P0 - 紧急 |
| **影响** | 高 (可靠性) |
| **受影响服务** | metadata-service |
| **预计修复时间** | 8小时 |
| **月度成本** | 5小时 (启动问题排查) |
| **负责人** | Architecture Team |

**问题描述**:
metadata-service启动时HTTP调用其他3个服务采集元数据，任一服务未就绪导致10秒timeout。

**影响范围**:
- metadata-service/src/api/collection.py:register_on_startup

**修复方案**:
```python
async def collect_metadata_async():
    """异步采集 + 重试机制"""
    async def collect_with_retry(service: str, max_retries=3):
        for i in range(max_retries):
            try:
                return await fetch_metadata(service)
            except Exception as e:
                logger.warning(f"Failed to collect from {service}: {e}")
                if i < max_retries - 1:
                    await asyncio.sleep(2 ** i)  # 指数退避
        return None

    results = await asyncio.gather(
        collect_with_retry("workflow-engine"),
        collect_with_retry("mcp-gateway"),
        collect_with_retry("knowledge-base"),
        return_exceptions=True
    )
```

**验收标准**:
- [ ] 服务可以在依赖未就绪时启动
- [ ] 后台异步采集元数据
- [ ] 失败不影响服务启动

---

### 10. 架构: 共享数据库紧耦合 🏗️

| 属性 | 值 |
|------|---|
| **ID** | TECH-DEBT-010 |
| **优先级** | 🔴 P0 - 紧急 |
| **影响** | 高 (可扩展性) |
| **受影响服务** | 所有服务 |
| **预计修复时间** | 20小时 |
| **月度成本** | 10小时 (数据冲突) |
| **负责人** | Architecture Team |

**问题描述**:
所有服务使用同一PostgreSQL数据库，所有表共享public schema，无法独立扩展。

**影响范围**:
- database/src/core/database.py
- 所有服务的数据库配置

**修复方案**:
```sql
-- 为每个服务创建独立schema
CREATE SCHEMA IF NOT EXISTS auth_schema;
CREATE SCHEMA IF NOT EXISTS metadata_schema;
CREATE SCHEMA IF NOT EXISTS mcp_schema;
CREATE SCHEMA IF NOT EXISTS workflow_schema;
CREATE SCHEMA IF NOT EXISTS knowledge_schema;

-- 迁移表到对应schema
ALTER TABLE users SET SCHEMA auth_schema;
ALTER TABLE data_assets SET SCHEMA metadata_schema;
-- ...
```

**验收标准**:
- [ ] 每个服务有独立schema
- [ ] 可以独立备份恢复
- [ ] 支持独立扩展

---

### 11. 架构: shared_libs导入路径问题 🏗️

| 属性 | 值 |
|------|---|
| **ID** | TECH-DEBT-011 |
| **优先级** | 🔴 P0 - 紧急 |
| **影响** | 中 (开发体验) |
| **受影响服务** | 所有服务 |
| **预计修复时间** | 4小时 |
| **月度成本** | 2小时 (IDE问题) |
| **负责人** | DevOps Team |

**问题描述**:
需要在每个服务main.py中手动修复sys.path，IDE无法识别导入。

**影响范围**:
- shared_libs/
- 所有服务的 src/main.py

**修复方案**:
```python
# shared_libs/setup.py
from setuptools import setup, find_packages

setup(
    name="luminaos-shared-libs",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0"
    ]
)

# Dockerfile
RUN pip install -e /app/shared_libs

# 删除各服务的sys.path修复代码
```

**验收标准**:
- [ ] IDE可以识别shared_libs导入
- [ ] 无需手动修改sys.path
- [ ] 可以正常运行测试

---

### 12. 错误处理: 数据库异常处理缺失 ⚠️

| 属性 | 值 |
|------|---|
| **ID** | TECH-DEBT-012 |
| **优先级** | 🔴 P0 - 紧急 |
| **影响** | 中 (用户体验) |
| **受影响服务** | 所有服务 |
| **预计修复时间** | 6小时 |
| **月度成本** | 5小时 |
| **负责人** | Backend Team |

**问题描述**:
数据库连接失败、约束冲突都返回500，无法区分错误类型。

**影响范围**:
- 所有服务的 src/main.py

**修复方案**:
```python
from sqlalchemy.exc import IntegrityError, OperationalError

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request, exc):
    return JSONResponse({
        "error": "Data conflict",
        "code": "ERR_409"
    }, status_code=409)

@app.exception_handler(OperationalError)
async def operational_error_handler(request, exc):
    logger.error(f"Database error: {exc}")
    return JSONResponse({
        "error": "Database unavailable",
        "code": "ERR_503"
    }, status_code=503)
```

**验收标准**:
- [ ] 约束冲突返回409
- [ ] 数据库不可用返回503
- [ ] 外键违反返回422

---

## 🟡 P1 - 高优先级问题 (第2-4周修复)

### 13. 数据库: 缺少MCPToolExecution工作流关联 🗄️

| 属性 | 值 |
|------|---|
| **ID** | TECH-DEBT-013 |
| **优先级** | 🟡 P1 - 高 |
| **影响** | 中 (功能不完整) |
| **受影响服务** | mcp-gateway |
| **预计修复时间** | 1小时 |
| **负责人** | Database Team |

**问题描述**: 缺少 `workflow_execution_id` 字段，无法追踪工具在工作流中的使用。

**修复方案**: 添加外键到 workflow_executions 表。

---

### 14. 性能: 索引覆盖率低 (18%) 🚀

| 属性 | 值 |
|------|---|
| **ID** | TECH-DEBT-014 |
| **优先级** | 🟡 P1 - 高 |
| **影响** | 中 (性能) |
| **受影响服务** | 所有服务 |
| **预计修复时间** | 2小时 |
| **月度成本** | 3小时 (性能问题) |
| **负责人** | Database Team |

**问题描述**: 缺少6个关键复合索引，查询性能可能下降5-10倍。

**修复方案**:
```sql
CREATE INDEX idx_workflow_execution_status
    ON workflow_executions(workflow_id, status);
CREATE INDEX idx_user_session_active
    ON user_sessions(user_id, is_active);
CREATE INDEX idx_audit_log_user
    ON audit_logs(timestamp DESC, user_id);
CREATE INDEX idx_document_category
    ON documents(category, status);
CREATE INDEX idx_document_chunk
    ON document_chunks(document_id, chunk_index);
CREATE INDEX idx_tool_execution_status
    ON mcp_tool_executions(tool_id, status);
```

---

### 15. 架构: 缺少服务发现机制 🏗️

| 属性 | 值 |
|------|---|
| **ID** | TECH-DEBT-015 |
| **优先级** | 🟡 P1 - 高 |
| **影响** | 中 (可维护性) |
| **受影响服务** | 所有服务 |
| **预计修复时间** | 12小时 |
| **负责人** | Architecture Team |

**问题描述**: 服务地址hard-coded在config.py中，无法动态发现。

**修复方案**: 使用环境变量 + Kubernetes DNS或Consul。

---

### 16. 可观测性: 缺少分布式追踪 📊

| 属性 | 值 |
|------|---|
| **ID** | TECH-DEBT-016 |
| **优先级** | 🟡 P1 - 高 |
| **影响** | 中 (可维护性) |
| **受影响服务** | 所有服务 |
| **预计修复时间** | 20小时 |
| **负责人** | DevOps Team |

**问题描述**: 无法追踪请求在多个服务中的执行链路，故障排查困难。

**修复方案**: 集成OpenTelemetry + Jaeger。

---

### 17-20. API问题 (P1)

- **TECH-DEBT-017**: 资源命名不一致 (kebab-case vs snake_case)
- **TECH-DEBT-018**: 分页参数不一致 (默认20 vs 100)
- **TECH-DEBT-019**: 错误响应格式不统一
- **TECH-DEBT-020**: 缺少API限流机制

---

## 🟢 P2 - 中优先级问题 (第5-12周改进)

### 21. 测试: 覆盖率未达标 🧪

| 属性 | 值 |
|------|---|
| **ID** | TECH-DEBT-021 |
| **优先级** | 🟢 P2 - 中 |
| **影响** | 中 (质量保证) |
| **受影响服务** | 所有服务 |
| **预计修复时间** | 30-40小时 |
| **负责人** | QA Team |

**问题描述**: 当前覆盖率65%+，项目目标80%。

**修复方案**: 持续添加单元测试和集成测试。

---

### 22. 架构: 元数据同步逻辑分散 🏗️

| 属性 | 值 |
|------|---|
| **ID** | TECH-DEBT-022 |
| **优先级** | 🟢 P2 - 中 |
| **影响** | 低 (可维护性) |
| **受影响服务** | workflow-engine, mcp-gateway, metadata-service |
| **预计修复时间** | 6小时 |
| **负责人** | Architecture Team |

**问题描述**: 相同API调用逻辑在3个地方重复。

**修复方案**: 创建统一的 metadata_api_client.py。

---

### 23. 文档: API文档不完整 📚

| 属性 | 值 |
|------|---|
| **ID** | TECH-DEBT-023 |
| **优先级** | 🟢 P2 - 中 |
| **影响** | 低 (可用性) |
| **受影响服务** | 所有服务 |
| **预计修复时间** | 10小时 |
| **负责人** | API Team |

**问题描述**: 部分API缺少OpenAPI文档和使用示例。

**修复方案**: 完善所有API的OpenAPI文档。

---

## 📈 技术债务趋势

### 历史趋势

```
80h |              *  (今天: 95-121h)
60h |         *
40h |    *
20h | *
    +---+---+---+---+---+---+
      W1  W2  W3  W4  W5  W6
```

### 预期趋势 (修复后)

```
100h |  *
 80h |
 60h |       *
 40h |          *
 20h |              *
  0h |                  * (目标)
     +---+---+---+---+---+---+
       现在 2W  4W  8W  12W
```

---

## 🎯 修复路线图

### 第1-2周 (P0关键项)
```
Week 1: □□□□□□ 6项 (40小时)
├─ TECH-DEBT-001 ✓ 敏感信息泄露
├─ TECH-DEBT-002 ✓ WorkflowConnection
├─ TECH-DEBT-003 ✓ KnowledgeGraphNode
├─ TECH-DEBT-004 ✓ DocumentChunk
├─ TECH-DEBT-005 ✓ HTTP方法
└─ TECH-DEBT-007 ✓ HTTP状态码

Week 2: □□□□□□ 6项 (40小时)
├─ TECH-DEBT-006 ✓ API版本控制
├─ TECH-DEBT-008 ✓ 错误代码体系
├─ TECH-DEBT-009 ✓ 启动依赖
├─ TECH-DEBT-011 ✓ shared_libs导入
├─ TECH-DEBT-012 ✓ 数据库异常
└─ TECH-DEBT-014 ✓ 性能索引
```

### 第3-6周 (P1高优先级)
```
Week 3-4: □□□□ 4项 (30小时)
├─ TECH-DEBT-010 ✓ 数据库schema隔离
├─ TECH-DEBT-017 ✓ API命名统一
├─ TECH-DEBT-018 ✓ 分页参数统一
└─ TECH-DEBT-019 ✓ 错误响应统一

Week 5-6: □□□ 3项 (32小时)
├─ TECH-DEBT-015 ✓ 服务发现
├─ TECH-DEBT-016 ✓ 分布式追踪
└─ TECH-DEBT-020 ✓ API限流
```

### 第7-12周 (P2中优先级)
```
Week 7-12: □□□ 3项 (46小时)
├─ TECH-DEBT-021 ✓ 测试覆盖率
├─ TECH-DEBT-022 ✓ 元数据客户端
└─ TECH-DEBT-023 ✓ API文档
```

---

## 📊 债务偿还进度

### 总体进度
```
P0 (关键):  [==========] 0/12 完成  (0%)
P1 (高):    [==========] 0/8  完成  (0%)
P2 (中):    [==========] 0/3  完成  (0%)
-------------------------------------------
总体:       [==========] 0/23 完成  (0%)
```

### 按类别进度
```
架构设计:   [==========] 0/5 完成  (0%)
API规范:    [==========] 0/5 完成  (0%)
错误处理:   [==========] 0/3 完成  (0%)
数据库:     [==========] 0/4 完成  (0%)
性能优化:   [==========] 0/6 完成  (0%)
```

---

## 💰 债务成本分析

### 月度利息成本

| 问题 | 月度成本 | 年度成本 |
|------|---------|---------|
| 启动级联依赖 | 5h | 60h |
| 共享数据库 | 10h | 120h |
| API不规范 | 8h | 96h |
| 错误处理不完整 | 15h | 180h |
| 索引缺失 | 3h | 36h |
| **总计** | **41h** | **492h** |

### 修复投资回报

```
修复投入: 95-121h (一次性)
年度节省: 492h
投资回报: 4.1-5.2倍
回本周期: 2.3-2.9个月
```

---

## 🔄 更新历史

| 日期 | 新增 | 完成 | 总债务 | 备注 |
|------|------|------|--------|------|
| 2025-11-13 | 23项 | 0项 | 95-121h | 初始评估 |
| - | - | - | - | - |

---

## 📞 负责团队

| 团队 | 负责债务项 | 联系方式 |
|------|-----------|---------|
| **Backend Team** | DEBT-001, 008, 012 | backend@luminaos.com |
| **API Team** | DEBT-005, 006, 007, 017-020, 023 | api@luminaos.com |
| **Database Team** | DEBT-002, 003, 004, 013, 014 | database@luminaos.com |
| **Architecture Team** | DEBT-009, 010, 015, 022 | architecture@luminaos.com |
| **DevOps Team** | DEBT-011, 016 | devops@luminaos.com |
| **QA Team** | DEBT-021 | qa@luminaos.com |

---

**看板版本**: 1.0
**下次更新**: 每周五更新
**负责人**: Tech Lead
**联系方式**: techlead@luminaos.com

---

*本看板由 Claude Code 自动生成*

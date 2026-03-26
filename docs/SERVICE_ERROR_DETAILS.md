# LuminaOS 各服务错误处理详细分析

## 1. 认证服务 (auth-service)

### 总体评分: 5/10

### 错误处理覆盖情况

#### ✓ 已实现的错误处理

1. **输入验证错误** - 422状态码
   - 用户名/邮箱/密码为空
   - 位置: `routes/auth_enhanced.py`

2. **业务逻辑错误** - 400状态码
   - 用户已存在
   - 邮箱已注册
   - 密码错误
   - 位置: `services/auth_service.py`

3. **全局异常处理** - 500状态码
   - 位置: `main.py`

#### ✗ 缺失的错误处理

1. **令牌错误**
   - 令牌过期 - 应返回401
   - 令牌无效 - 应返回401
   - 令牌签名错误 - 应返回401

2. **权限错误**
   - 权限不足 - 应返回403
   - 角色不存在 - 应返回404

3. **数据库错误**
   - 连接失败 - 应返回503
   - 查询失败 - 应返回500
   - 唯一性约束冲突 - 应返回409

4. **安全相关**
   - 用户被锁定 - 应返回403
   - 登录尝试过多 - 应返回429

### 安全问题

#### 信息泄露风险 (高)

```python
# ✗ 问题代码 - 泄露异常细节
except Exception as e:
    logger.error(f"Registration error: {str(e)}", exc_info=True)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"注册失败: {str(e)}"  # ✗ 敏感信息！
    )
```

可能暴露的信息:
- 数据库连接字符串
- SQL异常信息
- 密码哈希算法细节
- 内部代码路径

### 建议修复

1. 实现令牌失效处理
2. 添加权限检查
3. 隐藏敏感错误信息
4. 添加速率限制

---

## 2. 元数据服务 (metadata-service)

### 总体评分: 4/10

### 错误处理覆盖情况

#### ✓ 已实现的错误处理

1. **资源不存在** - 404状态码
   - 位置: `api/data_assets.py`

2. **验证错误** - 400状态码
   - 质量指标验证
   - 位置: `api/quality.py`

3. **全局异常处理** - 500状态码

#### ✗ 缺失的错误处理

1. **血缘关系查询** (高优先级)
   - 血缘关系不存在 - 完全无处理
   - 位置: `api/lineage.py`

2. **搜索功能** (高优先级)
   - 搜索失败 - 完全无处理
   - 位置: `api/search.py`

3. **质量检查** (中优先级)
   - 检查执行失败
   - 数据源不可用

4. **采集器错误** (中优先级)
   - 采集超时
   - 采集失败

### 混用两种错误处理方式的问题

```python
# ✗ 不一致的错误处理方式

# 方式1 - 使用 create_error_response
try:
    return service.create_data_asset(asset_data)
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

# 方式2 - 使用 HTTPException
try:
    asset = service.update_quality_metrics(asset_id, metrics)
    if not asset:
        raise HTTPException(status_code=404, detail="...")
except HTTPException:
    raise
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

后果:
- 响应格式不统一
- 难以维护
- 容易出错

### 建议修复

1. 统一使用一种错误处理方式
2. 为血缘查询添加完整的异常处理
3. 为搜索功能添加异常处理
4. 实现采集器的超时处理

---

## 3. 工作流引擎 (workflow-engine)

### 总体评分: 3/10

### 错误处理覆盖情况

#### ✓ 已实现的错误处理

1. **请求验证错误** - 422状态码
   - 自定义处理器
   - 位置: `main.py`

2. **资源不存在** - 404状态码
   - 工作流不存在
   - 执行不存在

3. **全局异常处理** - 500状态码

#### ✗ 严重缺失的错误处理

1. **节点执行失败** (高优先级)
   - LLM节点失败无处理
   - 知识库查询失败无处理
   - HTTP请求失败无处理
   - 数据转换失败无处理
   - 位置: `nodes/*.py`, `core/dynamic_workflow_engine.py`

2. **工作流超时** (高优先级)
   - 无超时处理机制
   - 可能导致资源泄漏

3. **工作流验证** (中优先级)
   - 工作流定义验证不足
   - 节点连接验证缺失

4. **资源管理** (中优先级)
   - 内存不足无处理
   - 并发限制无处理

### 具体问题分析

#### 问题1: 节点级异常未捕获

```python
# ✗ 问题代码 - nodes/llm_node.py
async def execute(self, input_data: Dict, context: Dict) -> Dict:
    response = await self.llm_client.generate(
        prompt=self.prompt,
        max_tokens=self.max_tokens
    )  # ✗ 如果LLM API调用失败，整个工作流崩溃！
    return {"output": response}
```

#### 问题2: 无超时处理

```python
# ✗ 问题代码 - 无超时
result = await workflow_manager.execute_workflow(
    workflow_name=request.workflow_name,
    input_data=request.input_data,
    context=request.context or {}
)  # ✗ 如果工作流耗时很长，请求会一直等待
```

### 建议修复

1. 为所有节点添加异常处理框架
2. 实现工作流执行超时
3. 添加节点失败重试机制
4. 实现工作流版本冲突检测

---

## 4. MCP网关 (mcp-gateway)

### 总体评分: 2/10 (最低)

### 错误处理覆盖情况

#### ✗ 严重缺陷

1. **工具注册错误** (高优先级)
   - 工具已存在时返回500（应返回409）
   - 位置: `routes/tools_db.py`

2. **工具执行错误** (高优先级)
   - 完全无异常处理
   - 工具超时无处理
   - 位置: `tools/*.py`

3. **工具配置错误** (中优先级)
   - 配置验证不足
   - 配置冲突无处理

### 具体问题

#### 问题1: 错误的状态码

```python
# ✗ 问题代码
@router.post("/register", response_model=ToolRegisterResponse)
async def register_tool(request: ToolRegisterRequest, db: Session):
    try:
        result = await service.register_tool(...)
        # 如果工具已存在，会抛出异常，返回500
        # ✗ 应该检查是否存在，返回409
    except Exception as e:
        logger.error(f"Failed to register tool: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### 问题2: 工具执行完全无保护

```python
# ✗ 问题代码 - tools/knowledge_search_tool.py
async def execute(self, **kwargs):
    query = kwargs.get("query")
    # ✗ 如果查询失败，整个工具执行失败！
    # ✗ 无超时处理，可能导致请求无限等待
    result = await self.search_service.search(query)
    return result
```

### 建议修复

1. 修改工具注册逻辑，返回正确的状态码
2. 为所有工具执行添加异常处理
3. 实现工具执行超时
4. 添加工具降级/备选方案

---

## 5. 知识库服务 (knowledge-base)

### 总体评分: 3/10

### 错误处理覆盖情况

#### ✓ 已实现的错误处理

1. **文件验证错误** - 400状态码
   - 文件类型不支持
   - 文件过大
   - 位置: `routes/documents_db.py`

#### ✗ 严重缺失的错误处理

1. **文档处理失败** (高优先级)
   - 文档解析失败无处理
   - 向量化失败无处理
   - 位置: `services/document_service.py`

2. **搜索失败** (高优先级)
   - 向量搜索失败无处理
   - 关键词搜索失败无处理
   - 位置: `routes/search_db.py`

3. **向量存储错误** (中优先级)
   - 向量存储连接失败
   - 向量存储容量满

4. **知识图谱操作** (中优先级)
   - 实体不存在无处理
   - 关系操作失败无处理

### 具体问题

#### 问题1: 后台任务异常未处理

```python
# ✗ 问题代码
@router.post("/documents/upload")
async def upload_document(..., background_tasks: BackgroundTasks):
    # ...
    background_tasks.add_task(process_document, document_id)
    # ✗ 如果后台任务失败，客户端无法感知！
    # ✗ 文档可能处于"已上传但未处理"的状态
    return DocumentUploadResponse(status="processing")
```

#### 问题2: 搜索异常未捕获

```python
# ✗ 问题代码 - routes/search_db.py
@router.post("/search/semantic")
async def search_semantic(query: str, db: Session):
    service = get_search_service(db)
    return service.search(query)  # ✗ 搜索失败无处理
```

### 建议修复

1. 为文档处理添加完整的异常处理
2. 为搜索操作添加异常处理
3. 实现文档处理状态跟踪
4. 添加向量存储健康检查

---

## 综合建议

### 按优先级排序

1. **高优先级 (本周完成)**
   - [ ] 隐藏生产环境敏感错误信息
   - [ ] 添加请求ID追踪
   - [ ] 修复HTTP状态码使用

2. **中优先级 (本月完成)**
   - [ ] 实现错误代码体系
   - [ ] 添加数据库异常处理
   - [ ] 完善节点/工具执行异常处理

3. **低优先级 (下月完成)**
   - [ ] 实现错误监控
   - [ ] 添加国际化
   - [ ] 实现熔断器和重试


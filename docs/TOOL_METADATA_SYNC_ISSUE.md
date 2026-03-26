# 工具元数据同步问题分析

## 🔴 问题描述

用户问："刚刚新增的工具没有添加到元数据里吗？"

**检查结果**：
- ✅ `send_email` 工具已在 `ToolRegistry` 中注册（内存中）
- ❌ 数据库中**没有** `send_email` 工具记录
- ❌ 元数据服务中**没有** `send_email` 工具元数据

## 📋 问题分析

### 当前工具注册流程

#### 1. 默认工具注册（`_register_default_tools`）

**代码位置**：`mcp-gateway/src/tools/tool_registry.py`

```python
def _register_default_tools(self):
    """注册默认工具"""
    # ...
    # 注册邮件发送工具
    try:
        from .email_tool import SEND_EMAIL_TOOL, execute_send_email
        self.register_tool(SEND_EMAIL_TOOL, executor=execute_send_email)
    except Exception as e:
        logger.warning(f"Failed to register send_email tool: {str(e)}")
```

**问题**：
- ❌ 只调用 `self.register_tool()`，仅注册到内存
- ❌ **没有**调用 `ToolService.register_tool()` 持久化到数据库
- ❌ **没有**同步到元数据服务

#### 2. 工具注册API（`/api/tools/register`）

**代码位置**：`mcp-gateway/src/routes/tools.py`

**修复前**：
```python
async def register_tool(request: ToolRegisterRequest):
    # 只注册到内存
    tool_registry.register_tool(
        tool_def=request.tool,
        overwrite=request.overwrite
    )
    # ❌ 没有持久化到数据库和元数据服务
```

**修复后**：
```python
async def register_tool(request: ToolRegisterRequest):
    # 1. 先注册到内存
    tool_registry.register_tool(...)
    
    # 2. 持久化到数据库和元数据服务
    tool_service = ToolService(db, tool_registry)
    await tool_service.register_tool(tool_def_dict, overwrite=...)
    # ✅ 现在会保存到数据库并同步到元数据服务
```

### ToolService.register_tool 的完整流程

**代码位置**：`mcp-gateway/src/services/tool_service.py`

```python
async def register_tool(self, tool_def: Dict[str, Any], ...):
    # 1. 保存到数据库
    tool = self.tool_repo.create_tool(...)
    self.db.commit()
    
    # 2. 注册到内存注册表
    self.tool_registry.register_tool(...)
    
    # 3. 同步到元数据服务
    metadata_client = get_metadata_client()
    await metadata_client.create_tool_metadata(tool_metadata)
    # ✅ 会调用 metadata-service 的 /api/workflows API
```

## ✅ 已修复

### 1. 修复工具注册API

**文件**：`mcp-gateway/src/routes/tools.py`

**修改**：
- 在 `register_tool` API 中添加了数据库和元数据服务同步逻辑
- 如果同步失败，只记录警告，不影响内存注册

### 2. 创建同步脚本

**文件**：`mcp-gateway/sync_send_email_tool_api.py`

用于手动同步现有工具到数据库和元数据服务。

## 🔧 解决方案

### 方案1：通过API同步（推荐）

```bash
# 使用同步脚本
python mcp-gateway/sync_send_email_tool_api.py
```

### 方案2：修改启动流程（长期方案）

在服务启动时自动同步默认工具：

**文件**：`mcp-gateway/src/main.py`

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... 现有代码 ...
    
    # 同步默认工具到数据库和元数据服务
    try:
        from .services.tool_service import ToolService
        from database.src.core.session import SessionLocal
        
        db = SessionLocal()
        try:
            tool_service = ToolService(db, tool_registry)
            
            # 获取所有已注册的工具
            all_tools = tool_registry.list_tools()
            
            for tool_dict in all_tools:
                tool_def = {
                    "name": tool_dict["name"],
                    "description": tool_dict.get("description", ""),
                    # ... 其他字段 ...
                }
                await tool_service.register_tool(tool_def, overwrite=True)
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to sync default tools: {e}")
```

## 📊 验证

### 检查数据库

```sql
SELECT name, description, status FROM mcp_tools WHERE name = 'send_email';
```

### 检查元数据服务

```bash
curl http://localhost:8005/api/workflows?workflow_type=tool
```

## 🎯 根本原因

**问题根源**：
- `ToolRegistry._register_default_tools()` 只负责内存注册
- 没有自动持久化机制
- API注册端点之前也没有持久化逻辑

**解决思路**：
1. ✅ 修复API注册端点，添加持久化逻辑
2. ⏭️ 可选：在服务启动时自动同步默认工具
3. ⏭️ 可选：定期同步工具元数据

## 📝 下一步

1. **立即执行**：通过API同步 `send_email` 工具
2. **验证**：检查数据库和元数据服务
3. **长期改进**：在服务启动时自动同步默认工具



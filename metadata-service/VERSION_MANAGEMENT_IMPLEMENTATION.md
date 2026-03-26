# 工作流版本管理功能实现文档

## 📋 实现概述

本文档描述了工作流版本管理功能的完整实现，包括数据模型、服务层、API端点和数据库迁移。

## ✅ 已实现的功能

### 1. 数据模型

**文件**: `metadata-service/src/models/workflow_version.py`

- ✅ `WorkflowVersion`: 工作流版本历史模型
  - 存储版本号、版本描述、变更摘要
  - 存储完整的工作流定义
  - 支持标记当前版本
  - 支持版本标签

- ✅ `WorkflowVersionTag`: 版本标签模型
  - 支持为版本添加标签（如stable, beta, deprecated）

- ✅ Pydantic Schema模型
  - `WorkflowVersionCreate`: 创建版本请求
  - `WorkflowVersionUpdate`: 更新版本请求
  - `WorkflowVersionSchema`: 版本响应模型
  - `WorkflowVersionListResponse`: 版本列表响应
  - `VersionRestoreRequest`: 恢复版本请求

### 2. 服务层

**文件**: `metadata-service/src/services/version_service.py`

- ✅ `create_version()`: 创建工作流新版本
- ✅ `get_versions()`: 获取版本列表（支持分页）
- ✅ `get_version()`: 获取特定版本
- ✅ `set_current_version()`: 设置当前版本
- ✅ `restore_version()`: 恢复历史版本（创建新版本）
- ✅ `add_version_tag()`: 添加版本标签
- ✅ `remove_version_tag()`: 移除版本标签

### 3. API端点

**文件**: `metadata-service/src/api/workflow_versions.py`

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | `/api/workflows/{workflow_id}/versions` | 创建工作流新版本 |
| GET | `/api/workflows/{workflow_id}/versions` | 获取版本列表 |
| GET | `/api/workflows/{workflow_id}/versions/{version}` | 获取特定版本 |
| PUT | `/api/workflows/{workflow_id}/versions/{version}/set-current` | 设置当前版本 |
| POST | `/api/workflows/{workflow_id}/versions/{version}/restore` | 恢复历史版本 |
| POST | `/api/workflows/{workflow_id}/versions/{version}/tags/{tag}` | 添加版本标签 |
| DELETE | `/api/workflows/{workflow_id}/versions/{version}/tags/{tag}` | 移除版本标签 |

### 4. 数据库迁移

**文件**: `database/src/migrations/versions/011_add_workflow_versions.py`

- ✅ 创建 `workflow_versions` 表
- ✅ 创建 `workflow_version_tags` 表
- ✅ 创建必要的索引
- ✅ 创建唯一约束
- ✅ 创建外键约束（级联删除）

### 5. 模型关系

**文件**: `metadata-service/src/models/workflow_metadata.py`

- ✅ 在 `WorkflowMetadata` 中添加了 `versions` 关系
- ✅ 支持级联删除（删除工作流时自动删除所有版本）

## 🚀 部署步骤

### 1. 执行数据库迁移

```bash
cd database
alembic upgrade head
```

或者直接运行迁移脚本：

```bash
alembic upgrade 011
```

### 2. 验证服务启动

```bash
cd metadata-service
uvicorn src.main:app --reload --port 8005
```

### 3. 测试API端点

访问API文档：
```
http://localhost:8005/api/docs
```

## 📝 API使用示例

### 创建工作流新版本

```bash
curl -X POST "http://localhost:8005/api/workflows/test_workflow_1/versions" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "test_workflow_1",
    "version": "v1.1",
    "version_number": 2,
    "description": "Updated version with new features",
    "definition": {
      "nodes": [{"id": "node1", "type": "start"}],
      "connections": []
    },
    "changes": {"added_nodes": ["node1"]},
    "created_by": "user123"
  }'
```

### 获取版本列表

```bash
curl "http://localhost:8005/api/workflows/test_workflow_1/versions?skip=0&limit=10"
```

### 获取特定版本

```bash
curl "http://localhost:8005/api/workflows/test_workflow_1/versions/v1.1"
```

### 设置当前版本

```bash
curl -X PUT "http://localhost:8005/api/workflows/test_workflow_1/versions/v1.0/set-current"
```

### 恢复历史版本

```bash
curl -X POST "http://localhost:8005/api/workflows/test_workflow_1/versions/v1.0/restore" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "v1.0",
    "description": "Restore to stable version"
  }'
```

### 添加版本标签

```bash
curl -X POST "http://localhost:8005/api/workflows/test_workflow_1/versions/v1.1/tags/stable"
```

### 移除版本标签

```bash
curl -X DELETE "http://localhost:8005/api/workflows/test_workflow_1/versions/v1.1/tags/stable"
```

## 🔗 与Workflow Engine集成

Workflow Engine可以通过以下方式使用版本管理功能：

### 1. 在工作流保存时创建版本

```python
import httpx

async def create_workflow_version(workflow_id: str, workflow_definition: dict, user_id: str):
    """在工作流保存时自动创建版本"""
    async with httpx.AsyncClient() as client:
        # 获取当前最高版本号
        versions_response = await client.get(
            f"{METADATA_SERVICE_URL}/api/workflows/{workflow_id}/versions",
            params={"limit": 1}
        )
        versions = versions_response.json()
        current_highest = versions["items"][0]["version_number"] if versions["items"] else 0
        
        # 创建新版本
        new_version_number = current_highest + 1
        new_version_name = f"v{new_version_number}.0"
        
        version_data = {
            "workflow_id": workflow_id,
            "version": new_version_name,
            "version_number": new_version_number,
            "description": "Automatically created version",
            "definition": workflow_definition,
            "changes": {},
            "created_by": user_id
        }
        
        response = await client.post(
            f"{METADATA_SERVICE_URL}/api/workflows/{workflow_id}/versions",
            json=version_data
        )
        return response.json()
```

### 2. 获取版本历史

```python
async def get_workflow_versions(workflow_id: str, skip: int = 0, limit: int = 100):
    """获取工作流的版本历史"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{METADATA_SERVICE_URL}/api/workflows/{workflow_id}/versions",
            params={"skip": skip, "limit": limit}
        )
        return response.json()
```

### 3. 恢复历史版本

```python
async def restore_workflow_version(workflow_id: str, version: str, description: str = None):
    """恢复工作流到历史版本"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{METADATA_SERVICE_URL}/api/workflows/{workflow_id}/versions/{version}/restore",
            json={
                "version": version,
                "description": description or f"Restore to version {version}"
            }
        )
        return response.json()
```

## 📊 数据库表结构

### workflow_versions 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| workflow_id | String(100) | 工作流ID（外键） |
| version | String(50) | 版本号 |
| version_number | Integer | 数字版本号（用于排序） |
| description | Text | 版本描述 |
| change_summary | Text | 变更摘要 |
| definition | JSON | 工作流定义 |
| changes | JSON | 变更详情 |
| created_by | String(255) | 创建者 |
| is_current | Boolean | 是否为当前版本 |
| deployed_at | DateTime | 部署时间 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

**索引**:
- `ix_workflow_versions_id`
- `ix_workflow_versions_workflow_id`
- `ix_workflow_versions_version`
- `ix_workflow_versions_is_current`
- `ix_workflow_versions_workflow_version_number` (复合索引)

**唯一约束**:
- `uq_workflow_version` (workflow_id, version)

### workflow_version_tags 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| version_id | Integer | 版本ID（外键） |
| tag | String(100) | 标签名称 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

**索引**:
- `ix_workflow_version_tags_id`
- `ix_workflow_version_tags_version_id`
- `ix_workflow_version_tags_tag`

**唯一约束**:
- `uq_version_tag` (version_id, tag)

## 🔒 安全特性

1. **数据验证**: 所有输入都通过Pydantic模型验证
2. **唯一约束**: 防止重复版本号和标签
3. **外键约束**: 确保数据完整性
4. **级联删除**: 删除工作流时自动删除所有版本

## 🎯 功能特性

1. **版本历史追踪**: 完整记录工作流的所有版本
2. **版本比较**: 通过changes字段记录版本间的变更
3. **版本标签**: 支持为版本添加标签（stable, beta等）
4. **版本恢复**: 可以基于历史版本创建新版本
5. **当前版本管理**: 自动管理当前活跃版本
6. **分页支持**: 版本列表支持分页查询

## 📝 注意事项

1. **版本号格式**: 建议使用语义化版本号（如v1.0.0），但系统不强制
2. **版本号唯一性**: 同一工作流的版本号必须唯一
3. **当前版本**: 创建新版本时，会自动将新版本设为当前版本
4. **级联删除**: 删除工作流时，所有相关版本和标签都会被删除
5. **版本定义**: 每个版本都存储完整的工作流定义，可以独立恢复

## 🐛 已知问题

无

## 🔄 后续优化建议

1. **版本比较功能**: 实现版本间的差异比较
2. **版本合并**: 支持合并多个版本的变更
3. **版本回滚**: 支持直接回滚到历史版本（不创建新版本）
4. **版本统计**: 添加版本使用统计和分析
5. **批量操作**: 支持批量管理版本标签

---

**实现完成时间**: 2024-01-XX  
**实现状态**: ✅ 完成  
**测试状态**: ⏳ 待测试


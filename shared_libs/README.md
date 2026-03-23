# 共享库 (Shared Libraries)

企业AI平台的共享库模块，提供通用的工具函数、数据模型和API客户端。

## 功能特性

- 🔧 **通用工具**: 日志、错误处理、配置管理
- 📡 **API客户端**: HTTP客户端和API调用封装
- 📊 **数据模型**: 共享的Pydantic模型和Schema
- 🔍 **元数据模型**: 元数据相关的数据模型

## 目录结构

```
shared_libs/
├── common/                  # 通用工具模块
│   ├── logger.py           # 日志工具
│   ├── error_handler.py    # 错误处理
│   ├── config.py           # 配置管理
│   ├── api_client.py       # API客户端
│   └── http_client.py      # HTTP客户端
├── schemas/                 # 数据模型和Schema
│   ├── base_models.py      # 基础模型
│   ├── common.py           # 通用模型
│   ├── monitoring_schemas.py # 监控模型
│   ├── tool_schemas.py     # 工具模型
│   └── workflow_schemas.py # 工作流模型
├── src/                     # 源代码模块
│   └── models/             # 元数据模型
│       ├── enums/          # 枚举类型
│       └── metadata_models.py # 元数据模型
├── requirements.txt        # Python依赖
└── README.md              # 本文档
```

## 使用方式

### 在服务中使用

所有服务通过以下方式使用共享库：

1. **Docker环境**: 通过Volume挂载 `/shared_libs`
2. **PYTHONPATH**: 在环境变量中设置 `PYTHONPATH=/app:/shared_libs:/database`
3. **导入**: 直接导入共享库模块

### 导入示例

```python
# 导入日志工具
from shared_libs.common.logger import setup_logger

logger = setup_logger(__name__)
logger.info("Hello from shared library")

# 导入错误处理
from shared_libs.common.error_handler import create_error_response

return create_error_response(
    status_code=400,
    message="Invalid request",
    details="Missing required field"
)

# 导入API客户端
from shared_libs.common.api_client import APIClient

client = APIClient(base_url="http://service:8000")
response = await client.get("/api/endpoint")

# 导入数据模型
from shared_libs.schemas.monitoring_schemas import ServiceMonitoringData

data = ServiceMonitoringData(
    service_name="my-service",
    status="healthy",
    metrics={}
)
```

## 模块说明

### common/logger.py

统一的日志工具，提供：
- 日志级别配置
- 格式化输出
- 文件日志支持

**使用示例**:
```python
from shared_libs.common.logger import setup_logger

logger = setup_logger(__name__)
logger.info("Info message")
logger.error("Error message", exc_info=True)
```

### common/error_handler.py

统一的错误处理，提供：
- 错误响应格式化
- 异常类型处理
- 错误详情记录

**使用示例**:
```python
from shared_libs.common.error_handler import create_error_response

try:
    # 业务逻辑
    pass
except ValueError as e:
    return create_error_response(
        status_code=400,
        message="Validation error",
        details=str(e)
    )
```

### common/api_client.py

API客户端封装，提供：
- 异步HTTP请求
- 请求重试
- 错误处理
- 响应解析

**使用示例**:
```python
from shared_libs.common.api_client import APIClient

client = APIClient(
    base_url="http://service:8000",
    timeout=30,
    retries=3
)

# GET请求
response = await client.get("/api/endpoint", params={"key": "value"})

# POST请求
response = await client.post("/api/endpoint", json={"data": "value"})
```

### schemas/

共享的数据模型和Schema，包括：
- **base_models.py**: 基础响应模型
- **common.py**: 通用数据模型
- **monitoring_schemas.py**: 监控相关模型
- **tool_schemas.py**: 工具相关模型
- **workflow_schemas.py**: 工作流相关模型

**使用示例**:
```python
from shared_libs.schemas.monitoring_schemas import (
    ServiceMonitoringData,
    HealthStatus
)

monitoring_data = ServiceMonitoringData(
    service_name="my-service",
    status=HealthStatus.HEALTHY,
    metrics={"cpu": 0.5, "memory": 0.7}
)
```

### src/models/

元数据相关的数据模型，包括：
- **metadata_models.py**: 元数据模型定义
- **enums/**: 枚举类型定义
  - **data_types.py**: 数据类型枚举
  - **quality_levels.py**: 质量级别枚举

## 依赖

主要依赖项：
- `pydantic>=2.5.0` - 数据验证
- `pydantic-settings>=2.1.0` - 配置管理
- `httpx>=0.25.2` - HTTP客户端

## 开发指南

### 添加新模块

1. 在相应目录下创建新文件
2. 实现功能
3. 在 `__init__.py` 中导出（如需要）
4. 更新本文档

### 添加新模型

1. 在 `schemas/` 目录下创建或修改文件
2. 定义Pydantic模型
3. 添加文档字符串
4. 更新本文档

## 注意事项

1. **导入路径**: 使用绝对导入 `from shared_libs.xxx import yyy`
2. **版本兼容**: 确保所有服务使用相同版本的共享库
3. **向后兼容**: 修改共享库时注意保持向后兼容
4. **依赖管理**: 共享库的依赖应尽可能少，避免版本冲突

## 相关文档

- [项目主文档](../README.md)
- [数据库模块文档](../database/README.md)
- [开发文档](../docs/development-docs/README.md)


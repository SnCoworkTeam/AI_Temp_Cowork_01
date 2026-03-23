# Python编码规范

## 代码风格

### 格式化工具
- **Black**: 代码格式化
- **isort**: 导入排序
- **flake8**: 代码检查

### 配置

```bash
# 格式化代码
black .

# 排序导入
isort .

# 检查代码
flake8 .
```

## 命名规范

### 变量和函数
- 使用小写字母和下划线: `user_name`, `get_user_info()`
- 私有方法以下划线开头: `_internal_method()`

### 类
- 使用大驼峰命名: `UserService`, `WorkflowRepository`

### 常量
- 使用大写字母和下划线: `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT`

## 类型注解

所有函数都应该有类型注解：

```python
def get_user(user_id: str) -> Optional[User]:
    """获取用户信息"""
    pass
```

## 文档字符串

使用Google风格的文档字符串：

```python
def process_workflow(workflow_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """处理工作流
    
    Args:
        workflow_id: 工作流ID
        input_data: 输入数据
        
    Returns:
        处理结果
        
    Raises:
        ValueError: 当工作流ID无效时
    """
    pass
```

## 导入顺序

1. 标准库导入
2. 第三方库导入
3. 本地应用导入

```python
import os
from typing import Dict, List

from fastapi import FastAPI
from sqlalchemy.orm import Session

from shared_libs.common.logger import setup_logger
```

## 错误处理

使用具体的异常类型，提供清晰的错误信息：

```python
try:
    result = process_data()
except ValueError as e:
    logger.error(f"数据验证失败: {e}")
    raise
except Exception as e:
    logger.error(f"未知错误: {e}")
    raise RuntimeError("处理失败") from e
```










# Service层模式

## 概述

Service层模式用于封装业务逻辑，位于Controller和Repository之间。

## 架构层次

```
Controller (Routes)
    ↓
Service (Business Logic)
    ↓
Repository (Data Access)
    ↓
Database
```

## 实现示例

```python
from workflow_engine.src.services.workflow_service import WorkflowService
from workflow_engine.src.repositories.workflow_repository import WorkflowRepository

class WorkflowService:
    def __init__(self, repo: WorkflowRepository):
        self.repo = repo
    
    def create_workflow(self, workflow_data: dict) -> WorkflowDefinition:
        # 业务逻辑验证
        if not workflow_data.get("name"):
            raise ValueError("工作流名称不能为空")
        
        # 调用Repository
        workflow = self.repo.create(workflow_data)
        return workflow
```

## 优势

- 业务逻辑集中管理
- 便于单元测试
- 支持事务管理
- 代码复用










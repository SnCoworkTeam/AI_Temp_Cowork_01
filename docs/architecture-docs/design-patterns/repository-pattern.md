# Repository模式

## 概述

Repository模式用于抽象数据访问层，提供统一的数据访问接口。

## 实现

### 基础Repository

```python
from database.src.repositories.base_repository import BaseRepository
from database.src.models.user_models import User

class UserRepository(BaseRepository[User]):
    def __init__(self, session: Session):
        super().__init__(User, session)
    
    def get_by_username(self, username: str) -> Optional[User]:
        return self.session.query(User).filter_by(username=username).first()
```

## 使用场景

- 数据访问统一管理
- 便于单元测试（可以mock Repository）
- 支持多种数据源切换

## 优势

- 业务逻辑与数据访问分离
- 易于测试和维护
- 支持数据源切换










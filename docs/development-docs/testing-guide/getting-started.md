# 测试指南

## 测试类型

### 单元测试
- **位置**: `service-name/tests/unit/`
- **特点**: 快速、独立、无外部依赖
- **运行**: `pytest -m unit`

### 集成测试
- **位置**: `tests/test-integration/`
- **特点**: 测试服务间集成
- **运行**: `pytest -m integration`

### 性能测试
- **位置**: `tests/test-performance/`
- **工具**: pytest + locust
- **运行**: `pytest -m performance`

### 安全测试
- **位置**: `tests/test-security/`
- **覆盖**: 认证、授权、输入验证
- **运行**: `pytest -m security`

## 编写测试

### 单元测试示例

```python
import pytest
from unittest.mock import Mock

@pytest.mark.unit
class TestUserService:
    def test_get_user(self):
        """测试获取用户"""
        mock_repo = Mock()
        mock_repo.get_by_id.return_value = User(id="1", username="test")
        
        service = UserService(mock_repo)
        user = service.get_user("1")
        
        assert user.username == "test"
```

### 集成测试示例

```python
import pytest
from fastapi.testclient import TestClient

@pytest.mark.integration
def test_create_workflow(client: TestClient):
    """测试创建工作流"""
    response = client.post(
        "/api/workflows",
        json={"name": "test_workflow"}
    )
    assert response.status_code == 201
```

## 运行测试

```bash
# 运行所有测试
pytest

# 运行特定类型
pytest -m unit
pytest -m integration

# 生成覆盖率报告
pytest --cov=. --cov-report=html
```

## 测试覆盖率

目标覆盖率：>= 80%

查看覆盖率报告：
```bash
open htmlcov/index.html
```










# 测试覆盖情况报告

## 概述

本报告展示了项目中所有模块的测试覆盖情况，帮助识别需要添加测试的模块。

## 测试覆盖统计

### 各服务测试覆盖情况

| 服务 | 源代码文件 | 测试文件 | 单元测试 | 集成测试 | 覆盖率 | 状态 |
|------|-----------|---------|---------|---------|--------|------|
| mcp-gateway | - | - | - | - | - | - |
| workflow-engine | - | - | - | - | - | - |
| auth-service | - | - | - | - | - | - |
| knowledge-base | - | - | - | - | - | - |
| metadata-service | - | - | - | - | - | - |
| database | - | - | - | - | - | - |
| shared_libs | - | - | - | - | - | - |

### 全局测试

- **架构测试**: 测试项目结构和导入依赖
- **集成测试**: 测试服务之间的交互
- **性能测试**: 测试API和数据库性能
- **安全测试**: 测试认证、授权和输入验证

## 运行测试覆盖检查

### 在服务器上运行

```bash
cd /opt/enterprise-ai-platform
bash tests/check-test-coverage.sh
```

### 在本地运行

```bash
cd tests
bash check-test-coverage.sh
```

## 测试覆盖目标

- **目标覆盖率**: >= 80%
- **关键路径**: 100%
- **最低要求**: >= 50%

## 缺失的测试

运行 `check-test-coverage.sh` 脚本会列出所有缺少测试的模块。

## 如何添加测试

### 1. 为服务添加单元测试

在 `service-name/tests/unit/` 目录下创建测试文件：

```python
# service-name/tests/unit/test_module_name.py
import pytest
from service_name.module_name import function_name

def test_function_name():
    result = function_name()
    assert result is not None
```

### 2. 为服务添加集成测试

在 `service-name/tests/integration/` 目录下创建测试文件：

```python
# service-name/tests/integration/test_api.py
import pytest
from fastapi.testclient import TestClient

def test_api_endpoint(test_app):
    response = test_app.get("/api/endpoint")
    assert response.status_code == 200
```

### 3. 运行新添加的测试

```bash
# 运行特定服务的测试
pytest service-name/tests/

# 运行特定测试文件
pytest service-name/tests/unit/test_module_name.py
```

## 持续改进

1. **定期检查**: 每次添加新功能后运行覆盖检查
2. **优先关键路径**: 优先为关键业务逻辑添加测试
3. **提高覆盖率**: 逐步提高测试覆盖率到80%以上
4. **维护测试**: 代码变更时同步更新测试

## 相关文档

- [测试指南](./TEST_GUIDE.md)
- [测试README](./README.md)


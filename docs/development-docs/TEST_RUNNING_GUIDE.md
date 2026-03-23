# 测试运行指南

## 概述

本指南说明如何运行测试、修复问题，并验证测试覆盖率。

## 快速开始

### 1. 安装测试依赖

```bash
# 安装所有测试依赖
pip install pytest pytest-asyncio pytest-cov pytest-mock httpx sqlalchemy

# 或者从requirements.txt安装
pip install -r tests/requirements.txt
```

### 2. 运行单个服务的测试

```bash
# metadata-service
cd metadata-service
pytest tests/ -v

# database
cd database
pytest tests/ -v

# workflow-engine
cd workflow-engine
pytest tests/ -v

# auth-service
cd auth-service
pytest tests/ -v

# knowledge-base
cd knowledge-base
pytest tests/ -v

# mcp-gateway
cd mcp-gateway
pytest tests/ -v
```

### 3. 运行所有测试

```bash
# 从项目根目录运行
cd tests
bash run-all-tests.sh all

# 或者使用pytest直接运行
pytest --cov=. --cov-report=html --cov-report=term
```

## 测试类型

### 单元测试

运行所有单元测试：

```bash
pytest -m unit -v
```

### 集成测试

运行所有集成测试：

```bash
pytest -m integration -v
```

## 测试覆盖率

### 生成覆盖率报告

```bash
# 生成HTML和终端报告
pytest --cov=. --cov-report=html --cov-report=term-missing

# 查看HTML报告
# 打开 htmlcov/index.html
```

### 检查覆盖率

```bash
# 使用覆盖率检查脚本
bash tests/check-test-coverage.sh
```

### 覆盖率目标

- 目标覆盖率：**80%+**
- 当前配置在 `pytest.ini` 中设置：`--cov-fail-under=80`

## 常见问题修复

### 1. 导入错误

**问题**：`ModuleNotFoundError: No module named 'src'`

**解决方案**：
- 确保测试文件正确设置了路径
- 检查 `conftest.py` 是否正确添加了项目路径
- 确保在正确的目录下运行测试

**示例修复**：
```python
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "service-name" / "src"))
```

### 2. 数据库连接错误

**问题**：数据库连接失败

**解决方案**：
- 单元测试应使用SQLite内存数据库
- 集成测试需要配置测试数据库
- 检查 `conftest.py` 中的数据库配置

### 3. 依赖缺失

**问题**：缺少测试依赖包

**解决方案**：
```bash
# 安装缺失的包
pip install package-name

# 添加到requirements.txt
echo "package-name" >> requirements.txt
```

### 4. Mock对象错误

**问题**：Mock对象未正确设置

**解决方案**：
- 确保使用 `unittest.mock` 或 `pytest-mock`
- 检查Mock对象的返回值类型
- 确保异步函数使用 `AsyncMock`

## 测试-修复循环

### 本地测试-修复流程

1. **运行测试**
   ```bash
   pytest tests/ -v --tb=short
   ```

2. **分析失败原因**
   - 查看错误堆栈
   - 检查导入路径
   - 验证依赖是否安装

3. **修复问题**
   - 修复导入错误
   - 添加缺失依赖
   - 修正测试逻辑

4. **重新运行测试**
   ```bash
   pytest tests/ -v
   ```

5. **重复直到所有测试通过**

### 服务器测试-修复流程

使用自动化脚本：

```powershell
# Windows PowerShell
.\scripts\deployment\test-and-fix.ps1
```

脚本功能：
- 自动在服务器上运行测试
- 解析测试结果
- 识别失败原因
- 等待修复后上传

## 测试文件结构

```
service-name/
├── tests/
│   ├── conftest.py          # 测试配置和fixtures
│   ├── unit/                # 单元测试
│   │   ├── test_models.py
│   │   ├── test_services.py
│   │   └── test_routes.py
│   └── integration/         # 集成测试
│       ├── test_api_integration.py
│       └── test_database_integration.py
```

## 测试最佳实践

### 1. 使用Fixtures

```python
@pytest.fixture
def db_session():
    """数据库会话fixture"""
    engine = create_engine("sqlite:///:memory:")
    # ...
    yield session
    # 清理
```

### 2. 使用Mock

```python
from unittest.mock import Mock, patch

@patch('module.external_api')
def test_function(mock_api):
    mock_api.return_value = {"result": "success"}
    # 测试代码
```

### 3. 测试命名

- 测试文件：`test_*.py`
- 测试类：`Test*`
- 测试函数：`test_*`

### 4. 使用标记

```python
@pytest.mark.unit
def test_unit_function():
    pass

@pytest.mark.integration
def test_integration_function():
    pass
```

## 调试测试

### 运行单个测试

```bash
# 运行特定测试文件
pytest tests/unit/test_models.py -v

# 运行特定测试函数
pytest tests/unit/test_models.py::TestDataAsset::test_create -v
```

### 详细输出

```bash
# 显示详细输出
pytest -v -s

# 显示失败测试的完整堆栈
pytest --tb=long
```

### 使用调试器

```python
import pytest

def test_function():
    # 设置断点
    import pdb; pdb.set_trace()
    # 或使用ipdb
    import ipdb; ipdb.set_trace()
```

## 持续集成

### CI配置示例

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest --cov=. --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## 性能测试

运行性能测试：

```bash
pytest -m performance -v
```

## 安全测试

运行安全测试：

```bash
pytest -m security -v
```

## 相关文档

- [测试实施总结](./TEST_IMPLEMENTATION_SUMMARY.md)
- [API文档](../api-docs/API_REFERENCE.md)
- [开发规范](../development-docs/DEVELOPMENT_GUIDE.md)

## 获取帮助

如果遇到问题：

1. 检查测试日志
2. 查看错误堆栈
3. 验证依赖安装
4. 检查配置文件
5. 参考本文档的常见问题部分



# 完整测试指南

## 概述

`tests` 文件夹包含了项目的完整测试框架，用于测试所有模块和服务。测试框架支持：

- **单元测试**: 测试单个函数和类
- **集成测试**: 测试服务之间的交互
- **性能测试**: 测试API和数据库性能
- **安全测试**: 测试认证、授权和输入验证
- **架构测试**: 验证项目结构和导入依赖

## 快速开始

### 1. 安装测试依赖

```bash
pip install -r tests/requirements.txt
```

### 2. 运行所有测试

**Linux/Mac:**
```bash
cd tests
chmod +x run-all-tests.sh
./run-all-tests.sh all
```

**Windows (PowerShell):**
```powershell
cd tests
.\run-all-tests.ps1 -TestType all
```

### 3. 运行特定类型的测试

```bash
# 只运行单元测试
./run-all-tests.sh unit

# 只运行集成测试
./run-all-tests.sh integration

# 只运行安全测试
./run-all-tests.sh security

# 运行特定服务的所有测试
./run-all-tests.sh service mcp-gateway
```

### 4. 生成覆盖率报告

```bash
# 运行所有测试并生成覆盖率报告
./run-all-tests.sh all true

# 查看覆盖率报告
# 打开 htmlcov/index.html
```

## 测试结构

```
tests/
├── conftest.py                    # 测试配置和共享fixtures
├── test-architecture/            # 架构测试
│   ├── test_imports.py           # 导入依赖测试
│   └── test_project_structure.py # 项目结构测试
├── test-integration/             # 集成测试
│   ├── test_api_integration.py   # API集成测试
│   ├── test_database_integration.py # 数据库集成测试
│   └── test_external_services.py # 外部服务测试
├── test-performance/             # 性能测试
│   ├── test_api_performance.py   # API性能测试
│   ├── test_database_performance.py # 数据库性能测试
│   └── locustfile.py             # Locust性能测试配置
└── test-security/                # 安全测试
    ├── test_authentication.py    # 认证测试
    ├── test_authorization.py     # 授权测试
    └── test_input_validation.py  # 输入验证测试

各服务目录:
service-name/
└── tests/
    ├── unit/                     # 单元测试
    ├── integration/              # 集成测试
    └── fixtures/                 # 测试数据
```

## 测试各服务模块

### MCP Gateway

```bash
# 运行MCP Gateway的所有测试
pytest mcp-gateway/tests/

# 只运行单元测试
pytest mcp-gateway/tests/unit -m unit

# 只运行集成测试
pytest mcp-gateway/tests/integration -m integration
```

### Workflow Engine

```bash
# 运行Workflow Engine的所有测试
pytest workflow-engine/tests/

# 测试工作流节点
pytest workflow-engine/tests/unit/test_nodes.py

# 测试数据库集成
pytest workflow-engine/tests/integration/test_database.py
```

### Auth Service

```bash
# 运行Auth Service的所有测试
pytest auth-service/tests/

# 测试认证功能
pytest auth-service/tests/integration/test_api.py -k login
```

### Knowledge Base

```bash
# 运行Knowledge Base的所有测试
pytest knowledge-base/tests/

# 测试知识库模型
pytest knowledge-base/tests/unit/test_models.py
```

### Metadata Service

```bash
# 运行Metadata Service的所有测试
pytest metadata-service/tests/
```

## 测试类型说明

### 单元测试

- **位置**: `service-name/tests/unit/`
- **特点**: 快速、独立、无外部依赖
- **运行**: `pytest -m unit`

### 集成测试

- **位置**: `service-name/tests/integration/` 和 `tests/test-integration/`
- **特点**: 测试服务之间的交互，需要数据库和Redis
- **运行**: `pytest -m integration`

### 性能测试

- **位置**: `tests/test-performance/`
- **工具**: pytest + locust
- **运行**: 
  ```bash
  pytest -m performance
  # 或使用Locust
  locust -f tests/test-performance/locustfile.py
  ```

### 安全测试

- **位置**: `tests/test-security/`
- **覆盖**: 认证、授权、输入验证、SQL注入、XSS等
- **运行**: `pytest -m security`

### 架构测试

- **位置**: `tests/test-architecture/`
- **覆盖**: 项目结构、导入依赖、架构符合性
- **运行**: `pytest tests/test-architecture/`

## 测试覆盖率

### 查看覆盖率

```bash
# 生成覆盖率报告
pytest --cov=. --cov-report=html --cov-report=term-missing

# 查看报告
# 打开 htmlcov/index.html
```

### 覆盖率要求

- **目标覆盖率**: >= 80%
- **关键路径**: 100%
- **当前覆盖率**: 运行测试后查看报告

## 常见问题排查

### 1. 测试失败 - 导入错误

**问题**: `ModuleNotFoundError: No module named 'shared_libs'`

**解决**:
```bash
# 确保PYTHONPATH包含项目根目录
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
# 或在pytest.ini中配置
```

### 2. 测试失败 - 数据库连接错误

**问题**: 集成测试需要数据库连接

**解决**:
- 单元测试使用内存数据库，无需配置
- 集成测试需要运行Docker服务：
  ```bash
  docker compose up -d postgres redis
  ```

### 3. 测试失败 - Redis连接错误

**问题**: 测试需要Redis

**解决**:
- 单元测试使用fakeredis mock
- 集成测试需要运行Redis：
  ```bash
  docker compose up -d redis
  ```

### 4. 性能测试超时

**问题**: 性能测试运行时间过长

**解决**:
- 调整性能阈值
- 使用 `-m "not slow"` 跳过慢速测试

## 持续集成

测试会自动在CI/CD流水线中运行。查看 `.github/workflows/` 了解CI配置。

## 最佳实践

1. **编写测试**: 每个新功能都应该有对应的测试
2. **测试命名**: 使用描述性的测试名称
3. **测试隔离**: 每个测试应该独立运行
4. **使用Fixtures**: 复用测试数据和配置
5. **Mock外部依赖**: 单元测试中mock所有外部服务
6. **定期运行**: 在提交代码前运行相关测试

## 测试报告

运行测试后会生成：

- **终端输出**: 实时测试结果
- **HTML覆盖率报告**: `htmlcov/index.html`
- **JSON覆盖率报告**: `coverage.json`
- **JUnit XML报告**: `junit.xml` (如果配置)

## 下一步

1. 运行完整测试套件：`./run-all-tests.sh all`
2. 查看覆盖率报告，找出未覆盖的代码
3. 为缺失的功能添加测试
4. 修复失败的测试
5. 提高测试覆盖率到80%以上


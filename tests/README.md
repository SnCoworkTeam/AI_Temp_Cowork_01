# 自动化测试框架

## 概述

本目录包含完整的自动化测试框架，包括单元测试、集成测试、性能测试和安全测试。

## 目录结构

```
tests/
├── conftest.py               # 测试配置和fixture
├── test-architecture/        # 架构测试
├── test-integration/         # 集成测试
├── test-performance/        # 性能测试
└── test-security/           # 安全测试

各服务中的测试结构：
service-name/
├── tests/
│   ├── unit/                # 单元测试
│   ├── integration/         # 集成测试
│   └── fixtures/            # 测试数据
```

## 测试类型

### 1. 单元测试
- **位置**: `service-name/tests/unit/`
- **特点**: 快速、独立、无外部依赖
- **运行**: `pytest tests/unit -m unit`

### 2. 集成测试
- **位置**: `tests/test-integration/` 和 `service-name/tests/integration/`
- **特点**: 覆盖关键业务流程
- **运行**: `pytest tests/test-integration -m integration`

### 3. 性能测试
- **位置**: `tests/test-performance/`
- **工具**: pytest + locust
- **运行**: 
  - `pytest tests/test-performance -m performance`
  - `locust -f tests/test-performance/locustfile.py`

### 4. 安全测试
- **位置**: `tests/test-security/`
- **覆盖**: 认证、授权、输入验证、数据安全
- **运行**: `pytest tests/test-security -m security`

### 5. 架构测试
- **位置**: `tests/test-architecture/`
- **覆盖**: 项目结构、导入依赖、架构符合性
- **运行**: `pytest tests/test-architecture -m unit`

## 运行测试

### 运行所有测试
```bash
pytest
```

### 运行特定类型的测试
```bash
# 单元测试
pytest -m unit

# 集成测试
pytest -m integration

# 性能测试
pytest -m performance

# 安全测试
pytest -m security
```

### 运行特定服务的测试
```bash
# MCP Gateway测试
pytest mcp-gateway/tests/

# Workflow Engine测试
pytest workflow-engine/tests/
```

### 运行并生成覆盖率报告
```bash
pytest --cov=. --cov-report=html
```

### 运行性能测试（Locust）
```bash
# 启动Locust Web界面
locust -f tests/test-performance/locustfile.py

# 命令行模式
locust -f tests/test-performance/locustfile.py --headless -u 100 -r 10 -t 60s
```

## 测试工具

### 必需工具
- **pytest**: 测试框架
- **pytest-asyncio**: 异步测试支持
- **pytest-cov**: 代码覆盖率
- **pytest-mock**: Mock支持

### 可选工具
- **hypothesis**: 属性测试
- **locust**: 性能测试
- **fakeredis**: Redis mock
- **httpx**: HTTP客户端

安装所有工具:
```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock hypothesis locust fakeredis httpx
```

## 测试Fixtures

### 数据库Fixtures
- `db_session`: 同步数据库会话
- `async_db_session`: 异步数据库会话

### Redis Fixtures
- `redis_client`: Redis客户端（使用fakeredis）
- `async_redis_client`: 异步Redis客户端

### HTTP Fixtures
- `http_client`: HTTP客户端
- `async_http_client`: 异步HTTP客户端
- `test_app`: FastAPI测试客户端
- `async_test_app`: 异步FastAPI测试客户端

### 认证Fixtures
- `mock_user`: 模拟用户
- `auth_token`: 认证token
- `authenticated_client`: 已认证的客户端

### 测试数据Fixtures
- `sample_workflow_data`: 示例工作流数据
- `sample_tool_data`: 示例工具数据
- `sample_document_data`: 示例文档数据

## 测试覆盖率要求

- **目标覆盖率**: >= 80%
- **关键路径**: 100%
- **工具**: pytest-cov
- **报告**: HTML和JSON格式

## 性能测试基准

- **API响应时间**: < 0.5秒
- **数据库查询**: < 0.1秒
- **并发请求**: 100个请求 < 5秒
- **内存使用**: < 500MB

## 安全测试覆盖

- **认证**: 无效凭证、token验证、token过期
- **授权**: 未授权访问、基于角色的访问控制
- **输入验证**: SQL注入、XSS、路径遍历、命令注入
- **数据安全**: 敏感数据泄露、加密、HTTPS强制

## 最佳实践

1. **单元测试**: 每个函数/方法都应该有对应的单元测试
2. **集成测试**: 覆盖关键业务流程和API端点
3. **性能测试**: 定期运行性能基准测试
4. **安全测试**: 每次发布前运行安全测试
5. **测试数据**: 使用fixtures和工厂模式生成测试数据
6. **Mock外部依赖**: 单元测试中mock所有外部服务

## CI/CD集成

测试会自动在CI/CD流水线中运行：

```yaml
# .github/workflows/tests.yml
- name: Run tests
  run: |
    pytest --cov=. --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## 故障排查

### 测试失败
- 检查测试环境是否正确配置
- 确认所有依赖已安装
- 查看测试日志和错误信息

### 覆盖率不足
- 运行 `pytest --cov=. --cov-report=term-missing` 查看未覆盖的代码
- 添加缺失的测试用例

### 性能测试失败
- 检查服务器是否运行
- 确认性能阈值设置合理
- 检查系统资源使用情况

## 联系方式

如有问题，请联系开发团队或查看项目文档。










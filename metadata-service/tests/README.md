# 工作流版本管理功能测试文档

## 📋 测试概览

本测试套件包含了对工作流版本管理功能的全面测试，包括单元测试、集成测试和性能测试。

## 🧪 测试结构

```
tests/
├── conftest.py              # 测试配置和fixtures
├── factories.py             # 测试数据工厂
├── test_models.py          # 数据模型测试
├── test_services.py        # 服务层测试
├── test_api.py             # API端点测试
├── test_integration.py     # 集成测试
└── test_performance.py     # 性能测试
```

## 🚀 快速开始

### 1. 安装测试依赖

```bash
cd metadata-service
pip install -r requirements.txt
```

### 2. 设置测试环境

#### 选项A：使用SQLite内存数据库（快速测试）

```bash
export USE_SQLITE=true
```

#### 选项B：使用PostgreSQL测试数据库

```bash
export TEST_DATABASE_URL="postgresql+psycopg2://test_user:test_pass@localhost:5432/test_metadata_db"
```

### 3. 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_models.py -v

# 运行特定测试类
pytest tests/test_services.py::TestVersionService -v

# 运行特定测试方法
pytest tests/test_api.py::TestWorkflowVersionsAPI::test_create_workflow_version_success -v

# 运行性能测试
pytest tests/test_performance.py -v

# 生成测试报告
pytest --html=report.html --self-contained-html
```

### 4. 测试覆盖率

```bash
# 运行测试并生成覆盖率报告
pytest --cov=src --cov-report=html --cov-report=term-missing

# 查看HTML报告
# Windows: start htmlcov/index.html
# Linux/Mac: open htmlcov/index.html
```

## 📝 测试说明

### 单元测试

#### test_models.py
- 测试数据模型的创建和关系
- 测试唯一约束
- 测试版本标签功能

#### test_services.py
- 测试版本服务的所有方法
- 测试错误处理
- 测试分页功能
- 测试版本标签操作

### API测试

#### test_api.py
- 测试所有RESTful API端点
- 测试HTTP状态码
- 测试请求/响应格式
- 测试错误处理

### 集成测试

#### test_integration.py
- 测试与Workflow Engine的集成场景
- 测试端到端工作流
- 测试版本恢复流程

### 性能测试

#### test_performance.py
- 测试并发版本创建
- 测试大数据量查询性能
- 验证性能要求

## 🔧 测试配置

### conftest.py

提供以下fixtures：
- `test_engine`: 测试数据库引擎
- `test_session`: 测试数据库会话
- `client`: FastAPI测试客户端
- `cleanup_test_data`: 自动清理测试数据

### factories.py

提供测试数据工厂：
- `WorkflowMetadataFactory`: 创建工作流元数据
- `WorkflowVersionFactory`: 创建工作流版本

## 📊 测试检查清单

### 功能测试
- [x] 创建工作流版本
- [x] 获取版本列表（分页）
- [x] 获取特定版本
- [x] 设置当前版本
- [x] 恢复历史版本
- [x] 版本标签管理
- [x] 错误处理（工作流不存在、版本重复等）

### 集成测试
- [x] Workflow Engine集成
- [x] 数据库操作
- [x] API端点集成

### 性能测试
- [x] 并发版本创建
- [x] 大数据量查询
- [x] 版本恢复性能

## 🐛 常见问题排查

### 1. 数据库连接问题

```bash
# 检查数据库连接
psql -h localhost -U test_user -d test_metadata_db

# 检查表是否存在
\dt
```

### 2. 测试数据清理

测试会自动清理数据，但如果需要手动清理：

```sql
-- 手动清理测试数据
DELETE FROM workflow_version_tags;
DELETE FROM workflow_versions;
DELETE FROM workflow_metadata;
```

### 3. 端口冲突

测试使用TestClient，不需要实际启动服务，因此不会有端口冲突问题。

### 4. 导入错误

确保项目根目录在Python路径中：

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## 📈 性能基准

### 并发版本创建
- **目标**: 10个版本创建 < 10秒
- **实际**: 根据数据库性能而定

### 大数据量查询
- **目标**: 20个版本查询 < 2秒
- **实际**: 根据数据库性能而定

## 🔄 持续集成

### GitHub Actions示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test_pass
          POSTGRES_USER: test_user
          POSTGRES_DB: test_metadata_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd metadata-service
          pip install -r requirements.txt
      
      - name: Run tests
        env:
          TEST_DATABASE_URL: postgresql+psycopg2://test_user:test_pass@localhost:5432/test_metadata_db
        run: |
          cd metadata-service
          pytest --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 📝 测试最佳实践

1. **隔离性**: 每个测试应该独立，不依赖其他测试
2. **可重复性**: 测试应该可以重复运行，结果一致
3. **快速性**: 单元测试应该快速执行
4. **清晰性**: 测试名称应该清晰描述测试内容
5. **覆盖率**: 尽量覆盖所有代码路径

## 🎯 下一步

- [ ] 添加更多边界测试
- [ ] 添加压力测试
- [ ] 添加安全测试
- [ ] 集成到CI/CD流程


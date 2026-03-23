# 工作流版本管理功能测试指南

## 📋 测试概览

本测试套件为工作流版本管理功能提供了全面的测试覆盖，包括：

- ✅ **单元测试**: 数据模型和服务层测试
- ✅ **API测试**: RESTful API端点测试
- ✅ **集成测试**: 与Workflow Engine的集成测试
- ✅ **性能测试**: 并发和大数据量测试

## 🚀 快速开始

### 1. 安装依赖

```bash
cd metadata-service
pip install -r requirements.txt
```

### 2. 配置测试环境

#### 选项A：使用SQLite（推荐用于快速测试）

```bash
export USE_SQLITE=true
```

#### 选项B：使用PostgreSQL

```bash
export TEST_DATABASE_URL="postgresql+psycopg2://user:pass@localhost:5432/test_db"
```

### 3. 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_models.py -v

# 运行特定测试类
pytest tests/test_services.py::TestVersionService -v

# 运行并显示覆盖率
pytest --cov=src --cov-report=html --cov-report=term-missing
```

## 📁 测试文件结构

```
tests/
├── conftest.py              # 测试配置和fixtures
├── factories.py             # 测试数据工厂
├── test_models.py          # 数据模型测试
├── test_services.py        # 服务层测试
├── test_api.py             # API端点测试
├── test_integration.py     # 集成测试
├── test_performance.py     # 性能测试
└── README.md               # 测试文档
```

## 🧪 测试说明

### 单元测试

#### test_models.py
测试数据模型的基本功能：
- 版本创建和关系
- 版本标签
- 唯一约束

#### test_services.py
测试版本服务的业务逻辑：
- 版本创建、查询、更新
- 当前版本管理
- 版本恢复
- 标签管理
- 错误处理

### API测试

#### test_api.py
测试所有RESTful API端点：
- POST `/api/workflows/{id}/versions` - 创建版本
- GET `/api/workflows/{id}/versions` - 获取版本列表
- GET `/api/workflows/{id}/versions/{version}` - 获取特定版本
- PUT `/api/workflows/{id}/versions/{version}/set-current` - 设置当前版本
- POST `/api/workflows/{id}/versions/{version}/restore` - 恢复版本
- POST `/api/workflows/{id}/versions/{version}/tags/{tag}` - 添加标签
- DELETE `/api/workflows/{id}/versions/{version}/tags/{tag}` - 移除标签

### 集成测试

#### test_integration.py
测试与Workflow Engine的集成场景：
- 工作流保存时自动创建版本
- 版本恢复工作流

### 性能测试

#### test_performance.py
测试性能指标：
- 并发版本创建（10个版本 < 10秒）
- 大数据量查询（20个版本 < 2秒）

## 📊 测试覆盖率目标

- **目标覆盖率**: > 80%
- **关键路径**: 100%
- **错误处理**: > 90%

## 🔧 测试配置

### conftest.py Fixtures

- `test_engine`: 测试数据库引擎（session scope）
- `test_session`: 测试数据库会话（function scope）
- `client`: FastAPI测试客户端（function scope）
- `cleanup_test_data`: 自动清理测试数据（autouse）

### factories.py

提供测试数据工厂：
- `WorkflowMetadataFactory.create()`: 创建工作流元数据
- `WorkflowVersionFactory.create()`: 创建工作流版本

## 🐛 常见问题

### 1. 数据库连接失败

**问题**: `psycopg2.OperationalError: could not connect to server`

**解决**:
- 检查PostgreSQL服务是否运行
- 验证数据库连接字符串
- 使用SQLite进行快速测试：`export USE_SQLITE=true`

### 2. 导入错误

**问题**: `ModuleNotFoundError: No module named 'src'`

**解决**:
```bash
# 确保在metadata-service目录下运行
cd metadata-service
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### 3. 测试数据未清理

**问题**: 测试之间数据污染

**解决**:
- 检查`cleanup_test_data` fixture是否正常工作
- 手动清理：`pytest --setup-show`查看fixture执行顺序

### 4. 性能测试失败

**问题**: 性能测试超时

**解决**:
- 检查数据库性能
- 调整性能阈值
- 使用更快的测试数据库（SQLite）

## 📈 持续集成

### GitHub Actions配置

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
```

## 📝 测试最佳实践

1. **测试隔离**: 每个测试应该独立，不依赖其他测试
2. **数据清理**: 使用fixtures自动清理测试数据
3. **快速执行**: 单元测试应该在毫秒级完成
4. **清晰命名**: 测试名称应该清晰描述测试内容
5. **完整覆盖**: 覆盖正常路径、错误路径和边界条件

## 🎯 下一步

- [ ] 添加更多边界测试
- [ ] 添加压力测试
- [ ] 添加安全测试
- [ ] 集成到CI/CD流程
- [ ] 添加测试报告自动化

---

**最后更新**: 2024-01-XX  
**测试状态**: ✅ 完成  
**覆盖率**: 待运行测试后确定


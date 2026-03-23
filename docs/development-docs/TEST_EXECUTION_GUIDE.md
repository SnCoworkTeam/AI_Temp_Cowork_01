# 测试执行指南

## 当前状态

### ✅ 已完成的工作

1. **测试文件创建** - 所有服务的测试文件已创建（19个文件）
2. **代码修复** - 修复了导入格式问题
3. **文档更新** - 更新了所有相关文档
4. **测试工具** - 创建了测试运行脚本

### 📋 下一步：执行测试-修复循环

## 执行步骤

### 步骤1：准备测试环境

#### 本地环境

```bash
# 安装测试依赖
pip install pytest pytest-asyncio pytest-cov pytest-mock httpx sqlalchemy

# 或从requirements.txt安装
pip install -r tests/requirements.txt
```

#### 服务器环境

确保服务器上已安装：
- Python 3.11+
- pytest及相关依赖
- 所有服务的依赖包

### 步骤2：运行测试

#### 选项A：本地测试（推荐先执行）

**Windows PowerShell:**
```powershell
# 运行所有测试
.\tests\run-tests-local.ps1 all -Coverage

# 运行单个服务测试
.\tests\run-tests-local.ps1 metadata-service
```

**Linux/Mac:**
```bash
# 运行所有测试
bash tests/run-tests-local.sh all true

# 运行单个服务测试
bash tests/run-tests-local.sh metadata-service
```

#### 选项B：服务器测试（需要SSH连接）

```powershell
# 使用自动化脚本
.\scripts\deployment\test-and-fix.ps1
```

### 步骤3：分析测试结果

#### 常见错误类型

1. **导入错误 (ModuleNotFoundError)**
   - 检查 `conftest.py` 中的路径设置
   - 确保 `sys.path` 正确配置
   - 验证服务 `src` 目录在路径中

2. **依赖缺失**
   - 检查 `requirements.txt`
   - 安装缺失的包
   - 更新 `requirements.txt`

3. **数据库连接错误**
   - 单元测试应使用SQLite内存数据库
   - 检查 `conftest.py` 中的数据库配置
   - 确保使用 `sqlite:///:memory:`

4. **Mock对象错误**
   - 检查Mock对象的返回值类型
   - 确保异步函数使用 `AsyncMock`
   - 验证Mock对象的调用次数

5. **模型/服务初始化错误**
   - 检查模型初始化参数
   - 验证必需字段
   - 检查枚举值

### 步骤4：修复问题

#### 修复导入错误

如果遇到 `ModuleNotFoundError: No module named 'src'`：

1. 检查测试文件开头的路径设置：
```python
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "service-name" / "src"))
```

2. 确保 `conftest.py` 也设置了路径

#### 修复依赖缺失

1. 安装缺失的包：
```bash
pip install package-name
```

2. 添加到 `requirements.txt`：
```bash
echo "package-name" >> service-name/requirements.txt
```

#### 修复数据库错误

确保测试使用内存数据库：
```python
@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
```

### 步骤5：重新运行测试

修复后重新运行测试：

```bash
# 运行特定服务的测试
pytest service-name/tests/ -v

# 运行所有测试
pytest --cov=. --cov-report=html --cov-report=term-missing
```

### 步骤6：验证覆盖率

```bash
# 检查覆盖率
bash tests/check-test-coverage.sh

# 查看覆盖率报告
# 打开 htmlcov/index.html
```

**目标**：所有服务达到80%+覆盖率

### 步骤7：功能验证

#### 验证用户名密码登录注册

1. **后端API测试**：
```bash
# 测试注册端点
curl -X POST http://localhost:8003/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"SecurePass123!"}'

# 测试登录端点
curl -X POST http://localhost:8003/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"SecurePass123!"}'
```

2. **前端功能测试**：
   - 访问 `http://localhost:3000/login`
   - 测试注册表单
   - 测试登录表单
   - 验证SSO登录仍然工作

#### 验证SSO功能

确保SSO登录功能不受影响：
- 测试SSO登录流程
- 验证令牌刷新
- 检查用户会话管理

#### 验证所有API端点

运行API集成测试：
```bash
pytest -m integration -v
```

## 测试执行顺序

### 推荐顺序

1. **metadata-service** - 基础服务，依赖较少
2. **database** - 数据库服务，其他服务依赖
3. **auth-service** - 认证服务，其他服务可能依赖
4. **workflow-engine** - 工作流服务
5. **knowledge-base** - 知识库服务
6. **mcp-gateway** - 网关服务

### 执行策略

1. **先运行单元测试** - 快速发现问题
2. **再运行集成测试** - 验证完整流程
3. **最后验证覆盖率** - 确保达到目标

## 问题跟踪

### 记录问题

建议创建一个问题跟踪文档：

```markdown
# 测试问题跟踪

## metadata-service
- [ ] 问题1：导入错误
- [ ] 问题2：依赖缺失

## database
- [ ] 问题1：数据库连接错误

...
```

### 修复优先级

1. **高优先级**：导入错误、依赖缺失（阻塞测试运行）
2. **中优先级**：Mock对象错误、模型初始化错误
3. **低优先级**：测试逻辑优化、覆盖率提升

## 自动化脚本使用

### test-and-fix.ps1

这个脚本会自动：
1. 在服务器上运行测试
2. 解析测试结果
3. 识别失败原因
4. 等待修复后上传

**使用方式**：
```powershell
.\scripts\deployment\test-and-fix.ps1
```

**注意事项**：
- 需要配置 `remote.ssh` 文件
- 需要SSH访问权限
- 脚本会等待手动修复后继续

## 测试覆盖目标

### 各服务目标

| 服务 | 当前覆盖率 | 目标覆盖率 | 状态 |
|------|----------|----------|------|
| metadata-service | ~0% | 80%+ | 🔄 进行中 |
| database | ~0% | 80%+ | 🔄 进行中 |
| workflow-engine | ~11.5% | 80%+ | 🔄 进行中 |
| auth-service | ~8.3% | 80%+ | 🔄 进行中 |
| knowledge-base | ~7.5% | 80%+ | 🔄 进行中 |
| mcp-gateway | ~21.4% | 80%+ | 🔄 进行中 |

### 覆盖率检查

运行覆盖率检查：
```bash
bash tests/check-test-coverage.sh
```

查看详细报告：
```bash
pytest --cov=. --cov-report=html
# 打开 htmlcov/index.html
```

## 完成标准

### 测试通过标准

- ✅ 所有单元测试通过
- ✅ 所有集成测试通过
- ✅ 所有服务覆盖率达到80%+
- ✅ 无lint错误
- ✅ 无导入错误

### 功能验证标准

- ✅ 用户名密码注册功能正常
- ✅ 用户名密码登录功能正常
- ✅ SSO登录功能正常
- ✅ 所有API端点正常工作
- ✅ 前端登录表单正常

### 文档更新标准

- ✅ 测试文档已更新
- ✅ API文档已更新
- ✅ README已更新
- ✅ 测试运行指南已创建

## 获取帮助

### 参考文档

- [测试运行指南](./TEST_RUNNING_GUIDE.md)
- [测试实施总结](./TEST_IMPLEMENTATION_SUMMARY.md)
- [测试实施完成报告](./TEST_IMPLEMENTATION_COMPLETE.md)
- [API文档](../api-docs/API_REFERENCE.md)

### 常见问题

参考 [测试运行指南](./TEST_RUNNING_GUIDE.md) 中的"常见问题修复"部分。

## 下一步

1. **立即执行**：运行本地测试，识别问题
2. **修复问题**：根据错误信息修复代码
3. **验证覆盖率**：确保达到80%+目标
4. **功能验证**：测试所有功能正常工作
5. **文档更新**：更新最终文档

---

**提示**：建议先在一个服务上完成完整的测试-修复循环，然后再扩展到其他服务。



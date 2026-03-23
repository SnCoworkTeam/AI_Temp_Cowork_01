# Shared Library 重构方案

## 当前问题

1. **包结构混乱**：`shared_libs` 既作为包名又作为目录名，导致导入路径混乱
2. **PYTHONPATH依赖**：需要复杂的PYTHONPATH配置才能正确导入
3. **Docker挂载冗余**：多个位置挂载同一个目录
4. **不符合Python包规范**：缺少标准的打包配置

## 主流解决方案对比

### 方案1：独立Python包（推荐）⭐

**特点：**
- 最符合Python生态标准
- 易于版本管理和发布
- 可以发布到私有PyPI或直接从Git安装
- 明确的依赖关系

**结构：**
```
shared_libs/
├── pyproject.toml          # 现代Python包配置
├── setup.py                # 向后兼容
├── README.md
├── luminaos_common/        # 包名（使用下划线）
│   ├── __init__.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── workflow_schemas.py
│   │   ├── agent_schemas.py
│   │   └── workflow_states.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── base.py
│   ├── common/
│   │   ├── __init__.py
│   │   └── utils.py
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
└── tests/
    ├── __init__.py
    ├── test_schemas.py
    └── test_utils.py
```

**Dockerfile示例：**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 方式1：开发环境 - 可编辑安装
COPY shared_libs /tmp/shared_libs
RUN pip install -e /tmp/shared_libs

# 方式2：生产环境 - 从Git安装
RUN pip install git+https://github.com/org/repo.git@v1.0.0#subdirectory=shared_libs

# 方式3：从wheel安装
COPY shared_libs/dist/luminaos_common-1.0.0-py3-none-any.whl /tmp/
RUN pip install /tmp/luminaos_common-1.0.0-py3-none-any.whl

# 应用代码
COPY src/ ./src/
```

**使用方式：**
```python
# 统一的导入方式
from luminaos_common.schemas.workflow_schemas import WorkflowCreate
from luminaos_common.schemas.workflow_states import WorkflowState
from luminaos_common import __version__

# 简洁的导入
from luminaos_common import WorkflowCreate, WorkflowState
```

**优点：**
- ✅ 符合Python包规范
- ✅ 不需要复杂的PYTHONPATH
- ✅ 易于测试和发布
- ✅ 版本控制清晰
- ✅ IDE支持良好

**缺点：**
- ❌ 需要重构现有代码的导入语句
- ❌ Docker构建时间稍长（需要pip install）

---

### 方案2：Monorepo + Bazel/Pants

**特点：**
- Google、Uber等大公司使用
- 适合超大型项目（100+服务）
- 强大的依赖管理和增量构建

**示例：**
```
enterprise-ai-platform/
├── WORKSPACE              # Bazel配置
├── libs/
│   ├── schemas/
│   │   ├── BUILD          # 构建规则
│   │   └── workflow.py
│   └── utils/
│       ├── BUILD
│       └── helpers.py
└── services/
    └── workflow-engine/
        ├── BUILD          # 依赖声明：//libs/schemas
        └── main.py
```

**优点：**
- ✅ 强大的依赖分析
- ✅ 增量构建
- ✅ 统一的构建系统

**缺点：**
- ❌ 学习曲线陡峭
- ❌ 工具链复杂
- ❌ 对小项目过度设计

---

### 方案3：Git Submodule

**特点：**
- 共享库独立的Git仓库
- 各服务作为submodule引用

**结构：**
```
enterprise-ai-platform/
├── .gitmodules
├── libs/
│   └── luminaos-common/   # Git submodule
│       └── .git
└── services/
    └── workflow-engine/
        └── Dockerfile
```

**Dockerfile：**
```dockerfile
COPY libs/luminaos-common /tmp/luminaos-common
RUN pip install /tmp/luminaos-common
```

**优点：**
- ✅ 共享库可独立版本控制
- ✅ 可以被其他项目复用

**缺点：**
- ❌ Git submodule操作复杂
- ❌ 团队成员容易忘记更新submodule
- ❌ CI/CD需要额外配置

---

### 方案4：Docker多阶段构建

**特点：**
- 在Docker层面共享
- 构建wheel包统一分发

**Dockerfile：**
```dockerfile
# Stage 1: 构建共享库wheel
FROM python:3.11-slim as builder
WORKDIR /build
COPY shared_libs/ /build/shared_libs/
RUN cd shared_libs && pip wheel --no-deps -w /wheels .

# Stage 2: 各服务基础镜像
FROM python:3.11-slim as base
COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels luminaos-common

# Stage 3: Workflow Engine
FROM base as workflow-engine
WORKDIR /app
COPY workflow-engine/src /app/src
CMD ["python", "-m", "src.main"]
```

**优点：**
- ✅ Docker层缓存
- ✅ 构建速度快
- ✅ 一次构建多次使用

**缺点：**
- ❌ 调试相对困难
- ❌ 开发环境需要额外配置

---

## 推荐的迁移步骤（方案1）

### Step 1: 重构包结构 ✅ 已完成

```bash
shared_libs/
├── pyproject.toml           # ✅ 已创建
├── luminaos_common/         # ✅ 已创建
│   ├── __init__.py          # ✅ 已创建
│   ├── schemas/             # ✅ 已移动
│   └── common/              # ✅ 已移动
```

### Step 2: 更新导入语句

**需要修改的文件：**
1. `workflow-engine/src/models/workflow_models.py`
2. `workflow-engine/src/routes/*.py`
3. `mcp-gateway/src/**/*.py`
4. `auth-service/src/**/*.py`
5. 其他所有引用`shared_libs`的文件

**修改示例：**
```python
# 旧的导入（不一致）
from shared_libs.schemas.workflow_schemas import WorkflowCreate
from shared_libs.schemas import workflow_states

# 新的导入（统一标准）
from luminaos_common.schemas.workflow_schemas import WorkflowCreate
from luminaos_common.schemas.workflow_states import WorkflowState

# 或者使用顶层导入
from luminaos_common import WorkflowCreate, WorkflowState
```

### Step 3: 更新Dockerfile

**workflow-engine/Dockerfile.dev:**
```dockerfile
FROM python:3.11-slim as builder
# 安装共享库
COPY shared_libs /tmp/shared_libs
RUN pip install -e /tmp/shared_libs

FROM builder as development
WORKDIR /app
# 不再需要volume挂载shared_libs
# 不再需要复杂的PYTHONPATH配置
COPY workflow-engine/src /app/src
```

### Step 4: 更新docker-compose.yml

```yaml
workflow-engine:
  environment:
    - PYTHONPATH=/app:/database  # 移除/shared_libs相关路径
  volumes:
    - ./workflow-engine/src:/app/src:cached
    - ./database:/database:cached
    # 移除shared_libs的volume挂载
```

### Step 5: 测试和验证

```bash
# 1. 本地测试安装
cd shared_libs
pip install -e .

# 2. 测试导入
python -c "from luminaos_common import WorkflowState; print('OK')"

# 3. 运行单元测试
pytest shared_libs/tests/

# 4. 构建Docker镜像
docker-compose build workflow-engine

# 5. 启动服务测试
docker-compose up -d workflow-engine
```

---

## 其他公司的实践案例

### Netflix
- 使用独立Python包 + 内部PyPI服务器
- 每个共享库都是独立的包，有自己的版本和测试
- 通过 `requirements.txt` 声明依赖版本

### Uber
- Monorepo + Bazel
- 所有代码在一个巨大的repo中
- 使用Bazel管理依赖和构建

### Airbnb
- Git Submodule + 内部Gem/PyPI
- 共享库独立repo，各项目通过submodule引用
- 发布到内部包管理器供生产使用

### Spotify
- 独立包 + Artifactory（包管理器）
- 每个共享库CI/CD自动发布
- 服务通过版本号引用稳定版本

---

## 总结

**对于你的项目（中等规模微服务）：**

1. **短期方案**（当前）：
   - 使用 `/` 作为PYTHONPATH
   - 保持`shared_libs`作为包名
   - ✅ 优点：快速修复，不需要大规模重构
   - ❌ 缺点：不够优雅，仍有技术债

2. **长期方案**（推荐）：
   - 重构为 `luminaos_common` 标准包
   - 使用 `pip install -e` 安装
   - 移除PYTHONPATH和volume挂载
   - ✅ 优点：符合规范，易于维护和扩展
   - ✅ 可以发布到私有PyPI或直接从Git安装

**建议：**
1. 先完成功能开发
2. 等系统稳定后，安排专门的重构sprint
3. 一次性重构所有导入语句和Docker配置
4. 添加自动化测试确保重构正确

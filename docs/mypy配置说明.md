# mypy 类型检查配置说明

## 问题描述

项目包名包含连字符（`project_management`），这不符合 Python 包命名规范（应使用下划线）。mypy 在检查时无法正确识别这种包结构，会报错：

```
project_management is not a valid Python package name
```

这是因为 mypy 在解析文件路径时，会尝试将路径转换为包名，而包含连字符的路径会被识别为无效的包名。

## 解决方案

### 方案一：使用模块路径而非文件路径（推荐）

由于包名包含连字符，**不能直接使用文件路径**运行 mypy。需要使用以下方法之一：

#### 方法1：使用 -m 参数（推荐）

```bash
# 设置 PYTHONPATH
$env:PYTHONPATH="project_management\src"

# 使用 -m 参数指定模块
# 注意：需要从项目根目录运行，且模块路径不能包含连字符
# 由于项目结构限制，此方法可能不适用
```

#### 方法2：使用 --namespace-packages（推荐）

```bash
# 设置 PYTHONPATH
$env:PYTHONPATH="project_management\src"

# 使用 --namespace-packages 选项
mypy --config-file mypy.ini --namespace-packages project_management/src/routes/project_plans.py
```

#### 方法3：创建符号链接（最佳方案）

在项目根目录创建符号链接，将 `project_management` 链接为 `project_management`：

```bash
# Windows (需要管理员权限)
mklink /D project_management project_management

# Linux/Mac
ln -s project_management project_management
```

然后使用符号链接路径运行 mypy：

```bash
mypy --config-file mypy.ini project_management/src/routes/project_plans.py
```

### 方案二：使用 mypy.ini 配置文件

已创建 `mypy.ini` 配置文件，主要配置如下：

#### 1. 基本配置

```ini
[mypy]
python_version = 3.10
ignore_missing_imports = True
follow_imports = normal
show_error_codes = True
```

#### 2. 路径匹配配置

mypy 使用文件系统路径匹配，而不是 Python 包名，所以可以这样配置：

```ini
# 使用通配符匹配路由模块
[mypy-*.routes.*]
ignore_missing_imports = False
follow_imports = normal
```

### 方案二：使用 PYTHONPATH 环境变量

在运行 mypy 时设置 PYTHONPATH：

```bash
# Windows PowerShell
$env:PYTHONPATH="project_management\src"
mypy --config-file mypy.ini project_management\src\routes\project_plans.py

# Linux/Mac
export PYTHONPATH="project_management/src"
mypy --config-file mypy.ini project_management/src/routes/project_plans.py
```

### 方案三：使用 pyproject.toml（推荐用于新项目）

如果项目使用 `pyproject.toml`，可以添加 mypy 配置：

```toml
[tool.mypy]
python_version = "3.10"
ignore_missing_imports = true
follow_imports = "normal"
show_error_codes = true

[[tool.mypy.overrides]]
module = [
    "database.*",
    "project_management.*",
]
ignore_missing_imports = true
```

## 使用方法

### ⚠️ 重要提示

由于包名包含连字符，**不能直接使用文件路径**。请使用以下方法之一：

### ⚠️ 重要：mypy 无法直接处理包含连字符的路径

mypy 在解析文件路径时会尝试将其转换为 Python 包名，包含连字符的路径会被拒绝。因此，**必须使用符号链接**。

### 方法：创建符号链接（唯一可行方案）

```bash
# Windows (PowerShell管理员模式)
# 注意：需要以管理员身份运行 PowerShell
New-Item -ItemType SymbolicLink -Path "project_management" -Target "project_management"

# 验证符号链接
Test-Path project_management

# 然后使用符号链接路径运行 mypy
$env:PYTHONPATH="project_management\src"
mypy --config-file mypy.ini project_management/src/routes/project_plans.py

# 检查整个目录
mypy --config-file mypy.ini project_management/src/routes/
```

**Linux/Mac 系统：**

```bash
# 创建符号链接
ln -s project_management project_management

# 设置 PYTHONPATH
export PYTHONPATH="project_management/src"

# 运行 mypy
mypy --config-file mypy.ini project_management/src/routes/project_plans.py
```

### 方法3：使用相对导入检查（临时方案）

```bash
# 进入src目录
cd project_management/src

# 使用相对路径
mypy --config-file ../../mypy.ini routes/project_plans.py
```

### 4. 生成 HTML 报告

```bash
mypy --config-file mypy.ini project_management/src/routes/ --html-report mypy-report
```

## 配置选项说明

### 常用选项

- `python_version`: Python 版本
- `ignore_missing_imports`: 忽略无法解析的导入（第三方库）
- `follow_imports`: 导入跟踪级别（normal/silent/skip）
- `show_error_codes`: 显示错误代码
- `disallow_untyped_defs`: 禁止未类型化的函数定义
- `warn_return_any`: 警告返回 Any 类型
- `warn_unused_ignores`: 警告未使用的 ignore 注释

### 严格模式

如果需要更严格的类型检查，可以启用：

```ini
[mypy]
strict = True
# 或者单独启用
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_return_any = True
warn_unused_configs = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True
```

## 处理导入问题

### 1. 相对导入

对于相对导入（如 `from ..middleware import ...`），mypy 需要正确的包结构：

```ini
[mypy-*.middleware.*]
ignore_missing_imports = False
```

### 2. 第三方库

对于第三方库，建议忽略：

```ini
[mypy-fastapi.*]
ignore_missing_imports = True

[mypy-sqlalchemy.*]
ignore_missing_imports = True

[mypy-pydantic.*]
ignore_missing_imports = True
```

### 3. 本地模块

对于本地模块，可以启用检查：

```ini
[mypy-database.*]
ignore_missing_imports = False
```

## 常见问题

### Q1: mypy 报错 "project_management is not a valid Python package name"

**原因**: mypy 无法识别包含连字符的包名。

**解决**:
1. 使用文件路径而不是包名运行 mypy
2. 配置 `mypy.ini` 使用路径匹配
3. 设置 `PYTHONPATH` 环境变量

### Q2: 无法解析相对导入

**原因**: mypy 需要正确的包结构信息。

**解决**:
1. 确保 `PYTHONPATH` 包含项目根目录
2. 使用 `--namespace-packages` 选项
3. 在配置中设置 `explicit_package_bases = True`

### Q3: 第三方库类型检查失败

**原因**: 第三方库可能没有类型存根。

**解决**:
1. 安装类型存根：`pip install types-requests types-python-dateutil`
2. 在配置中忽略：`[mypy-库名.*] ignore_missing_imports = True`

## 最佳实践

### 1. 渐进式类型检查

不要一开始就启用严格模式，逐步添加类型注解：

```ini
# 第一阶段：只检查明显错误
disallow_untyped_defs = False
ignore_missing_imports = True

# 第二阶段：启用更多检查
disallow_untyped_defs = True
warn_return_any = True

# 第三阶段：严格模式
strict = True
```

### 2. 使用类型注解

逐步为函数添加类型注解：

```python
from typing import List, Optional

def get_project_plans(
    project_id: str,
    skip: int = 0,
    limit: int = 100
) -> List[dict]:
    """获取项目计划列表"""
    ...
```

### 3. 使用类型忽略

对于暂时无法修复的问题，使用类型忽略：

```python
# type: ignore[import]
from some_module import something

# 或者指定具体错误代码
# type: ignore[assignment]
result = some_function()  # mypy: ignore
```

### 4. 配置 CI/CD

在 CI/CD 流程中添加 mypy 检查：

```yaml
# .github/workflows/type-check.yml
- name: Type check with mypy
  run: |
    pip install mypy
    mypy --config-file mypy.ini project_management/src/
```

## 验证配置

运行以下命令验证配置是否正确：

```bash
# 检查配置文件语法
mypy --config-file mypy.ini --show-config

# 测试单个文件
mypy --config-file mypy.ini project_management/src/routes/project_plans.py

# 检查所有路由文件
mypy --config-file mypy.ini project_management/src/routes/
```

## 参考资源

- [mypy 官方文档](https://mypy.readthedocs.io/)
- [mypy 配置选项](https://mypy.readthedocs.io/en/stable/config_file.html)
- [Python 类型注解指南](https://docs.python.org/3/library/typing.html)


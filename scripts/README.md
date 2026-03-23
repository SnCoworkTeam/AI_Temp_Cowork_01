# 架构守护脚本

## 概述

架构守护脚本用于确保代码质量和不偏离设计理念，自动检查项目结构、导入规范、API规范等。

## 使用方法

### 架构守护脚本 (architecture_guard.py)

```bash
# 检查项目结构
python scripts/architecture_guard.py --check

# 验证特定文件的导入
python scripts/architecture_guard.py --validate-imports mcp-gateway/src/main.py

# 生成健康报告
python scripts/architecture_guard.py --report --output architecture_report.json

# 自动修复可修复的违规
python scripts/architecture_guard.py --auto-fix
```

### 预提交钩子 (pre-commit-hook.py)

```bash
# 安装git预提交钩子
python scripts/pre-commit-hook.py --install

# 手动运行预提交检查
python scripts/pre-commit-hook.py
```

## 检查规则

### 1. 项目结构验证
- 检查必需的服务目录（mcp-gateway, workflow-engine, web-ui, shared-libs）
- 检查必需的文件（requirements.txt, Dockerfile, package.json等）
- 检查目录结构是否符合规范

### 2. 导入验证
- 检查Python文件的导入是否符合服务规范
- 验证不允许的依赖导入
- 确保使用共享库而非直接导入

### 3. API规范验证
- 检查OpenAPI文档完整性
- 验证健康检查端点存在
- 检查API描述和响应模型

### 4. 测试覆盖率
- 检查测试文件存在
- 验证测试覆盖率（目标>80%）

## 集成到CI/CD

在CI/CD流程中添加架构检查：

```yaml
# .github/workflows/architecture-check.yml
name: Architecture Guard

on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r shared-libs/requirements.txt
      - name: Run architecture guard
        run: |
          python scripts/architecture_guard.py --report --output report.json
      - name: Upload report
        uses: actions/upload-artifact@v2
        with:
          name: architecture-report
          path: report.json
```

## 配置

可以通过修改 `ArchitectureGuard` 类的配置来调整检查规则：

- `required_services`: 必需的服务列表
- `required_service_structure`: 服务结构要求
- `allowed_imports`: 允许的导入列表

## 退出代码

- `0`: 检查通过
- `1`: 检查失败（有错误）










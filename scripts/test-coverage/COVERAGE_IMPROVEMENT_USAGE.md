# 测试覆盖率提升使用指南

## 概述

本系统用于将所有服务的测试覆盖率提升到80%。所有操作使用命令直接执行，不使用PowerShell脚本。

## 快速开始

### 方法1：使用批处理文件（推荐）

```cmd
run-coverage-improvement.bat
```

### 方法2：直接运行Python脚本

```cmd
python scripts\test-coverage\coverage-improvement-main.py
```

### 方法3：处理单个服务

```cmd
python scripts\test-coverage\coverage-improvement-main.py --service database
```

### 方法4：跳过某些服务

```cmd
python scripts\test-coverage\coverage-improvement-main.py --skip shared_libs
```

## 前置要求

1. **SSH配置**：确保`remote.ssh`文件存在且配置正确
2. **服务器连接**：确保可以SSH连接到服务器
3. **Docker环境**：服务器上必须运行Docker容器
4. **Python环境**：本地需要Python 3.11+

## 工作流程

程序会按照以下顺序处理服务：

1. `database` - 基础模块
2. `shared_libs` - 共享库
3. `auth-service` - 认证服务
4. `mcp-gateway` - MCP网关
5. `workflow-engine` - 工作流引擎
6. `knowledge-base` - 知识库
7. `metadata-service` - 元数据服务

对每个服务，程序会：

1. **检查当前覆盖率**：在服务器Docker容器中运行测试，获取当前覆盖率
2. **分析缺失的测试**：如果覆盖率 < 80%，分析哪些代码缺少测试
3. **生成测试文件**：自动为缺失的代码生成测试模板
4. **上传文件**：将测试文件上传到服务器
5. **运行测试**：在服务器上运行测试
6. **修复bug**：如果测试失败，自动分析并尝试修复
7. **验证覆盖率**：检查是否达到80%目标
8. **循环**：如果未达标，重复步骤2-7

## 命令超时设置

所有命令都设置了10秒超时限制（测试命令为120秒），超时会自动重试最多3次。

## 输出文件

- `.coverage-reports/` - 各服务的覆盖率JSON报告
- `.coverage-improvement-results.json` - 处理结果汇总

## 工具脚本

### 1. parse-ssh-config.py

解析SSH配置文件，提取连接信息。

```cmd
python scripts\test-coverage\parse-ssh-config.py --host enterprise-ai-server
```

### 2. check-coverage.py

检查单个服务的测试覆盖率。

```cmd
python scripts\test-coverage\check-coverage.py database --target 80.0
```

### 3. upload-files.py

上传文件到服务器。

```cmd
python scripts\test-coverage\upload-files.py --file auth-service/tests/test_auth.py --remote /opt/enterprise-ai-platform/auth-service/tests/test_auth.py
```

### 4. run-service-test.py

在服务器Docker容器中运行测试。

```cmd
python scripts\test-coverage\run-service-test.py database --download .coverage-reports/database-coverage.json
```

### 5. improve-coverage.py

自动生成测试文件。

```cmd
python scripts\test-coverage\improve-coverage.py --service database
```

## 故障排查

### SSH连接失败

1. 检查`remote.ssh`文件是否存在
2. 验证SSH配置是否正确
3. 检查网络连接
4. 确认SSH密钥文件路径正确

### Docker容器不存在

1. 检查服务器上Docker容器是否运行
2. 确认容器名称是否正确（格式：`enterprise-ai-{service}`）
3. 运行`docker ps`查看容器状态

### 测试失败

1. 查看测试输出中的错误信息
2. 检查测试文件中的导入路径
3. 确认依赖是否正确安装
4. 查看`.coverage-improvement-results.json`了解详细错误

### 覆盖率不达标

1. 查看覆盖率报告，找出未覆盖的代码
2. 手动编写更完整的测试用例
3. 检查测试是否真的执行了所有代码路径

## 注意事项

1. **Windows兼容性**：所有命令都兼容Windows，不使用`&&`连接符
2. **超时限制**：所有命令都有10秒超时（测试为120秒），超时会自动重试
3. **文件同步**：确保本地和服务器文件同步
4. **迭代限制**：每个服务最多迭代10次，防止无限循环

## 示例输出

```
============================================================
处理服务: database (迭代 1)
============================================================

[步骤1] 检查当前覆盖率...
  当前覆盖率: 45.23%
  目标覆盖率: 80.00%
  是否达标: 否

[步骤3] 分析缺失的测试...
  发现 12 个文件覆盖率不足:
    - src/models/user.py: 32.45%
    - src/repositories/auth.py: 28.90%
    ...

[步骤4] 生成测试文件...
  ✓ 创建了 8 个测试文件

[步骤5] 上传文件到服务器...
  上传 8 个测试文件...
  ✓ 所有测试文件上传成功

[步骤1] 检查当前覆盖率...
  当前覆盖率: 78.56%
  目标覆盖率: 80.00%
  是否达标: 否

... (继续迭代直到达到80%)
```

## 联系支持

如有问题，请查看项目文档或联系开发团队。


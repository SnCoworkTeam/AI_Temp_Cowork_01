# 测试覆盖率80%自动化提升系统

## 概述

这是一个自动化系统，用于将所有服务的测试覆盖率提升到80%。系统通过SSH上传文件到服务器，在Docker容器中运行测试，自动修复bug并循环执行，直到达到目标覆盖率。

## 系统架构

### 核心组件

1. **parse-ssh-config.py** - SSH配置解析器
   - 解析 `remote.ssh` 配置文件
   - 提取连接信息（HostName, User, IdentityFile等）

2. **run-command-with-timeout.py** - 命令执行器
   - 执行Windows命令（git/ssh/scp等）
   - 所有命令默认10秒超时
   - 超时后自动重试（最多3次）

3. **upload-files.py** - 文件上传器
   - 使用scp命令上传文件到服务器
   - 连接限时10秒
   - 支持批量上传

4. **check-coverage.py** - 覆盖率检查器
   - 在Docker容器中运行测试
   - 下载覆盖率报告（JSON格式）
   - 判断是否达到80%目标

5. **improve-coverage.py** - 测试生成器（已增强）
   - 分析缺失的测试
   - 自动生成测试文件
   - 修复常见的测试错误

6. **coverage-improvement-main.py** - 主循环控制器
   - 按服务优先级逐个处理
   - 实现测试-修复-上传循环
   - 记录进度和状态

## 使用方法

### 前置要求

1. **SSH配置**：确保项目根目录下有 `remote.ssh` 文件
2. **服务器访问**：确保可以SSH连接到服务器
3. **Docker环境**：服务器上需要运行Docker容器

### 基本用法

#### 处理所有服务

```bash
python scripts/test-coverage/coverage-improvement-main.py
```

#### 处理单个服务

```bash
python scripts/test-coverage/coverage-improvement-main.py --service auth-service
```

#### 从上次中断的地方继续

```bash
python scripts/test-coverage/coverage-improvement-main.py --resume
```

### 高级选项

```bash
python scripts/test-coverage/coverage-improvement-main.py \
    --service auth-service \
    --target 80.0 \
    --max-iterations 20
```

参数说明：
- `--service`: 指定服务名称（如果不指定则处理所有服务）
- `--target`: 目标覆盖率（默认80%）
- `--max-iterations`: 每个服务的最大迭代次数（默认20）
- `--resume`: 从上次中断的地方继续

## 工作流程

对于每个服务，系统会执行以下循环：

1. **生成/修复测试文件**
   - 分析缺失的测试
   - 自动生成测试文件模板

2. **上传文件到服务器**
   - 使用scp命令上传测试文件
   - 连接限时10秒

3. **运行测试并检查覆盖率**
   - 在Docker容器中运行pytest
   - 生成覆盖率报告（JSON格式）
   - 下载覆盖率报告到本地

4. **检查是否达到目标**
   - 如果达到80%，标记为完成
   - 如果未达到，继续下一轮迭代

5. **修复测试错误**
   - 分析测试失败原因
   - 自动修复常见的错误（如导入错误）
   - 重新上传并测试

## 服务优先级

系统按以下优先级顺序处理服务：

1. `auth-service` (优先级1)
2. `knowledge-base` (优先级2)
3. `metadata-service` (优先级3)
4. `workflow-engine` (优先级4)
5. `mcp-gateway` (优先级5)
6. `database` (优先级6)

## 进度跟踪

系统会在项目根目录创建以下文件：

- `.coverage-progress.json` - 进度记录文件
- `coverage-improvement.log` - 执行日志
- `.coverage-reports/` - 覆盖率报告目录

### 进度文件格式

```json
{
  "services": {
    "auth-service": {
      "service": "auth-service",
      "status": "SUCCESS",
      "coverage": 82.5,
      "target": 80.0,
      "meets_target": true,
      "iteration": 3
    }
  },
  "started_at": "2024-01-20T10:00:00",
  "last_updated": "2024-01-20T10:30:00"
}
```

## 独立组件使用

### 解析SSH配置

```bash
python scripts/test-coverage/parse-ssh-config.py
python scripts/test-coverage/parse-ssh-config.py --host enterprise-ai-server
python scripts/test-coverage/parse-ssh-config.py --all
```

### 执行命令（带超时）

```bash
python scripts/test-coverage/run-command-with-timeout.py "git status" --timeout 10
```

### 上传文件

```bash
python scripts/test-coverage/upload-files.py --file auth-service/tests/test_auth.py --remote /opt/enterprise-ai-platform/auth-service/tests/
python scripts/test-coverage/upload-files.py --service auth-service --files tests/test_auth.py tests/test_user.py
```

### 检查覆盖率

```bash
python scripts/test-coverage/check-coverage.py auth-service --target 80.0
```

### 生成测试文件

```bash
python scripts/test-coverage/improve-coverage.py --service auth-service
python scripts/test-coverage/improve-coverage.py --all
```

## 关键特性

1. **不使用PowerShell脚本**：所有逻辑用Python实现
2. **所有命令10秒超时**：通过 `run-command-with-timeout.py` 实现
3. **SSH连接限时10秒**：使用 `-o ConnectTimeout=10`
4. **Windows不支持&&**：使用Python的流程控制
5. **循环执行**：直到所有服务达到80%覆盖率
6. **断点续传**：支持从上次中断的地方继续

## 故障排查

### SSH连接失败

- 检查 `remote.ssh` 文件是否存在
- 验证SSH密钥文件路径是否正确
- 确认服务器地址和端口

### 文件上传失败

- 检查文件路径是否正确
- 确认服务器目录权限
- 验证网络连接

### 测试运行失败

- 检查Docker容器是否运行
- 确认容器名称是否正确
- 查看测试输出日志

### 覆盖率不提升

- 检查是否生成了新的测试文件
- 确认测试文件是否正确上传
- 查看覆盖率报告详情

## 日志和报告

- **执行日志**：`coverage-improvement.log`
- **覆盖率报告**：`.coverage-reports/{service-name}-coverage.json`
- **进度文件**：`.coverage-progress.json`

## 注意事项

1. 系统会自动重试失败的命令（最多3次）
2. 每个服务的最大迭代次数为20次（可通过参数调整）
3. 如果覆盖率连续3次没有提升，系统会停止迭代
4. 所有命令都有10秒超时限制（测试命令除外，为120秒）

## 示例输出

```
[2024-01-20 10:00:00] [INFO] 开始处理服务: auth-service
[2024-01-20 10:00:01] [INFO]   [auth-service] 迭代 1/20
[2024-01-20 10:00:02] [INFO]   [auth-service] 生成测试文件...
[2024-01-20 10:00:05] [INFO]   [auth-service] 创建了 5 个测试文件
[2024-01-20 10:00:06] [INFO]   [auth-service] 上传文件到服务器...
[2024-01-20 10:00:10] [INFO]   [auth-service] 上传成功: 5 个文件
[2024-01-20 10:00:11] [INFO]   [auth-service] 运行测试并检查覆盖率...
[2024-01-20 10:01:30] [INFO]   [auth-service] 当前覆盖率: 65.50% (目标: 80.00%)
[2024-01-20 10:01:31] [INFO]   [auth-service] 迭代 2/20
...
[2024-01-20 10:15:00] [INFO]   [auth-service] ✓ 达到目标覆盖率！
```

## 联系和支持

如有问题，请查看日志文件或联系开发团队。


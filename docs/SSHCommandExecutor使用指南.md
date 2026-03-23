# SSHCommandExecutor 使用指南

## 📦 安装依赖

```bash
pip install -r tools/requirements.txt
```

或者直接安装：

```bash
pip install paramiko>=2.12.0
```

## 🚀 快速开始

### 1. 基础使用

```python
from tools.ssh_executor import SSHCommandExecutor

# 初始化执行器
executor = SSHCommandExecutor(
    host="43.143.139.197",
    username="ubuntu",
    private_key_path="enterprise_ai_platform.pem",
    base_workdir="/opt/enterprise-ai-platform"
)

# 连接并执行命令
executor.connect()
result = executor.execute("ls -la")

print(f"退出码: {result.exit_code}")
print(f"输出: {result.stdout}")

# 关闭连接
executor.close()
```

### 2. 使用上下文管理器（推荐）

```python
with SSHCommandExecutor(
    host="43.143.139.197",
    username="ubuntu",
    private_key_path="enterprise_ai_platform.pem"
) as executor:
    result = executor.execute("docker compose ps")
    print(result.stdout)
    # 自动关闭连接
```

### 3. 执行命令序列

```python
executor = SSHCommandExecutor(...)

commands = [
    "cd /opt/enterprise-ai-platform",
    "git pull origin main",
    "docker compose restart web-ui"
]

results = executor.execute_sequence(commands, stop_on_failure=True)

for result in results:
    print(f"{'✓' if result.success else '✗'} {result.command}")
```

### 4. 流式输出（实时显示）

```python
def print_line(line: str):
    print(f"  {line}")

result = executor.execute_streaming(
    "docker compose logs -f web-ui",
    callback=print_line
)
```

### 5. 文件传输

```python
# 上传文件
executor.upload_file("local_file.txt", "remote_file.txt")

# 下载文件
executor.download_file("remote_file.txt", "local_downloaded.txt")
```

### 6. 使用部署执行器

```python
from tools.ssh_executor import DeploymentExecutor

executor = DeploymentExecutor(
    host="43.143.139.197",
    username="ubuntu",
    private_key_path="enterprise_ai_platform.pem"
)

# 部署项目
results = executor.deploy_project("project-id", branch="main")

# 运行数据库迁移
result = executor.run_migration()

# 重启服务
result = executor.restart_service("web-ui")

# 查看日志
result = executor.view_logs("web-ui", lines=50)

# 检查服务状态
result = executor.check_service_status()
```

## 🔧 配置选项

### SSHCommandExecutor 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `host` | str | 是 | - | 服务器地址 |
| `username` | str | 是 | - | SSH用户名 |
| `private_key_path` | str | 否 | None | 私钥文件路径（优先使用） |
| `password` | str | 否 | None | 密码（私钥不存在时使用） |
| `port` | int | 否 | 22 | SSH端口 |
| `base_workdir` | str | 否 | "/opt/enterprise-ai-platform" | 基础工作目录 |
| `connection_timeout` | int | 否 | 30 | 连接超时时间（秒） |

### 认证方式

**方式1: 使用私钥（推荐）**
```python
executor = SSHCommandExecutor(
    host="server.com",
    username="user",
    private_key_path="/path/to/private_key.pem"
)
```

**方式2: 使用密码**
```python
executor = SSHCommandExecutor(
    host="server.com",
    username="user",
    password="your_password"
)
```

## 📊 CommandResult 结构

执行命令后返回的 `CommandResult` 对象包含以下字段：

```python
@dataclass
class CommandResult:
    command: str          # 原始命令
    safe_command: str     # 处理后的命令
    exit_code: int        # 退出码（0表示成功）
    stdout: str          # 标准输出
    stderr: str          # 标准错误
    success: bool        # 是否成功（exit_code == 0）
    timestamp: str       # 执行时间戳（ISO格式）
    duration: float      # 执行耗时（秒）
```

## 💡 使用场景

### 场景1: 自动化部署

```python
class AutoDeployer:
    def __init__(self, config):
        self.executor = DeploymentExecutor(**config)

    def deploy(self, project_id: str):
        # 1. 拉取代码
        result = self.executor.execute("git pull origin main", project_id)
        if not result.success:
            return {"success": False, "error": "拉取代码失败"}

        # 2. 重启服务
        result = self.executor.restart_service("web-ui", project_id)
        if not result.success:
            return {"success": False, "error": "重启服务失败"}

        # 3. 检查状态
        result = self.executor.check_service_status(project_id)
        return {"success": True, "status": result.stdout}
```

### 场景2: 智能体集成

```python
class DevelopmentAgent:
    def __init__(self, server_config):
        self.executor = SSHCommandExecutor(**server_config)

    def implement_feature(self, task: str, project_id: str):
        # 调用LLM生成命令序列
        commands = self._generate_commands(task, project_id)

        # 执行命令
        results = self.executor.execute_sequence(commands, project_id)

        # 返回结果
        return {
            "success": all(r.success for r in results),
            "results": [asdict(r) for r in results]
        }
```

### 场景3: 批量操作

```python
def batch_deploy(projects: List[str], config: Dict):
    executor = DeploymentExecutor(**config)

    for project_id in projects:
        print(f"部署项目: {project_id}")
        results = executor.deploy_project(project_id)

        success = all(r.success for r in results)
        print(f"  {'✓ 成功' if success else '✗ 失败'}")
```

## ⚠️ 注意事项

1. **连接管理**: 使用完毕后记得调用 `close()` 或使用上下文管理器
2. **超时设置**: 长时间运行的命令需要设置合适的 `timeout` 参数
3. **错误处理**: 建议使用 try-except 捕获异常
4. **文件路径**: 确保本地文件路径和远程文件路径正确
5. **权限问题**: 确保SSH用户有足够的权限执行命令

## 🔍 故障排查

### 问题1: 连接失败

```python
try:
    executor.connect()
except Exception as e:
    print(f"连接失败: {e}")
    # 检查:
    # 1. 服务器地址和端口是否正确
    # 2. 私钥文件路径是否正确
    # 3. 网络连接是否正常
    # 4. SSH服务是否运行
```

### 问题2: 命令执行超时

```python
# 增加超时时间
result = executor.execute("long_running_command", timeout=300)
```

### 问题3: 文件传输失败

```python
# 检查文件路径和权限
if os.path.exists(local_file):
    success = executor.upload_file(local_file, remote_file)
    if not success:
        print("上传失败，检查远程目录权限")
```

## 📝 完整示例

查看 `tools/ssh_executor_example.py` 获取更多使用示例。

运行示例：

```bash
python tools/ssh_executor_example.py
```

## 🔗 相关文档

- [SSHCommandExecutor可行性分析报告](./SSHCommandExecutor可行性分析报告.md)
- [Paramiko官方文档](https://www.paramiko.org/)


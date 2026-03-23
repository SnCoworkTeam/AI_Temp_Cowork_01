# Bug监控和自动修复系统

## 🎯 功能

这个系统可以：
1. **自动监控**测试服务器的测试报告
2. **智能识别**常见bug模式（模块缺失、导入错误、数据库连接等）
3. **自动修复**部分安全的问题（如添加缺失的依赖）
4. **生成修复报告**，提供详细的修复建议
5. **及时通知**发现的问题

## 🚀 快速开始

### 方式1: Python脚本（推荐，可在虚拟环境中运行）

```bash
# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\Activate.ps1  # Windows

# 运行一次监控（不自动修复）
python scripts/test/monitor-and-fix.py --once

# 运行一次监控（启用自动修复）
python scripts/test/monitor-and-fix.py --once --auto-fix

# 持续监控（每30分钟）
python scripts/test/monitor-and-fix.py --interval 30

# 持续监控并自动修复
python scripts/test/monitor-and-fix.py --interval 30 --auto-fix
```

### 方式2: PowerShell脚本（Windows）

```powershell
# 运行一次监控
.\scripts\test\monitor-and-fix.ps1 -RunOnce

# 运行一次监控（启用自动修复）
.\scripts\test\monitor-and-fix.ps1 -RunOnce -AutoFix

# 持续监控
.\scripts\test\monitor-and-fix.ps1 -IntervalMinutes 30 -AutoFix
```

## 🔍 支持的Bug类型

### 1. 模块缺失 (MissingModule) - 可自动修复
- **检测**: `ModuleNotFoundError: No module named 'xxx'`
- **自动修复**: 在requirements.txt中添加缺失的模块
- **示例**: 发现缺少`pytest-asyncio`，自动添加到requirements.txt

### 2. 导入错误 (ImportError) - 需手动修复
- **检测**: `ImportError: cannot import name 'xxx'`
- **修复建议**: 检查导入路径和模块结构

### 3. 数据库连接错误 (DatabaseConnection) - 需手动修复
- **检测**: 连接被拒绝、数据库不存在、认证失败
- **修复建议**: 检查数据库服务状态和配置

### 4. 文件不存在 (FileNotFound) - 需手动修复
- **检测**: `FileNotFoundError`、`No such file or directory`
- **修复建议**: 检查文件路径，确保文件已同步

### 5. 断言失败 (AssertionFailure) - 需手动修复
- **检测**: `AssertionError`
- **修复建议**: 检查测试逻辑和业务逻辑

### 6. 超时 (Timeout) - 需手动修复
- **检测**: `timeout`、`timed out`
- **修复建议**: 优化性能或增加超时时间

## 📊 修复报告

每次检测到问题后，会在 `fix-reports/` 目录生成详细的修复报告：

```
fix-reports/
└── fix-report-20231203-143022.md
```

报告包含：
- 失败统计
- 问题详情（按严重程度分类）
- 修复建议
- 自动修复操作记录
- 下一步操作指南

## ⚙️ 配置

### 环境变量

可以在脚本中修改以下配置：

```python
SERVER_IP = "43.143.139.197"
SERVER_USER = "ubuntu"
KEY_PATH = "enterprise_ai_platform.pem"
REMOTE_PATH = "/opt/enterprise-ai-platform"
INTERVAL_MINUTES = 30
```

### 自动修复策略

**安全修复**（默认启用）:
- ✅ 添加缺失的Python模块到requirements.txt

**需要谨慎的修复**（默认禁用）:
- ⚠️ 修改代码文件
- ⚠️ 修改配置文件
- ⚠️ 重启服务

## 📋 工作流程

```
1. 定时从服务器拉取测试报告
   ↓
2. 分析失败的测试用例
   ↓
3. 识别问题类型和严重程度
   ↓
4. 尝试自动修复（如果启用）
   ↓
5. 生成修复报告
   ↓
6. 发送通知（如果有配置）
   ↓
7. 等待下次检查
```

## 🔔 通知集成（可选）

可以在脚本中添加通知功能：

### 邮件通知

```python
import smtplib
from email.mime.text import MIMEText

def send_email(subject, body):
    # 配置SMTP
    # ...
```

### Slack/Teams Webhook

```python
import requests

def send_webhook(message):
    webhook_url = "https://your-webhook-url"
    requests.post(webhook_url, json={"text": message})
```

## 🛠️ 设置定时任务

### Windows（任务计划程序）

```powershell
# 使用setup-monitor-task.ps1
.\scripts\test\setup-monitor-task.ps1
```

### Linux/Mac（cron）

```bash
# 编辑crontab
crontab -e

# 添加（每30分钟运行一次）
*/30 * * * * cd /path/to/project && /path/to/venv/bin/python scripts/test/monitor-and-fix.py --once --auto-fix >> /tmp/bug-monitor.log 2>&1
```

## 📈 最佳实践

1. **开发阶段**: 使用 `--once` 手动触发，不启用自动修复
2. **CI/CD阶段**: 设置定时任务，启用自动修复
3. **重要发布前**: 手动运行并检查所有报告
4. **问题排查**: 查看 `fix-reports/` 目录下的详细报告

## ⚠️ 注意事项

1. **自动修复谨慎使用**: 只对安全的操作启用自动修复
2. **定期检查报告**: 即使启用了自动修复，也要定期检查报告
3. **代码审查**: 自动修复的更改需要代码审查
4. **备份**: 重要操作前建议备份

## 🎯 示例场景

### 场景1: 发现缺失模块

```
[2023-12-03 14:30:22] 开始检查...
=== 从服务器拉取测试报告 ===
✅ 测试报告已拉取
=== 分析测试失败 ===
❌ 发现 3 个失败的测试
=== 问题摘要 ===
  MissingModule: 2 个
  ImportError: 1 个

=== 尝试自动修复 ===
修复: 添加缺失模块 pytest-asyncio
修复: 添加缺失模块 httpx
✅ 已修复 2 个问题
  - 在 requirements.txt 中添加了 pytest-asyncio
  - 在 requirements.txt 中添加了 httpx

📄 修复报告已生成: fix-reports/fix-report-20231203-143022.md
```

### 场景2: 数据库连接问题

```
❌ 发现 5 个失败的测试
=== 问题摘要 ===
  DatabaseConnection: 3 个
  AssertionFailure: 2 个

🔴 严重问题: 3
🟠 高优先级: 0

📋 请查看修复报告: fix-reports/fix-report-20231203-143022.md
```

## ✅ 总结

Bug监控和修复系统提供了：

- ✅ **自动化监控**: 定时检查测试状态
- ✅ **智能识别**: 自动识别常见问题类型
- ✅ **自动修复**: 安全地修复部分问题
- ✅ **详细报告**: 完整的修复建议和操作记录
- ✅ **及时通知**: 发现问题立即通知

**开始使用**: `python scripts/test/monitor-and-fix.py --once`


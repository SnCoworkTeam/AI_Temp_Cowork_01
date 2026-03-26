# 测试报告监控使用指南

## 📋 概述

测试报告监控系统可以定时从测试服务器拉取测试报告，分析结果，并在发现问题时及时通知。

## 🚀 快速开始

### 方式1: PowerShell脚本（Windows）

#### 手动运行

```powershell
# 运行一次
.\scripts\test\monitor-test-reports.ps1 -RunOnce

# 持续监控（每30分钟检查一次）
.\scripts\test\monitor-test-reports.ps1 -IntervalMinutes 30

# 检查前先运行测试
.\scripts\test\monitor-test-reports.ps1 -RunTests -IntervalMinutes 30
```

#### 设置Windows定时任务

```powershell
# 以管理员身份运行PowerShell，执行：
.\scripts\test\setup-monitor-task.ps1
```

这将创建一个Windows定时任务，自动在后台运行监控。

### 方式2: Python脚本（跨平台，推荐在虚拟环境中使用）

#### 安装依赖

```bash
# 在虚拟环境中
pip install -r requirements.txt  # 如果还没有安装
```

#### 运行监控

```bash
# 运行一次
python scripts/test/monitor-test-reports.py --once

# 持续监控（每30分钟检查一次）
python scripts/test/monitor-test-reports.py --interval 30

# 检查前先运行测试
python scripts/test/monitor-test-reports.py --run-tests --interval 30
```

#### 设置Linux/Mac定时任务（cron）

```bash
# 编辑crontab
crontab -e

# 添加以下行（每30分钟运行一次）
*/30 * * * * cd /path/to/enterprise-ai-platform && /path/to/venv/bin/python scripts/test/monitor-test-reports.py --once
```

## 📊 报告位置

监控脚本会将测试报告拉取到本地：

```
test-reports-local/
├── test-results/          # 测试结果XML和日志
├── coverage-report/        # 代码覆盖率报告
├── test-report.md         # 服务器生成的报告
└── test-report-*.md       # 本地生成的监控报告
```

## 🔍 查看报告

### 方式1: 使用查看脚本

```bash
# 在服务器上
bash scripts/test/view-test-report.sh

# 或指定功能
bash scripts/test/view-test-report.sh latest    # 查看最新报告
bash scripts/test/view-test-report.sh stats    # 查看统计
bash scripts/test/view-test-report.sh logs     # 查看日志
bash scripts/test/view-test-report.sh coverage  # 查看覆盖率
```

### 方式2: 直接查看文件

- **HTML覆盖率报告**: 打开 `test-reports-local/coverage-report/` 目录下的HTML文件
- **测试日志**: 查看 `test-reports-local/test-results/*-output.log`
- **测试报告**: 查看 `test-reports-local/test-report-*.md`

## ⚙️ 配置选项

### PowerShell脚本参数

- `-ServerIP`: 服务器IP（默认: 43.143.139.197）
- `-ServerUser`: 服务器用户（默认: ubuntu）
- `-KeyPath`: SSH密钥路径（默认: enterprise_ai_platform.pem）
- `-RemotePath`: 服务器项目路径（默认: /opt/enterprise-ai-platform）
- `-IntervalMinutes`: 检查间隔（默认: 30分钟）
- `-RunOnce`: 只运行一次，不循环
- `-RunTests`: 在检查前先运行测试

### Python脚本参数

- `--once`: 只运行一次，不循环
- `--run-tests`: 在检查前先运行测试
- `--interval`: 检查间隔（分钟，默认30）

## 🔔 通知设置（可选）

可以在脚本中添加通知功能：

### 邮件通知

在Python脚本中添加：

```python
import smtplib
from email.mime.text import MIMEText

def send_email_notification(subject, body):
    # 配置SMTP服务器
    smtp_server = "smtp.example.com"
    smtp_port = 587
    sender = "your-email@example.com"
    receiver = "your-email@example.com"
    password = "your-password"
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver
    
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
```

### Webhook通知

```python
import requests

def send_webhook_notification(message):
    webhook_url = "https://your-webhook-url"
    requests.post(webhook_url, json={"text": message})
```

## 📈 最佳实践

1. **开发环境**: 使用 `--once` 模式，手动触发
2. **持续集成**: 设置定时任务，每30分钟检查一次
3. **重要发布前**: 使用 `--run-tests` 确保测试通过
4. **问题排查**: 查看 `test-reports-local/test-results/` 下的详细日志

## 🛠️ 故障排查

### 问题: 无法连接到服务器

- 检查SSH密钥路径是否正确
- 确认服务器IP和用户正确
- 测试SSH连接: `ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197`

### 问题: 拉取报告失败

- 确认服务器上测试已运行
- 检查服务器上的 `test-results` 目录是否存在
- 查看脚本输出的错误信息

### 问题: 定时任务不运行

- Windows: 检查任务计划程序，确认任务已启用
- Linux/Mac: 检查cron服务是否运行: `systemctl status cron`

## 📝 示例工作流

### 日常开发

```bash
# 1. 在本地开发
# 2. 提交代码
# 3. 代码自动同步到服务器（通过watch-and-sync）
# 4. 监控脚本自动检测并运行测试
# 5. 收到测试结果通知
```

### 发布前检查

```bash
# 手动运行完整测试
python scripts/test/monitor-test-reports.py --run-tests --once

# 查看报告
bash scripts/test/view-test-report.sh all
```

## 🎯 总结

测试报告监控系统提供了：

- ✅ **自动化监控**: 定时检查测试状态
- ✅ **及时通知**: 发现问题立即通知
- ✅ **详细报告**: 完整的测试结果和覆盖率
- ✅ **易于集成**: 支持Windows定时任务和Linux cron
- ✅ **灵活配置**: 多种运行模式和参数

**开始使用**: 运行 `python scripts/test/monitor-test-reports.py --once` 进行首次测试！


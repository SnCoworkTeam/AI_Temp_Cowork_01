# 测试报告监控 - 快速开始

## 🎯 目标

在本地虚拟环境中定时监控测试服务器的测试报告，及时发现问题并修复。

## 🚀 快速开始（3步）

### 步骤1: 激活虚拟环境并安装依赖

```bash
# 激活虚拟环境（根据你的环境调整）
# Windows
.\venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate

# 确保已安装依赖（pytest等已在requirements.txt中）
pip install -r requirements.txt
```

### 步骤2: 运行监控脚本（测试一次）

```bash
# 在虚拟环境中运行
python scripts/test/monitor-test-reports.py --once
```

这将：
1. 从服务器拉取最新的测试报告
2. 分析测试结果
3. 在本地生成报告到 `test-reports-local/` 目录

### 步骤3: 设置定时任务

#### Windows（PowerShell）

```powershell
# 以管理员身份运行
.\scripts\test\setup-monitor-task.ps1
```

#### Linux/Mac（cron）

```bash
# 编辑crontab
crontab -e

# 添加以下行（每30分钟运行一次）
*/30 * * * * cd /path/to/enterprise-ai-platform && /path/to/venv/bin/python scripts/test/monitor-test-reports.py --once >> /tmp/test-monitor.log 2>&1
```

## 📊 查看报告

### 方式1: 查看本地报告

```bash
# 查看最新报告
cat test-reports-local/test-report-*.md | tail -1

# 查看HTML覆盖率报告
# Windows
start test-reports-local/coverage-report/index.html

# Linux/Mac
open test-reports-local/coverage-report/index.html
```

### 方式2: 在服务器上查看

```bash
# SSH到服务器
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197

# 运行查看脚本
cd /opt/enterprise-ai-platform
bash scripts/test/view-test-report.sh
```

## 🔔 收到失败通知后

1. **查看详细日志**: `test-reports-local/test-results/*-output.log`
2. **分析失败原因**: 查看JUnit XML报告中的错误信息
3. **修复问题**: 在本地修复代码
4. **同步到服务器**: 使用 `watch-and-sync.ps1` 或手动同步
5. **重新运行测试**: 等待下次监控或手动运行

## ⚙️ 常用命令

```bash
# 只运行一次监控
python scripts/test/monitor-test-reports.py --once

# 监控并自动运行测试
python scripts/test/monitor-test-reports.py --run-tests --once

# 持续监控（每30分钟）
python scripts/test/monitor-test-reports.py --interval 30

# 自定义间隔（每15分钟）
python scripts/test/monitor-test-reports.py --interval 15
```

## 📁 报告文件位置

- **本地报告**: `test-reports-local/`
- **服务器报告**: `/opt/enterprise-ai-platform/test-results/`
- **覆盖率报告**: `test-reports-local/coverage-report/`

## ✅ 完成！

现在你的测试报告监控系统已经设置完成。定时任务会自动检查测试状态，你只需要：

1. **等待通知** - 定时任务会自动运行
2. **查看报告** - 定期检查 `test-reports-local/` 目录
3. **修复问题** - 根据报告中的失败信息修复代码

**建议**: 首次运行后，检查 `test-reports-local/` 目录确认报告已正确拉取。


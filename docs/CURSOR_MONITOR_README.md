# Cursor任务监控系统

## 概述

这个系统自动监控Cursor的任务执行状态，如果检测到任务卡住（超过5分钟无活动），会自动发送继续执行指令，确保测试覆盖率提升计划能够持续执行直到完成。

## 功能特性

- ✅ 自动检测Cursor任务是否卡住
- ✅ 超时自动发送继续执行指令
- ✅ 支持Windows定时任务自动运行
- ✅ 记录活动日志
- ✅ 创建指令文件供手动使用

## 快速开始

### 方法1: 直接运行（推荐用于测试）

```powershell
# 启动监控（持续运行）
.\start-cursor-monitor.ps1

# 或者使用批处理文件
.\start-cursor-monitor.bat
```

### 方法2: 安装Windows定时任务（推荐用于生产）

```powershell
# 安装定时任务（每5分钟自动检查一次）
.\start-cursor-monitor.ps1 -InstallTask

# 或者直接运行安装脚本
.\scripts\test-coverage\install-cursor-monitor.ps1 -Install
```

### 方法3: 手动运行Python脚本

```bash
# 持续监控模式
python scripts/test-coverage/cursor-monitor.py

# 单次检查模式
python scripts/test-coverage/cursor-monitor.py --once

# 自定义参数
python scripts/test-coverage/cursor-monitor.py --interval 30 --timeout 300
```

## 参数说明

- `--interval`: 检查间隔（秒），默认30秒
- `--timeout`: 超时阈值（秒），默认300秒（5分钟）
- `--once`: 只检查一次然后退出

## 工作原理

1. **监控循环**: 每30秒检查一次任务状态
2. **超时检测**: 如果超过5分钟没有活动，认为任务卡住
3. **自动恢复**: 检测到卡住时，自动发送继续执行指令
4. **指令文件**: 创建 `continue-coverage-improvement.txt` 文件
5. **活动日志**: 记录所有活动到 `.cursor-activity.log`

## 输出文件

### 1. continue-coverage-improvement.txt
包含继续执行的指令文本，可以直接复制到Cursor对话框。

**内容示例：**
```
继续执行测试覆盖率提升计划，为所有未达到80%覆盖率的服务添加测试，直到所有服务都达到80%覆盖率。
```

### 2. .cursor-activity.log
记录所有监控活动的日志文件。

**格式：**
```
[2024-01-01 12:00:00] 监控循环启动
[2024-01-01 12:05:00] 检测到任务可能卡住，发送继续执行指令
[2024-01-01 12:05:01] 已创建继续执行指令文件
```

### 3. .cursor-continue-requested
标记文件，表示已请求继续执行。

## 安装Windows定时任务

### 安装

```powershell
# 以管理员身份运行PowerShell
.\scripts\test-coverage\install-cursor-monitor.ps1 -Install
```

### 查看状态

```powershell
.\scripts\test-coverage\install-cursor-monitor.ps1 -Status
```

### 卸载

```powershell
.\scripts\test-coverage\install-cursor-monitor.ps1 -Uninstall
```

## 使用场景

### 场景1: 持续监控

当你在Cursor中执行测试覆盖率提升任务时，启动监控脚本：

```powershell
# 在另一个终端窗口运行
.\start-cursor-monitor.ps1
```

如果Cursor卡住超过5分钟，监控脚本会自动发送继续执行指令。

### 场景2: 定时检查

安装Windows定时任务后，系统会每5分钟自动检查一次，无需手动启动。

### 场景3: 手动触发

如果发现任务卡住，可以手动运行单次检查：

```bash
python scripts/test-coverage/cursor-monitor.py --once
```

## 依赖要求

### Python包

```bash
# 基础功能（必需）
# 无需额外包，使用标准库

# 可选：自动发送指令到Cursor窗口
pip install pyautogui
```

### 系统要求

- Windows 10/11
- Python 3.7+
- PowerShell 5.1+（用于定时任务）

## 故障排除

### 问题1: Python未找到

**错误信息：**
```
错误: 未找到Python，请先安装Python
```

**解决方法：**
1. 安装Python 3.7或更高版本
2. 确保Python已添加到系统PATH
3. 验证：运行 `python --version`

### 问题2: 权限不足

**错误信息：**
```
错误: 安装任务失败: 拒绝访问
```

**解决方法：**
1. 以管理员身份运行PowerShell
2. 右键点击PowerShell，选择"以管理员身份运行"

### 问题3: pyautogui发送失败

**现象：**
监控脚本运行，但无法自动发送指令到Cursor窗口。

**解决方法：**
1. 这是正常的，脚本会使用文件方式作为备选
2. 检查 `continue-coverage-improvement.txt` 文件
3. 手动复制文件内容到Cursor对话框

### 问题4: 定时任务未执行

**解决方法：**
1. 打开"任务计划程序"
2. 查找任务 "EnterpriseAI-CursorMonitor"
3. 检查任务状态和上次运行结果
4. 手动运行一次任务测试

## 高级配置

### 修改检查间隔

编辑 `cursor-monitor.py` 或使用参数：

```bash
python scripts/test-coverage/cursor-monitor.py --interval 60 --timeout 600
```

### 修改超时阈值

```bash
# 10分钟超时
python scripts/test-coverage/cursor-monitor.py --timeout 600
```

### 自定义指令内容

编辑 `cursor-monitor.py` 中的 `send_continue_instruction()` 方法。

## 与测试覆盖率系统集成

这个监控系统与测试覆盖率提升系统配合使用：

1. **覆盖率监控** (`coverage-monitor.ps1`): 检查覆盖率状态
2. **Cursor监控** (`cursor-monitor.py`): 检测Cursor是否卡住
3. **自动提升** (`improve-coverage.py`): 生成测试文件

三个系统协同工作，确保任务持续执行直到完成。

## 注意事项

1. ⚠️ 监控脚本会持续运行，占用少量系统资源
2. ⚠️ 如果Cursor窗口不在前台，pyautogui可能无法发送指令
3. ⚠️ 建议在测试环境中先验证功能
4. ✅ 即使pyautogui失败，文件方式仍然可用

## 相关文件

- `scripts/test-coverage/cursor-monitor.py` - 主监控脚本
- `scripts/test-coverage/install-cursor-monitor.ps1` - 定时任务安装脚本
- `start-cursor-monitor.ps1` - 快速启动脚本
- `start-cursor-monitor.bat` - 批处理启动脚本


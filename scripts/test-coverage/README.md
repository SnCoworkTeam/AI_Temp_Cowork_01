# 测试覆盖率自动提升系统

## 概述

这个系统自动监控各服务的测试覆盖率，并在检测到停止时自动继续执行测试覆盖率提升计划，直到所有服务达到80%覆盖率。

## 组件

### 1. check-coverage-status.py
检查所有服务的当前测试覆盖率状态。

**用法：**
```bash
python scripts/test-coverage/check-coverage-status.py
```

**输出：** JSON格式的覆盖率报告

### 2. improve-coverage.py
自动分析缺失的测试并生成测试文件模板。

**用法：**
```bash
# 为所有服务提升覆盖率
python scripts/test-coverage/improve-coverage.py --all

# 为特定服务提升覆盖率
python scripts/test-coverage/improve-coverage.py --service auth-service
```

### 3. auto-continue-coverage.ps1
自动监控脚本，检测到停止时自动发送继续执行指令。

**用法：**
```powershell
.\scripts\test-coverage\auto-continue-coverage.ps1
```

**功能：**
- 每5分钟检查一次覆盖率状态
- 检测到未达到80%时，检查是否有正在运行的进程
- 如果没有运行，自动发送继续执行指令

### 4. coverage-monitor.ps1
完整的监控脚本，包含日志记录和进程管理。

**用法：**
```powershell
.\scripts\test-coverage\coverage-monitor.ps1

# 单次运行
.\scripts\test-coverage\coverage-monitor.ps1 -RunOnce
```

### 5. start-coverage-monitor.ps1
安装和管理Windows定时任务。

**用法：**
```powershell
# 安装定时任务（每5分钟执行一次）
.\scripts\test-coverage\start-coverage-monitor.ps1 -Install

# 启动监控
.\scripts\test-coverage\start-coverage-monitor.ps1 -Start

# 卸载定时任务
.\scripts\test-coverage\start-coverage-monitor.ps1 -Uninstall
```

## 工作流程

1. **监控循环**：每5分钟检查一次覆盖率状态
2. **状态检查**：运行 `check-coverage-status.py` 获取当前覆盖率
3. **判断条件**：
   - 如果所有服务都达到80%：任务完成，退出
   - 如果有服务未达到80%：继续下一步
4. **进程检查**：检查是否有正在运行的覆盖率提升进程
5. **自动恢复**：如果没有运行，发送继续执行指令
6. **执行提升**：运行 `improve-coverage.py` 生成测试文件

## 继续执行指令

当检测到停止时，系统会创建以下文件：

- `continue-coverage-improvement.txt` - 包含继续执行的指令文本
- `.coverage-improvement-active` - 标记文件，表示任务处于活动状态

**指令内容：**
```
继续执行测试覆盖率提升计划，为所有未达到80%覆盖率的服务添加测试，直到所有服务都达到80%覆盖率。
```

这个指令可以直接作为对话框输入，让AI agent继续执行。

## 安装和使用

### 快速开始

1. **安装定时任务**（推荐）：
```powershell
cd E:\enterprise-ai-platform
.\scripts\test-coverage\start-coverage-monitor.ps1 -Install
.\scripts\test-coverage\start-coverage-monitor.ps1 -Start
```

2. **手动运行监控**：
```powershell
.\scripts\test-coverage\auto-continue-coverage.ps1
```

3. **检查状态**：
```bash
python scripts/test-coverage/check-coverage-status.py
```

### 在Cursor中使用

当监控脚本检测到停止时，会输出继续执行的指令。你可以：

1. 复制指令内容
2. 在Cursor对话框中粘贴
3. AI agent会自动继续执行测试覆盖率提升

或者，监控脚本会自动创建 `continue-coverage-improvement.txt` 文件，你可以读取该文件内容并发送给AI。

## 日志

监控脚本会生成日志文件：
- `coverage-monitor.log` - 详细的监控日志

## 注意事项

1. 确保Python环境已配置
2. 确保有权限创建Windows定时任务（需要管理员权限）
3. 监控脚本会持续运行，直到所有服务达到80%覆盖率
4. 可以通过 `Ctrl+C` 手动停止监控

## 故障排除

### 问题：Python命令未找到
**解决：** 确保Python已添加到PATH，或使用完整路径

### 问题：权限不足
**解决：** 以管理员身份运行PowerShell

### 问题：定时任务未执行
**解决：** 
1. 检查任务计划程序中的任务状态
2. 手动运行一次测试脚本
3. 检查日志文件

### 问题：覆盖率检查失败
**解决：**
1. 确保pytest和pytest-cov已安装
2. 检查各服务的测试目录是否存在
3. 查看错误日志


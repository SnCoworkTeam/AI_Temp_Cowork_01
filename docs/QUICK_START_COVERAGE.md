# 测试覆盖率自动提升 - 快速开始指南

## 🚀 快速启动

### 步骤1: 启动Cursor监控（检测卡住并自动恢复）

```powershell
# 方法1: 使用PowerShell脚本（推荐）
.\start-cursor-monitor.ps1

# 方法2: 使用批处理文件
.\start-cursor-monitor.bat

# 方法3: 安装Windows定时任务（自动运行）
.\start-cursor-monitor.ps1 -InstallTask
```

### 步骤2: 在Cursor中执行测试覆盖率提升

在Cursor对话框中输入：
```
继续执行测试覆盖率提升计划，为所有未达到80%覆盖率的服务添加测试，直到所有服务都达到80%覆盖率。
```

## 📋 系统组件

### 1. Cursor监控系统
- **脚本**: `scripts/test-coverage/cursor-monitor.py`
- **功能**: 检测Cursor是否卡住，自动发送继续执行指令
- **启动**: `.\start-cursor-monitor.ps1`

### 2. 覆盖率检查系统
- **脚本**: `scripts/test-coverage/check-coverage-status.py`
- **功能**: 检查各服务的测试覆盖率
- **用法**: `python scripts/test-coverage/check-coverage-status.py`

### 3. 覆盖率提升系统
- **脚本**: `scripts/test-coverage/improve-coverage.py`
- **功能**: 自动生成测试文件
- **用法**: `python scripts/test-coverage/improve-coverage.py --all`

### 4. 持续改进系统
- **脚本**: `scripts/test-coverage/run-continuous-improvement.ps1`
- **功能**: 持续监控并提升覆盖率
- **启动**: `.\start-coverage-monitoring.ps1`

## 🔄 工作流程

```
1. 启动Cursor监控
   ↓
2. 在Cursor中执行覆盖率提升任务
   ↓
3. 如果Cursor卡住（超过5分钟）
   ↓
4. 监控脚本自动发送继续执行指令
   ↓
5. 创建 continue-coverage-improvement.txt 文件
   ↓
6. 复制文件内容到Cursor对话框
   ↓
7. 继续执行，直到所有服务达到80%覆盖率
```

## 📝 使用示例

### 示例1: 基本使用

```powershell
# 终端1: 启动监控
.\start-cursor-monitor.ps1

# 终端2或Cursor: 执行覆盖率提升任务
# 如果卡住，监控会自动发送继续执行指令
```

### 示例2: 安装定时任务

```powershell
# 安装定时任务（每5分钟自动检查）
.\scripts\test-coverage\install-cursor-monitor.ps1 -Install

# 查看任务状态
.\scripts\test-coverage\install-cursor-monitor.ps1 -Status
```

### 示例3: 测试脚本

```powershell
# 测试监控脚本是否正常工作
.\scripts\test-coverage\test-cursor-monitor.ps1
```

## 📂 输出文件

### continue-coverage-improvement.txt
继续执行指令文件，可以直接复制到Cursor对话框。

### .cursor-activity.log
监控活动日志，记录所有检测和操作。

### .cursor-continue-requested
标记文件，表示已请求继续执行。

## ⚙️ 配置选项

### 修改检查间隔

```bash
# 60秒检查一次
python scripts/test-coverage/cursor-monitor.py --interval 60
```

### 修改超时阈值

```bash
# 10分钟超时
python scripts/test-coverage/cursor-monitor.py --timeout 600
```

## 🔍 故障排除

### Python未找到
```powershell
# 检查Python
python --version
# 或
py --version

# 如果未安装，请安装Python 3.7+
```

### 权限问题
```powershell
# 以管理员身份运行PowerShell
# 右键点击PowerShell -> 以管理员身份运行
```

### 脚本无法运行
```powershell
# 检查执行策略
Get-ExecutionPolicy

# 如果需要，设置执行策略
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 📚 详细文档

- **Cursor监控**: `CURSOR_MONITOR_README.md`
- **覆盖率系统**: `scripts/test-coverage/README.md`
- **改进计划**: `TEST_COVERAGE_IMPROVEMENT_PLAN.md`

## ✅ 验证安装

运行测试脚本验证所有组件：

```powershell
.\scripts\test-coverage\test-cursor-monitor.ps1
```

如果所有检查通过，系统已准备就绪！

## 🎯 目标

- ✅ 所有服务达到80%测试覆盖率
- ✅ 自动检测并恢复卡住的任务
- ✅ 持续执行直到完成


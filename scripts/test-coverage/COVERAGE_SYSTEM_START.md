# 测试覆盖率自动化提升系统 - 启动指南

## 系统已创建完成

所有核心组件已创建并准备就绪。系统将持续运行直到所有服务达到80%覆盖率。

## 快速启动

### 方式1: 一键启动（推荐）

```powershell
# 在项目根目录执行
.\start-coverage-improvement.ps1 -InstallMonitor -StartMonitor -StartLoop
```

这将：
1. 安装监控定时任务（每10分钟检查一次）
2. 启动监控（后台运行）
3. 启动主循环（持续运行）

### 方式2: 分步启动

```powershell
# 步骤1: 安装监控定时任务
.\scripts\test-coverage\install-coverage-monitor.ps1 -Install

# 步骤2: 启动监控（可选，定时任务会自动运行）
.\start-coverage-improvement.ps1 -StartMonitor

# 步骤3: 启动主循环
.\start-coverage-improvement.ps1 -StartLoop
```

## 系统工作流程

1. **主循环**（持续运行）：
   - 每10分钟执行一次完整循环
   - 检查覆盖率 → 生成测试 → 同步到服务器 → 执行测试 → 修复错误

2. **监控任务**（每10分钟）：
   - 检查任务是否卡住
   - 如果卡住，创建继续执行指令文件

3. **自动恢复**：
   - 监控检测到卡住时，创建 `continue-coverage-improvement.txt`
   - Cursor监控脚本读取并发送到对话框
   - 任务自动继续执行

## 重要提示

- **系统将持续运行**，直到所有服务达到80%覆盖率
- **不要手动停止**主循环，除非所有服务都已达到80%
- **监控任务**会自动检测卡住并恢复
- **所有测试在服务器Docker中执行**

## 查看进度

```powershell
# 查看进度文件
Get-Content .coverage-progress.json | ConvertFrom-Json | ConvertTo-Json -Depth 10

# 查看覆盖率状态（从服务器）
# 需要SSH连接到服务器后执行
bash scripts/test-coverage/check-coverage-server.sh
```

## 系统状态文件

- `.coverage-progress.json` - 本地进度跟踪
- `.coverage-status.json` - 服务器覆盖率状态（需要从服务器复制）
- `.test-results.json` - 测试执行结果（在服务器上）
- `continue-coverage-improvement.txt` - 继续执行指令（监控创建）
- `test-fixes-needed.md` - 需要人工修复的问题

## 下一步

系统已准备就绪，可以开始执行。运行启动脚本后，系统将：

1. 自动检查各服务覆盖率
2. 为未达到80%的服务生成测试
3. 同步测试文件到服务器
4. 在Docker中执行测试
5. 自动修复常见错误
6. 持续循环直到完成

**系统将自动持续运行，直到目标达成！**


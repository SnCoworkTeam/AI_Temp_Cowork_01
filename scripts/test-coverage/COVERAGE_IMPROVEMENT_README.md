# 测试覆盖率80%自动化提升系统

## 概述

这是一个自动化系统，持续提升各服务的测试覆盖率至80%，包括：
- 每10分钟检查任务状态，检测是否卡住
- 在服务器Docker容器中执行测试
- 通过git同步测试文件到服务器
- 自动修复测试中的bug
- 持续循环直到所有服务达到80%覆盖率

## 系统组件

### 1. 任务监控系统
**文件**: `coverage-task-monitor.ps1`
- 每10分钟检查一次任务状态
- 检测方式：
  - 检查进度文件最后修改时间
  - 检查相关进程是否运行
  - 检查git提交历史
- 如果检测到卡住，创建继续执行指令文件

### 2. 覆盖率检查（服务器端）
**文件**: `check-coverage-server.sh`
- 在服务器上运行，检查各服务在Docker中的测试覆盖率
- 输出JSON格式的覆盖率报告

### 3. 测试文件同步
**文件**: `sync-tests-to-server.ps1`
- 检测本地新增/修改的测试文件
- 通过git push推送到远程仓库
- 在服务器上执行git pull拉取最新代码

### 4. Docker测试执行（服务器端）
**文件**: `run-tests-in-docker.sh`
- 在服务器上运行，遍历所有服务
- 在各自的Docker容器中执行测试
- 收集覆盖率结果

### 5. 自动bug修复
**文件**: `auto-fix-tests.py`
- 分析测试失败的原因
- 自动修复常见问题：
  - 导入错误
  - 语法错误
  - 缺少依赖
  - 类型错误

### 6. 主循环
**文件**: `coverage-improvement-loop.ps1`
- 持续运行的主循环
- 整合所有功能模块
- 直到所有服务达到80%覆盖率

## 快速开始

### 步骤1: 安装监控定时任务

```powershell
# 安装Windows定时任务（每10分钟检查一次）
.\scripts\test-coverage\install-coverage-monitor.ps1 -Install
```

### 步骤2: 启动监控（可选）

```powershell
# 启动监控（后台运行）
.\start-coverage-improvement.ps1 -StartMonitor
```

### 步骤3: 启动主循环

```powershell
# 启动主循环（持续运行直到完成）
.\start-coverage-improvement.ps1 -StartLoop
```

或者使用一键启动：

```powershell
# 安装监控 + 启动监控 + 启动主循环
.\start-coverage-improvement.ps1 -InstallMonitor -StartMonitor -StartLoop
```

## 工作流程

1. **主循环**（持续运行）：
   - 检查覆盖率状态（从服务器）
   - 如果所有服务≥80% → 退出
   - 识别需要改进的服务
   - 生成/更新测试文件（本地）
   - Git commit + push测试文件
   - SSH到服务器执行git pull
   - 在Docker中执行测试
   - 分析结果，自动修复bug
   - 更新进度文件
   - 等待10分钟

2. **监控循环**（每10分钟）：
   - 检查进度文件最后修改时间
   - 检查是否有相关进程运行
   - 检查git提交历史
   - 如果超过10分钟无活动 → 创建继续执行指令文件

3. **自动修复**：
   - 解析测试错误输出
   - 识别错误类型
   - 应用修复规则
   - 重新运行测试验证

## 文件说明

### 进度跟踪文件
- `.coverage-progress.json` - 记录每个服务的当前覆盖率、状态、最后检查时间等

### 覆盖率状态文件
- `.coverage-status.json` - 服务器上的覆盖率检查结果（JSON格式）

### 测试结果文件
- `.test-results.json` - 测试执行结果

### 继续执行指令
- `continue-coverage-improvement.txt` - 当监控检测到卡住时创建，包含继续执行的指令

### 需要人工修复的问题
- `test-fixes-needed.md` - 记录无法自动修复的测试错误

## 服务器端要求

1. **Docker容器运行**：
   - 确保所有服务的Docker容器正常运行
   - 容器命名格式：`enterprise-ai-{service-name}`

2. **Git仓库**：
   - 确保服务器可以访问git仓库
   - 确保有pull权限

3. **脚本部署**：
   - 将 `check-coverage-server.sh` 和 `run-tests-in-docker.sh` 部署到服务器
   - 确保脚本有执行权限：`chmod +x scripts/test-coverage/*.sh`

## 监控和管理

### 查看监控任务状态

```powershell
.\scripts\test-coverage\install-coverage-monitor.ps1 -Status
```

### 卸载监控任务

```powershell
.\scripts\test-coverage\install-coverage-monitor.ps1 -Uninstall
```

### 查看进度

```powershell
# 查看进度文件
Get-Content .coverage-progress.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

## 注意事项

1. **持续运行**：系统必须持续运行，不能中断，直到所有服务达到80%覆盖率
2. **服务器连接**：确保SSH连接正常，`remote.ssh`配置文件正确
3. **Git权限**：确保有git push/pull权限
4. **Docker容器**：确保服务器上的Docker容器正常运行
5. **自动修复**：自动修复仅处理常见错误，复杂问题需要人工介入（记录在`test-fixes-needed.md`）

## 故障排除

### 问题1: 监控任务未执行
**解决**：
- 检查任务计划程序中的任务状态
- 确保以管理员身份安装任务
- 手动运行一次监控脚本测试

### 问题2: 无法连接到服务器
**解决**：
- 检查`remote.ssh`配置文件
- 测试SSH连接：`ssh -F remote.ssh enterprise-ai-server echo "test"`
- 检查SSH密钥权限

### 问题3: Git推送失败
**解决**：
- 检查git配置和权限
- 确保有推送权限
- 检查远程仓库地址

### 问题4: Docker容器未运行
**解决**：
- 在服务器上检查容器状态：`docker ps`
- 启动容器：`docker-compose up -d`

## 系统状态

系统会持续运行，每10分钟执行一次循环，直到：
- 所有服务都达到80%覆盖率
- 或者手动停止

进度和状态会实时更新到 `.coverage-progress.json` 文件中。


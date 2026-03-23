# 系统性服务测试快速指南

## 快速启动

### Windows

```powershell
# 按层测试（推荐）
.\scripts\cicd\start-systematic-test.ps1 -Mode layer

# 逐个服务测试
.\scripts\cicd\start-systematic-test.ps1 -Mode service

# 全部服务一起测试
.\scripts\cicd\start-systematic-test.ps1 -Mode all

# 恢复上次测试进度
.\scripts\cicd\start-systematic-test.ps1 -Mode layer -Resume

# 重置并重新开始
.\scripts\cicd\start-systematic-test.ps1 -Mode layer -Reset
```

### Linux/Mac

```bash
# 按层测试（推荐）
python3 scripts/cicd/systematic-service-tester.py --mode layer

# 逐个服务测试
python3 scripts/cicd/systematic-service-tester.py --mode service

# 全部服务一起测试
python3 scripts/cicd/systematic-service-tester.py --mode all
```

## 测试模式说明

### 1. 按层测试 (layer) - 推荐

按照服务依赖关系分层测试，从基础服务到应用服务：

**Layer 1: 基础设施服务**
- postgres (数据库)
- redis (缓存)
- registry-service (服务注册)
- config-center (配置中心)

**Layer 2: 认证与网关**
- auth-service (认证服务)
- api-gateway (API网关)

**Layer 3: 核心业务服务**
- metadata-service (元数据)
- knowledge-base (知识库)
- workflow-engine (工作流)
- chat-service (聊天)
- mcp-gateway (MCP网关)
- sap-mcp-server (SAP MCP)

**Layer 4: 智能编排服务**
- agent-service (Agent服务)
- agent-orchestrator (Agent编排)
- agent-registry (Agent注册)
- dag-orchestrator (DAG编排)
- memory-service (内存管理)

**Layer 5: 扩展与适配服务**
- joyagent-adapter (JoyAgent适配)
- sap-metadata-agent (SAP元数据)
- vector-coordinator-service (向量协调)

**Layer 6: 前端服务**
- web-ui (前端界面)

**特点**:
- 从底层到上层逐层测试
- 确保依赖服务先通过测试
- 每层测试完成后可选择是否继续
- 适合系统性、全面的测试

### 2. 逐个服务测试 (service)

按照服务列表顺序，一个一个地测试。

**特点**:
- 灵活控制测试顺序
- 可以专注于特定服务
- 每个服务最多重试 3 次

### 3. 全部服务测试 (all)

所有服务一起测试。

**特点**:
- 最快速的测试方式
- 适合快速验证整体状态
- 不区分服务优先级

## 自动化闭环流程

### 完整流程

```
启动测试 → 等待完成 → 下载日志 → 分析错误
    ↓
修复Bug → 验证修复 → 提交代码 → 推送到Git
    ↓
触发CI/CD → 自动部署 → 健康检查
    ↓
测试通过？ ─No─→ 返回"启动测试"
    ↓
   Yes
    ↓
  完成！
```

### 每个服务的测试循环

1. **启动工作流**
   - 使用 `gh workflow run deploy.yml`
   - 设置环境为 staging

2. **等待测试完成**
   - 监控工作流状态
   - 最多等待 1 小时
   - 每 10 秒检查一次状态

3. **下载日志**
   - 下载所有作业的日志
   - 保存到 `%TEMP%\service-test-logs\run-{id}\`

4. **分析错误**
   - TypeScript 类型错误
   - Docker 构建错误
   - Python 运行时错误
   - 提取文件、行号、错误信息

5. **自动修复**
   - 修复 TypeScript 类型错误
   - 修复缺失的导入
   - 修复接口定义问题
   - 简单的语法错误

6. **验证修复**
   - 本地运行 `npx tsc --noEmit`
   - 确保修复没有引入新问题

7. **提交代码**
   - `git add -A`
   - `git commit -m "fix: Auto-fix {service} CI/CD errors"`
   - `git push origin main`

8. **自动部署**
   - 推送触发新的 CI/CD
   - 蓝绿部署到服务器
   - 健康检查验证

9. **判断结果**
   - 如果测试通过：标记服务完成，进入下一个
   - 如果测试失败：重试最多 3 次
   - 如果无法自动修复：记录失败，人工介入

## 测试进度跟踪

### 进度文件

测试进度保存在：
```
Windows: %TEMP%\service-test-logs\test_progress.json
Linux/Mac: /tmp/service-test-logs/test_progress.json
```

### 进度文件内容

```json
{
  "current_layer": "layer1_infrastructure",
  "current_service": "postgres",
  "completed_services": ["postgres", "redis"],
  "failed_services": ["api-gateway"],
  "test_results": {
    "postgres": {
      "service": "postgres",
      "status": "passed",
      "iterations": 1,
      "errors": [],
      "start_time": "2025-12-04T10:00:00",
      "end_time": "2025-12-04T10:15:00"
    }
  },
  "start_time": "2025-12-04T10:00:00",
  "last_update": "2025-12-04T10:30:00"
}
```

### 恢复测试

使用 `-Resume` 参数可以从上次中断的地方继续：

```powershell
.\scripts\cicd\start-systematic-test.ps1 -Mode layer -Resume
```

会跳过已完成的服务，继续测试未完成的服务。

### 重置进度

使用 `-Reset` 参数可以清除进度，从头开始：

```powershell
.\scripts\cicd\start-systematic-test.ps1 -Mode layer -Reset
```

## 查看日志和报告

### 日志目录

```
Windows: %TEMP%\service-test-logs\
Linux/Mac: /tmp/service-test-logs/
```

### 日志结构

```
service-test-logs/
├── test_progress.json          # 测试进度
├── run-123456/                 # 运行ID
│   ├── Build_Docker_Images_api-gateway.log
│   ├── Frontend_Tests.log
│   ├── Unit_Tests.log
│   └── ...
├── run-123457/
│   └── ...
└── ...
```

### 查看测试报告

```powershell
# 查看进度
Get-Content $env:TEMP\service-test-logs\test_progress.json | ConvertFrom-Json

# 查看最新日志
Get-ChildItem $env:TEMP\service-test-logs\ -Directory | Sort-Object Name -Descending | Select-Object -First 1
```

## 监控和管理

### 实时监控

在测试运行时，可以使用其他脚本监控状态：

```powershell
# 检查工作流状态
gh run list --workflow=deploy.yml --limit 5

# 查看特定运行
gh run view {run_id}

# 实时查看日志
gh run view {run_id} --log
```

### 中断测试

按 `Ctrl+C` 可以随时中断测试。

进度会自动保存，下次可以使用 `-Resume` 恢复。

### 手动干预

如果遇到无法自动修复的问题：

1. 查看日志文件找到具体错误
2. 手动修复代码
3. 提交并推送
4. 使用 `-Resume` 继续测试

## 成功标准

### 单个服务测试通过标准

- CI/CD 工作流状态为 `success`
- 日志中未发现错误
- 健康检查通过
- 自动部署成功

### 整体测试完成标准

- 所有服务测试通过
- 测试覆盖率达到目标
- 部署到服务器成功
- 所有健康检查通过

## 预期效果

### 测试覆盖率提升

| 阶段 | 周数 | 测试覆盖率 | 累计通过服务 |
|------|-----|-----------|-------------|
| 基础设施 | 1-2 | 20% | 4 |
| 认证网关 | 3-4 | 30% | 6 |
| 核心业务 | 5-8 | 45% | 12 |
| 智能编排 | 9-12 | 55% | 17 |
| 扩展适配 | 13-14 | 58% | 20 |
| 前端服务 | 15-16 | 60%+ | 21 |

### 质量指标改善

- **自动修复率**: 70%+
- **测试通过率**: 95%+
- **平均修复时间**: < 30 分钟
- **部署频率**: 每天 2-5 次
- **故障恢复时间**: < 1 小时

## 故障排查

### 常见问题

1. **GitHub CLI 未安装**
   ```powershell
   winget install --id GitHub.cli
   ```

2. **Python 版本过低**
   需要 Python 3.11+

3. **Git 权限问题**
   确保有 push 权限

4. **工作流触发失败**
   检查 GitHub token 是否有效

5. **自动修复失败**
   查看日志，可能需要人工介入

### 获取帮助

查看详细文档：
- `docs/SYSTEMATIC_TESTING_PLAN.md` - 完整测试计划
- `scripts/cicd/README.md` - CI/CD 脚本说明

## 总结

系统性服务测试器提供了一个完整的自动化测试闭环解决方案：

✅ **自动化**: 从测试到部署全自动
✅ **系统性**: 按照依赖关系分层测试
✅ **智能修复**: 自动识别和修复常见错误
✅ **快速反馈**: 30分钟完成一个完整循环
✅ **可追溯**: 完整的日志和进度记录
✅ **可恢复**: 支持中断和恢复
✅ **渐进式**: 逐步提升测试覆盖率

开始使用：
```powershell
.\scripts\cicd\start-systematic-test.ps1 -Mode layer
```

祝测试顺利！

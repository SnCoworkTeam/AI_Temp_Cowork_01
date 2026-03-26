# 系统性测试计划

## 目标
通过 CI/CD 自动化测试闭环，逐个服务进行测试，持续提升代码覆盖率和质量。

## 一、现状分析

### 1.1 现有 CI/CD 架构

#### 工作流配置
- **test-suite.yml**: 完整测试套件
  - 单元测试 (unit-tests)
  - 集成测试 (integration-tests)
  - 前端测试 (frontend-tests)
  - 前端 API 集成测试 (frontend-api-tests)
  - E2E 测试 (e2e-tests)

- **deploy.yml**: 部署工作流
  - 测试阶段 (test, frontend-test)
  - 镜像构建阶段 (build-images)
  - 自动部署阶段 (deploy)
  - 蓝绿部署策略
  - 健康检查

#### 触发条件
- push 到 main/develop 分支
- PR 到 main/develop 分支
- 定时任务（每天凌晨 2 点）
- 手动触发 (workflow_dispatch)

### 1.2 已有自动化脚本

#### Python 脚本
1. **continuous-test-until-pass.py** (scripts/cicd/)
   - 持续测试直到所有服务通过
   - 支持 Windows/Linux
   - 最多 999 次迭代
   - 自动下载日志、分析错误、修复 bug
   - 自动提交并推送

2. **auto-fix-cycle.py** (scripts/cicd/)
   - 完整的 8 步自动修复循环
   - 最多 5 次迭代
   - 更聚焦于快速修复

3. **test-core-services-first.py** (scripts/cicd/)
   - 核心服务优先测试

#### PowerShell 脚本
1. **check-test-status.ps1**
   - 检查测试状态
   - 显示运行记录和结果

2. **check-cicd-status.ps1**
   - 检查持续测试系统状态
   - 监控 Python 进程
   - 查看最新工作流运行状态

### 1.3 服务清单

#### 业务服务 (共 19 个)
1. **api-gateway** - API 网关
2. **auth-service** - 认证服务
3. **knowledge-base** - 知识库服务
4. **metadata-service** - 元数据服务
5. **workflow-engine** - 工作流引擎
6. **web-ui** - Web 前端
7. **registry-service** - 服务注册中心
8. **config-center** - 配置中心
9. **sap-mcp-server** - SAP MCP 服务器
10. **mcp-gateway** - MCP 网关
11. **chat-service** - 聊天服务
12. **dag-orchestrator** - DAG 编排器
13. **agent-service** - Agent 服务
14. **agent-orchestrator** - Agent 编排器
15. **agent-registry** - Agent 注册中心
16. **joyagent-adapter** - JoyAgent 适配器
17. **memory-service** - 内存服务
18. **sap-metadata-agent** - SAP 元数据代理
19. **vector-coordinator-service** - 向量协调服务

#### 基础设施服务
- **postgres** - PostgreSQL 数据库
- **redis** - Redis 缓存
- **redis-commander** - Redis 管理界面

## 二、系统性测试策略

### 2.1 分层测试策略

#### 第一层：核心基础服务
优先级最高，其他服务依赖这些基础服务

1. **postgres** (数据库)
2. **redis** (缓存)
3. **registry-service** (服务注册)
4. **config-center** (配置中心)

**测试重点**:
- 服务启动健康检查
- 基础连接测试
- 数据持久化验证

#### 第二层：认证与网关服务
负责流量入口和安全认证

5. **auth-service** (认证)
6. **api-gateway** (网关)

**测试重点**:
- 认证流程测试
- Token 管理
- API 路由转发
- 权限验证

#### 第三层：核心业务服务
主要业务逻辑服务

7. **metadata-service** (元数据)
8. **knowledge-base** (知识库)
9. **workflow-engine** (工作流)
10. **chat-service** (聊天)
11. **mcp-gateway** (MCP 网关)
12. **sap-mcp-server** (SAP MCP)

**测试重点**:
- 业务逻辑测试
- 服务间集成
- 数据流转
- 错误处理

#### 第四层：智能编排服务
AI Agent 相关服务

13. **agent-service** (Agent 核心)
14. **agent-orchestrator** (Agent 编排)
15. **agent-registry** (Agent 注册)
16. **dag-orchestrator** (DAG 编排)
17. **memory-service** (内存管理)

**测试重点**:
- Agent 生命周期
- 编排逻辑
- 状态管理
- 并发处理

#### 第五层：扩展与适配服务
特定业务适配器

18. **joyagent-adapter** (JoyAgent 适配)
19. **sap-metadata-agent** (SAP 元数据)
20. **vector-coordinator-service** (向量协调)

**测试重点**:
- 适配器功能
- 外部集成
- 数据转换

#### 第六层：前端服务
用户界面

21. **web-ui** (前端)

**测试重点**:
- TypeScript 编译
- 组件测试
- API 集成
- 构建成功

### 2.2 测试类型

#### 单元测试
- 独立函数/类测试
- Mock 外部依赖
- 覆盖率目标: 60%+

#### 集成测试
- 服务间调用测试
- 数据库集成
- 缓存集成
- 覆盖率目标: 40%+

#### E2E 测试
- 完整业务流程
- 真实环境模拟
- 关键路径验证
- 覆盖率目标: 20%+

#### 前端测试
- TypeScript 类型检查
- 组件渲染测试
- API 调用测试
- 构建测试

## 三、自动化测试闭环流程

### 3.1 闭环步骤

```
┌─────────────────────────────────────────────────┐
│  1. 启动测试流程                                  │
│     - 触发 GitHub Actions 工作流                 │
│     - 使用 gh workflow run deploy.yml           │
└──────────────┬──────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────┐
│  2. 等待测试完成                                  │
│     - 监控工作流状态                              │
│     - gh run view {run_id}                      │
│     - 最多等待 1 小时                            │
└──────────────┬──────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────┐
│  3. 获取测试结果                                  │
│     - 使用 check-test-status.ps1                │
│     - 下载日志文件                                │
│     - gh run view {run_id} --log                │
└──────────────┬──────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────┐
│  4. 分析测试错误                                  │
│     - 解析日志文件                                │
│     - 提取错误信息                                │
│     - 分类错误类型                                │
└──────────────┬──────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────┐
│  5. 自动修复 Bug                                 │
│     - TypeScript 类型错误                        │
│     - 缺失导入                                   │
│     - 接口定义                                   │
│     - 简单语法错误                               │
└──────────────┬──────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────┐
│  6. 验证修复                                     │
│     - 本地 TypeScript 编译检查                   │
│     - npx tsc --noEmit                          │
│     - pytest 本地测试                            │
└──────────────┬──────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────┐
│  7. 提交代码                                     │
│     - git add -A                                │
│     - git commit -m "fix: Auto-fix CI/CD..."   │
│     - git push origin main                      │
└──────────────┬──────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────┐
│  8. 自动部署                                     │
│     - 触发部署工作流                              │
│     - 蓝绿部署到服务器                            │
│     - 健康检查                                   │
└──────────────┬──────────────────────────────────┘
               ↓
           测试通过? ──No──> 返回步骤 1
               │
              Yes
               ↓
          ┌─────────┐
          │ 完成！  │
          └─────────┘
```

### 3.2 核心特性

1. **完全自动化**: 无需人工干预
2. **持续迭代**: 直到所有测试通过
3. **智能修复**: 识别常见错误模式并自动修复
4. **快速反馈**: 10-15 分钟一个完整循环
5. **可追溯**: 所有日志和修复记录保存

## 四、逐服务测试计划

### 4.1 第一阶段：基础服务稳定性 (Week 1-2)

#### 目标
确保基础设施服务稳定运行

#### 服务列表
- postgres
- redis
- registry-service
- config-center

#### 测试内容
1. 服务启动测试
2. 健康检查端点
3. 基础连接测试
4. 数据持久化测试

#### 成功标准
- 所有服务健康检查通过
- 连接测试成功率 100%
- 无启动失败

### 4.2 第二阶段：认证与网关 (Week 3-4)

#### 目标
确保认证和流量入口正常

#### 服务列表
- auth-service
- api-gateway

#### 测试内容
1. 用户注册/登录流程
2. Token 生成与验证
3. API 路由测试
4. 权限验证
5. 限流测试

#### 成功标准
- 认证流程成功率 100%
- API 路由正确率 100%
- 权限验证准确率 100%
- 覆盖率达到 50%+

### 4.3 第三阶段：核心业务服务 (Week 5-8)

#### 目标
核心业务逻辑稳定

#### 服务列表
- metadata-service
- knowledge-base
- workflow-engine
- chat-service
- mcp-gateway
- sap-mcp-server

#### 测试内容
1. 元数据 CRUD 操作
2. 知识库查询与检索
3. 工作流创建与执行
4. 聊天会话管理
5. MCP 协议通信
6. SAP 数据集成

#### 成功标准
- 业务逻辑测试覆盖率 60%+
- 集成测试覆盖率 40%+
- 关键路径测试通过率 100%

### 4.4 第四阶段：智能编排服务 (Week 9-12)

#### 目标
AI Agent 编排能力验证

#### 服务列表
- agent-service
- agent-orchestrator
- agent-registry
- dag-orchestrator
- memory-service

#### 测试内容
1. Agent 创建与销毁
2. 编排策略执行
3. DAG 工作流运行
4. 状态同步测试
5. 内存管理测试

#### 成功标准
- Agent 生命周期管理测试覆盖率 50%+
- 编排逻辑测试覆盖率 40%+
- 并发场景测试通过

### 4.5 第五阶段：扩展与适配服务 (Week 13-14)

#### 目标
外部集成功能验证

#### 服务列表
- joyagent-adapter
- sap-metadata-agent
- vector-coordinator-service

#### 测试内容
1. 适配器数据转换
2. 外部系统集成
3. 向量操作测试

#### 成功标准
- 适配器测试覆盖率 40%+
- 外部集成测试通过
- 数据转换准确率 100%

### 4.6 第六阶段：前端服务 (Week 15-16)

#### 目标
前端功能与集成验证

#### 服务列表
- web-ui

#### 测试内容
1. TypeScript 类型检查
2. 组件单元测试
3. API 集成测试
4. E2E 测试
5. 构建测试

#### 成功标准
- TypeScript 零错误
- 组件测试覆盖率 50%+
- E2E 关键流程覆盖
- 构建成功

## 五、执行指南

### 5.1 启动自动化测试闭环

#### 方式一：持续测试（推荐）

使用 continuous-test-until-pass.py，测试直到全部通过：

```bash
# Windows
python scripts/cicd/continuous-test-until-pass.py

# Linux
./scripts/cicd/continuous-test-until-pass.py
```

**特点**:
- 最多 999 次迭代
- 自动修复常见错误
- 连续 2 次成功才停止
- 适合长期运行

#### 方式二：快速修复循环

使用 auto-fix-cycle.py，最多 5 次迭代：

```bash
python scripts/cicd/auto-fix-cycle.py
```

**特点**:
- 最多 5 次迭代
- 快速反馈
- 适合快速验证修复

### 5.2 监控测试进度

#### 检查测试状态
```powershell
# Windows
.\check-test-status.ps1

# 或使用 GitHub CLI
gh run list --workflow=deploy.yml --limit 5
gh run view {run_id}
```

#### 检查持续测试系统状态
```powershell
.\check-cicd-status.ps1
```

#### 查看服务状态
```bash
# 本地服务
docker-compose ps

# 远程服务器
ssh user@server 'cd /opt/enterprise-ai-platform && docker-compose ps'
```

### 5.3 手动触发测试

#### 触发测试工作流
```bash
gh workflow run test-suite.yml
```

#### 触发部署工作流
```bash
gh workflow run deploy.yml --field environment=staging
```

### 5.4 查看测试报告

#### 下载测试报告
```bash
gh run view {run_id} --log > test-log.txt
```

#### 下载测试产物
```bash
gh run download {run_id}
```

#### 查看覆盖率报告
测试产物中包含:
- `coverage.xml` - XML 格式覆盖率
- `htmlcov/` - HTML 格式覆盖率报告
- `test-results.xml` - JUnit 格式测试结果
- `test-report.html` - HTML 格式测试报告

### 5.5 自定义测试策略

#### 按服务测试
修改 `test-suite.yml` 中的服务列表

#### 按优先级测试
使用 `test-core-services-first.py`

#### 调整迭代次数
修改脚本中的 `max_iterations` 参数

## 六、关键指标

### 6.1 测试覆盖率目标

| 测试类型 | 当前覆盖率 | 目标覆盖率 | 预期时间 |
|---------|----------|----------|---------|
| 单元测试 | ~10% | 60%+ | 16 周 |
| 集成测试 | ~5% | 40%+ | 16 周 |
| E2E 测试 | ~3% | 20%+ | 16 周 |
| 总体覆盖率 | ~15% | 50%+ | 16 周 |

### 6.2 质量指标

- **测试通过率**: 95%+
- **CI/CD 成功率**: 90%+
- **平均修复时间**: < 30 分钟
- **自动修复率**: 70%+
- **部署频率**: 每天 2-5 次

### 6.3 性能指标

- **测试运行时间**: < 20 分钟
- **部署时间**: < 5 分钟
- **健康检查时间**: < 2 分钟
- **完整循环时间**: < 30 分钟

## 七、风险与应对

### 7.1 风险识别

1. **测试不稳定**: 偶尔失败的间歇性测试
   - **应对**: 重试机制、隔离不稳定测试

2. **修复不完整**: 自动修复无法解决复杂问题
   - **应对**: 人工介入、记录复杂问题

3. **资源消耗**: GitHub Actions 分钟数限制
   - **应对**: 优化测试速度、选择性运行

4. **服务依赖**: 服务间依赖导致测试复杂
   - **应对**: Mock 依赖、独立测试

### 7.2 最佳实践

1. **小步快跑**: 每次只修复少量问题
2. **快速反馈**: 尽快发现和修复问题
3. **持续监控**: 关注测试趋势和指标
4. **团队协作**: 定期回顾和改进
5. **文档更新**: 及时更新测试文档

## 八、总结

### 8.1 核心优势

1. **完全自动化**: 从测试到部署全自动
2. **持续改进**: 逐步提升覆盖率
3. **快速反馈**: 30 分钟完成一个循环
4. **稳定可靠**: 蓝绿部署保证稳定性
5. **可扩展**: 易于添加新服务测试

### 8.2 预期成果

经过 16 周的系统性测试:
- 测试覆盖率从 15% 提升到 50%+
- CI/CD 成功率达到 90%+
- 自动部署频率提高到每天 2-5 次
- Bug 修复时间缩短到 30 分钟内
- 整体代码质量显著提升

### 8.3 下一步行动

1. 启动持续测试脚本
2. 监控测试进度和结果
3. 定期回顾和调整策略
4. 扩展测试覆盖范围
5. 持续优化自动化流程

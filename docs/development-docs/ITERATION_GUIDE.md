# 项目迭代指南

本文档为项目连续迭代提供指南，确保新功能和改进能够平稳、持续地集成到项目中。

## 迭代原则

### 1. 持续集成
- 每次提交都应该是可部署的
- 保持代码质量门禁
- 自动化测试和检查

### 2. 小步快跑
- 优先实现MVP（最小可行产品）
- 逐步完善功能
- 快速反馈和调整

### 3. 向后兼容
- 保持API向后兼容
- 数据库迁移平滑进行
- 配置变更有默认值

### 4. 文档同步
- 代码变更同步更新文档
- 重要决策记录ADR
- API变更更新OpenAPI规范

## 迭代流程

### 阶段1: 需求分析

#### 1.1 创建功能请求
- 在 `feedback-loop/user-feedback/feature-requests/` 创建功能请求
- 描述问题、需求、预期效果
- 评估优先级和影响范围

#### 1.2 影响分析
- 评估对现有功能的影响
- 识别需要修改的服务和模块
- 评估数据库变更需求
- 评估API变更影响

#### 1.3 创建变更请求
- 在 `release-management/change-control/change-requests/` 创建变更请求
- 包含详细的变更计划
- 包含测试计划
- 包含回滚计划

### 阶段2: 架构设计

#### 2.1 架构审查
- 确保符合架构原则
- 检查服务边界
- 评估性能影响
- 评估安全影响

#### 2.2 创建ADR（如需要）
- 重要架构决策创建ADR
- 记录在 `docs/architecture-docs/decision-records/`
- 使用ADR模板

#### 2.3 设计评审
- 团队评审设计
- 确认技术方案
- 确认实现计划

### 阶段3: 代码实现

#### 3.1 创建功能分支
```bash
git checkout -b feature/feature-name
```

#### 3.2 实现功能
- 遵循编码规范（`docs/development-docs/coding-standards/`）
- 使用共享库（`shared-libs/`）
- 编写单元测试（覆盖率 >= 80%）
- 编写API文档（OpenAPI）

#### 3.3 代码质量检查
```bash
# 运行架构守护
python scripts/architecture_guard.py --check

# 运行测试
pytest

# 检查代码覆盖率
pytest --cov --cov-report=html

# 检查代码健康度
python scripts/code-health/check-all.sh
```

### 阶段4: 测试验证

#### 4.1 单元测试
- 所有新功能必须有单元测试
- 覆盖率目标 >= 80%
- 关键业务逻辑 >= 90%

#### 4.2 集成测试
- 测试服务间交互
- 测试API端点
- 测试数据库操作

#### 4.3 自动化调试系统测试（如适用）
- 如果涉及错误处理，使用自动化调试系统测试
- 验证错误分析准确性
- 验证修复策略有效性

```python
from src.auto_debug import get_error_analyzer, get_test_validator

# 测试错误分析
analyzer = get_error_analyzer()
analysis = await analyzer.analyze_error(...)

# 测试验证
validator = get_test_validator()
result = await validator.run_functional_tests(...)
```

### 阶段5: 代码审查

#### 5.1 提交Pull Request
- 创建PR，包含：
  - 功能描述
  - 变更说明
  - 测试结果
  - 截图（如适用）

#### 5.2 代码审查检查清单
- [ ] 代码符合编码规范
- [ ] 所有测试通过
- [ ] 代码覆盖率达标
- [ ] 架构合规性检查通过
- [ ] 文档已更新
- [ ] API文档已更新
- [ ] 安全扫描通过

#### 5.3 审查反馈处理
- 及时响应审查意见
- 修改代码并更新测试
- 重新提交审查

### 阶段6: 合并和部署

#### 6.1 合并到主分支
- 所有检查通过后合并
- 使用squash merge保持历史清晰
- 删除功能分支

#### 6.2 预发布环境验证
- 自动部署到预发布环境
- 运行端到端测试
- 验证功能正常

#### 6.3 生产环境部署
- 创建发布计划
- 执行渐进式部署
- 监控部署过程
- 验证功能正常

## 特定场景迭代指南

### 添加新服务

1. **创建服务目录**
   ```
   new-service/
   ├── src/
   │   ├── main.py
   │   ├── routes/
   │   ├── services/
   │   └── models/
   ├── tests/
   ├── requirements.txt
   └── Dockerfile
   ```

2. **更新docker-compose.yml**
   - 添加服务定义
   - 配置环境变量
   - 配置依赖关系

3. **更新文档**
   - 更新系统架构文档
   - 更新API文档
   - 更新快速开始指南

4. **集成到自动化调试系统**（如需要）
   - 在 `config/platform_integration.yaml` 添加服务监控配置
   - 更新错误分析器识别新服务错误
   - 更新修复策略管理器

### 修改现有API

1. **保持向后兼容**
   - 添加新字段时设为可选
   - 废弃旧字段时保留一段时间
   - 使用API版本控制

2. **更新OpenAPI规范**
   - 更新API文档
   - 更新请求/响应模型
   - 提供迁移指南

3. **更新客户端代码**
   - 更新前端API客户端
   - 更新测试用例
   - 更新使用示例

### 数据库变更

1. **创建迁移脚本**
   ```bash
   cd database
   alembic revision --autogenerate -m "description"
   ```

2. **测试迁移**
   - 测试升级迁移
   - 测试回滚迁移
   - 验证数据完整性

3. **生产环境迁移**
   - 备份数据库
   - 在维护窗口执行
   - 监控迁移过程
   - 验证数据完整性

### 添加自动化调试功能

1. **扩展错误分析器**
   - 在 `platform_error_analyzer.py` 添加新错误模式
   - 更新错误分类规则
   - 添加新的错误类型

2. **添加修复策略**
   - 在 `platform_fix_strategies.py` 实现新策略
   - 注册到策略管理器
   - 编写测试用例

3. **更新工作流配置**
   - 在 `config/debug_workflows.yaml` 添加新工作流
   - 定义触发条件和步骤
   - 配置决策规则

4. **更新决策规则**
   - 在 `config/decision_rules.yaml` 添加新规则
   - 定义自动执行条件
   - 定义人工决策条件

### 性能优化

1. **性能分析**
   - 识别性能瓶颈
   - 建立性能基线
   - 使用性能分析工具

2. **优化实现**
   - 实现优化方案
   - 保持功能不变
   - 添加性能测试

3. **验证优化效果**
   - 运行性能测试
   - 对比优化前后性能
   - 确保没有回归

## 版本发布

### 版本号规则

使用语义化版本号：`MAJOR.MINOR.PATCH`

- **MAJOR**: 不兼容的API变更
- **MINOR**: 向后兼容的功能添加
- **PATCH**: 向后兼容的问题修复

### 发布流程

1. **创建发布分支**
   ```bash
   git checkout -b release/v1.2.0
   ```

2. **更新版本号**
   - 更新所有服务的版本号
   - 更新CHANGELOG.md
   - 更新文档版本号

3. **创建发布说明**
   - 在 `release-management/release-notes/` 创建发布说明
   - 列出新功能
   - 列出修复的问题
   - 列出破坏性变更

4. **发布准备检查**
   - [ ] 所有测试通过
   - [ ] 文档已更新
   - [ ] 变更请求已批准
   - [ ] 回滚计划已准备
   - [ ] 监控告警已配置

5. **创建Git标签**
   ```bash
   git tag -a v1.2.0 -m "Release version 1.2.0"
   git push origin v1.2.0
   ```

6. **部署到生产**
   - 使用渐进式部署策略
   - 监控部署过程
   - 验证功能正常

## 持续改进

### 反馈收集

1. **用户反馈**
   - 收集用户反馈（`feedback-loop/user-feedback/`）
   - 分析反馈趋势
   - 优先级排序

2. **系统反馈**
   - 监控系统指标（`feedback-loop/system-feedback/`）
   - 分析性能趋势
   - 识别改进机会

3. **开发反馈**
   - 代码审查反馈
   - 技术债务追踪
   - 开发效率分析

### 技术债务管理

1. **识别技术债务**
   - 代码健康度监控
   - 架构合规性检查
   - 团队反馈

2. **规划偿还**
   - 在 `code-health/improvement-plans/debt-repayment/` 创建偿还计划
   - 评估优先级
   - 分配资源

3. **执行偿还**
   - 在迭代中逐步偿还
   - 记录偿还进度
   - 验证改进效果

## 工具和脚本

### 架构守护
```bash
# 检查架构合规性
python scripts/architecture_guard.py --check

# 自动修复可修复的问题
python scripts/architecture_guard.py --auto-fix
```

### 代码健康度
```bash
# 检查代码健康度
python scripts/code-health/check-all.sh

# 生成健康度报告
python scripts/code-health/generate-report.py
```

### 依赖管理
```bash
# 检查依赖更新
python scripts/dependencies/check-updates.py

# 更新依赖
python scripts/dependencies/update-dependencies.py
```

### 文档生成
```bash
# 生成所有文档
python scripts/docs/generate-all.py

# 生成API文档
python scripts/docs/generate-api-docs.py
```

## 最佳实践

1. **小步提交**
   - 频繁提交，每次提交都是可工作的
   - 清晰的提交信息
   - 原子性变更

2. **测试驱动**
   - 先写测试，再写实现
   - 保持高测试覆盖率
   - 自动化测试

3. **文档同步**
   - 代码变更同步更新文档
   - 重要决策记录ADR
   - API变更更新规范

4. **代码审查**
   - 所有代码必须经过审查
   - 及时响应审查意见
   - 学习最佳实践

5. **持续监控**
   - 监控系统指标
   - 监控代码质量
   - 及时发现问题

## 故障处理

### 发现问题

1. **快速响应**
   - 创建事故记录
   - 评估影响范围
   - 通知相关人员

2. **问题分析**
   - 使用自动化调试系统分析
   - 收集相关日志
   - 重现问题

3. **修复实施**
   - 使用修复策略管理器
   - 执行修复
   - 验证修复效果

4. **事后总结**
   - 记录事故原因
   - 更新错误分析器
   - 更新修复策略
   - 改进预防措施

## 相关文档

- [快速开始指南](QUICK_START.md)
- [编码规范](coding-standards/)
- [测试指南](testing-guide/getting-started.md)
- [自动化调试系统](auto-debug-system.md)
- [项目宪法](../../.project_constitution.md)


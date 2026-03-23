# 架构决策记录 (ADR)

## 概述

本文档记录项目中的重要架构决策。每个决策都遵循ADR格式，包括上下文、决策、后果等信息。

## ADR格式

每个ADR文件应包含以下部分：

1. **标题**: ADR编号和简短标题
2. **状态**: 提议、已接受、已弃用、已替代
3. **日期**: 决策日期 (YYYY-MM-DD)
4. **作者**: 决策者或团队
5. **相关ADR**: 相关的其他ADR编号
6. **标签**: 决策类型（技术决策、架构决策、工具选择、流程决策）

## ADR列表

- [ADR-0001: 记录架构决策](./0001-record-architecture-decisions.md)
- [ADR-0002: 使用FastAPI作为后端服务框架](./0002-use-fastapi-for-backend-services.md)
- [ADR-0003: 采用微服务架构](./0003-adopt-microservices-architecture.md)
- [ADR-0004: 选择PostgreSQL作为主数据库](./0004-choose-postgresql-as-primary-database.md)
- [ADR-0005: 使用Next.js作为前端框架](./0005-use-nextjs-for-frontend.md)
- [ADR-0006: 使用LangGraph作为工作流引擎](./0006-use-langgraph-for-workflow-engine.md)
- [ADR-0007: 实现SSO单点登录认证](./0007-implement-sso-authentication.md)
- [ADR-0008: 使用共享库管理公共代码](./0008-use-shared-libraries-for-common-code.md)

详细索引请查看 [INDEX.md](./INDEX.md)（自动生成）

## 如何创建新的ADR

### 1. 使用模板

```bash
# 复制模板
cp docs/architecture-docs/decision-records/adr-template.md \
   docs/architecture-docs/decision-records/0006-your-decision-title.md
```

### 2. 填写内容

- 使用下一个可用的编号（如0006）
- 填写所有必需部分
- 确保状态和日期正确

### 3. 验证格式

```bash
# 验证ADR格式
python scripts/docs/validate-adr.py --validate

# 生成索引
python scripts/docs/generate-adr-index.py
```

### 4. 提交到版本控制

```bash
git add docs/architecture-docs/decision-records/0006-your-decision-title.md
git commit -m "docs: 添加ADR-0006 - 决策标题"
```

## ADR状态管理

### 状态说明

- **提议**: 正在讨论的决策
- **已接受**: 已接受的决策，正在实施或已实施
- **已弃用**: 已弃用的决策，不再使用
- **已替代**: 被其他ADR替代的决策

### 更新状态

当决策状态改变时，更新ADR文件中的状态字段，并添加说明：

```markdown
**状态**: 已接受 → 已弃用（2024-06-01，原因：被ADR-0010替代）
```

## ADR命名规范

- 格式: `0001-short-title.md`
- 编号: 4位数字，从0001开始
- 标题: 简短描述，使用连字符分隔

示例:
- `0001-record-architecture-decisions.md`
- `0002-use-fastapi-for-backend.md`

## 自动化工具

### 验证ADR

```bash
# 验证所有ADR文件
python scripts/docs/validate-adr.py --validate

# 列出所有ADR
python scripts/docs/validate-adr.py --list
```

### 生成索引

```bash
# 生成ADR索引
python scripts/docs/generate-adr-index.py
```

### 检查ADR要求

```bash
# 检查是否有架构变更但未创建ADR
python scripts/docs/check-adr-requirement.py
```

## CI/CD集成

ADR验证已集成到CI/CD流程：

- **Pull Request**: 自动验证ADR格式
- **代码审查**: 检查架构变更是否创建ADR
- **索引生成**: 自动更新ADR索引

## 决策追溯和审计

### 查看决策历史

```bash
# 使用Git查看ADR变更历史
git log docs/architecture-docs/decision-records/

# 查看特定ADR的变更
git log docs/architecture-docs/decision-records/0002-use-fastapi-for-backend.md
```

### 决策审计

ADR系统支持完整的决策审计：

1. **决策时间**: 通过日期字段记录
2. **决策者**: 通过作者字段记录
3. **决策过程**: 通过附录中的会议记录记录
4. **决策变更**: 通过Git历史记录

## 最佳实践

1. **及时记录**: 在做出决策时立即创建ADR
2. **详细描述**: 充分描述背景、方案和后果
3. **定期审查**: 定期审查ADR状态，更新过时决策
4. **保持更新**: 当决策变更时，及时更新ADR状态
5. **链接相关**: 使用相关ADR字段链接相关决策

## 相关资源

- [ADR模板](./adr-template.md)
- [ADR索引](./INDEX.md)（自动生成）
- [ADR验证工具](../../../scripts/docs/validate-adr.py)
- [ADR生成工具](../../../scripts/docs/generate-adr-index.py)

## 参考资料

- [ADR格式规范](https://adr.github.io/)
- [记录架构决策](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)

# 依赖关系图

## 概述

本目录包含项目的依赖关系图，包括服务间依赖、外部依赖和依赖冲突分析。

## 目录结构

```
dependency-graph/
├── service-dependencies/    # 服务间依赖
│   ├── graph.json          # 依赖关系图（JSON）
│   ├── graph.dot           # 依赖关系图（DOT格式）
│   └── graph.png           # 依赖关系图（图片）
├── external-dependencies/   # 外部依赖
│   ├── python-dependencies.json
│   ├── nodejs-dependencies.json
│   └── docker-dependencies.json
└── dependency-conflicts/     # 依赖冲突
    ├── conflicts.json
    └── resolution-guide.md
```

## 服务间依赖

### 依赖关系
```
web-ui
  ├── auth-service (认证)
  ├── workflow-engine (工作流)
  └── mcp-gateway (工具)

workflow-engine
  ├── mcp-gateway (工具调用)
  ├── knowledge-base (知识库)
  └── auth-service (认证)

auth-service
  └── database (数据存储)

knowledge-base
  ├── database (数据存储)
  └── vector-db (向量存储)

mcp-gateway
  ├── knowledge-base (知识库工具)
  └── database (数据存储)
```

## 外部依赖

### Python依赖
- FastAPI生态系统
- LangChain/LangGraph
- SQLAlchemy
- Pydantic

### Node.js依赖
- Next.js生态系统
- React生态系统
- TypeScript

### Docker依赖
- 基础镜像
- 运行时依赖

## 依赖冲突

### 常见冲突类型
1. **版本冲突**: 不同服务需要不同版本
2. **许可证冲突**: 不兼容的许可证
3. **安全冲突**: 依赖包含已知漏洞

### 冲突解决
参见 [dependency-conflicts/resolution-guide.md](./dependency-conflicts/resolution-guide.md)

## 生成依赖图

```bash
# 生成所有依赖图
./scripts/dependencies/generate-graph.sh

# 生成服务依赖图
./scripts/dependencies/generate-service-graph.sh

# 生成外部依赖图
./scripts/dependencies/generate-external-graph.sh
```










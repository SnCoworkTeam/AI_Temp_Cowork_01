# LuminaOS平台 - 架构图详细说明

**文档版本**: 1.0.0  
**生成日期**: 2025-12-16

---

## 🏗️ 系统架构图（详细版）

### 完整系统架构

```mermaid
graph TB
    subgraph "用户层"
        UI[Web UI<br/>Next.js 14<br/>Port: 3000]
        Mobile[移动端<br/>可选]
    end
    
    subgraph "API网关层"
        Gateway[API Gateway<br/>FastAPI<br/>Port: 8080]
        Registry[Registry Service<br/>服务注册<br/>Port: 8000]
        Config[Config Center<br/>配置中心<br/>Port: 8090]
    end
    
    subgraph "AIOS核心层 - 里程碑1-4"
        subgraph "OS Core - 里程碑1"
            OS[OS Core<br/>统一资源抽象层]
            ResModel[Resource Model<br/>资源模型]
            ResReg[Resource Registry<br/>资源注册表]
            ResResolver[Resource Resolver<br/>资源解析器]
            Adapters[Resource Adapters<br/>资源适配器]
        end
        
        subgraph "AI Shell - 统一意图服务"
            Intent[Unified Intent Service<br/>统一意图服务<br/>AI Shell]
            LLM[LLM Client<br/>LLM客户端]
        end
        
        subgraph "语义引擎"
            Semantic[Enterprise Semantic Engine<br/>企业语义引擎]
        end
        
        subgraph "EA服务 - 里程碑2"
            EAVec[EA Vectorization<br/>EA向量化]
            EAGraph[EA Knowledge Graph<br/>EA知识图谱]
            EAQuery[EA Hybrid Query<br/>EA混合查询]
        end
        
        subgraph "策略治理 - 里程碑3"
            Policy[Policy Engine<br/>策略引擎]
            Audit[Audit Logger<br/>审计日志]
            Gov[Governance Dashboard<br/>治理仪表板]
        end
        
        subgraph "自演进 - 里程碑4"
            Behavior[Behavior Collector<br/>行为收集器]
            Optimize[Optimization Engine<br/>优化引擎]
            Evolution[Evolution Manager<br/>自演进管理器]
            Scenario[Scenario Recommender<br/>场景推荐]
        end
    end
    
    subgraph "业务服务层"
        Agent[Agent Service<br/>智能体服务<br/>Port: 8010]
        Workflow[Workflow Engine<br/>工作流引擎<br/>Port: 8002]
        Knowledge[Knowledge Base<br/>知识库<br/>Port: 8004]
        Metadata[Metadata Service<br/>元数据服务<br/>Port: 8005]
        Auth[Auth Service<br/>认证服务<br/>Port: 8003]
        Chat[Chat Service<br/>聊天服务<br/>Port: 8006]
        MCP[MCP Gateway<br/>MCP工具网关<br/>Port: 8001]
    end
    
    subgraph "编排层"
        AgentOrch[Agent Orchestrator<br/>智能体编排<br/>Port: 8011]
        AgentReg[Agent Registry<br/>智能体注册<br/>Port: 8012]
        DAGOrch[DAG Orchestrator<br/>DAG编排<br/>Port: 8009]
    end
    
    subgraph "基础设施层"
        Postgres[(PostgreSQL 15<br/>关系数据库<br/>Port: 5432)]
        Redis[(Redis 7<br/>缓存<br/>Port: 6379)]
        Qdrant[(Qdrant<br/>向量数据库<br/>Port: 6333)]
        Neo4j[(Neo4j 5<br/>图数据库<br/>Port: 7474/7687)]
    end
    
    subgraph "集成层"
        SAP[SAP OData MCP<br/>SAP集成<br/>Port: 3001]
        SAPMeta[SAP Metadata Agent<br/>SAP元数据代理<br/>Port: 8015]
    end
    
    UI --> Gateway
    Gateway --> Registry
    Gateway --> Intent
    Gateway --> Auth
    
    Intent --> OS
    Intent --> Semantic
    Intent --> Policy
    Intent --> Behavior
    
    OS --> ResModel
    OS --> ResReg
    OS --> ResResolver
    OS --> Adapters
    
    Semantic --> EAVec
    Semantic --> EAGraph
    Semantic --> EAQuery
    
    EAVec --> Qdrant
    EAGraph --> Neo4j
    EAQuery --> EAVec
    EAQuery --> EAGraph
    
    Policy --> Audit
    Gov --> Audit
    Audit --> Postgres
    
    Behavior --> Postgres
    Optimize --> Behavior
    Evolution --> Optimize
    Scenario --> Behavior
    
    Intent --> Agent
    Intent --> Workflow
    Intent --> Knowledge
    Intent --> Metadata
    
    Adapters --> Agent
    Adapters --> Workflow
    Adapters --> Knowledge
    Adapters --> Metadata
    
    Agent --> AgentOrch
    Agent --> AgentReg
    Agent --> Workflow
    Agent --> MCP
    
    Workflow --> DAGOrch
    Workflow --> Postgres
    
    Metadata --> Postgres
    Metadata --> Qdrant
    Metadata --> Neo4j
    
    Knowledge --> Postgres
    Knowledge --> Qdrant
    
    SAP --> MCP
    SAPMeta --> Metadata
    
    Gateway --> Redis
    Agent --> Redis
    Metadata --> Redis
    Registry --> Redis
    Config --> Redis
```

---

## 🎯 功能架构图（详细版）

### 功能分层架构

```mermaid
graph TB
    subgraph "用户交互层"
        A1[自然语言输入]
        A2[Web界面]
        A3[API调用]
        A4[移动端]
    end
    
    subgraph "AI Shell层 - 统一意图服务"
        B1[意图识别<br/>LLM分析]
        B2[语义增强<br/>企业语义引擎]
        B3[EA增强<br/>企业架构查询]
        B4[资源解析<br/>Resource Resolver]
        B5[策略评估<br/>Policy Engine]
        B6[行为收集<br/>Behavior Collector]
        B7[动态融合<br/>Fusion Strategy]
    end
    
    subgraph "OS核心层 - 里程碑1"
        C1[资源模型<br/>Resource Model<br/>5种资源类型]
        C2[资源注册表<br/>Resource Registry<br/>注册/查询/发现]
        C3[资源解析器<br/>Resource Resolver<br/>意图→资源]
        C4[资源适配器<br/>Adapters<br/>4种适配器]
        C5[资源元数据<br/>Resource Metadata<br/>元数据管理]
    end
    
    subgraph "业务能力层"
        D1[智能体服务<br/>Agent Service<br/>多智能体协作]
        D2[工作流引擎<br/>Workflow Engine<br/>动态工作流]
        D3[知识库服务<br/>Knowledge Base<br/>文档管理]
        D4[元数据服务<br/>Metadata Service<br/>EA管理]
    end
    
    subgraph "企业架构层 - 里程碑2"
        E1[EA向量化<br/>EA Vectorization<br/>Qdrant存储]
        E2[EA知识图谱<br/>EA Knowledge Graph<br/>Neo4j存储]
        E3[EA混合查询<br/>EA Hybrid Query<br/>向量+图谱]
    end
    
    subgraph "治理层 - 里程碑3"
        F1[策略引擎<br/>Policy Engine<br/>5类策略规则]
        F2[审计日志<br/>Audit Logger<br/>完整审计]
        F3[治理仪表板<br/>Governance Dashboard<br/>4个角色视图]
        F4[策略管理API<br/>Policy Management API<br/>CRUD操作]
    end
    
    subgraph "自演进层 - 里程碑4"
        G1[行为收集<br/>Behavior Collector<br/>3类数据收集]
        G2[优化引擎<br/>Optimization Engine<br/>性能分析]
        G3[自演进管理<br/>Evolution Manager<br/>版本管理/A/B测试]
        G4[场景推荐<br/>Scenario Recommender<br/>自动化推荐]
    end
    
    A1 --> B1
    A2 --> B1
    A3 --> B1
    A4 --> B1
    
    B1 --> B2
    B2 --> B3
    B3 --> B4
    B4 --> B5
    B5 --> B6
    B6 --> B7
    
    B4 --> C1
    C1 --> C2
    C2 --> C3
    C3 --> C4
    C4 --> C5
    
    C4 --> D1
    C4 --> D2
    C4 --> D3
    C4 --> D4
    
    B3 --> E1
    E1 --> E2
    E2 --> E3
    E3 --> D4
    
    B5 --> F1
    F1 --> F2
    F2 --> F3
    F3 --> F4
    
    B6 --> G1
    G1 --> G2
    G2 --> G3
    G3 --> G4
```

---

## 🔄 数据流架构（详细版）

### 完整数据流

```mermaid
sequenceDiagram
    participant User as 用户
    participant Gateway as API Gateway
    participant Intent as 统一意图服务<br/>AI Shell
    participant OS as OS Core
    participant Semantic as 语义引擎
    participant EA as EA服务
    participant Policy as 策略引擎
    participant Behavior as 行为收集
    participant Agent as Agent Service
    participant Workflow as Workflow Engine
    participant DB as PostgreSQL
    participant Vector as Qdrant
    participant Graph as Neo4j
    
    User->>Gateway: 1. 自然语言输入<br/>"创建采购订单"
    Gateway->>Intent: 2. 转发请求
    
    Intent->>Intent: 3. LLM意图分析
    Intent->>Semantic: 4. 语义搜索
    Intent->>EA: 5. EA增强查询
    
    Semantic->>Vector: 6. 向量搜索
    Vector-->>Semantic: 7. 向量结果
    Semantic-->>Intent: 8. 语义结果
    
    EA->>Vector: 9. EA向量查询
    EA->>Graph: 10. EA图谱查询
    Vector-->>EA: 11. EA向量结果
    Graph-->>EA: 12. EA图谱结果
    EA-->>Intent: 13. EA增强结果
    
    Intent->>OS: 14. 资源解析
    OS->>DB: 15. 查询资源
    DB-->>OS: 16. 资源数据
    OS-->>Intent: 17. 资源操作
    
    Intent->>Policy: 18. 策略评估
    Policy->>DB: 19. 查询策略
    DB-->>Policy: 20. 策略数据
    Policy-->>Intent: 21. 评估结果
    
    Intent->>Behavior: 22. 收集行为数据
    Behavior->>DB: 23. 存储行为数据
    
    Intent->>Agent: 24. 执行操作
    Agent->>Workflow: 25. 创建工作流
    Workflow->>DB: 26. 存储工作流
    Workflow-->>Agent: 27. 执行结果
    Agent-->>Intent: 28. 执行结果
    
    Intent-->>Gateway: 29. 返回结果
    Gateway-->>User: 30. 响应
```

---

## 📊 技术架构详细说明

### 技术栈分层

#### 1. 前端技术栈
- **框架**: Next.js 14
- **语言**: TypeScript
- **UI库**: React
- **状态管理**: React Context / Zustand
- **HTTP客户端**: Fetch API / Axios

#### 2. API网关技术栈
- **框架**: FastAPI
- **服务器**: Uvicorn
- **认证**: JWT
- **限流**: Redis-based rate limiting
- **熔断**: Circuit breaker pattern

#### 3. 核心服务技术栈
- **框架**: FastAPI
- **异步**: asyncio / aiohttp
- **ORM**: SQLAlchemy
- **数据验证**: Pydantic
- **LLM**: LangChain + OpenAI API

#### 4. 数据存储技术栈
- **关系数据库**: PostgreSQL 15 + SQLAlchemy
- **缓存**: Redis 7
- **向量数据库**: Qdrant + sentence-transformers
- **图数据库**: Neo4j 5 + Cypher

#### 5. 工作流技术栈
- **框架**: LangGraph
- **执行引擎**: LangChain
- **状态管理**: PostgreSQL

#### 6. 容器化技术栈
- **容器**: Docker
- **编排**: Docker Compose
- **网络**: Docker Network (enterprise-ai-network)

---

## 🔐 安全架构详细说明

### 安全层次

```mermaid
graph TB
    subgraph "网络层安全"
        N1[防火墙规则]
        N2[端口限制]
        N3[Docker网络隔离]
    end
    
    subgraph "认证授权层"
        A1[Auth Service<br/>JWT认证]
        A2[SSO单点登录]
        A3[角色管理]
        A4[权限管理]
    end
    
    subgraph "API安全层"
        API1[API Gateway<br/>统一入口]
        API2[请求限流]
        API3[请求验证]
        API4[HTTPS/TLS]
    end
    
    subgraph "策略层"
        P1[Policy Engine<br/>策略评估]
        P2[基于角色的策略]
        P3[基于资源的策略]
        P4[基于操作的策略]
    end
    
    subgraph "审计层"
        AU1[Audit Logger<br/>操作审计]
        AU2[日志完整性]
        AU3[日志加密]
        AU4[日志备份]
    end
    
    subgraph "数据安全层"
        D1[数据加密<br/>传输加密]
        D2[数据脱敏]
        D3[访问控制]
        D4[数据备份]
    end
    
    N1 --> A1
    A1 --> API1
    API1 --> P1
    P1 --> AU1
    AU1 --> D1
```

---

## 📈 性能架构

### 性能优化策略

```mermaid
graph LR
    subgraph "缓存层"
        C1[Redis缓存<br/>查询结果]
        C2[内存缓存<br/>LLM响应]
        C3[向量缓存<br/>嵌入向量]
    end
    
    subgraph "异步处理"
        A1[异步IO<br/>asyncio]
        A2[并发请求<br/>aiohttp]
        A3[后台任务<br/>Celery可选]
    end
    
    subgraph "数据库优化"
        D1[索引优化<br/>PostgreSQL]
        D2[连接池<br/>SQLAlchemy]
        D3[查询优化<br/>SQL优化]
    end
    
    subgraph "向量搜索优化"
        V1[向量索引<br/>Qdrant]
        V2[批量查询<br/>批量向量化]
        V3[近似搜索<br/>ANN算法]
    end
    
    C1 --> A1
    A1 --> D1
    D1 --> V1
```

---

## 🎯 部署架构

### 部署拓扑详细说明

```
生产环境部署架构
├── 服务器: 43.143.139.197
│   ├── Docker Compose
│   │   ├── 27个服务容器
│   │   ├── 统一网络: enterprise-ai-network
│   │   └── 数据卷管理
│   │
│   ├── 数据持久化
│   │   ├── PostgreSQL数据卷
│   │   ├── Redis数据卷
│   │   ├── Qdrant数据卷
│   │   └── Neo4j数据卷
│   │
│   └── 代码部署
│       ├── /opt/enterprise-ai-platform
│       ├── os-core/ (里程碑1-4代码)
│       ├── services/ (核心服务)
│       └── tests/ (测试文件)
│
└── 本地开发环境
    ├── Docker Desktop
    ├── 本地代码
    └── 测试环境
```

---

## 📋 API端点清单

### API Gateway端点

**基础端点**:
- `GET /health` - 健康检查
- `GET /api/docs` - API文档

**统一意图端点**:
- `POST /api/v1/unified/process` - 统一意图处理（在Agent Service）

**策略管理端点**:
- `GET /api/v1/policies` - 获取策略列表
- `POST /api/v1/policies` - 创建策略
- `PUT /api/v1/policies/{id}` - 更新策略
- `DELETE /api/v1/policies/{id}` - 删除策略
- `POST /api/v1/policies/{id}/enable` - 启用策略
- `POST /api/v1/policies/{id}/disable` - 禁用策略
- `POST /api/v1/policies/load-from-config` - 从配置加载策略

**治理端点**:
- `GET /api/v1/governance/dashboard` - 获取治理仪表板
- `GET /api/v1/governance/metrics` - 获取治理指标
- `GET /api/v1/audit/events` - 查询审计事件
- `GET /api/v1/audit/reports` - 生成审计报告

### Agent Service端点

**基础端点**:
- `GET /api/v1/health` - 健康检查
- `GET /docs` - API文档

**统一意图端点**:
- `POST /api/v1/unified/process` - 统一意图处理
- `GET /api/v1/unified/process` - 统一意图处理（SSE流式）

**智能体端点**:
- `POST /api/v1/agents/{agent_id}/execute` - 执行智能体
- `GET /api/v1/agents` - 获取智能体列表

---

## 🔄 工作流架构

### 工作流执行流程

```mermaid
graph LR
    A[用户意图] --> B[意图识别]
    B --> C[资源解析]
    C --> D[策略评估]
    D --> E{是否允许}
    E -->|允许| F[生成工作流]
    E -->|拒绝| G[返回拒绝]
    F --> H[工作流执行]
    H --> I[Agent执行]
    I --> J[结果收集]
    J --> K[行为记录]
    K --> L[返回结果]
```

---

## 📊 数据模型架构

### 核心数据模型关系

```mermaid
erDiagram
    Resource ||--o{ ResourceOperation : "has"
    Resource ||--o{ ResourceMetadata : "has"
    Resource ||--o{ ResourceRelationship : "has"
    
    UnifiedIntentResult ||--o{ Resource : "resolves_to"
    UnifiedIntentResult ||--o{ ResourceOperation : "generates"
    UnifiedIntentResult ||--o{ PolicyEvaluationResult : "evaluated_by"
    
    PolicyRule ||--o{ PolicyEvaluationResult : "evaluates"
    PolicyRule ||--o{ PolicyAction : "triggers"
    
    AuditEvent ||--o{ ResourceOperation : "logs"
    AuditEvent ||--o{ PolicyEvaluationResult : "logs"
    
    BehaviorEvent ||--o{ IntentCallData : "collects"
    BehaviorEvent ||--o{ WorkflowExecutionData : "collects"
    BehaviorEvent ||--o{ ResourceUsageData : "collects"
    
    OptimizationRecommendation ||--o{ EvolutionVersion : "creates"
    EvolutionVersion ||--o{ ABTestResult : "tests"
```

---

**文档版本**: 1.0.0  
**生成时间**: 2025-12-16


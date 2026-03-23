# SAP元数据智能体

SAP ERP系统元数据管理和发现智能体，支持通过OData服务和直接数据库查询两种方式构建完整的SAP元数据。

## 功能特性

- 🔍 **多源数据发现**：支持OData服务和直接数据库查询
- 📊 **数据资产管理**：自动发现和注册SAP数据资产
- 🏢 **业务实体提取**：识别和分类SAP业务实体
- 🔄 **业务流程分析**：分析SAP业务流程和数据血缘
- 🧠 **语义索引构建**：为元数据构建语义索引支持智能搜索
- 🔌 **可扩展架构**：支持其他ERP系统复用

## 架构设计

```
sap-metadata-agent/
├── src/
│   ├── core/                    # 核心业务逻辑
│   │   ├── sap_data_asset_discoverer.py      # 数据资产发现器
│   │   ├── sap_business_entity_extractor.py   # 业务实体提取器
│   │   ├── sap_business_process_analyzer.py   # 业务流程分析器
│   │   ├── sap_semantic_index_builder.py      # 语义索引构建器
│   │   └── sap_metadata_orchestrator.py       # 元数据编排器
│   ├── services/                # 服务层
│   │   ├── sap_database_client.py             # SAP数据库客户端
│   │   ├── sap_mcp_client.py                  # SAP MCP客户端
│   │   └── metadata_client.py                 # 元数据服务客户端
│   ├── models/                 # 数据模型
│   │   └── sap_metadata_models.py             # SAP元数据模型
│   ├── collectors/             # 采集器
│   │   └── sap_metadata_collector.py          # SAP元数据采集器
│   ├── routes/                 # API路由
│   │   └── sap_metadata_routes.py             # SAP元数据API
│   └── main.py                 # 应用入口
├── tests/                      # 测试
├── requirements.txt            # 依赖
├── Dockerfile                  # Docker配置
└── docker-compose.yml          # Docker Compose配置
```

## 快速开始

### 环境变量配置

```bash
# SAP连接配置
SAP_DB_HOST=your-sap-db-host
SAP_DB_PORT=33015
SAP_DB_NAME=your-database
SAP_DB_USER=your-user
SAP_DB_PASSWORD=your-password
SAP_DB_TYPE=hdb  # hdb (HANA) 或 mssql (SQL Server)

# OData服务配置（可选）
SAP_ODATA_BASE_URL=https://your-sap-server:8000
SAP_ODATA_USER=your-user
SAP_ODATA_PASSWORD=your-password

# 服务集成
MCP_GATEWAY_URL=http://mcp-gateway:8001
METADATA_SERVICE_URL=http://metadata-service:8005
KNOWLEDGE_BASE_URL=http://knowledge-base:8004
AGENT_SERVICE_URL=http://agent-service:8010
```

### 启动服务

```bash
docker-compose up -d sap-metadata-agent
```

## API文档

### 发现SAP元数据

```bash
POST /api/sap-metadata/discover
```

### 获取SAP数据资产

```bash
GET /api/sap-metadata/assets?asset_type=business_object&domain=sales
```

### 获取业务流程

```bash
GET /api/sap-metadata/processes/{process_name}
```

### 语义搜索

```bash
POST /api/sap-metadata/search/semantic
{
  "query": "销售订单",
  "domain": "sales"
}
```

## 扩展性

本智能体设计为可扩展架构，支持其他ERP系统：

1. 实现ERP特定的数据库客户端
2. 实现ERP特定的业务实体提取器
3. 复用核心编排器和采集器框架



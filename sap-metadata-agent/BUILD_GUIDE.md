# SAP元数据构建指南

## 快速开始

### 1. 启动服务

```bash
# 启动SAP元数据智能体
docker-compose up -d sap-metadata-agent

# 等待服务启动（约10-30秒）
docker-compose logs -f sap-metadata-agent
```

### 2. 构建SAP元数据

#### 方式1: 仅从OData服务发现（推荐，无需数据库连接）

```bash
curl -X POST http://localhost:8015/api/sap-metadata/discover \
  -H "Content-Type: application/json" \
  -d '{
    "include_database": false,
    "include_odata": true,
    "build_semantic_index": true,
    "sync_to_metadata_service": true
  }'
```

#### 方式2: 从数据库和OData服务发现（需要SAP数据库连接）

```bash
# 首先配置.env文件中的SAP数据库连接信息
# SAP_DB_TYPE=hdb
# SAP_DB_HOST=your-sap-host
# SAP_DB_PORT=33015
# SAP_DB_NAME=your-database
# SAP_DB_USER=your-user
# SAP_DB_PASSWORD=your-password

curl -X POST http://localhost:8015/api/sap-metadata/discover \
  -H "Content-Type: application/json" \
  -d '{
    "include_database": true,
    "include_odata": true,
    "build_semantic_index": true,
    "sync_to_metadata_service": true
  }'
```

### 3. 验证结果

```bash
# 检查发现的数据资产
curl http://localhost:8015/api/sap-metadata/assets

# 检查业务实体
curl http://localhost:8015/api/sap-metadata/entities

# 检查业务流程
curl http://localhost:8015/api/sap-metadata/processes

# 验证是否同步到metadata-service
curl http://localhost:8005/api/data-assets?source_system=SAP
```

## 前置条件

### 必需服务

1. **MCP Gateway** (端口8001)
   - 用于访问SAP OData MCP服务器

2. **Metadata Service** (端口8005)
   - 用于存储发现的元数据

3. **SAP MCP Server** (可选)
   - 如果要从OData服务发现，需要SAP MCP服务器运行

### 可选配置

1. **SAP数据库连接** (可选)
   - 如果要从数据库直接发现，需要配置SAP数据库连接信息
   - 支持HANA (hdb) 和 SQL Server (mssql)

2. **Knowledge Base** (可选)
   - 如果启用语义索引，需要Knowledge Base服务运行

## 常见问题

### 1. 发现结果为0

**可能原因：**
- SAP MCP服务器未启动或未配置
- MCP Gateway无法连接到SAP MCP服务器
- SAP系统连接配置错误

**解决方法：**
```bash
# 检查SAP MCP服务器状态
docker-compose ps sap-mcp-server

# 检查MCP Gateway日志
docker-compose logs mcp-gateway

# 检查SAP元数据智能体日志
docker-compose logs sap-metadata-agent
```

### 2. 数据库连接失败

**可能原因：**
- SAP数据库连接信息配置错误
- 网络无法访问SAP数据库
- 数据库驱动未安装

**解决方法：**
- 检查.env文件中的SAP数据库配置
- 确保Docker容器可以访问SAP数据库
- 如果不需要数据库发现，设置`include_database: false`

### 3. 同步到metadata-service失败

**可能原因：**
- Metadata Service未运行
- 数据格式不兼容
- 网络连接问题

**解决方法：**
```bash
# 检查Metadata Service状态
docker-compose ps metadata-service

# 查看同步错误日志
docker-compose logs sap-metadata-agent | grep -i sync
```

## 下一步

构建完成后，SAP元数据将可用于：
1. **意图识别系统** - 基于SAP元数据理解用户意图
2. **任务编排** - 根据SAP业务流程自动编排任务
3. **语义搜索** - 通过语义索引搜索SAP相关资源
4. **数据血缘分析** - 分析SAP数据之间的关系

## API文档

详细API文档请访问：http://localhost:8015/docs



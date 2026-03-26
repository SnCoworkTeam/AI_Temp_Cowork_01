# SAP数据库元数据发现指南

## 概述

除了从OData服务发现元数据外，系统还支持直接连接SAP ERP数据库，发现所有数据库表的元数据。这样可以获得更完整的SAP元数据覆盖。

## 支持的数据库类型

- **SAP HANA** (`hdb`) - SAP HANA数据库
- **SQL Server** (`mssql`) - SAP on SQL Server

## 配置步骤

### 1. 配置环境变量

在 `.env` 文件或 Docker Compose 配置中添加以下环境变量：

```bash
# SAP数据库连接配置
SAP_DB_TYPE=hdb                    # 数据库类型: 'hdb' (HANA) 或 'mssql' (SQL Server)
SAP_DB_HOST=your-sap-db-host       # 数据库主机地址
SAP_DB_PORT=33015                  # 数据库端口 (HANA默认33015, SQL Server默认1433)
SAP_DB_NAME=your-database          # 数据库名称
SAP_DB_USER=your-username          # 数据库用户名
SAP_DB_PASSWORD=your-password      # 数据库密码
```

### 2. 配置示例

#### SAP HANA 示例
```bash
SAP_DB_TYPE=hdb
SAP_DB_HOST=sap-hana.example.com
SAP_DB_PORT=33015
SAP_DB_NAME=SYSTEMDB
SAP_DB_USER=SAPR3
SAP_DB_PASSWORD=your-password
```

#### SQL Server 示例
```bash
SAP_DB_TYPE=mssql
SAP_DB_HOST=sap-sql.example.com
SAP_DB_PORT=1433
SAP_DB_NAME=SAP
SAP_DB_USER=sa
SAP_DB_PASSWORD=your-password
```

### 3. 重启服务

配置完成后，重启 sap-metadata-agent 服务：

```bash
docker-compose restart sap-metadata-agent
```

### 4. 验证连接

检查服务日志，确认数据库连接成功：

```bash
docker-compose logs sap-metadata-agent | grep -i "database"
```

应该看到类似以下日志：
```
SAP database client connected successfully
```

## 使用方法

### 方式1: 仅从数据库发现

```bash
curl -X POST http://localhost:8015/api/sap-metadata/discover \
  -H "Content-Type: application/json" \
  -d '{
    "include_database": true,
    "include_odata": false,
    "build_semantic_index": true,
    "sync_to_metadata_service": true
  }'
```

### 方式2: 同时从数据库和OData发现（推荐）

```bash
curl -X POST http://localhost:8015/api/sap-metadata/discover \
  -H "Content-Type: application/json" \
  -d '{
    "include_database": true,
    "include_odata": true,
    "build_semantic_index": true,
    "sync_to_metadata_service": true
  }'
```

### 方式3: 使用构建脚本

使用改进的构建脚本，自动同时发现数据库和OData：

```bash
cd sap-metadata-agent
python build_with_database.py
```

## 发现的内容

从数据库发现时，系统会：

1. **发现所有表**
   - 扫描所有schema（跳过系统schema如SYS、SYSTEM）
   - 获取表结构信息（列、数据类型、约束等）
   - 获取主键和外键关系
   - 获取索引信息

2. **提取业务实体**
   - 根据表名模式识别业务实体（客户、供应商、物料等）
   - 提取关键字段信息
   - 建立实体关系

3. **分析业务流程**
   - 基于表之间的关系分析业务流程
   - 识别订单到现金、采购到付款等流程

4. **分类资产类型**
   - 主数据表（Master Data）
   - 事务数据表（Transaction Data）
   - 配置表（Configuration）

## 表分类规则

系统会根据SAP表命名规则自动分类：

- **主数据表**: 以K、LFA、M开头的表（如KNA1客户、LFA1供应商、MARA物料）
- **事务数据表**: 以V、E开头的表（如VBAK销售订单、EKKO采购订单）
- **配置表**: 以T开头的表（如T001公司代码、T001W工厂）

## 注意事项

1. **数据库权限**
   - 确保数据库用户有读取表结构和数据的权限
   - 建议使用只读账户，避免误操作

2. **网络连接**
   - 确保Docker容器能够访问SAP数据库
   - 检查防火墙规则

3. **性能考虑**
   - 大型SAP系统可能有数千个表，发现过程可能需要较长时间
   - 建议分批处理或使用limit参数

4. **数据量**
   - 获取表行数可能需要时间，系统会跳过无法访问的表
   - 某些系统表可能无法访问，这是正常的

## 故障排查

### 问题1: 无法连接数据库

**错误**: `Failed to connect to SAP database`

**解决方案**:
1. 检查数据库主机和端口是否正确
2. 检查网络连接：`docker exec enterprise-ai-sap-metadata-agent ping your-db-host`
3. 检查数据库服务是否运行
4. 验证用户名和密码是否正确

### 问题2: 连接字符串错误

**错误**: `Unsupported database type` 或连接字符串格式错误

**解决方案**:
1. 确认 `SAP_DB_TYPE` 设置为 `hdb` 或 `mssql`
2. 检查连接字符串格式是否正确
3. 对于SQL Server，确保已安装ODBC驱动

### 问题3: 权限不足

**错误**: `Access denied` 或 `Permission denied`

**解决方案**:
1. 检查数据库用户权限
2. 确保用户有SELECT权限
3. 对于HANA，确保用户有读取系统表的权限

### 问题4: 表发现不完整

**可能原因**:
1. 某些schema被跳过（系统schema）
2. 某些表无法访问（权限问题）
3. 表数量太多，需要分批处理

**解决方案**:
1. 检查日志中的警告信息
2. 使用limit和offset参数分批处理
3. 检查是否有权限问题

## 性能优化

1. **分批处理**
   - 对于大型系统，使用limit参数分批处理
   - 每批处理100-200个表

2. **并行处理**
   - 系统使用线程池并行处理表
   - 可以通过调整 `max_workers` 参数优化

3. **跳过系统表**
   - 系统自动跳过SYS、SYSTEM等系统schema
   - 可以手动指定要处理的schema

## 示例输出

```json
{
  "data_assets": [
    {
      "name": "sap_table_kna1",
      "display_name": "客户主数据",
      "description": "SAP数据库表: KNA1",
      "asset_type": "master_data",
      "sap_table_name": "KNA1",
      "sap_module": "sales",
      "schema_info": {
        "fields": [
          {"name": "KUNNR", "type": "VARCHAR(10)", "nullable": false},
          {"name": "NAME1", "type": "VARCHAR(35)", "nullable": true}
        ],
        "primary_key": ["KUNNR"],
        "foreign_keys": []
      },
      "tags": ["SAP", "database", "table", "KNA1"],
      "classification": "sap_table"
    }
  ],
  "tables_discovered": 1500,
  "odata_services_discovered": 0
}
```

## 相关文档

- [构建指南](./BUILD_GUIDE.md)
- [分批构建指南](./BATCH_BUILD_GUIDE.md)
- [API文档](./README.md)




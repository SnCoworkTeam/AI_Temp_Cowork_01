# SAP ERP表查询工具设置指南

## 工具说明

`sap_erp_table_query` 工具用于通过RFC直接连接SAP ERP（S4 HANA）系统并查询表数据。

## 功能特性

- ✅ 直接RFC连接SAP ERP系统
- ✅ 查询SAP表数据（如BKPF、VBAK等）
- ✅ 支持字段选择
- ✅ 支持WHERE条件过滤
- ✅ 支持分页（max_rows）
- ✅ 自动注册到元数据服务

## 安装依赖

### 1. 安装pyRFC库

```bash
pip install pyrfc
```

**注意**：pyRFC需要SAP NWRFC SDK。请确保已安装：
- Windows: 下载并安装SAP NWRFC SDK
- Linux: 安装SAP NWRFC SDK库文件

### 2. 配置SAP连接参数

设置环境变量：

```bash
export SAP_USER=admin
export SAP_PASSWORD=ad@kf29!()G
export SAP_HOST=10.24.49.128
export SAP_SYSNR=00
export SAP_CLIENT=100
```

或在 `.env` 文件中配置：

```env
SAP_USER=admin
SAP_PASSWORD=ad@kf29!()G
SAP_HOST=10.24.49.128
SAP_SYSNR=00
SAP_CLIENT=100
```

## 工具注册

### 自动注册

工具会在MCP Gateway启动时自动注册到内存、数据库和元数据服务。

### 手动注册

如果需要手动注册，运行：

```bash
cd mcp-gateway
python sync_sap_erp_table_tool.py
```

## 测试工具

### 测试查询BKPF表

```bash
cd mcp-gateway
python test_sap_erp_table_tool.py
```

测试脚本会：
1. 查询BKPF表的前10条记录（指定字段）
2. 查询BKPF表（带WHERE条件：BUKRS = '1000'）
3. 查询BKPF表（所有字段，前3条）

### 通过API测试

```bash
curl -X POST http://localhost:8001/api/tools/sap_erp_table_query/execute \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "table_name": "BKPF",
      "fields": ["BELNR", "GJAHR", "BUKRS", "BLART", "BUDAT"],
      "max_rows": 10
    }
  }'
```

## 使用示例

### 示例1：查询BKPF表（会计凭证表）

```python
parameters = {
    "table_name": "BKPF",
    "fields": ["BELNR", "GJAHR", "BUKRS", "BLART", "BUDAT", "USNAM"],
    "max_rows": 10
}

result = await execute_query_sap_table(parameters)
```

### 示例2：带WHERE条件查询

```python
parameters = {
    "table_name": "BKPF",
    "fields": ["BELNR", "GJAHR", "BUKRS"],
    "where_clause": "BUKRS = '1000' AND GJAHR = '2024'",
    "max_rows": 100
}

result = await execute_query_sap_table(parameters)
```

### 示例3：查询所有字段

```python
parameters = {
    "table_name": "BKPF",
    "max_rows": 50
}

result = await execute_query_sap_table(parameters)
```

## 参数说明

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| table_name | string | ✅ | SAP表名（如：BKPF、VBAK、MARA） |
| fields | array | ❌ | 要查询的字段列表。不指定则查询所有字段 |
| where_clause | string | ❌ | WHERE条件（ABAP语法），如：`BUKRS = '1000'` |
| max_rows | integer | ❌ | 最大返回行数（默认100，最大10000） |
| order_by | string | ❌ | 排序字段（可选） |

## 返回格式

```json
{
  "success": true,
  "table_name": "BKPF",
  "row_count": 10,
  "fields": ["BELNR", "GJAHR", "BUKRS", "BLART", "BUDAT"],
  "data": [
    {
      "BELNR": "0000000001",
      "GJAHR": "2024",
      "BUKRS": "1000",
      "BLART": "SA",
      "BUDAT": "20240101"
    }
  ],
  "query_info": {
    "where_clause": null,
    "max_rows": 10,
    "order_by": null
  }
}
```

## 常见SAP表

- **BKPF**: 会计凭证表（Accounting Document Header）
- **BSEG**: 会计凭证行项目表（Accounting Document Line Items）
- **VBAK**: 销售订单表（Sales Order Header）
- **VBAP**: 销售订单行项目表（Sales Order Line Items）
- **MARA**: 物料主数据表（Material Master）
- **KNA1**: 客户主数据表（Customer Master）
- **LFA1**: 供应商主数据表（Vendor Master）

## 注意事项

1. **pyRFC安装**：需要先安装SAP NWRFC SDK
2. **连接参数**：确保SAP系统可访问，防火墙允许RFC连接
3. **权限**：确保SAP用户有查询表的权限
4. **性能**：大表查询建议使用WHERE条件限制，避免查询过多数据
5. **字符编码**：SAP表数据使用UTF-8编码

## 故障排查

### 问题1：pyRFC未安装

**错误**：`ImportError: pyRFC library not installed`

**解决**：
```bash
pip install pyrfc
```

### 问题2：连接失败

**错误**：`Failed to connect to SAP ERP`

**检查**：
1. SAP系统是否运行
2. 网络是否可达（ping 10.24.49.128）
3. 用户名密码是否正确
4. 客户端编号是否正确

### 问题3：表不存在

**错误**：`Table BKPF does not exist`

**解决**：
1. 确认表名拼写正确（SAP表名通常是大写）
2. 确认用户有权限访问该表
3. 确认表在当前客户端中存在

## 元数据注册

工具会自动注册到：
- ✅ MCP Gateway工具注册表（内存）
- ✅ 数据库（mcp_tools表）
- ✅ 元数据服务（作为数据资产）

注册后可以在：
- 后台管理界面查看工具信息
- 元数据服务中搜索工具
- 通过API查询工具元数据


# SAP ERP表查询工具快速开始

## 已完成的工作

✅ **工具创建**：`sap_erp_table_query` 工具已创建
✅ **工具注册**：已添加到 `tool_registry.py`，启动时自动注册
✅ **元数据同步**：启动时会自动同步到数据库和元数据服务
✅ **测试脚本**：已创建测试脚本 `test_sap_erp_table_tool.py`

## 快速开始

### 1. 安装pyRFC（如果未安装）

```bash
pip install pyrfc
```

**注意**：需要先安装SAP NWRFC SDK

### 2. 配置SAP连接参数

创建或编辑 `.env` 文件：

```env
SAP_USER=admin
SAP_PASSWORD=ad@kf29!()G
SAP_HOST=10.24.49.128
SAP_SYSNR=00
SAP_CLIENT=100
```

### 3. 启动MCP Gateway

工具会在启动时自动注册到：
- ✅ 内存（ToolRegistry）
- ✅ 数据库（mcp_tools表）
- ✅ 元数据服务（作为数据资产）

### 4. 测试查询BKPF表

```bash
cd mcp-gateway
python test_sap_erp_table_tool.py
```

## 工具信息

**工具名称**：`sap_erp_table_query`

**功能**：通过RFC直接连接SAP ERP（S4 HANA）并查询表数据

**连接信息**：
- 主机：10.24.49.128
- 客户端：100
- 系统编号：00
- 用户：admin

## 使用示例

### 通过API调用

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

### 通过MCP工具智能体调用

在对话界面输入：
```
查询SAP ERP的BKPF表，返回前10条记录，字段包括BELNR、GJAHR、BUKRS
```

系统会自动：
1. 识别为工具执行任务
2. 选择 `sap_erp_table_query` 工具
3. 提取参数
4. 执行查询
5. 返回结果

## 验证工具注册

### 检查工具是否在内存中注册

```bash
curl http://localhost:8001/api/tools/list | grep sap_erp_table_query
```

### 检查工具是否在数据库中

```sql
SELECT * FROM mcp_tools WHERE name = 'sap_erp_table_query';
```

### 检查工具是否在元数据服务中

```bash
curl http://localhost:8080/api/v1/metadata/data-assets?search=sap_erp_table_query
```

## 下一步

1. **安装pyRFC**：确保已安装pyRFC和SAP NWRFC SDK
2. **配置连接**：设置SAP连接参数
3. **启动服务**：启动MCP Gateway，工具会自动注册
4. **测试查询**：运行测试脚本验证BKPF表查询

## 注意事项

⚠️ **pyRFC依赖**：需要先安装SAP NWRFC SDK才能使用pyRFC
⚠️ **网络连接**：确保可以访问SAP服务器（10.24.49.128）
⚠️ **权限**：确保SAP用户有查询表的权限


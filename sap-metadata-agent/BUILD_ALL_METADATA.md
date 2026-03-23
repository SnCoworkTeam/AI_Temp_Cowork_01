# SAP元数据完整构建指南

## 概述

本指南说明如何使用自动化脚本构建所有SAP元数据，确保所有元数据都被完整构建。

## 功能特性

- ✅ **自动检测总服务数**：无需手动配置，自动从SAP系统获取服务总数
- ✅ **分批处理**：自动将大量服务分批处理，避免超时和资源压力
- ✅ **进度保存**：支持断点续传，构建过程中断后可继续
- ✅ **错误重试**：自动重试失败的批次，提高成功率
- ✅ **语义索引构建**：所有批次完成后自动构建语义索引
- ✅ **同步验证**：验证所有元数据是否成功同步到metadata-service
- ✅ **详细报告**：提供完整的构建统计和进度报告

## 使用方法

### 方法1: PowerShell脚本（Windows）

```powershell
cd sap-metadata-agent
.\build_all_metadata.ps1
```

### 方法2: Python脚本（跨平台）

```bash
cd sap-metadata-agent
python build_all_metadata.py
```

或使用Python 3：

```bash
python3 build_all_metadata.py
```

## 构建流程

脚本会自动执行以下步骤：

1. **检测总服务数**
   - 自动调用API获取SAP OData服务总数
   - 如果无法检测，使用默认值348

2. **分批处理所有服务**
   - 每批处理10个服务（可配置）
   - 自动处理所有批次直到完成
   - 每批都会：
     - 发现数据资产
     - 提取业务实体
     - 分析业务流程
     - 同步到metadata-service

3. **构建语义索引**
   - 所有批次完成后，自动构建语义索引
   - 将元数据索引到知识库

4. **验证同步状态**
   - 检查metadata-service中的数据资产数量
   - 检查metadata-service中的业务实体数量
   - 验证同步是否成功

## 进度跟踪

脚本会在当前目录创建 `build_status.json` 文件保存进度：

```json
{
  "lastOffset": 100,
  "batchSize": 10,
  "completedBatches": 10,
  "totalAssets": 2500,
  "totalEntities": 150,
  "totalProcesses": 3,
  "failedBatches": 0,
  "timestamp": "2024-01-01 12:00:00"
}
```

如果构建过程中断，重新运行脚本会自动从上次停止的地方继续。

## 配置参数

可以在脚本中修改以下参数：

- `BATCH_SIZE`: 每批处理的服务数量（默认：10）
- `MAX_RETRIES`: 失败重试次数（默认：3）
- `RETRY_DELAY`: 重试延迟（秒，默认：5）
- `REQUEST_TIMEOUT`: 请求超时时间（秒，默认：600）

## 输出示例

```
========================================
SAP元数据完整构建
========================================
总服务数: 348
批次大小: 10
总批次数: 35
开始时间: 2024-01-01 12:00:00
========================================

[1/35] 处理批次 0 (offset=0, limit=10)...
  ✅ 成功完成 (耗时: 45.2秒)
     发现数据资产: 250
     发现业务实体: 15
     发现业务流程: 1
     同步数据资产: 250/250 (失败: 0)
     同步业务实体: 15/15 (失败: 0)

...

========================================
批次构建完成
========================================
总批次数: 35
成功批次: 35
失败批次: 0
累计数据资产: 20316
累计业务实体: 150
累计业务流程: 3
总耗时: 25.5 分钟
========================================

开始构建语义索引...
  ✅ 语义索引构建完成
     已索引文档: 20469
     失败: 0

验证元数据同步状态...
  ✅ 元数据服务中的数据资产: 20316
  ✅ 元数据服务中的业务实体: 150

========================================
构建完成报告
========================================
数据资产发现: 20316
业务实体提取: 150
业务流程分析: 3
语义索引构建: ✅ 完成
元数据服务同步:
  - 数据资产: 20316
  - 业务实体: 150
结束时间: 2024-01-01 12:30:00
========================================

✅ 所有元数据构建成功！
```

## 故障排查

### 问题1: 无法连接到API

**错误**: `Connection refused` 或 `Timeout`

**解决方案**:
1. 确保sap-metadata-agent服务正在运行：
   ```bash
   docker-compose ps sap-metadata-agent
   ```
2. 检查服务健康状态：
   ```bash
   curl http://localhost:8015/api/sap-metadata/health
   ```

### 问题2: 服务数为0

**错误**: 检测到的总服务数为0

**解决方案**:
1. 检查SAP MCP服务器是否运行：
   ```bash
   docker-compose ps sap-mcp-server
   ```
2. 检查SAP连接配置：
   ```bash
   docker-compose logs sap-mcp-server | grep -i error
   ```

### 问题3: 同步失败

**错误**: 数据资产或业务实体同步失败

**解决方案**:
1. 检查metadata-service是否运行：
   ```bash
   docker-compose ps metadata-service
   ```
2. 检查数据库连接：
   ```bash
   docker-compose logs metadata-service | grep -i database
   ```

### 问题4: 构建中断

**解决方案**:
- 脚本支持断点续传，直接重新运行脚本即可
- 进度保存在 `build_status.json` 文件中
- 脚本会自动从上次停止的地方继续

## 手动构建

如果需要手动构建特定批次，可以使用API：

```bash
curl -X POST http://localhost:8015/api/sap-metadata/discover \
  -H "Content-Type: application/json" \
  -d '{
    "include_database": false,
    "include_odata": true,
    "build_semantic_index": false,
    "sync_to_metadata_service": true,
    "limit": 10,
    "offset": 0
  }'
```

## 检查构建状态

使用API检查当前构建状态：

```bash
curl http://localhost:8015/api/sap-metadata/build-status
```

返回示例：

```json
{
  "total_services": 348,
  "synced_assets": 20316,
  "synced_entities": 150,
  "build_progress": {
    "services_processed": 348,
    "services_total": 348,
    "percentage": 100.0
  },
  "status": "ready"
}
```

## 注意事项

1. **构建时间**: 完整构建所有348个服务可能需要20-30分钟
2. **资源使用**: 构建过程会消耗一定的CPU和内存资源
3. **网络连接**: 确保能够访问SAP系统和所有相关服务
4. **数据库空间**: 确保metadata-service数据库有足够的空间存储元数据

## 相关文档

- [分批构建指南](./BATCH_BUILD_GUIDE.md)
- [构建状态报告](./BUILD_STATUS.md)
- [API文档](./README.md)




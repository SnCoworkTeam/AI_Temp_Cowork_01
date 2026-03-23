# SAP元数据分批构建指南

## 概述

SAP元数据构建支持分批处理，避免一次性处理所有348个服务导致超时或资源压力。

## 使用方法

### API参数

- `limit`: 每批处理的服务数量（建议10-20）
- `offset`: 起始偏移量（从0开始）
- `include_odata`: 是否从OData服务发现（默认true）
- `include_database`: 是否从数据库发现（默认false）
- `build_semantic_index`: 是否构建语义索引（默认true，可设为false加快速度）
- `sync_to_metadata_service`: 是否同步到元数据服务（默认true）

### 构建示例

#### 第一批（服务0-9）
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

#### 第二批（服务10-19）
```bash
curl -X POST http://localhost:8015/api/sap-metadata/discover \
  -H "Content-Type: application/json" \
  -d '{
    "include_database": false,
    "include_odata": true,
    "build_semantic_index": false,
    "sync_to_metadata_service": true,
    "limit": 10,
    "offset": 10
  }'
```

#### 第三批（服务20-29）
```bash
curl -X POST http://localhost:8015/api/sap-metadata/discover \
  -H "Content-Type: application/json" \
  -d '{
    "include_database": false,
    "include_odata": true,
    "build_semantic_index": false,
    "sync_to_metadata_service": true,
    "limit": 10,
    "offset": 20
  }'
```

## 构建进度

- **总服务数**: 348个
- **建议批次大小**: 10-20个服务/批
- **预计批次数**: 约18-35批

## 响应格式

```json
{
  "data_assets": [...],
  "business_entities": [...],
  "business_processes": [...],
  "tables_discovered": 0,
  "odata_services_discovered": 912,
  "metadata": {
    "total_services": 348,
    "processed_services": 912,
    "has_more": true,
    "sync_result": {
      "data_assets": {
        "total": 912,
        "created": 912,
        "failed": 0
      },
      "business_entities": {
        "total": 50,
        "created": 50,
        "failed": 0
      }
    }
  }
}
```

## 注意事项

1. **批次大小**: 建议每批10-20个服务，避免超时
2. **构建语义索引**: 可以设为false加快速度，最后统一构建
3. **同步状态**: 检查`metadata.sync_result`了解同步情况
4. **继续构建**: 根据`has_more`字段判断是否还有更多服务需要处理

## 自动化脚本

可以使用PowerShell脚本自动化分批构建：

```powershell
$batchSize = 10
$totalServices = 348
$batches = [math]::Ceiling($totalServices / $batchSize)

for ($i = 0; $i -lt $batches; $i++) {
    $offset = $i * $batchSize
    Write-Host "构建第 $($i+1)/$batches 批 (offset=$offset, limit=$batchSize)..."
    
    $body = @{
        include_database = $false
        include_odata = $true
        build_semantic_index = $false
        sync_to_metadata_service = $true
        limit = $batchSize
        offset = $offset
    } | ConvertTo-Json
    
    $result = Invoke-RestMethod -Method Post -Uri "http://localhost:8015/api/sap-metadata/discover" `
        -Body $body -ContentType "application/json" -TimeoutSec 300
    
    Write-Host "  发现 $($result.data_assets.Count) 个数据资产"
    Write-Host "  同步成功: $($result.metadata.sync_result.data_assets.created)/$($result.metadata.sync_result.data_assets.total)"
    
    Start-Sleep -Seconds 2
}
```

## 状态检查

检查已同步的元数据：

```bash
# 检查数据资产
curl http://localhost:8005/api/data-assets?limit=100

# 检查业务实体
curl http://localhost:8005/api/business-entities?limit=100
```



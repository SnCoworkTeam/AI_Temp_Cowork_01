# 清理SAP相关元数据脚本

## 功能说明

此脚本用于批量清理所有SAP相关的元数据记录，支持处理10万+条记录。

## 脚本版本

提供两个版本：

1. **`cleanup_sap_metadata_sql.py`** (推荐) - 使用SQL直接删除，更高效，适合10万+条记录
2. **`cleanup_sap_metadata.py`** - 使用ORM批量删除，支持自定义批量大小

## 使用方法（SQL版本 - 推荐）

### 1. 预览模式（推荐先运行）

查看将要删除的记录数量，不实际删除：

```bash
cd metadata-service
python scripts/cleanup_sap_metadata_sql.py --dry-run
```

### 2. 实际删除

确认预览结果后，执行实际删除：

```bash
python scripts/cleanup_sap_metadata_sql.py --confirm
```

## 使用方法（ORM版本）

### 1. 预览模式

```bash
python scripts/cleanup_sap_metadata.py --dry-run
```

### 2. 实际删除

```bash
python scripts/cleanup_sap_metadata.py --confirm --batch-size 1000
```

## 参数说明

- `--dry-run`: 预览模式，只统计不删除
- `--confirm`: 确认删除（必须指定才会实际删除）
- `--batch-size`: 批量删除大小（默认1000）

## 识别规则

脚本会识别以下字段中包含"SAP"（不区分大小写）的记录：

- `source_system`
- `name`
- `display_name`
- `description`
- `source_path`
- `source_connection`
- `tags` (JSON数组)
- `metadata` (JSON对象)

## 涉及的表

- `data_assets` - 数据资产表
- `business_entities` - 业务实体表
- `ai_models` - AI模型表

## 注意事项

1. **备份数据**: 删除操作不可逆，建议先备份数据库
2. **预览模式**: 强烈建议先使用 `--dry-run` 预览
3. **批量处理**: 10万+条记录会分批处理，每批默认1000条
4. **数据库连接**: 确保 `DATABASE_URL` 或 `POSTGRES_URL` 环境变量已设置

## 环境变量

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/database"
# 或
export POSTGRES_URL="postgresql://user:password@localhost:5432/database"
```

## 示例输出

```
2025-11-26 20:30:00 - INFO - 连接数据库: localhost:5432/enterprise_ai
2025-11-26 20:30:01 - INFO - 正在统计SAP相关记录...
2025-11-26 20:30:05 - INFO -   - data_assets: 85000 条
2025-11-26 20:30:10 - INFO -   - business_entities: 12000 条
2025-11-26 20:30:12 - INFO -   - ai_models: 3000 条
2025-11-26 20:30:12 - INFO - 总计: 100000 条SAP相关记录
```


# 元数据升级指南

## 📋 现状分析

根据检查，metadata-service中已有 **68,390** 个数据资产。这些是之前构建的元数据。

## 🔍 现有元数据与新标准的对比

### 新标准要求

增强版元数据应该包含：

1. ✅ **ABAP字典信息** (`schema_info.abap_dictionary`)
   - 表描述（DD02L）
   - 字段描述（DD03L）
   - 数据元素文本（DD04T）
   - 域值（DD07T）

2. ✅ **业务术语映射** (`metadata.business_terms`)
   - 业务术语列表
   - 业务术语到技术资产的映射

3. ✅ **语义关系** (`metadata.semantic_relationships`)
   - 资产-实体关系
   - 实体-实体关系

4. ✅ **细化的分类** (`classification`)
   - `sap_master_data_customer`
   - `sap_transaction_sales_order`
   - 等15+种细分类

### 现有元数据检查

**如果现有元数据缺少以上字段，建议：**

## 🎯 升级策略

### 方案1: 保留现有 + 增量更新（推荐）

**适用场景**：现有元数据数量大（68,390个），全部重建耗时

**步骤**：
1. 保留现有元数据
2. 使用增强版构建脚本重新构建
3. 新构建的元数据会包含所有增强字段
4. 系统会自动更新已存在的资产（基于name匹配）

**优点**：
- 不丢失现有数据
- 增量更新，效率高
- 新资产自动包含增强字段

**执行**：
```bash
cd sap-metadata-agent
python build_complete_enhanced_metadata.py
```

### 方案2: 完全重建

**适用场景**：现有元数据质量不高，或需要确保所有资产都符合新标准

**步骤**：
1. 备份现有元数据（可选）
2. 清空metadata-service中的数据资产
3. 使用增强版构建脚本重新构建

**优点**：
- 确保所有元数据都符合新标准
- 数据一致性更好

**缺点**：
- 耗时较长（需要重建68,390+个资产）
- 可能丢失一些自定义的元数据

## 🔧 检查现有元数据质量

运行检查脚本：

```bash
# 检查示例资产
curl "http://localhost:8005/api/data-assets?limit=1" | jq '.[0] | {name, classification, has_schema_info: (.schema_info != null), has_abap_dict: (.schema_info.abap_dictionary != null), has_business_terms: (.metadata.business_terms != null), has_semantic_rels: (.metadata.semantic_relationships != null)}'
```

## ✅ 建议

**基于当前情况（68,390个资产），建议采用方案1：**

1. **保留现有元数据**
2. **运行增强版构建脚本**
   - 脚本会自动检测已存在的资产
   - 新构建的资产会包含所有增强字段
   - 已存在的资产会被更新（如果API支持更新）

3. **验证升级结果**
   - 检查新构建的资产是否包含ABAP字典信息
   - 检查业务术语映射是否生成
   - 检查语义关系是否构建

## 📊 升级后预期

升级完成后，元数据应该包含：

- ✅ 68,390+ 数据资产（保留现有 + 新增）
- ✅ ABAP字典信息（数据库表）
- ✅ 业务术语映射（所有资产）
- ✅ 语义关系（资产间关系）
- ✅ 细化的分类（15+种分类）

## 🚀 开始升级

```bash
cd sap-metadata-agent
python build_complete_enhanced_metadata.py
```

脚本会：
1. 检查数据库连接（如果可用，构建数据库元数据）
2. 分批处理所有OData服务（348个服务，每批10个）
3. 自动包含ABAP字典、业务术语、语义关系
4. 同步到metadata-service（会自动处理已存在的资产）

## ⚠️ 注意事项

1. **构建时间**：348个服务，每批约1分钟，总计约35-40分钟
2. **数据保留**：现有元数据会被保留，新构建的会更新或新增
3. **服务状态**：确保sap-metadata-agent和metadata-service都在运行

## 📝 验证升级

升级完成后，验证：

```bash
# 检查资产是否包含增强字段
curl "http://localhost:8005/api/data-assets?classification=sap_master_data_customer&limit=1" | jq '.[0].schema_info.abap_dictionary'

# 检查业务术语
curl "http://localhost:8005/api/data-assets?search=客户&limit=1" | jq '.[0].metadata.business_terms'

# 检查语义关系
curl "http://localhost:8005/api/data-assets?search=KNA1&limit=1" | jq '.[0].metadata.semantic_relationships'
```



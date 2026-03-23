# SAP MM模块元数据和知识库构建方案

## 📋 方案信息

**目标模块**: SAP MM (Material Management - 物料管理)  
**构建日期**: 2025-11-28  
**方案状态**: 🟡 **准备实施**

---

## 🎯 构建目标

### 元数据构建目标

1. **业务实体**
   - SAP MM核心业务实体（物料、供应商、采购订单等）
   - 业务流程实体（采购流程、库存管理流程等）
   - 数据对象实体（物料主数据、供应商主数据等）

2. **数据资产**
   - SAP MM数据表（MARA, MARC, MARD等）
   - 数据字段和属性
   - 数据字典信息

3. **知识图谱**
   - 实体间关系网络
   - 业务流程关系
   - 数据依赖关系

### 知识库构建目标

1. **业务文档**
   - SAP MM业务流程文档
   - 操作手册和SOP
   - 配置文档

2. **技术文档**
   - SAP MM数据字典
   - 表结构文档
   - 接口文档

3. **知识关联**
   - 文档与实体关联
   - 文档向量化
   - 语义搜索支持

---

## 📊 SAP MM模块核心实体

### 1. 物料管理核心实体

**物料主数据**:
- 物料（Material）
- 物料类型（Material Type）
- 物料组（Material Group）
- 物料分类（Material Classification）

**供应商管理**:
- 供应商（Vendor）
- 供应商主数据（Vendor Master Data）
- 供应商评估（Vendor Evaluation）

**采购管理**:
- 采购订单（Purchase Order）
- 采购申请（Purchase Requisition）
- 采购信息记录（Info Record）
- 货源清单（Source List）

**库存管理**:
- 库存地点（Storage Location）
- 库存（Stock）
- 物料凭证（Material Document）
- 移动类型（Movement Type）

### 2. 业务流程实体

**采购流程**:
- 需求识别
- 供应商选择
- 采购订单创建
- 收货
- 发票校验

**库存管理流程**:
- 入库
- 出库
- 库存盘点
- 库存转移

---

## 🚀 构建步骤

### 阶段1: 准备SAP MM数据源

**步骤1.1: 收集数据源**

1. **SAP数据字典**
   - 表结构定义（MARA, MARC, MARD, EKKO, EKPO等）
   - 字段定义和说明
   - 数据关系说明

2. **业务流程文档**
   - 采购流程文档
   - 库存管理流程文档
   - 配置文档

3. **业务规则文档**
   - 物料分类规则
   - 供应商评估规则
   - 采购审批规则

**步骤1.2: 数据格式准备**

准备以下格式的数据：
- CSV格式：实体列表、关系列表
- JSON格式：结构化数据
- 文档格式：PDF、Word、Markdown

---

### 阶段2: 构建SAP MM业务实体

**步骤2.1: 创建核心业务实体**

使用API批量创建业务实体：

```bash
# 1. 创建物料实体
POST /api/metadata/business-entities
{
  "name": "material",
  "display_name": "物料",
  "entity_type": "data_object",
  "description": "SAP MM模块中的物料主数据，包含物料的基本信息",
  "business_definition": "物料是SAP MM模块的核心对象，用于管理企业的物料信息，包括物料编号、描述、单位、价格等",
  "metadata": {
    "sap_table": "MARA",
    "sap_module": "MM",
    "category": "master_data"
  }
}

# 2. 创建供应商实体
POST /api/metadata/business-entities
{
  "name": "vendor",
  "display_name": "供应商",
  "entity_type": "data_object",
  "description": "SAP MM模块中的供应商主数据",
  "business_definition": "供应商是企业采购业务中的合作伙伴，包含供应商的基本信息、联系方式、银行信息等",
  "metadata": {
    "sap_table": "LFA1",
    "sap_module": "MM",
    "category": "master_data"
  }
}

# 3. 创建采购订单实体
POST /api/metadata/business-entities
{
  "name": "purchase_order",
  "display_name": "采购订单",
  "entity_type": "business_process",
  "description": "SAP MM模块中的采购订单",
  "business_definition": "采购订单是向供应商下达的正式采购文件，包含采购物料、数量、价格、交货日期等信息",
  "metadata": {
    "sap_table": "EKKO",
    "sap_module": "MM",
    "category": "transaction_data"
  }
}
```

**步骤2.2: 批量导入实体**

创建批量导入脚本：

```python
# sap_mm_entities_import.py
import requests
import json

BASE_URL = "http://localhost:8005/api/metadata/business-entities"

# SAP MM核心实体定义
sap_mm_entities = [
    {
        "name": "material",
        "display_name": "物料",
        "entity_type": "data_object",
        "description": "SAP MM模块中的物料主数据",
        "business_definition": "物料是SAP MM模块的核心对象",
        "metadata": {"sap_table": "MARA", "sap_module": "MM"}
    },
    {
        "name": "vendor",
        "display_name": "供应商",
        "entity_type": "data_object",
        "description": "SAP MM模块中的供应商主数据",
        "business_definition": "供应商是企业采购业务中的合作伙伴",
        "metadata": {"sap_table": "LFA1", "sap_module": "MM"}
    },
    # ... 更多实体
]

# 批量创建
for entity in sap_mm_entities:
    response = requests.post(BASE_URL, json=entity)
    print(f"Created: {entity['name']} - {response.status_code}")
```

---

### 阶段3: 构建SAP MM知识图谱

**步骤3.1: 使用SAP MM本体构建API**

```bash
# 执行SAP MM专用本体构建
POST /api/ontology/sap/build
{
  "use_llm": true,
  "module": "MM"
}
```

**步骤3.2: 手动建立关键关系**

如果自动发现的关系不足，可以手动建立：

```bash
# 建立物料与供应商的关系
POST /api/knowledge-graph/edges
{
  "source_node_id": "material_node_id",
  "target_node_id": "vendor_node_id",
  "relationship_type": "supplied_by",
  "properties": {
    "description": "物料由供应商提供",
    "confidence": 1.0
  }
}

# 建立采购订单与物料的关系
POST /api/knowledge-graph/edges
{
  "source_node_id": "purchase_order_node_id",
  "target_node_id": "material_node_id",
  "relationship_type": "contains",
  "properties": {
    "description": "采购订单包含物料",
    "confidence": 1.0
  }
}
```

---

### 阶段4: 导入SAP MM知识库文档

**步骤4.1: 准备文档数据**

文档类型：
- SAP MM业务流程文档
- SAP MM配置指南
- SAP MM数据字典
- SAP MM操作手册

**步骤4.2: 批量导入文档**

```bash
# 导入SAP MM业务流程文档
POST /api/knowledge/documents
{
  "title": "SAP MM采购流程",
  "content": "采购流程包括：1. 需求识别 2. 供应商选择 3. 采购订单创建...",
  "content_type": "sop",
  "metadata": {
    "module": "MM",
    "category": "business_process",
    "tags": ["SAP", "MM", "采购", "流程"]
  }
}

# 导入SAP MM数据字典
POST /api/knowledge/documents
{
  "title": "SAP MM数据字典 - MARA表",
  "content": "MARA表是物料主数据表，包含以下字段：MATNR(物料号)、MAKTX(物料描述)...",
  "content_type": "data_dictionary",
  "metadata": {
    "module": "MM",
    "category": "data_dictionary",
    "sap_table": "MARA",
    "tags": ["SAP", "MM", "数据字典", "MARA"]
  }
}
```

**步骤4.3: 文档向量化**

文档导入后会自动向量化，也可以手动触发：

```bash
# 文档会自动向量化，存储在向量数据库
# 可以通过统一搜索进行语义搜索
POST /api/unified/search
{
  "query": "SAP MM物料主数据",
  "types": ["document"]
}
```

---

### 阶段5: 建立文档与实体关联

**步骤5.1: 关联文档到实体**

```bash
# 关联SAP MM数据字典文档到物料实体
POST /api/document-entity-linker/link
{
  "document_id": "doc-sap-mm-mara",
  "entity_ids": [material_entity_id],
  "relationship_type": "describes"
}

# 关联业务流程文档到采购订单实体
POST /api/document-entity-linker/link
{
  "document_id": "doc-sap-mm-purchase-process",
  "entity_ids": [purchase_order_entity_id],
  "relationship_type": "explains"
}
```

---

## 📋 详细操作步骤

### 步骤1: 准备SAP MM实体数据

**创建SAP MM实体定义文件** (`sap_mm_entities.json`):

```json
{
  "entities": [
    {
      "name": "material",
      "display_name": "物料",
      "entity_type": "data_object",
      "description": "SAP MM模块中的物料主数据，包含物料的基本信息如物料号、描述、单位等",
      "business_definition": "物料是SAP MM模块的核心对象，用于管理企业的物料信息",
      "metadata": {
        "sap_table": "MARA",
        "sap_module": "MM",
        "category": "master_data",
        "key_fields": ["MATNR", "MAKTX", "MEINS"]
      }
    },
    {
      "name": "vendor",
      "display_name": "供应商",
      "entity_type": "data_object",
      "description": "SAP MM模块中的供应商主数据",
      "business_definition": "供应商是企业采购业务中的合作伙伴",
      "metadata": {
        "sap_table": "LFA1",
        "sap_module": "MM",
        "category": "master_data"
      }
    },
    {
      "name": "purchase_order",
      "display_name": "采购订单",
      "entity_type": "business_process",
      "description": "SAP MM模块中的采购订单",
      "business_definition": "采购订单是向供应商下达的正式采购文件",
      "metadata": {
        "sap_table": "EKKO",
        "sap_module": "MM",
        "category": "transaction_data"
      }
    },
    {
      "name": "purchase_requisition",
      "display_name": "采购申请",
      "entity_type": "business_process",
      "description": "SAP MM模块中的采购申请",
      "business_definition": "采购申请是内部需求部门提出的采购需求",
      "metadata": {
        "sap_table": "EBAN",
        "sap_module": "MM",
        "category": "transaction_data"
      }
    },
    {
      "name": "storage_location",
      "display_name": "库存地点",
      "entity_type": "data_object",
      "description": "SAP MM模块中的库存地点",
      "business_definition": "库存地点是物料存储的物理位置",
      "metadata": {
        "sap_table": "T001L",
        "sap_module": "MM",
        "category": "master_data"
      }
    },
    {
      "name": "material_document",
      "display_name": "物料凭证",
      "entity_type": "business_process",
      "description": "SAP MM模块中的物料凭证",
      "business_definition": "物料凭证记录物料的移动，如入库、出库、转移等",
      "metadata": {
        "sap_table": "MKPF",
        "sap_module": "MM",
        "category": "transaction_data"
      }
    }
  ]
}
```

---

### 步骤2: 批量导入SAP MM实体

**创建导入脚本** (`import_sap_mm_entities.py`):

```python
#!/usr/bin/env python3
"""
SAP MM实体批量导入脚本
"""
import requests
import json
import time

BASE_URL = "http://localhost:8005/api/metadata/business-entities"

def load_entities(file_path):
    """加载实体定义"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['entities']

def create_entity(entity):
    """创建单个实体"""
    try:
        response = requests.post(BASE_URL, json=entity, timeout=10)
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✅ Created: {entity['display_name']} (ID: {result.get('id', 'N/A')})")
            return result
        else:
            print(f"❌ Failed: {entity['display_name']} - {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating {entity['display_name']}: {e}")
        return None

def main():
    """主函数"""
    print("=== SAP MM实体批量导入 ===\n")
    
    # 加载实体定义
    entities = load_entities('sap_mm_entities.json')
    print(f"加载了 {len(entities)} 个实体定义\n")
    
    # 批量创建
    created = 0
    failed = 0
    
    for entity in entities:
        result = create_entity(entity)
        if result:
            created += 1
        else:
            failed += 1
        time.sleep(0.5)  # 避免请求过快
    
    print(f"\n=== 导入完成 ===")
    print(f"成功: {created}")
    print(f"失败: {failed}")

if __name__ == "__main__":
    main()
```

**执行导入**:

```bash
# 1. 准备实体定义文件
# 创建 sap_mm_entities.json

# 2. 运行导入脚本
python import_sap_mm_entities.py

# 3. 验证导入结果
curl http://localhost:8005/api/metadata/business-entities?entity_type=data_object
```

---

### 步骤3: 构建SAP MM知识图谱

**使用SAP MM专用本体构建API**:

```bash
# 执行SAP MM本体构建
curl -X POST http://localhost:8005/api/ontology/sap/build \
  -H "Content-Type: application/json" \
  -d '{"use_llm": true}'
```

**或者使用通用本体构建（过滤SAP MM实体）**:

```bash
# 先查询SAP MM相关实体
curl "http://localhost:8005/api/metadata/business-entities?metadata.sap_module=MM"

# 然后执行本体构建（会自动发现SAP MM实体间的关系）
curl -X POST http://localhost:8005/api/ontology/build \
  -H "Content-Type: application/json" \
  -d '{"use_llm": true, "filter": {"metadata.sap_module": "MM"}}'
```

**验证构建结果**:

```bash
# 检查知识图谱节点（SAP MM相关）
curl "http://localhost:8005/api/knowledge-graph/nodes?properties.sap_module=MM"

# 检查知识图谱边
curl "http://localhost:8005/api/knowledge-graph/edges?limit=100"

# 检查图谱统计
curl http://localhost:8005/api/knowledge-graph/stats
```

---

### 步骤4: 导入SAP MM知识库文档

**准备文档数据** (`sap_mm_documents.json`):

```json
{
  "documents": [
    {
      "title": "SAP MM采购流程",
      "content": "SAP MM采购流程包括以下步骤：\n1. 需求识别：业务部门提出采购需求\n2. 采购申请创建：在系统中创建采购申请\n3. 供应商选择：选择合适的供应商\n4. 采购订单创建：向供应商下达采购订单\n5. 收货：接收供应商交付的物料\n6. 发票校验：核对供应商发票",
      "content_type": "sop",
      "metadata": {
        "module": "MM",
        "category": "business_process",
        "tags": ["SAP", "MM", "采购", "流程", "SOP"]
      }
    },
    {
      "title": "SAP MM数据字典 - MARA表",
      "content": "MARA表是SAP MM模块的物料主数据表，包含以下关键字段：\n- MATNR: 物料号\n- MAKTX: 物料描述\n- MEINS: 基本计量单位\n- MTART: 物料类型\n- MATKL: 物料组",
      "content_type": "data_dictionary",
      "metadata": {
        "module": "MM",
        "category": "data_dictionary",
        "sap_table": "MARA",
        "tags": ["SAP", "MM", "数据字典", "MARA", "物料"]
      }
    },
    {
      "title": "SAP MM库存管理流程",
      "content": "SAP MM库存管理流程包括：\n1. 入库：物料入库时创建物料凭证\n2. 出库：物料出库时创建物料凭证\n3. 库存转移：在不同库存地点间转移物料\n4. 库存盘点：定期进行库存盘点",
      "content_type": "sop",
      "metadata": {
        "module": "MM",
        "category": "business_process",
        "tags": ["SAP", "MM", "库存", "管理", "流程"]
      }
    }
  ]
}
```

**创建文档导入脚本** (`import_sap_mm_documents.py`):

```python
#!/usr/bin/env python3
"""
SAP MM文档批量导入脚本
"""
import requests
import json
import time

BASE_URL = "http://localhost:8003/api/knowledge/documents"  # knowledge-base服务

def load_documents(file_path):
    """加载文档定义"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['documents']

def create_document(doc):
    """创建单个文档"""
    try:
        response = requests.post(BASE_URL, json=doc, timeout=30)
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✅ Created: {doc['title']} (ID: {result.get('id', 'N/A')})")
            return result
        else:
            print(f"❌ Failed: {doc['title']} - {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating {doc['title']}: {e}")
        return None

def main():
    """主函数"""
    print("=== SAP MM文档批量导入 ===\n")
    
    # 加载文档定义
    documents = load_documents('sap_mm_documents.json')
    print(f"加载了 {len(documents)} 个文档定义\n")
    
    # 批量创建
    created = 0
    failed = 0
    
    for doc in documents:
        result = create_document(doc)
        if result:
            created += 1
        else:
            failed += 1
        time.sleep(1)  # 文档处理需要更多时间
    
    print(f"\n=== 导入完成 ===")
    print(f"成功: {created}")
    print(f"失败: {failed}")
    print(f"\n注意: 文档会自动向量化，可能需要几分钟时间")

if __name__ == "__main__":
    main()
```

**执行导入**:

```bash
# 1. 准备文档定义文件
# 创建 sap_mm_documents.json

# 2. 运行导入脚本
python import_sap_mm_documents.py

# 3. 验证导入结果
curl http://localhost:8003/api/knowledge/documents?metadata.module=MM
```

---

### 步骤5: 建立文档与实体关联

**创建关联脚本** (`link_sap_mm_documents.py`):

```python
#!/usr/bin/env python3
"""
SAP MM文档与实体关联脚本
"""
import requests
import json

METADATA_URL = "http://localhost:8005/api/metadata/business-entities"
DOCUMENT_URL = "http://localhost:8003/api/knowledge/documents"
LINKER_URL = "http://localhost:8005/api/document-entity-linker/link"

def get_entities_by_module(module="MM"):
    """获取指定模块的实体"""
    response = requests.get(
        METADATA_URL,
        params={"metadata.sap_module": module}
    )
    if response.status_code == 200:
        return response.json()
    return []

def get_documents_by_module(module="MM"):
    """获取指定模块的文档"""
    response = requests.get(
        DOCUMENT_URL,
        params={"metadata.module": module}
    )
    if response.status_code == 200:
        return response.json()
    return []

def link_document_to_entity(doc_id, entity_id, relationship_type="describes"):
    """关联文档到实体"""
    try:
        response = requests.post(
            LINKER_URL,
            json={
                "document_id": doc_id,
                "entity_ids": [entity_id],
                "relationship_type": relationship_type
            }
        )
        if response.status_code == 200:
            print(f"✅ Linked document {doc_id} to entity {entity_id}")
            return True
        else:
            print(f"❌ Failed to link: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """主函数"""
    print("=== SAP MM文档与实体关联 ===\n")
    
    # 获取实体和文档
    entities = get_entities_by_module("MM")
    documents = get_documents_by_module("MM")
    
    print(f"找到 {len(entities)} 个实体")
    print(f"找到 {len(documents)} 个文档\n")
    
    # 建立关联规则
    # 例如：数据字典文档关联到对应的实体
    entity_map = {e['name']: e['id'] for e in entities}
    
    for doc in documents:
        doc_metadata = doc.get('metadata', {})
        sap_table = doc_metadata.get('sap_table')
        
        if sap_table:
            # 根据SAP表名找到对应实体
            # 例如：MARA表对应material实体
            entity_name_map = {
                'MARA': 'material',
                'LFA1': 'vendor',
                'EKKO': 'purchase_order',
                'EBAN': 'purchase_requisition',
                'T001L': 'storage_location',
                'MKPF': 'material_document'
            }
            
            entity_name = entity_name_map.get(sap_table)
            if entity_name and entity_name in entity_map:
                link_document_to_entity(
                    doc['id'],
                    entity_map[entity_name],
                    "describes"
                )

if __name__ == "__main__":
    main()
```

---

## 🎯 完整操作流程

### 快速开始（推荐）

```bash
# 1. 准备数据文件
# - sap_mm_entities.json (实体定义)
# - sap_mm_documents.json (文档定义)

# 2. 批量导入实体
python import_sap_mm_entities.py

# 3. 构建知识图谱
curl -X POST http://localhost:8005/api/ontology/sap/build \
  -H "Content-Type: application/json" \
  -d '{"use_llm": true}'

# 4. 批量导入文档
python import_sap_mm_documents.py

# 5. 建立文档实体关联
python link_sap_mm_documents.py

# 6. 验证结果
curl http://localhost:8005/api/knowledge-graph/stats
curl "http://localhost:8005/api/metadata/business-entities?metadata.sap_module=MM"
```

---

## 📊 预期结果

### 元数据结果

- ✅ SAP MM业务实体: 20+ 个
- ✅ 知识图谱节点: 20+ 个
- ✅ 知识图谱边: 50+ 条
- ✅ 实体关系: 完整的关系网络

### 知识库结果

- ✅ SAP MM文档: 10+ 篇
- ✅ 文档向量化: 100%
- ✅ 文档实体关联: 80%+

### 功能验证

- ✅ 推荐功能: 能推荐SAP MM相关实体
- ✅ 搜索功能: 能搜索SAP MM文档和实体
- ✅ 分析功能: 能分析SAP MM实体关系

---

## 💡 最佳实践

### 1. 数据准备

- 使用标准化的实体命名
- 提供完整的描述和业务定义
- 包含SAP表名等元数据

### 2. 关系建立

- 优先使用自动关系发现（LLM增强）
- 手动补充关键关系
- 验证关系准确性

### 3. 文档管理

- 文档标题清晰
- 内容结构化
- 标签准确

---

**方案生成时间**: 2025-11-28  
**状态**: ✅ **准备实施**





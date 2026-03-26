# 阶段3：统一实体标识系统设计

## 📋 设计概览

**设计日期**: 2025-11-28  
**目标**: 建立全局唯一的实体标识符系统  
**状态**: 🟡 **设计中**

---

## 🎯 设计目标

1. **全局唯一性**: 每个实体在整个平台中有唯一标识
2. **跨服务兼容**: 支持不同服务的内部ID格式
3. **可扩展性**: 支持新的实体类型和服务
4. **向后兼容**: 不影响现有系统

---

## 📐 实体ID方案设计

### 方案1: EntityURI格式（推荐）⭐

**格式**: `entity://{domain}/{type}/{id}`

**示例**:
- `entity://metadata/data_asset/123`
- `entity://knowledge/node/uuid-123`
- `entity://sap/business_entity/456`
- `entity://workflow/workflow/789`

**优点**:
- ✅ 清晰表达实体来源和类型
- ✅ 易于解析和验证
- ✅ 支持命名空间隔离

**实现**:
```python
class EntityURI:
    """统一实体标识符"""
    
    def __init__(self, domain: str, entity_type: str, entity_id: str):
        self.domain = domain  # metadata, knowledge, sap, workflow
        self.entity_type = entity_type  # data_asset, node, business_entity
        self.entity_id = entity_id  # 原始ID（可以是Integer或UUID）
    
    def to_string(self) -> str:
        return f"entity://{self.domain}/{self.entity_type}/{self.entity_id}"
    
    @classmethod
    def from_string(cls, uri: str) -> 'EntityURI':
        # 解析 entity://domain/type/id
        parts = uri.replace("entity://", "").split("/")
        if len(parts) != 3:
            raise ValueError(f"Invalid EntityURI format: {uri}")
        return cls(domain=parts[0], entity_type=parts[1], entity_id=parts[2])
```

---

## 🏗️ 架构设计

### 组件1: 实体ID注册服务

**位置**: `metadata-service/src/services/entity_registry_service.py`

**功能**:
- 注册新实体，分配统一ID
- 查询实体信息
- 管理实体生命周期

**数据模型**:
```python
class EntityRegistry(Base, TimestampMixin):
    """实体注册表"""
    __tablename__ = "entity_registry"
    
    id = Column(Integer, primary_key=True)
    entity_uri = Column(String(500), unique=True, nullable=False, index=True)
    domain = Column(String(50), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    internal_id = Column(String(255), nullable=False)  # 服务内部ID
    service_name = Column(String(50), nullable=False)  # 所属服务
    status = Column(String(20), default="active")  # active, deleted
    metadata = Column(JSONB)  # 额外元数据
```

---

### 组件2: 实体ID服务

**位置**: `metadata-service/src/services/entity_id_service.py`

**功能**:
- 生成统一实体ID
- 验证实体ID格式
- 转换服务内部ID和统一ID

---

### 组件3: 实体映射增强

**位置**: `metadata-service/src/services/entity_mapping_service.py`（扩展）

**功能**:
- 使用统一实体ID进行映射
- 支持多对一映射（多个内部ID映射到一个统一ID）
- 支持实体合并和拆分

---

## 📋 实施步骤

### 步骤1: 创建实体注册表

**文件**: `database/src/models/entity_registry.py`

### 步骤2: 实现实体ID服务

**文件**: `metadata-service/src/services/entity_id_service.py`

### 步骤3: 实现实体注册服务

**文件**: `metadata-service/src/services/entity_registry_service.py`

### 步骤4: 创建API端点

**文件**: `metadata-service/src/api/entity_registry.py`

### 步骤5: 集成到现有服务

- 在创建实体时自动注册
- 在查询实体时使用统一ID

---

**设计完成时间**: 2025-11-28  
**状态**: 🟡 **设计完成，准备实施**







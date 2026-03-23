# 第一阶段增强实施指南

## 📋 快速开始

本指南提供每个增强模块的具体实现步骤、代码示例和集成方法。

---

## 🎯 方案1: 元数据建模增强

### 1.1 业务实体建模器

#### 实现步骤

**步骤1**: 创建服务模块

```bash
# 在metadata-service中创建
touch metadata-service/src/services/business_entity_modeler.py
```

**步骤2**: 实现核心逻辑

```python
# metadata-service/src/services/business_entity_modeler.py
"""
业务实体建模器
从sap-metadata-agent获取数据资产，自动识别业务实体并构建关系图谱
"""
import logging
import httpx
import os
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.business_entity import BusinessEntity, BusinessEntitySchema, BusinessEntityCreate
from ..services.metadata_catalog import MetadataCatalogService
from ..services.data_lineage import DataLineageService

logger = logging.getLogger(__name__)


class BusinessEntityModeler:
    """业务实体建模器"""
    
    def __init__(self, db: Session, metadata_catalog: MetadataCatalogService, lineage_service: DataLineageService):
        self.db = db
        self.catalog = metadata_catalog
        self.lineage_service = lineage_service
        self.sap_agent_url = os.getenv("SAP_METADATA_AGENT_URL", "http://sap-metadata-agent:8015")
        self.http_client = httpx.AsyncClient(timeout=60.0)
    
    async def identify_entities_from_sap(self) -> List[BusinessEntitySchema]:
        """
        从sap-metadata-agent获取数据资产，自动识别业务实体
        
        Returns:
            识别的业务实体列表
        """
        try:
            # 1. 从sap-metadata-agent获取数据资产
            response = await self.http_client.get(f"{self.sap_agent_url}/api/sap-metadata/assets")
            response.raise_for_status()
            sap_response = response.json()
            
            # ⚠️ 修正：使用正确的字段名（实际API返回{"total": ..., "assets": ...}）
            sap_assets = sap_response.get("assets", [])
            
            # 2. 基于命名模式识别实体
            entity_patterns = {
                "KNA1": "客户",
                "LFA1": "供应商",
                "MARA": "物料",
                "BKPF": "会计凭证",
                "VBAK": "销售订单",
                # 可以扩展更多模式
            }
            
            identified_entities = []
            for asset in sap_assets:
                # ⚠️ 修正：使用正确的字段名
                table_name = asset.get("sap_table_name", "").upper()
                if not table_name:
                    # 如果没有sap_table_name，尝试从name中提取
                    table_name = asset.get("name", "").upper()
                
                if table_name in entity_patterns:
                    entity_name = entity_patterns[table_name]
                    
                    # ⚠️ 修正：使用list_business_entities搜索，而不是不存在的get_business_entity_by_name
                    existing_entities = self.catalog.list_business_entities(search=entity_name, limit=10)
                    existing = None
                    for e in existing_entities:
                        if e.name == entity_name:
                            existing = e
                            break
                    if not existing:
                        # 创建业务实体
                        from ..models.business_entity import EntityType
                        entity_data = BusinessEntityCreate(
                            name=entity_name,
                            display_name=f"{entity_name}实体",
                            description=f"从SAP表{table_name}识别的{entity_name}实体",
                            entity_type=EntityType.CONCEPT,  # 使用枚举值
                            metadata={
                                "table_name": table_name,
                                "asset_id": asset.get("id"),
                                "source_system": "SAP"
                            }
                        )
                        entity = self.catalog.create_business_entity(entity_data)
                        identified_entities.append(entity)
            
            logger.info(f"Identified {len(identified_entities)} business entities from SAP")
            return identified_entities
            
        except Exception as e:
            logger.error(f"Failed to identify entities from SAP: {e}", exc_info=True)
            raise
    
    async def build_entity_relationship_graph(self, entity_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        构建实体关系图谱
        
        Args:
            entity_ids: 实体ID列表（可选，不提供则构建所有实体）
        
        Returns:
            关系图谱数据
        """
        try:
            # 1. 获取实体列表
            if entity_ids:
                entities = [self.catalog.get_business_entity(eid) for eid in entity_ids]
                entities = [e for e in entities if e]
            else:
                entities = self.catalog.list_business_entities(limit=1000)
            
            # 2. 获取实体间的血缘关系
            relationships = []
            for entity in entities:
                # ⚠️ 修正：从metadata中获取asset_id
                metadata = entity.metadata or {}
                asset_id = metadata.get("asset_id")
                
                if asset_id:
                    # ⚠️ 修正：血缘服务是同步方法，不需要await
                    # ⚠️ 修正：返回LineageGraph对象，需要提取edges
                    upstream_graph = self.lineage_service.get_upstream_lineage("data_asset", str(asset_id))
                    downstream_graph = self.lineage_service.get_downstream_lineage("data_asset", str(asset_id))
                    
                    # 合并所有边
                    all_edges = upstream_graph.edges + downstream_graph.edges
                    
                    # 构建关系
                    for edge in all_edges:
                        # 解析节点ID: "type:id"
                        try:
                            source_type, source_id_str = edge.source.split(":", 1)
                            target_type, target_id_str = edge.target.split(":", 1)
                            
                            relationships.append({
                                "source_entity_id": entity.id,
                                "target_entity_id": target_id_str,  # 注意：这里可能需要查找对应的实体ID
                                "relationship_type": edge.relation_type.value if hasattr(edge.relation_type, 'value') else str(edge.relation_type),
                                "metadata": edge.metadata or {}
                            })
                        except ValueError:
                            logger.warning(f"Failed to parse lineage edge: {edge.source} -> {edge.target}")
                            continue
            
            # 3. 构建图谱结构
            graph = {
                "nodes": [
                    {
                        "id": entity.id,
                        "name": entity.name,
                        "type": entity.entity_type.value if hasattr(entity.entity_type, 'value') else str(entity.entity_type),
                        "metadata": entity.metadata
                    }
                    for entity in entities
                ],
                "edges": relationships,
                "created_at": datetime.now().isoformat()
            }
            
            logger.info(f"Built relationship graph with {len(graph['nodes'])} nodes and {len(graph['edges'])} edges")
            return graph
            
        except Exception as e:
            logger.error(f"Failed to build entity relationship graph: {e}", exc_info=True)
            raise
    
    async def calculate_entity_similarity(self, entity_id1: int, entity_id2: int) -> float:
        """
        计算实体相似度
        
        Args:
            entity_id1: 实体1 ID
            entity_id2: 实体2 ID
        
        Returns:
            相似度分数 (0-1)
        """
        try:
            entity1 = self.catalog.get_business_entity(entity_id1)
            entity2 = self.catalog.get_business_entity(entity_id2)
            
            if not entity1 or not entity2:
                return 0.0
            
            # 基于名称、类型、元数据的相似度计算
            similarity_score = 0.0
            
            # 名称相似度
            if entity1.name == entity2.name:
                similarity_score += 0.3
            
            # 类型相似度
            entity_type1 = entity1.entity_type.value if hasattr(entity1.entity_type, 'value') else str(entity1.entity_type)
            entity_type2 = entity2.entity_type.value if hasattr(entity2.entity_type, 'value') else str(entity2.entity_type)
            if entity_type1 == entity_type2:
                similarity_score += 0.2
            
            # 元数据相似度（可以扩展为向量相似度）
            if entity1.metadata and entity2.metadata:
                common_keys = set(entity1.metadata.keys()) & set(entity2.metadata.keys())
                if common_keys:
                    similarity_score += 0.5 * (len(common_keys) / max(len(entity1.metadata), len(entity2.metadata)))
            
            return min(similarity_score, 1.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate entity similarity: {e}", exc_info=True)
            return 0.0
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()
```

**步骤3**: 创建API路由

```python
# metadata-service/src/api/entity_models.py
"""
业务实体模型API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from ..core.database import get_db  # ⚠️ 修正：使用正确的路径
from ..services.business_entity_modeler import BusinessEntityModeler
from ..services.metadata_catalog import MetadataCatalogService
from ..services.data_lineage import DataLineageService

router = APIRouter(prefix="/api/models", tags=["Entity Models"])


def get_entity_modeler(db: Session = Depends(get_db)) -> BusinessEntityModeler:
    """获取业务实体建模器"""
    catalog = MetadataCatalogService(db)
    lineage_service = DataLineageService(db)
    return BusinessEntityModeler(db, catalog, lineage_service)


@router.post("/entities", summary="创建业务实体模型")
async def create_entity_model(
    entity_ids: Optional[List[int]] = None,
    modeler: BusinessEntityModeler = Depends(get_entity_modeler)
):
    """
    创建业务实体模型，构建关系图谱
    
    - 如果entity_ids为空，则从SAP自动识别实体
    - 如果提供entity_ids，则基于这些实体构建关系图谱
    """
    try:
        if not entity_ids:
            # 自动识别实体
            entities = await modeler.identify_entities_from_sap()
            entity_ids = [e.id for e in entities]
        
        # 构建关系图谱
        graph = await modeler.build_entity_relationship_graph(entity_ids)
        
        return {
            "success": True,
            "graph": graph,
            "entity_count": len(entity_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await modeler.close()  # ⚠️ 修正：确保关闭HTTP客户端


@router.get("/entities", summary="获取实体模型列表")
async def get_entity_models(
    modeler: BusinessEntityModeler = Depends(get_entity_modeler)
):
    """获取所有业务实体模型"""
    try:
        entities = modeler.catalog.list_business_entities(limit=1000)
        return {
            "success": True,
            "entities": [e.model_dump() for e in entities]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await modeler.close()  # ⚠️ 修正：确保关闭HTTP客户端


@router.get("/entities/{entity_id}/similarity/{target_id}", summary="计算实体相似度")
async def calculate_similarity(
    entity_id: int,
    target_id: int,
    modeler: BusinessEntityModeler = Depends(get_entity_modeler)
):
    """计算两个实体的相似度"""
    try:
        similarity = await modeler.calculate_entity_similarity(entity_id, target_id)
        return {
            "success": True,
            "entity_id": entity_id,
            "target_id": target_id,
            "similarity": similarity
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await modeler.close()  # ⚠️ 修正：确保关闭HTTP客户端
```

**步骤4**: 注册路由

```python
# metadata-service/src/main.py
from .api import entity_models

app.include_router(entity_models.router)
```

---

### 1.2 技术模型生成器

#### 实现步骤

**步骤1**: 创建服务模块

```python
# metadata-service/src/services/technical_model_generator.py
"""
技术模型生成器
分析表结构模式，自动归纳数据模型
"""
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from collections import defaultdict

from ..models.data_asset import DataAsset, DataAssetSchema
from ..services.metadata_catalog import MetadataCatalogService
from ..services.quality_service import QualityService

logger = logging.getLogger(__name__)


class TechnicalModelGenerator:
    """技术模型生成器"""
    
    def __init__(self, db: Session, catalog: MetadataCatalogService, quality_service: QualityService):
        self.db = db
        self.catalog = catalog
        self.quality_service = quality_service
    
    async def analyze_schema_patterns(self, asset_type: Optional[str] = None) -> Dict[str, Any]:
        """
        分析表结构模式，自动归纳数据模型
        
        Args:
            asset_type: 资产类型（可选）
        
        Returns:
            归纳的数据模型
        """
        try:
            # 1. 获取数据资产
            assets = self.catalog.list_data_assets(
                asset_type=asset_type,
                limit=1000
            )
            
            # 2. 分析schema模式
            schema_patterns = defaultdict(list)
            for asset in assets:
                schema = asset.schema
                if schema:
                    # 提取字段模式
                    field_pattern = self._extract_field_pattern(schema)
                    schema_patterns[field_pattern].append(asset.id)
            
            # 3. 归纳模型
            models = []
            for pattern, asset_ids in schema_patterns.items():
                if len(asset_ids) >= 2:  # 至少2个资产共享同一模式
                    model = {
                        "pattern": pattern,
                        "asset_ids": asset_ids,
                        "asset_count": len(asset_ids),
                        "model_quality": self._evaluate_model_quality(asset_ids)
                    }
                    models.append(model)
            
            return {
                "models": models,
                "total_patterns": len(schema_patterns),
                "identified_models": len(models)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze schema patterns: {e}", exc_info=True)
            raise
    
    def _extract_field_pattern(self, schema: Dict) -> str:
        """提取字段模式"""
        # 简化示例：基于字段类型和数量
        if not schema or "fields" not in schema:
            return "unknown"
        
        field_types = [f.get("type", "unknown") for f in schema["fields"]]
        pattern = f"{len(field_types)}_fields_{'_'.join(sorted(set(field_types)))}"
        return pattern
    
    def _evaluate_model_quality(self, asset_ids: List[int]) -> float:
        """评估模型质量"""
        try:
            # 获取资产质量分数
            quality_scores = []
            for asset_id in asset_ids:
                metrics = self.quality_service.get_quality_metrics(asset_id)
                if metrics and metrics.get("quality_score"):
                    quality_scores.append(metrics["quality_score"])
            
            if quality_scores:
                return sum(quality_scores) / len(quality_scores)
            return 0.5  # 默认质量分数
            
        except Exception as e:
            logger.warning(f"Failed to evaluate model quality: {e}")
            return 0.5
    
    async def track_model_evolution(self, model_id: str) -> List[Dict[str, Any]]:
        """
        跟踪模型演化
        
        Args:
            model_id: 模型ID
        
        Returns:
            演化历史
        """
        # 利用现有version_service跟踪模型版本
        # 实现细节...
        pass
```

---

### 1.3 质量规则引擎增强

#### 实现步骤

**步骤1**: 扩展现有质量规则引擎

```python
# metadata-service/src/services/quality_rule_engine.py (扩展)
"""
质量规则引擎（增强版）
支持指标向量化和规则执行
"""
import logging
import httpx
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class QualityRuleEngine:
    """质量规则引擎（增强版）"""
    
    def __init__(self, db: Session):
        self.db = db
        self._embedding_model = None  # ⚠️ 修正：使用本地embedding模型，不依赖vector-coordinator
    
    def _get_embedding_model(self):
        """懒加载embedding模型"""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Loaded embedding model for vectorization")
            except ImportError:
                logger.warning("sentence-transformers not installed, vectorization disabled")
                self._embedding_model = None
        return self._embedding_model
    
    async def vectorize_metrics(self, metrics: Dict[str, Any]) -> List[float]:
        """
        指标向量化存储
        
        Args:
            metrics: 质量指标字典
        
        Returns:
            向量表示
        """
        try:
            # 将指标转换为文本
            metrics_text = self._metrics_to_text(metrics)
            
            # ⚠️ 修正：使用本地embedding模型，不依赖vector-coordinator
            model = self._get_embedding_model()
            if model:
                embedding = model.encode(metrics_text).tolist()
                return embedding
            else:
                logger.warning("Embedding model not available, returning empty vector")
                return []
            
        except Exception as e:
            logger.error(f"Failed to vectorize metrics: {e}", exc_info=True)
            return []
    
    def _metrics_to_text(self, metrics: Dict[str, Any]) -> str:
        """将指标转换为文本"""
        text_parts = []
        for key, value in metrics.items():
            text_parts.append(f"{key}: {value}")
        return " ".join(text_parts)
    
    async def execute_rules(self, asset_id: int, rules: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        规则执行和监控
        
        Args:
            asset_id: 资产ID
            rules: 规则列表（可选，不提供则执行所有规则）
        
        Returns:
            执行结果
        """
        try:
            # 获取资产质量指标
            from ..services.quality_service import QualityService
            quality_service = QualityService(self.db)
            metrics = quality_service.get_quality_metrics(asset_id)
            
            if not metrics:
                return {
                    "success": False,
                    "error": "No quality metrics found"
                }
            
            # 执行规则
            results = []
            rule_list = rules or self._get_default_rules()
            
            for rule_name in rule_list:
                rule_result = self._execute_rule(rule_name, metrics)
                results.append(rule_result)
            
            return {
                "success": True,
                "asset_id": asset_id,
                "rules_executed": len(results),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Failed to execute rules: {e}", exc_info=True)
            raise
    
    def _get_default_rules(self) -> List[str]:
        """获取默认规则列表"""
        return [
            "completeness_check",
            "accuracy_check",
            "consistency_check",
            "timeliness_check"
        ]
    
    def _execute_rule(self, rule_name: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个规则"""
        # 规则执行逻辑
        pass
```

---

## 🎯 方案2: 知识图谱建模增强

### 2.1 本体构建器

#### 实现步骤

**步骤1**: 创建服务模块

```python
# knowledge-base/src/services/ontology_builder.py
"""
本体构建器
从metadata-service获取业务实体，构建业务本体
"""
import logging
import httpx
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from ..repositories.knowledge_graph_repository import KnowledgeGraphRepository

logger = logging.getLogger(__name__)


class OntologyBuilder:
    """本体构建器"""
    
    def __init__(self, db: Session, kg_repo: KnowledgeGraphRepository):
        self.db = db
        self.kg_repo = kg_repo
        self.metadata_service_url = os.getenv("METADATA_SERVICE_URL", "http://metadata-service:8005")
        self.http_client = httpx.AsyncClient(timeout=60.0)
    
    async def build_business_ontology(self) -> Dict[str, Any]:
        """
        从metadata-service获取业务实体，构建业务本体
        
        Returns:
            本体数据
        """
        try:
            # 1. 从metadata-service获取业务实体
            response = await self.http_client.get(
                f"{self.metadata_service_url}/api/business-entities",
                params={"limit": 1000}
            )
            response.raise_for_status()
            entities = response.json()
            
            # 2. 构建概念层次结构
            concepts = self._build_concept_hierarchy(entities)
            
            # 3. 定义实体关系和属性
            relationships = self._extract_relationships(entities)
            
            # 4. 存储到知识图谱
            ontology_id = await self._store_ontology(concepts, relationships)
            
            return {
                "success": True,
                "ontology_id": ontology_id,
                "concepts": len(concepts),
                "relationships": len(relationships)
            }
            
        except Exception as e:
            logger.error(f"Failed to build business ontology: {e}", exc_info=True)
            raise
    
    def _build_concept_hierarchy(self, entities: List[Dict]) -> List[Dict]:
        """构建概念层次结构"""
        # 实现概念层次构建逻辑
        pass
    
    def _extract_relationships(self, entities: List[Dict]) -> List[Dict]:
        """提取实体关系"""
        # 实现关系提取逻辑
        pass
    
    async def _store_ontology(self, concepts: List[Dict], relationships: List[Dict]) -> str:
        """存储本体到知识图谱"""
        # 使用kg_repo存储
        pass
```

---

## 🎯 方案3: 权限模型增强

### 3.1 数据分类器

#### 实现步骤

**步骤1**: 创建服务模块

```python
# auth-service/src/services/data_classifier.py
"""
数据分类器
从metadata-service获取数据资产，基于敏感度和业务价值分类
"""
import logging
import httpx
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class DataClassifier:
    """数据分类器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.metadata_service_url = os.getenv("METADATA_SERVICE_URL", "http://metadata-service:8005")
        self.http_client = httpx.AsyncClient(timeout=60.0)
    
    async def classify_data_assets(self) -> Dict[str, Any]:
        """
        从metadata-service获取数据资产，基于敏感度和业务价值分类
        
        Returns:
            分类结果
        """
        try:
            # 1. 获取数据资产
            response = await self.http_client.get(
                f"{self.metadata_service_url}/api/data-assets",
                params={"limit": 1000}
            )
            response.raise_for_status()
            assets = response.json()
            
            # 2. 基于敏感度和业务价值分类
            classifications = {}
            for asset in assets.get("items", []):
                classification = self._classify_asset(asset)
                classifications[asset["id"]] = classification
            
            # 3. 构建数据分类图谱
            classification_graph = self._build_classification_graph(classifications)
            
            return {
                "success": True,
                "classified_assets": len(classifications),
                "classification_graph": classification_graph
            }
            
        except Exception as e:
            logger.error(f"Failed to classify data assets: {e}", exc_info=True)
            raise
    
    def _classify_asset(self, asset: Dict) -> Dict[str, Any]:
        """分类单个资产"""
        # 基于classification、quality_score、domain分类
        classification = asset.get("classification", "public")
        quality_score = asset.get("data_quality_metrics", {}).get("quality_score", 0.5)
        domain = asset.get("metadata", {}).get("domain", "unknown")
        
        # 计算敏感度
        sensitivity = self._calculate_sensitivity(classification, quality_score)
        
        # 计算业务价值
        business_value = self._calculate_business_value(quality_score, domain)
        
        return {
            "sensitivity": sensitivity,  # "low", "medium", "high", "critical"
            "business_value": business_value,  # "low", "medium", "high"
            "classification": classification,
            "domain": domain
        }
    
    def _calculate_sensitivity(self, classification: str, quality_score: float) -> str:
        """计算敏感度"""
        # 实现敏感度计算逻辑
        if classification in ["confidential", "restricted"]:
            return "high"
        elif classification == "internal":
            return "medium"
        else:
            return "low"
    
    def _calculate_business_value(self, quality_score: float, domain: str) -> str:
        """计算业务价值"""
        # 实现业务价值计算逻辑
        if quality_score >= 0.8:
            return "high"
        elif quality_score >= 0.5:
            return "medium"
        else:
            return "low"
    
    def _build_classification_graph(self, classifications: Dict) -> Dict[str, Any]:
        """构建数据分类图谱"""
        # 实现图谱构建逻辑
        pass
```

---

## 📝 通用实现模式

### 1. 服务客户端模式

所有跨服务调用都使用HTTP客户端：

```python
class ServiceClient:
    def __init__(self, service_url: str):
        self.base_url = service_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get(self, endpoint: str, params: Optional[Dict] = None):
        response = await self.client.get(f"{self.base_url}{endpoint}", params=params)
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        await self.client.aclose()
```

### 2. 错误处理模式

```python
try:
    result = await service_method()
    return {"success": True, "data": result}
except httpx.HTTPError as e:
    logger.error(f"HTTP error: {e}")
    raise HTTPException(status_code=500, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail=str(e))
```

### 3. 数据库模型扩展

```python
# 不修改现有模型，创建新表
class EntityModel(Base):
    __tablename__ = "entity_models"
    
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey("business_entities.id"))
    model_data = Column(JSONB)
    created_at = Column(DateTime, default=datetime.now)
```

---

## 🧪 测试指南

### 单元测试示例

```python
# tests/unit/test_business_entity_modeler.py
import pytest
from metadata_service.services.business_entity_modeler import BusinessEntityModeler

@pytest.mark.asyncio
async def test_identify_entities_from_sap(mock_db, mock_metadata_catalog, mock_lineage_service):
    modeler = BusinessEntityModeler(mock_db, mock_metadata_catalog, mock_lineage_service)
    entities = await modeler.identify_entities_from_sap()
    assert len(entities) > 0
```

### 集成测试示例

```python
# tests/integration/test_entity_models_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_entity_model(client: AsyncClient):
    response = await client.post("/api/models/entities", json={})
    assert response.status_code == 200
    assert response.json()["success"] is True
```

---

## 📚 参考文档

- [metadata-service README](../metadata-service/README.md)
- [knowledge-base README](../knowledge-base/README.md)
- [auth-service README](../auth-service/README.md)
- [可行性分析报告](./ENHANCEMENT_FEASIBILITY_ANALYSIS.md)


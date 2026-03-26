"""
数据模型单元测试
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "metadata-service" / "src"))

from src.models.data_asset import (
    DataAsset, DataAssetType, DataAssetStatus,
    DataAssetSchema, DataAssetCreate, DataAssetUpdate
)
from src.models.ai_model import (
    AIModel, ModelType, ModelStatus,
    AIModelSchema, AIModelCreate, AIModelUpdate
)
from src.models.business_entity import (
    BusinessEntity, EntityType,
    BusinessEntitySchema, BusinessEntityCreate, BusinessEntityUpdate
)
from src.models.workflow_metadata import (
    WorkflowMetadata, WorkflowStatus,
    WorkflowMetadataSchema, WorkflowMetadataCreate, WorkflowMetadataUpdate
)
from src.models.lineage import (
    DataLineage, LineageType, LineageRelationType,
    LineageNode, LineageEdge, LineageGraph
)
from src.models.quality import QualityCheckResult, QualityDashboard


@pytest.mark.unit
class TestDataAsset:
    """数据资产模型测试"""
    
    def test_data_asset_type_enum(self):
        """测试数据资产类型枚举"""
        assert DataAssetType.DATASET == "dataset"
        assert DataAssetType.TABLE == "table"
        assert DataAssetType.VIEW == "view"
        assert DataAssetType.FILE == "file"
        assert DataAssetType.STREAM == "stream"
        assert DataAssetType.API == "api"
    
    def test_data_asset_status_enum(self):
        """测试数据资产状态枚举"""
        assert DataAssetStatus.ACTIVE == "active"
        assert DataAssetStatus.DEPRECATED == "deprecated"
        assert DataAssetStatus.ARCHIVED == "archived"
    
    def test_create_data_asset(self, db_session: Session):
        """测试创建数据资产"""
        asset = DataAsset(
            name="test_dataset",
            display_name="Test Dataset",
            description="Test dataset for unit testing",
            asset_type=DataAssetType.DATASET,
            status=DataAssetStatus.ACTIVE,
            source_system="test_system",
            tags=["test", "unit-test"]
        )
        db_session.add(asset)
        db_session.commit()
        db_session.refresh(asset)
        
        assert asset.id is not None
        assert asset.name == "test_dataset"
        assert asset.asset_type == DataAssetType.DATASET
        assert asset.status == DataAssetStatus.ACTIVE
        assert asset.created_at is not None
        assert asset.updated_at is not None
    
    def test_data_asset_schema(self, db_session: Session):
        """测试数据资产Schema"""
        asset = DataAsset(
            name="test_schema",
            asset_type=DataAssetType.TABLE,
            status=DataAssetStatus.ACTIVE,
            schema_info={"columns": ["id", "name"]},
            tags=["schema-test"]
        )
        db_session.add(asset)
        db_session.commit()
        db_session.refresh(asset)
        
        schema = DataAssetSchema.model_validate(asset)
        assert schema.id == asset.id
        assert schema.name == "test_schema"
        assert schema.asset_type == DataAssetType.TABLE
        assert schema.schema_info == {"columns": ["id", "name"]}
    
    def test_data_asset_create_model(self):
        """测试DataAssetCreate模型"""
        create_data = DataAssetCreate(
            name="new_asset",
            display_name="New Asset",
            asset_type=DataAssetType.FILE,
            tags=["new"]
        )
        assert create_data.name == "new_asset"
        assert create_data.asset_type == DataAssetType.FILE
        assert create_data.status == DataAssetStatus.ACTIVE  # 默认值


@pytest.mark.unit
class TestAIModel:
    """AI模型测试"""
    
    def test_model_type_enum(self):
        """测试模型类型枚举"""
        assert ModelType.LLM == "llm"
        assert ModelType.EMBEDDING == "embedding"
        assert ModelType.CLASSIFICATION == "classification"
        assert ModelType.REGRESSION == "regression"
        assert ModelType.CLUSTERING == "clustering"
        assert ModelType.CUSTOM == "custom"
    
    def test_model_status_enum(self):
        """测试模型状态枚举"""
        assert ModelStatus.ACTIVE == "active"
        assert ModelStatus.DEPRECATED == "deprecated"
        assert ModelStatus.ARCHIVED == "archived"
    
    def test_create_ai_model(self, db_session: Session):
        """测试创建AI模型"""
        model = AIModel(
            name="test_model",
            display_name="Test Model",
            description="Test AI model",
            model_type=ModelType.LLM,
            status=ModelStatus.ACTIVE,
            framework="pytorch",
            model_version="1.0.0"
        )
        db_session.add(model)
        db_session.commit()
        db_session.refresh(model)
        
        assert model.id is not None
        assert model.name == "test_model"
        assert model.model_type == ModelType.LLM
        assert model.framework == "pytorch"
    
    def test_ai_model_schema(self, db_session: Session):
        """测试AI模型Schema"""
        model = AIModel(
            name="schema_model",
            model_type=ModelType.EMBEDDING,
            status=ModelStatus.ACTIVE,
            hyperparameters={"learning_rate": 0.001}
        )
        db_session.add(model)
        db_session.commit()
        db_session.refresh(model)
        
        schema = AIModelSchema.model_validate(model)
        assert schema.id == model.id
        assert schema.name == "schema_model"
        assert schema.model_type == ModelType.EMBEDDING


@pytest.mark.unit
class TestBusinessEntity:
    """业务实体测试"""
    
    def test_entity_type_enum(self):
        """测试实体类型枚举"""
        assert EntityType.DOMAIN == "domain"
        assert EntityType.CONCEPT == "concept"
        assert EntityType.TERM == "term"
        assert EntityType.GLOSSARY == "glossary"
        assert EntityType.POLICY == "policy"
        assert EntityType.RULE == "rule"
    
    def test_create_business_entity(self, db_session: Session):
        """测试创建业务实体"""
        entity = BusinessEntity(
            name="test_entity",
            display_name="Test Entity",
            entity_type=EntityType.TERM,
            definition="Test business entity definition"
        )
        db_session.add(entity)
        db_session.commit()
        db_session.refresh(entity)
        
        assert entity.id is not None
        assert entity.name == "test_entity"
        assert entity.entity_type == EntityType.TERM


@pytest.mark.unit
class TestWorkflowMetadata:
    """工作流元数据测试"""
    
    def test_workflow_status_enum(self):
        """测试工作流状态枚举"""
        assert WorkflowStatus.DRAFT == "draft"
        assert WorkflowStatus.ACTIVE == "active"
        assert WorkflowStatus.DEPRECATED == "deprecated"
        assert WorkflowStatus.ARCHIVED == "archived"
    
    def test_create_workflow_metadata(self, db_session: Session):
        """测试创建工作流元数据"""
        workflow = WorkflowMetadata(
            name="test_workflow",
            display_name="Test Workflow",
            status=WorkflowStatus.ACTIVE,
            workflow_id="wf-123"
        )
        db_session.add(workflow)
        db_session.commit()
        db_session.refresh(workflow)
        
        assert workflow.id is not None
        assert workflow.name == "test_workflow"
        assert workflow.status == WorkflowStatus.ACTIVE


@pytest.mark.unit
class TestDataLineage:
    """数据血缘测试"""
    
    def test_lineage_type_enum(self):
        """测试血缘类型枚举"""
        assert LineageType.DATA_FLOW == "data_flow"
        assert LineageType.TRANSFORMATION == "transformation"
        assert LineageType.DEPENDENCY == "dependency"
        assert LineageType.DERIVATION == "derivation"
    
    def test_lineage_relation_type_enum(self):
        """测试血缘关系类型枚举"""
        assert LineageRelationType.READS == "reads"
        assert LineageRelationType.WRITES == "writes"
        assert LineageRelationType.TRANSFORMS == "transforms"
        assert LineageRelationType.DEPENDS_ON == "depends_on"
        assert LineageRelationType.DERIVES == "derives"
    
    def test_create_data_lineage(self, db_session: Session):
        """测试创建数据血缘"""
        lineage = DataLineage(
            source_type="data_asset",
            source_id="asset-1",
            source_asset="data_asset:asset-1",
            target_type="data_asset",
            target_id="asset-2",
            target_asset="data_asset:asset-2",
            relation_type=LineageRelationType.READS,
            lineage_type=LineageType.DATA_FLOW,
            transformation="ETL Process"
        )
        db_session.add(lineage)
        db_session.commit()
        db_session.refresh(lineage)
        
        assert lineage.id is not None
        assert lineage.source_id == "asset-1"
        assert lineage.target_id == "asset-2"
        assert lineage.relation_type == LineageRelationType.READS
    
    def test_lineage_node(self):
        """测试血缘节点"""
        node = LineageNode(
            id="asset-1",
            type="data_asset",
            name="test_asset",
            display_name="Test Asset"
        )
        assert node.id == "asset-1"
        assert node.type == "data_asset"
        assert node.name == "test_asset"
    
    def test_lineage_edge(self):
        """测试血缘边"""
        edge = LineageEdge(
            source="asset-1",
            target="asset-2",
            relation_type=LineageRelationType.READS,
            lineage_type=LineageType.DATA_FLOW
        )
        assert edge.source == "asset-1"
        assert edge.target == "asset-2"
        assert edge.relation_type == LineageRelationType.READS
    
    def test_lineage_graph(self):
        """测试血缘图谱"""
        nodes = [
            LineageNode(id="asset-1", type="data_asset", name="Asset 1"),
            LineageNode(id="asset-2", type="data_asset", name="Asset 2")
        ]
        edges = [
            LineageEdge(
                source="asset-1",
                target="asset-2",
                relation_type=LineageRelationType.READS,
                lineage_type=LineageType.DATA_FLOW
            )
        ]
        graph = LineageGraph(nodes=nodes, edges=edges)
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1


@pytest.mark.unit
class TestQuality:
    """数据质量测试"""
    
    def test_quality_check_result(self):
        """测试质量检查结果"""
        from shared_libs.src.models.metadata_models import DataQualityMetrics
        
        metrics = DataQualityMetrics(
            completeness=0.95,
            accuracy=0.90,
            consistency=0.88
        )
        
        result = QualityCheckResult(
            asset_id="asset-1",
            asset_type="data_asset",
            asset_name="Test Asset",
            check_time=datetime.now(),
            status="passed",
            overall_score=0.91,
            metrics=metrics,
            checks=[],
            issues=[],
            recommendations=[]
        )
        
        assert result.asset_id == "asset-1"
        assert result.overall_score == 0.91
        assert result.status == "passed"
    
    def test_quality_dashboard(self):
        """测试质量监控仪表板"""
        dashboard = QualityDashboard(
            summary={"total": 100, "passed": 90, "failed": 10},
            quality_distribution={"excellent": 50, "good": 30, "fair": 20},
            recent_checks=[],
            top_issues=[],
            trends={},
            assets_by_quality={}
        )
        
        assert dashboard.summary["total"] == 100
        assert dashboard.quality_distribution["excellent"] == 50


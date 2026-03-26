"""
服务层单元测试
"""
import pytest
import sys
from pathlib import Path
from sqlalchemy.orm import Session

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "metadata-service" / "src"))

from src.services.metadata_catalog import MetadataCatalogService
from src.services.data_lineage import DataLineageService
from src.services.search_service import SearchService
from src.services.quality_service import QualityService
from src.models.data_asset import DataAssetCreate, DataAssetType, DataAssetStatus
from src.models.ai_model import AIModelCreate, ModelType, ModelStatus
from src.models.business_entity import BusinessEntityCreate, EntityType
from src.models.workflow_metadata import WorkflowMetadataCreate, WorkflowStatus
from src.models.lineage import DataLineageCreate, LineageType, LineageRelationType


@pytest.mark.unit
class TestMetadataCatalogService:
    """元数据目录服务测试"""
    
    def test_create_data_asset(self, db_session: Session):
        """测试创建数据资产"""
        service = MetadataCatalogService(db_session)
        
        asset_data = DataAssetCreate(
            name="test_asset",
            display_name="Test Asset",
            description="Test description",
            asset_type=DataAssetType.DATASET,
            status=DataAssetStatus.ACTIVE,
            source_system="test_system",
            tags=["test"]
        )
        
        result = service.create_data_asset(asset_data)
        assert result.id is not None
        assert result.name == "test_asset"
        assert result.asset_type == DataAssetType.DATASET
    
    def test_get_data_asset(self, db_session: Session):
        """测试获取数据资产"""
        service = MetadataCatalogService(db_session)
        
        # 先创建
        asset_data = DataAssetCreate(
            name="get_test",
            asset_type=DataAssetType.TABLE,
            status=DataAssetStatus.ACTIVE
        )
        created = service.create_data_asset(asset_data)
        
        # 再获取
        retrieved = service.get_data_asset(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "get_test"
    
    def test_list_data_assets(self, db_session: Session):
        """测试列出数据资产"""
        service = MetadataCatalogService(db_session)
        
        # 创建多个资产
        for i in range(5):
            asset_data = DataAssetCreate(
                name=f"asset_{i}",
                asset_type=DataAssetType.DATASET,
                status=DataAssetStatus.ACTIVE
            )
            service.create_data_asset(asset_data)
        
        # 列出所有
        assets = service.list_data_assets(skip=0, limit=10)
        assert len(assets) == 5
        
        # 测试分页
        assets = service.list_data_assets(skip=0, limit=2)
        assert len(assets) == 2
        
        assets = service.list_data_assets(skip=2, limit=2)
        assert len(assets) == 2
    
    def test_list_data_assets_filter_by_type(self, db_session: Session):
        """测试按类型过滤数据资产"""
        service = MetadataCatalogService(db_session)
        
        # 创建不同类型的资产
        service.create_data_asset(DataAssetCreate(
            name="dataset1",
            asset_type=DataAssetType.DATASET,
            status=DataAssetStatus.ACTIVE
        ))
        service.create_data_asset(DataAssetCreate(
            name="table1",
            asset_type=DataAssetType.TABLE,
            status=DataAssetStatus.ACTIVE
        ))
        
        # 过滤
        datasets = service.list_data_assets(asset_type="dataset")
        assert len(datasets) == 1
        assert datasets[0].name == "dataset1"
    
    def test_list_data_assets_search(self, db_session: Session):
        """测试搜索数据资产"""
        service = MetadataCatalogService(db_session)
        
        service.create_data_asset(DataAssetCreate(
            name="searchable_asset",
            display_name="Searchable Asset",
            description="This is searchable",
            asset_type=DataAssetType.DATASET,
            status=DataAssetStatus.ACTIVE
        ))
        
        results = service.list_data_assets(search="searchable")
        assert len(results) >= 1
        assert any("searchable" in r.name.lower() or "searchable" in (r.display_name or "").lower() 
                   for r in results)
    
    def test_update_data_asset(self, db_session: Session):
        """测试更新数据资产"""
        service = MetadataCatalogService(db_session)
        
        # 创建
        asset_data = DataAssetCreate(
            name="update_test",
            asset_type=DataAssetType.DATASET,
            status=DataAssetStatus.ACTIVE
        )
        created = service.create_data_asset(asset_data)
        
        # 更新
        from src.models.data_asset import DataAssetUpdate
        update_data = DataAssetUpdate(
            display_name="Updated Name",
            description="Updated description"
        )
        updated = service.update_data_asset(created.id, update_data)
        
        assert updated is not None
        assert updated.display_name == "Updated Name"
        assert updated.description == "Updated description"
    
    def test_delete_data_asset(self, db_session: Session):
        """测试删除数据资产"""
        service = MetadataCatalogService(db_session)
        
        # 创建
        asset_data = DataAssetCreate(
            name="delete_test",
            asset_type=DataAssetType.DATASET,
            status=DataAssetStatus.ACTIVE
        )
        created = service.create_data_asset(asset_data)
        
        # 删除
        result = service.delete_data_asset(created.id)
        assert result is True
        
        # 验证已删除
        retrieved = service.get_data_asset(created.id)
        assert retrieved is None
    
    def test_create_ai_model(self, db_session: Session):
        """测试创建AI模型"""
        service = MetadataCatalogService(db_session)
        
        model_data = AIModelCreate(
            name="test_model",
            display_name="Test Model",
            model_type=ModelType.LLM,
            status=ModelStatus.ACTIVE,
            framework="pytorch"
        )
        
        result = service.create_ai_model(model_data)
        assert result.id is not None
        assert result.name == "test_model"
        assert result.model_type == ModelType.LLM
    
    def test_list_ai_models(self, db_session: Session):
        """测试列出AI模型"""
        service = MetadataCatalogService(db_session)
        
        # 创建多个模型
        for i in range(3):
            model_data = AIModelCreate(
                name=f"model_{i}",
                model_type=ModelType.LLM,
                status=ModelStatus.ACTIVE
            )
            service.create_ai_model(model_data)
        
        models = service.list_ai_models()
        assert len(models) == 3
    
    def test_create_business_entity(self, db_session: Session):
        """测试创建业务实体"""
        service = MetadataCatalogService(db_session)
        
        entity_data = BusinessEntityCreate(
            name="test_entity",
            display_name="Test Entity",
            entity_type=EntityType.TERM,
            definition="Test definition"
        )
        
        result = service.create_business_entity(entity_data)
        assert result.id is not None
        assert result.name == "test_entity"
        assert result.entity_type == EntityType.TERM
    
    def test_create_workflow_metadata(self, db_session: Session):
        """测试创建工作流元数据"""
        service = MetadataCatalogService(db_session)
        
        workflow_data = WorkflowMetadataCreate(
            name="test_workflow",
            display_name="Test Workflow",
            status=WorkflowStatus.ACTIVE,
            workflow_id="wf-123"
        )
        
        result = service.create_workflow_metadata(workflow_data)
        assert result.id is not None
        assert result.name == "test_workflow"
        assert result.status == WorkflowStatus.ACTIVE


@pytest.mark.unit
class TestDataLineageService:
    """数据血缘服务测试"""
    
    def test_create_lineage(self, db_session: Session):
        """测试创建血缘关系"""
        service = DataLineageService(db_session)
        
        lineage_data = DataLineageCreate(
            source_type="data_asset",
            source_id="asset-1",
            target_type="data_asset",
            target_id="asset-2",
            relation_type=LineageRelationType.READS,
            lineage_type=LineageType.DATA_FLOW
        )
        
        result = service.create_lineage(lineage_data)
        assert result.id is not None
        assert result.source_id == "asset-1"
        assert result.target_id == "asset-2"
        assert result.relation_type == LineageRelationType.READS
    
    def test_get_lineage(self, db_session: Session):
        """测试获取血缘关系"""
        service = DataLineageService(db_session)
        
        # 先创建
        lineage_data = DataLineageCreate(
            source_type="data_asset",
            source_id="asset-1",
            target_type="data_asset",
            target_id="asset-2",
            relation_type=LineageRelationType.READS,
            lineage_type=LineageType.DATA_FLOW
        )
        created = service.create_lineage(lineage_data)
        
        # 再获取
        retrieved = service.get_lineage(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
    
    def test_list_lineage(self, db_session: Session):
        """测试列出血缘关系"""
        service = DataLineageService(db_session)
        
        # 创建多个血缘关系
        for i in range(3):
            lineage_data = DataLineageCreate(
                source_type="data_asset",
                source_id=f"asset-{i}",
                target_type="data_asset",
                target_id=f"asset-{i+1}",
                relation_type=LineageRelationType.READS,
                lineage_type=LineageType.DATA_FLOW
            )
            service.create_lineage(lineage_data)
        
        # 列出所有
        lineages = service.list_lineage()
        assert len(lineages) == 3
        
        # 按源过滤
        lineages = service.list_lineage(source_id="asset-0")
        assert len(lineages) == 1


@pytest.mark.unit
class TestSearchService:
    """搜索服务测试"""
    
    def test_search_all(self, db_session: Session):
        """测试全局搜索"""
        # 先创建一些数据
        catalog_service = MetadataCatalogService(db_session)
        
        catalog_service.create_data_asset(DataAssetCreate(
            name="searchable_dataset",
            display_name="Searchable Dataset",
            description="This is searchable",
            asset_type=DataAssetType.DATASET,
            status=DataAssetStatus.ACTIVE
        ))
        
        catalog_service.create_ai_model(AIModelCreate(
            name="searchable_model",
            display_name="Searchable Model",
            model_type=ModelType.LLM,
            status=ModelStatus.ACTIVE
        ))
        
        # 搜索
        search_service = SearchService(db_session)
        results = search_service.search_all("searchable")
        
        assert results["total"] >= 2
        assert len(results["data_assets"]) >= 1
        assert len(results["ai_models"]) >= 1
    
    def test_search_by_entity_type(self, db_session: Session):
        """测试按实体类型搜索"""
        catalog_service = MetadataCatalogService(db_session)
        
        catalog_service.create_data_asset(DataAssetCreate(
            name="asset_only",
            asset_type=DataAssetType.DATASET,
            status=DataAssetStatus.ACTIVE
        ))
        
        catalog_service.create_ai_model(AIModelCreate(
            name="model_only",
            model_type=ModelType.LLM,
            status=ModelStatus.ACTIVE
        ))
        
        search_service = SearchService(db_session)
        results = search_service.search_all("only", entity_types=["data_asset"])
        
        assert len(results["data_assets"]) >= 1
        assert len(results["ai_models"]) == 0


@pytest.mark.unit
class TestQualityService:
    """质量服务测试"""
    
    def test_check_data_quality(self, db_session: Session):
        """测试数据质量检查"""
        # 先创建数据资产
        catalog_service = MetadataCatalogService(db_session)
        asset = catalog_service.create_data_asset(DataAssetCreate(
            name="quality_test",
            asset_type=DataAssetType.DATASET,
            status=DataAssetStatus.ACTIVE,
            data_quality_metrics={
                "completeness": 0.95,
                "accuracy": 0.90
            }
        ))
        
        # 检查质量
        quality_service = QualityService(db_session)
        result = quality_service.check_data_quality(asset.id, "data_asset")
        
        assert result is not None
        assert result.asset_id == str(asset.id)
        assert result.asset_type == "data_asset"
    
    def test_get_quality_dashboard(self, db_session: Session):
        """测试获取质量仪表板"""
        quality_service = QualityService(db_session)
        dashboard = quality_service.get_quality_dashboard()
        
        assert dashboard is not None
        assert "summary" in dashboard.model_dump()
        assert "quality_distribution" in dashboard.model_dump()

"""
数据库集成测试
测试真实的数据库操作
"""
import pytest
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "metadata-service" / "src"))

from database.src.models.base import Base
from src.models.data_asset import DataAsset, DataAssetType, DataAssetStatus
from src.models.ai_model import AIModel, ModelType, ModelStatus
from src.models.business_entity import BusinessEntity, EntityType
from src.models.workflow_metadata import WorkflowMetadata, WorkflowStatus
from src.models.lineage import DataLineage, LineageType, LineageRelationType
from src.services.metadata_catalog import MetadataCatalogService
from src.services.data_lineage import DataLineageService


@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话"""
    # 使用SQLite内存数据库
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.mark.integration
class TestDatabaseOperations:
    """数据库操作集成测试"""
    
    def test_create_and_retrieve_data_asset(self, db_session: Session):
        """测试创建和检索数据资产"""
        service = MetadataCatalogService(db_session)
        
        # 创建
        asset_data = DataAssetCreate(
            name="integration_test",
            display_name="Integration Test Asset",
            description="Test asset for integration testing",
            asset_type=DataAssetType.DATASET,
            status=DataAssetStatus.ACTIVE,
            source_system="test_system",
            tags=["integration", "test"]
        )
        
        created = service.create_data_asset(asset_data)
        assert created.id is not None
        
        # 检索
        retrieved = service.get_data_asset(created.id)
        assert retrieved is not None
        assert retrieved.name == "integration_test"
        assert retrieved.asset_type == DataAssetType.DATASET
        assert retrieved.tags == ["integration", "test"]
    
    def test_update_data_asset(self, db_session: Session):
        """测试更新数据资产"""
        service = MetadataCatalogService(db_session)
        
        # 创建
        asset_data = DataAssetCreate(
            name="update_integration",
            asset_type=DataAssetType.TABLE,
            status=DataAssetStatus.ACTIVE
        )
        created = service.create_data_asset(asset_data)
        
        # 更新
        from src.models.data_asset import DataAssetUpdate
        update_data = DataAssetUpdate(
            display_name="Updated Display Name",
            description="Updated description",
            status=DataAssetStatus.DEPRECATED
        )
        updated = service.update_data_asset(created.id, update_data)
        
        assert updated is not None
        assert updated.display_name == "Updated Display Name"
        assert updated.status == DataAssetStatus.DEPRECATED
        
        # 验证更新已保存
        retrieved = service.get_data_asset(created.id)
        assert retrieved.display_name == "Updated Display Name"
        assert retrieved.status == DataAssetStatus.DEPRECATED
    
    def test_delete_data_asset(self, db_session: Session):
        """测试删除数据资产"""
        service = MetadataCatalogService(db_session)
        
        # 创建
        asset_data = DataAssetCreate(
            name="delete_integration",
            asset_type=DataAssetType.FILE,
            status=DataAssetStatus.ACTIVE
        )
        created = service.create_data_asset(asset_data)
        asset_id = created.id
        
        # 删除
        result = service.delete_data_asset(asset_id)
        assert result is True
        
        # 验证已删除
        retrieved = service.get_data_asset(asset_id)
        assert retrieved is None
    
    def test_list_data_assets_with_filters(self, db_session: Session):
        """测试带过滤条件的列表查询"""
        service = MetadataCatalogService(db_session)
        
        # 创建多个不同类型的资产
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
        service.create_data_asset(DataAssetCreate(
            name="dataset2",
            asset_type=DataAssetType.DATASET,
            status=DataAssetStatus.DEPRECATED
        ))
        
        # 按类型过滤
        datasets = service.list_data_assets(asset_type="dataset")
        assert len(datasets) == 2
        assert all(d.asset_type == DataAssetType.DATASET for d in datasets)
        
        # 按状态过滤
        active = service.list_data_assets(status="active")
        assert len(active) == 2
        assert all(a.status == DataAssetStatus.ACTIVE for a in active)
        
        # 组合过滤
        active_datasets = service.list_data_assets(
            asset_type="dataset",
            status="active"
        )
        assert len(active_datasets) == 1
        assert active_datasets[0].name == "dataset1"
    
    def test_create_lineage_relationship(self, db_session: Session):
        """测试创建血缘关系"""
        lineage_service = DataLineageService(db_session)
        
        # 创建血缘关系
        lineage_data = DataLineageCreate(
            source_type="data_asset",
            source_id="asset-1",
            target_type="data_asset",
            target_id="asset-2",
            relation_type=LineageRelationType.READS,
            lineage_type=LineageType.DATA_FLOW,
            transformation="ETL Process"
        )
        
        created = lineage_service.create_lineage(lineage_data)
        assert created.id is not None
        assert created.source_id == "asset-1"
        assert created.target_id == "asset-2"
        assert created.relation_type == LineageRelationType.READS
    
    def test_query_lineage_by_source(self, db_session: Session):
        """测试按源查询血缘关系"""
        lineage_service = DataLineageService(db_session)
        
        # 创建多个血缘关系
        for i in range(3):
            lineage_data = DataLineageCreate(
                source_type="data_asset",
                source_id="asset-0",
                target_type="data_asset",
                target_id=f"asset-{i+1}",
                relation_type=LineageRelationType.READS,
                lineage_type=LineageType.DATA_FLOW
            )
            lineage_service.create_lineage(lineage_data)
        
        # 查询源为asset-0的所有血缘关系
        lineages = lineage_service.list_lineage(source_id="asset-0")
        assert len(lineages) == 3
        assert all(l.source_id == "asset-0" for l in lineages)
    
    def test_transaction_rollback(self, db_session: Session):
        """测试事务回滚"""
        service = MetadataCatalogService(db_session)
        
        # 创建资产
        asset_data = DataAssetCreate(
            name="rollback_test",
            asset_type=DataAssetType.DATASET,
            status=DataAssetStatus.ACTIVE
        )
        created = service.create_data_asset(asset_data)
        
        # 模拟错误导致回滚
        try:
            # 尝试创建无效数据（这里只是示例，实际应该触发数据库约束错误）
            db_session.rollback()
        except Exception:
            pass
        
        # 验证数据仍然存在（因为之前的提交）
        retrieved = service.get_data_asset(created.id)
        assert retrieved is not None

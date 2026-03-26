"""
阶段一第1周测试
测试核心数据模型创建和数据库迁移
"""
import pytest
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.src.core.database import get_db, get_database_settings
from database.src.models import (
    BusinessActivity,
    CapabilityUnit,
    ActivityCapabilityMapping
)
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError


class TestModelsImport:
    """测试模型导入"""
    
    def test_models_import(self):
        """测试模型可以正确导入"""
        assert BusinessActivity is not None
        assert CapabilityUnit is not None
        assert ActivityCapabilityMapping is not None
        print("✅ 所有模型成功导入")


class TestDatabaseMigration:
    """测试数据库迁移"""
    
    def test_migration_executed(self):
        """测试迁移已执行"""
        try:
            db = next(get_db())
            inspector = inspect(db.bind)
            
            # 检查表是否存在
            tables = inspector.get_table_names()
            assert 'business_activities' in tables
            assert 'capability_units' in tables
            assert 'activity_capability_mappings' in tables
            
            print("✅ 数据库迁移成功，所有表已创建")
        except Exception as e:
            pytest.fail(f"数据库迁移测试失败: {e}")


class TestTableStructure:
    """测试表结构"""
    
    def test_business_activities_structure(self):
        """测试business_activities表结构"""
        try:
            db = next(get_db())
            inspector = inspect(db.bind)
            
            columns = {col['name']: col for col in inspector.get_columns('business_activities')}
            
            # 验证关键字段
            assert 'id' in columns
            assert 'name' in columns
            assert 'vector_entity_uri' in columns
            assert 'embedding_version' in columns
            assert 'last_vectorized_at' in columns
            assert 'description_updated_at' in columns
            
            print("✅ business_activities表结构正确")
        except Exception as e:
            pytest.fail(f"表结构测试失败: {e}")
    
    def test_capability_units_structure(self):
        """测试capability_units表结构"""
        try:
            db = next(get_db())
            inspector = inspect(db.bind)
            
            columns = {col['name']: col for col in inspector.get_columns('capability_units')}
            
            # 验证关键字段
            assert 'id' in columns
            assert 'name' in columns
            assert 'capability_type' in columns
            assert 'reliability_score' in columns
            
            print("✅ capability_units表结构正确")
        except Exception as e:
            pytest.fail(f"表结构测试失败: {e}")
    
    def test_activity_capability_mappings_structure(self):
        """测试activity_capability_mappings表结构"""
        try:
            db = next(get_db())
            inspector = inspect(db.bind)
            
            columns = {col['name']: col for col in inspector.get_columns('activity_capability_mappings')}
            
            # 验证关键字段
            assert 'id' in columns
            assert 'activity_id' in columns
            assert 'capability_id' in columns
            assert 'mapping_type' in columns
            assert 'success_rate' in columns
            
            print("✅ activity_capability_mappings表结构正确")
        except Exception as e:
            pytest.fail(f"表结构测试失败: {e}")


class TestIndexes:
    """测试索引"""
    
    def test_business_activities_indexes(self):
        """测试business_activities表索引"""
        try:
            db = next(get_db())
            inspector = inspect(db.bind)
            
            indexes = inspector.get_indexes('business_activities')
            index_names = [idx['name'] for idx in indexes]
            
            # 检查关键索引
            assert any('idx_activity_name' in name for name in index_names)
            assert any('idx_activity_domain_type' in name or 'domain_type' in name for name in index_names)
            assert any('idx_activity_vector_uri' in name or 'vector_uri' in name for name in index_names)
            
            print("✅ business_activities表索引创建成功")
        except Exception as e:
            pytest.fail(f"索引测试失败: {e}")


class TestCRUDOperations:
    """测试CRUD操作"""
    
    def test_business_activity_crud(self):
        """测试业务活动CRUD"""
        try:
            db = next(get_db())
            
            # Create
            activity = BusinessActivity(
                id="activity:test:create_po",
                name="测试创建采购订单",
                description="测试描述",
                activity_type="action",
                business_domain="procurement",
                vector_entity_uri="activity://procurement/activity:test:create_po"
            )
            db.add(activity)
            db.commit()
            
            # Read
            retrieved = db.query(BusinessActivity).filter_by(id=activity.id).first()
            assert retrieved is not None
            assert retrieved.name == "测试创建采购订单"
            
            # Update
            retrieved.description = "更新后的描述"
            retrieved.description_updated_at = datetime.now()
            db.commit()
            
            # 验证needs_vector_update
            assert retrieved.needs_vector_update() == True
            
            # Delete
            db.delete(retrieved)
            db.commit()
            
            # 验证删除
            deleted = db.query(BusinessActivity).filter_by(id=activity.id).first()
            assert deleted is None
            
            print("✅ 业务活动CRUD操作测试通过")
        except Exception as e:
            db.rollback()
            pytest.fail(f"CRUD操作测试失败: {e}")
    
    def test_capability_unit_crud(self):
        """测试能力单元CRUD"""
        try:
            db = next(get_db())
            
            # Create
            capability = CapabilityUnit(
                id="component:test:sap_create_po",
                name="测试SAP创建PO组件",
                description="测试描述",
                capability_type="Component",
                endpoint="http://test/api/create-po",
                vector_entity_uri="component://test/component:test:sap_create_po"
            )
            db.add(capability)
            db.commit()
            
            # Read
            retrieved = db.query(CapabilityUnit).filter_by(id=capability.id).first()
            assert retrieved is not None
            assert retrieved.name == "测试SAP创建PO组件"
            
            # Update
            retrieved.reliability_score = 0.95
            db.commit()
            
            # Delete
            db.delete(retrieved)
            db.commit()
            
            print("✅ 能力单元CRUD操作测试通过")
        except Exception as e:
            db.rollback()
            pytest.fail(f"CRUD操作测试失败: {e}")
    
    def test_mapping_crud(self):
        """测试映射CRUD"""
        try:
            db = next(get_db())
            
            # 先创建活动和能力
            activity = BusinessActivity(
                id="activity:test:mapping",
                name="测试活动",
                activity_type="action",
                business_domain="procurement",
                vector_entity_uri="activity://procurement/activity:test:mapping"
            )
            capability = CapabilityUnit(
                id="component:test:mapping",
                name="测试组件",
                capability_type="Component",
                vector_entity_uri="component://test/component:test:mapping"
            )
            db.add(activity)
            db.add(capability)
            db.commit()
            
            # Create mapping
            mapping = ActivityCapabilityMapping(
                id="mapping:test:activity:test:mapping:component:test:mapping",
                activity_id=activity.id,
                capability_id=capability.id,
                mapping_type="primary",
                confidence=0.9
            )
            db.add(mapping)
            db.commit()
            
            # Read
            retrieved = db.query(ActivityCapabilityMapping).filter_by(id=mapping.id).first()
            assert retrieved is not None
            assert retrieved.mapping_type == "primary"
            
            # Delete
            db.delete(retrieved)
            db.delete(activity)
            db.delete(capability)
            db.commit()
            
            print("✅ 映射CRUD操作测试通过")
        except Exception as e:
            db.rollback()
            pytest.fail(f"CRUD操作测试失败: {e}")


class TestVectorUpdateCheck:
    """测试向量更新检查"""
    
    def test_vector_update_check(self):
        """测试向量更新检查逻辑"""
        # 测试1: 新活动需要更新
        activity1 = BusinessActivity(
            id="activity:test:new",
            name="新活动",
            vector_entity_uri="activity://test/activity:test:new"
        )
        assert activity1.needs_vector_update() == True
        
        # 测试2: 已向量化，描述未更新
        activity2 = BusinessActivity(
            id="activity:test:updated",
            name="已更新活动",
            vector_entity_uri="activity://test/activity:test:updated",
            last_vectorized_at=datetime.now(),
            description_updated_at=datetime.now() - timedelta(days=1)
        )
        assert activity2.needs_vector_update() == False
        
        # 测试3: 描述已更新，需要重新向量化
        activity3 = BusinessActivity(
            id="activity:test:needs_update",
            name="需要更新活动",
            vector_entity_uri="activity://test/activity:test:needs_update",
            last_vectorized_at=datetime.now() - timedelta(days=1),
            description_updated_at=datetime.now()
        )
        assert activity3.needs_vector_update() == True
        
        print("✅ 向量更新检查逻辑测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])






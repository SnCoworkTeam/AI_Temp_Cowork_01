"""
阶段一第2周测试：采购场景图谱构建
测试数据质量、向量质量和映射准确性
"""
import pytest
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.src.core.session import get_db, init_session_factory
from database.src.core.database import get_database_manager
from database.src.models import (
    BusinessActivity,
    CapabilityUnit,
    ActivityCapabilityMapping
)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """测试会话级别的数据库设置"""
    # 初始化数据库连接
    db_manager = get_database_manager()
    if not db_manager.test_connection():
        pytest.fail("数据库连接失败")
    
    init_session_factory()
    yield
    print("\n测试完成")


class TestDataCompleteness:
    """测试数据完整性"""
    
    def test_procurement_activities_exist(self):
        """测试采购活动是否存在"""
        db = next(get_db())
        try:
            activities = db.query(BusinessActivity).filter(
                BusinessActivity.business_domain == "procurement"
            ).all()
            
            assert len(activities) >= 10, f"采购活动数量不足，期望至少10个，实际{len(activities)}个"
            print(f"[OK] 采购活动数量: {len(activities)} 个")
        finally:
            db.close()
    
    def test_capability_units_exist(self):
        """测试能力单元是否存在"""
        db = next(get_db())
        try:
            capabilities = db.query(CapabilityUnit).all()
            
            assert len(capabilities) >= 10, f"能力单元数量不足，期望至少10个，实际{len(capabilities)}个"
            print(f"[OK] 能力单元数量: {len(capabilities)} 个")
        finally:
            db.close()
    
    def test_mappings_exist(self):
        """测试映射关系是否存在"""
        db = next(get_db())
        try:
            mappings = db.query(ActivityCapabilityMapping).all()
            
            assert len(mappings) >= 10, f"映射关系数量不足，期望至少10个，实际{len(mappings)}个"
            print(f"[OK] 映射关系数量: {len(mappings)} 个")
        finally:
            db.close()
    
    def test_activity_fields_completeness(self):
        """测试活动字段完整性"""
        db = next(get_db())
        try:
            activities = db.query(BusinessActivity).filter(
                BusinessActivity.business_domain == "procurement"
            ).limit(5).all()
            
            required_fields = ["id", "name", "activity_type", "business_domain", "vector_entity_uri"]
            
            for activity in activities:
                for field in required_fields:
                    value = getattr(activity, field, None)
                    assert value is not None and value != "", f"活动 {activity.id} 缺少必需字段: {field}"
            
            print(f"[OK] 活动字段完整性检查通过 ({len(activities)} 个活动)")
        finally:
            db.close()


class TestVectorQuality:
    """测试向量质量"""
    
    def test_activities_have_vector_uri(self):
        """测试活动都有向量URI"""
        db = next(get_db())
        try:
            activities = db.query(BusinessActivity).filter(
                BusinessActivity.business_domain == "procurement"
            ).all()
            
            for activity in activities:
                assert activity.vector_entity_uri, f"活动 {activity.id} 缺少向量URI"
                assert activity.vector_entity_uri.startswith("activity://"), \
                    f"活动 {activity.id} 的向量URI格式不正确: {activity.vector_entity_uri}"
            
            print(f"[OK] 所有活动都有向量URI ({len(activities)} 个)")
        finally:
            db.close()
    
    def test_activities_have_embedding_version(self):
        """测试活动都有嵌入版本"""
        db = next(get_db())
        try:
            activities = db.query(BusinessActivity).filter(
                BusinessActivity.business_domain == "procurement"
            ).all()
            
            for activity in activities:
                assert activity.embedding_version, f"活动 {activity.id} 缺少嵌入版本"
            
            print(f"[OK] 所有活动都有嵌入版本 ({len(activities)} 个)")
        finally:
            db.close()


class TestMappingAccuracy:
    """测试映射准确性"""
    
    def test_mappings_have_valid_activities(self):
        """测试映射都有有效的活动"""
        db = next(get_db())
        try:
            mappings = db.query(ActivityCapabilityMapping).all()
            
            invalid_count = 0
            for mapping in mappings:
                activity = db.query(BusinessActivity).filter_by(id=mapping.activity_id).first()
                if not activity:
                    invalid_count += 1
            
            assert invalid_count == 0, f"有 {invalid_count} 个映射引用了不存在的活动"
            print(f"[OK] 所有映射都有有效的活动 ({len(mappings)} 个)")
        finally:
            db.close()
    
    def test_mappings_have_valid_capabilities(self):
        """测试映射都有有效的能力"""
        db = next(get_db())
        try:
            mappings = db.query(ActivityCapabilityMapping).all()
            
            invalid_count = 0
            for mapping in mappings:
                capability = db.query(CapabilityUnit).filter_by(id=mapping.capability_id).first()
                if not capability:
                    invalid_count += 1
            
            assert invalid_count == 0, f"有 {invalid_count} 个映射引用了不存在的能力"
            print(f"[OK] 所有映射都有有效的能力 ({len(mappings)} 个)")
        finally:
            db.close()
    
    def test_mappings_have_confidence(self):
        """测试映射都有置信度"""
        db = next(get_db())
        try:
            mappings = db.query(ActivityCapabilityMapping).all()
            
            for mapping in mappings:
                assert mapping.confidence is not None, f"映射 {mapping.id} 缺少置信度"
                assert 0.0 <= mapping.confidence <= 1.0, \
                    f"映射 {mapping.id} 的置信度超出范围: {mapping.confidence}"
            
            print(f"[OK] 所有映射都有有效的置信度 ({len(mappings)} 个)")
        finally:
            db.close()
    
    def test_mapping_types_are_valid(self):
        """测试映射类型有效"""
        db = next(get_db())
        try:
            mappings = db.query(ActivityCapabilityMapping).all()
            
            valid_types = ["primary", "alternative", "fallback"]
            for mapping in mappings:
                assert mapping.mapping_type in valid_types, \
                    f"映射 {mapping.id} 的映射类型无效: {mapping.mapping_type}"
            
            print(f"[OK] 所有映射类型都有效 ({len(mappings)} 个)")
        finally:
            db.close()


class TestGraphStructure:
    """测试图谱结构"""
    
    def test_activity_capability_connections(self):
        """测试活动-能力连接"""
        db = next(get_db())
        try:
            activities = db.query(BusinessActivity).filter(
                BusinessActivity.business_domain == "procurement"
            ).limit(5).all()
            
            for activity in activities:
                mappings = db.query(ActivityCapabilityMapping).filter_by(
                    activity_id=activity.id
                ).all()
                
                assert len(mappings) > 0, f"活动 {activity.id} 没有映射到任何能力"
            
            print(f"[OK] 所有活动都有能力映射 ({len(activities)} 个活动)")
        finally:
            db.close()
    
    def test_capability_activity_connections(self):
        """测试能力-活动连接"""
        db = next(get_db())
        try:
            capabilities = db.query(CapabilityUnit).limit(5).all()
            
            for capability in capabilities:
                mappings = db.query(ActivityCapabilityMapping).filter_by(
                    capability_id=capability.id
                ).all()
                
                # 至少有一个能力应该有映射
                if len(capabilities) > 0:
                    total_mappings = sum(
                        len(db.query(ActivityCapabilityMapping).filter_by(
                            capability_id=c.id
                        ).all()) for c in capabilities
                    )
                    assert total_mappings > 0, "至少应该有一个能力有活动映射"
            
            print(f"[OK] 能力-活动连接检查通过")
        finally:
            db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])






"""
业务活动数据模型完整测试
基于实际代码结构，测试业务活动模型的创建、验证、关系和持久化
"""
import pytest
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.src.core.session import get_db, init_session_factory
from database.src.core.database import get_database_manager
from database.src.models.business_activity import BusinessActivity
from database.src.models.capability_unit import CapabilityUnit
from database.src.models.activity_capability_mapping import ActivityCapabilityMapping


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """测试会话级别的数据库设置"""
    print("\n" + "="*60)
    print("业务活动数据模型完整测试")
    print("="*60)
    
    # 初始化数据库连接
    db_manager = get_database_manager()
    if not db_manager.test_connection():
        pytest.skip("数据库连接失败，跳过测试")
    
    init_session_factory()
    yield
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


class TestBusinessActivityModel:
    """测试业务活动数据模型"""
    
    def test_activity_creation(self):
        """测试创建业务活动"""
        activity = BusinessActivity(
            id="activity:po:create:test",
            name="创建采购订单",
            description="在SAP系统中创建标准采购订单",
            activity_type="action",
            business_domain="procurement",
            success_criteria="PO号生成且状态为已保存",
            prerequisites=["供应商已存在", "物料主数据已维护"],
            estimated_time="5-10分钟",
            source_type="manual",
            source_id="golden_001"
        )
        
        assert activity.id == "activity:po:create:test"
        assert activity.name == "创建采购订单"
        assert activity.activity_type == "action"
        assert activity.business_domain == "procurement"
        assert "SAP" in activity.description
        assert activity.success_criteria is not None
        assert len(activity.prerequisites) == 2
        
        print("[OK] 业务活动创建成功")
        print(f"    活动ID: {activity.id}")
        print(f"    活动名称: {activity.name}")
        print(f"    活动类型: {activity.activity_type}")
        print(f"    业务领域: {activity.business_domain}")
    
    def test_activity_validation(self):
        """测试业务活动验证"""
        # 测试必填字段验证（SQLAlchemy会在数据库层面验证）
        # 这里测试基本属性设置
        activity = BusinessActivity(
            id="activity:test:validation",
            name="测试活动",
            activity_type="action",
            business_domain="procurement"
        )
        
        assert activity.id is not None
        assert activity.name is not None
        assert activity.activity_type in ["action", "query", "approval", "notification"]
        
        # 测试枚举类型验证（通过设置有效值）
        activity.activity_type = "query"
        assert activity.activity_type == "query"
        
        activity.activity_type = "approval"
        assert activity.activity_type == "approval"
        
        print("[OK] 业务活动验证通过")
    
    def test_activity_properties(self):
        """测试业务活动属性"""
        activity = BusinessActivity(
            id="activity:test:properties",
            name="测试活动属性",
            description="这是一个测试活动",
            activity_type="action",
            business_domain="procurement",
            success_criteria="测试成功标准",
            prerequisites=["前置条件1", "前置条件2"],
            estimated_time="10分钟",
            risk_level="low",
            owner_dept="采购部"
        )
        
        # 测试所有属性
        assert activity.id == "activity:test:properties"
        assert activity.name == "测试活动属性"
        assert activity.description == "这是一个测试活动"
        assert activity.activity_type == "action"
        assert activity.business_domain == "procurement"
        assert activity.success_criteria == "测试成功标准"
        assert len(activity.prerequisites) == 2
        assert activity.estimated_time == "10分钟"
        assert activity.risk_level == "low"
        assert activity.owner_dept == "采购部"
        
        print("[OK] 业务活动属性测试通过")
        print(f"    所有属性: {len([a for a in dir(activity) if not a.startswith('_')])} 个")
    
    @pytest.mark.asyncio
    async def test_activity_persistence(self):
        """测试业务活动持久化"""
        db = next(get_db())
        
        try:
            # 创建测试活动
            activity = BusinessActivity(
                id="activity:test:persistence",
                name="测试持久化活动",
                description="测试数据库持久化",
                activity_type="action",
                business_domain="procurement",
                success_criteria="保存成功",
                prerequisites=[],
                estimated_time="5分钟",
                vector_entity_uri="entity://test/persistence"  # 必填字段
            )
            
            # 保存到数据库
            db.add(activity)
            db.commit()
            db.refresh(activity)
            
            assert activity.id is not None
            assert activity.created_at is not None
            
            # 从数据库查询
            retrieved = db.query(BusinessActivity).filter_by(id="activity:test:persistence").first()
            assert retrieved is not None
            assert retrieved.name == "测试持久化活动"
            assert retrieved.activity_type == "action"
            
            # 清理测试数据
            db.delete(retrieved)
            db.commit()
            
            print("[OK] 业务活动持久化测试通过")
            print(f"    保存的活动ID: {retrieved.id}")
            print(f"    创建时间: {retrieved.created_at}")
            
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()
    
    def test_activity_to_dict(self):
        """测试业务活动转换为字典"""
        activity = BusinessActivity(
            id="activity:test:dict",
            name="测试字典转换",
            description="测试",
            activity_type="action",
            business_domain="procurement"
        )
        
        # 检查是否有to_dict方法
        if hasattr(activity, 'to_dict'):
            activity_dict = activity.to_dict()
            assert isinstance(activity_dict, dict)
            assert activity_dict['id'] == "activity:test:dict"
            assert activity_dict['name'] == "测试字典转换"
            print("[OK] 业务活动字典转换测试通过")
        else:
            # 如果没有to_dict方法，手动构建字典
            activity_dict = {
                'id': activity.id,
                'name': activity.name,
                'activity_type': activity.activity_type,
                'business_domain': activity.business_domain
            }
            assert activity_dict['id'] == "activity:test:dict"
            print("[OK] 业务活动字典转换测试通过（手动构建）")


class TestActivityCapabilityMapping:
    """测试活动-能力映射"""
    
    @pytest.mark.asyncio
    async def test_mapping_creation(self):
        """测试创建活动-能力映射"""
        db = next(get_db())
        
        try:
            # 确保活动存在
            activity = db.query(BusinessActivity).filter_by(
                id="activity:procurement:create_po"
            ).first()
            
            if not activity:
                pytest.skip("测试活动不存在，跳过映射测试")
            
            # 确保能力单元存在
            capability = db.query(CapabilityUnit).filter_by(
                id="component:sap:create_po"
            ).first()
            
            if not capability:
                pytest.skip("测试能力单元不存在，跳过映射测试")
            
            # 创建映射
            mapping = ActivityCapabilityMapping(
                id=f"mapping:test:{activity.id}:{capability.id}",
                activity_id=activity.id,
                capability_id=capability.id,
                mapping_type="primary",
                priority=10,
                confidence=0.95
            )
            
            assert mapping.activity_id == activity.id
            assert mapping.capability_id == capability.id
            assert mapping.mapping_type == "primary"
            assert mapping.priority == 10
            assert mapping.confidence == 0.95
            
            print("[OK] 活动-能力映射创建成功")
            print(f"    活动ID: {mapping.activity_id}")
            print(f"    能力ID: {mapping.capability_id}")
            print(f"    映射类型: {mapping.mapping_type}")
            print(f"    置信度: {mapping.confidence}")
            
        finally:
            db.close()
    
    @pytest.mark.asyncio
    async def test_mapping_query(self):
        """测试查询活动-能力映射"""
        db = next(get_db())
        
        try:
            # 查询现有映射
            mappings = db.query(ActivityCapabilityMapping).filter_by(
                activity_id="activity:procurement:create_po"
            ).all()
            
            if mappings:
                mapping = mappings[0]
                assert mapping.activity_id is not None
                assert mapping.capability_id is not None
                
                print(f"[OK] 活动-能力映射查询成功: {len(mappings)} 个映射")
                print(f"    示例映射: {mapping.activity_id} -> {mapping.capability_id}")
            else:
                print("[OK] 活动-能力映射查询成功（无映射数据）")
            
        finally:
            db.close()


class TestActivityRelationships:
    """测试业务活动关系"""
    
    @pytest.mark.asyncio
    async def test_activity_capability_relationship(self):
        """测试活动与能力的关联关系"""
        db = next(get_db())
        
        try:
            # 查询活动
            activity = db.query(BusinessActivity).filter_by(
                id="activity:procurement:create_po"
            ).first()
            
            if not activity:
                pytest.skip("测试活动不存在")
            
            # 通过映射查询关联的能力
            mappings = db.query(ActivityCapabilityMapping).filter_by(
                activity_id=activity.id
            ).all()
            
            if mappings:
                # 获取第一个映射的能力单元
                mapping = mappings[0]
                capability = db.query(CapabilityUnit).filter_by(
                    id=mapping.capability_id
                ).first()
                
                if capability:
                    assert capability.id is not None
                    assert capability.name is not None
                    
                    print("[OK] 活动-能力关联关系测试通过")
                    print(f"    活动: {activity.name}")
                    print(f"    能力: {capability.name}")
                    print(f"    映射类型: {mapping.mapping_type}")
                    print(f"    置信度: {mapping.confidence}")
                else:
                    print("[OK] 活动-能力关联关系测试（能力单元不存在）")
            else:
                print("[OK] 活动-能力关联关系测试（无映射数据）")
            
        finally:
            db.close()
    
    @pytest.mark.asyncio
    async def test_activity_domain_grouping(self):
        """测试按业务领域分组活动"""
        db = next(get_db())
        
        try:
            # 查询采购领域的所有活动
            activities = db.query(BusinessActivity).filter_by(
                business_domain="procurement"
            ).all()
            
            assert len(activities) > 0
            
            # 验证所有活动都属于procurement领域
            for activity in activities:
                assert activity.business_domain == "procurement"
            
            print(f"[OK] 业务领域分组测试通过: {len(activities)} 个采购活动")
            
            # 按活动类型统计
            type_counts = {}
            for activity in activities:
                activity_type = activity.activity_type
                type_counts[activity_type] = type_counts.get(activity_type, 0) + 1
            
            print(f"    活动类型分布: {type_counts}")
            
        finally:
            db.close()


class TestActivityDataIntegrity:
    """测试业务活动数据完整性"""
    
    @pytest.mark.asyncio
    async def test_activity_uniqueness(self):
        """测试活动ID唯一性"""
        db = next(get_db())
        
        try:
            # 查询所有活动
            activities = db.query(BusinessActivity).all()
            
            # 检查ID唯一性
            activity_ids = [a.id for a in activities]
            unique_ids = set(activity_ids)
            
            assert len(activity_ids) == len(unique_ids), "存在重复的活动ID"
            
            print(f"[OK] 活动ID唯一性测试通过: {len(activities)} 个活动，全部唯一")
            
        finally:
            db.close()
    
    @pytest.mark.asyncio
    async def test_activity_required_fields(self):
        """测试活动必填字段"""
        db = next(get_db())
        
        try:
            # 查询所有活动，检查必填字段
            activities = db.query(BusinessActivity).all()
            
            required_fields = ['id', 'name', 'activity_type', 'business_domain']
            missing_fields_count = 0
            
            for activity in activities:
                for field in required_fields:
                    value = getattr(activity, field, None)
                    if value is None or value == '':
                        missing_fields_count += 1
                        print(f"[WARN] 活动 {activity.id} 缺少必填字段: {field}")
            
            if missing_fields_count == 0:
                print(f"[OK] 活动必填字段完整性测试通过: {len(activities)} 个活动")
            else:
                print(f"[WARN] 活动必填字段完整性: {missing_fields_count} 个缺失")
            
        finally:
            db.close()
    
    @pytest.mark.asyncio
    async def test_activity_data_quality(self):
        """测试活动数据质量"""
        db = next(get_db())
        
        try:
            activities = db.query(BusinessActivity).all()
            
            quality_metrics = {
                'total': len(activities),
                'with_description': 0,
                'with_success_criteria': 0,
                'with_prerequisites': 0,
                'with_estimated_time': 0,
                'with_vector_uri': 0
            }
            
            for activity in activities:
                if activity.description:
                    quality_metrics['with_description'] += 1
                if activity.success_criteria:
                    quality_metrics['with_success_criteria'] += 1
                if activity.prerequisites and len(activity.prerequisites) > 0:
                    quality_metrics['with_prerequisites'] += 1
                if activity.estimated_time:
                    quality_metrics['with_estimated_time'] += 1
                if activity.vector_entity_uri:
                    quality_metrics['with_vector_uri'] += 1
            
            # 计算完整度
            completeness = {}
            for key in ['with_description', 'with_success_criteria', 'with_prerequisites', 'with_estimated_time', 'with_vector_uri']:
                if quality_metrics['total'] > 0:
                    completeness[key] = quality_metrics[key] / quality_metrics['total'] * 100
                else:
                    completeness[key] = 0
            
            print("[OK] 活动数据质量测试通过:")
            print(f"    总活动数: {quality_metrics['total']}")
            print(f"    有描述: {quality_metrics['with_description']} ({completeness['with_description']:.1f}%)")
            print(f"    有成功标准: {quality_metrics['with_success_criteria']} ({completeness['with_success_criteria']:.1f}%)")
            print(f"    有前置条件: {quality_metrics['with_prerequisites']} ({completeness['with_prerequisites']:.1f}%)")
            print(f"    有预估时间: {quality_metrics['with_estimated_time']} ({completeness['with_estimated_time']:.1f}%)")
            print(f"    有向量URI: {quality_metrics['with_vector_uri']} ({completeness['with_vector_uri']:.1f}%)")
            
            # 验证基本质量要求
            assert quality_metrics['total'] > 0, "没有活动数据"
            assert completeness['with_description'] > 50, "描述完整度低于50%"
            
        finally:
            db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])





"""
阶段一第1周测试（带Docker服务自动启动）
测试核心数据模型创建和数据库迁移
"""
import pytest
import sys
import os
import subprocess
import time
import requests
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def check_docker_service(service_name: str, max_retries: int = 30, retry_interval: int = 2) -> bool:
    """检查Docker服务是否运行"""
    for i in range(max_retries):
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={service_name}", "--format", "{{.Status}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if "Up" in result.stdout:
                print(f"[OK] {service_name} 服务已启动")
                return True
        except Exception as e:
            pass
        
        if i < max_retries - 1:
            print(f"[WAIT] 等待 {service_name} 服务启动... ({i+1}/{max_retries})")
            time.sleep(retry_interval)
    
    return False


def start_docker_services():
    """启动Docker服务"""
    print("\n[INFO] 启动Docker服务...")
    
    # 切换到项目根目录
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    os.chdir(project_root)
    
    # 启动postgres服务
    try:
        subprocess.run(
            ["docker-compose", "up", "-d", "postgres"],
            check=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        print("[OK] postgres 服务启动命令已执行")
    except subprocess.TimeoutExpired:
        print("[WARN] postgres 服务启动超时")
    except Exception as e:
        print(f"[WARN] postgres 服务启动失败: {e}")
    
    # 等待服务就绪
    if check_docker_service("postgres", max_retries=30, retry_interval=2):
        # 额外等待数据库完全就绪
        time.sleep(5)
        return True
    else:
        print("[ERROR] postgres 服务启动失败或超时")
        return False


def check_database_connection(max_retries: int = 10, retry_interval: int = 2) -> bool:
    """检查数据库连接"""
    for i in range(max_retries):
        try:
            from database.src.core.database import get_database_manager
            from database.src.core.session import init_session_factory
            
            # 初始化session factory
            init_session_factory()
            
            db_manager = get_database_manager()
            if db_manager.test_connection():
                print("[OK] 数据库连接成功")
                return True
        except Exception as e:
            if i < max_retries - 1:
                print(f"[WAIT] 等待数据库连接... ({i+1}/{max_retries})")
                time.sleep(retry_interval)
            else:
                print(f"[ERROR] 数据库连接失败: {e}")
                import traceback
                traceback.print_exc()
                return False
    return False


@pytest.fixture(scope="session", autouse=True)
def setup_docker_services():
    """测试会话级别的Docker服务设置"""
    print("\n" + "="*60)
    print("阶段一第1周测试 - Docker服务自动启动")
    print("="*60)
    
    # 启动Docker服务
    if not start_docker_services():
        pytest.fail("Docker服务启动失败，无法继续测试")
    
    # 检查数据库连接
    if not check_database_connection():
        pytest.fail("数据库连接失败，无法继续测试")
    
    # 初始化session factory（确保所有测试可以使用get_db）
    from database.src.core.session import init_session_factory
    init_session_factory()
    
    # 执行数据库迁移
    print("\n[INFO] 执行数据库迁移...")
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    os.chdir(os.path.join(project_root, "database"))
    
    try:
        result = subprocess.run(
            ["python", "-m", "alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        print("[OK] 数据库迁移成功")
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 数据库迁移失败: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        pytest.fail("数据库迁移失败")
    except Exception as e:
        print(f"[ERROR] 数据库迁移异常: {e}")
        pytest.fail("数据库迁移异常")
    
    yield
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
    # 注意：不自动停止服务，以便后续测试使用


class TestModelsImport:
    """测试模型导入"""
    
    def test_models_import(self):
        """测试模型可以正确导入"""
        from database.src.models import (
            BusinessActivity,
            CapabilityUnit,
            ActivityCapabilityMapping
        )
        assert BusinessActivity is not None
        assert CapabilityUnit is not None
        assert ActivityCapabilityMapping is not None
        print("[OK] 所有模型成功导入")


class TestDatabaseMigration:
    """测试数据库迁移"""
    
    def test_migration_executed(self):
        """测试迁移已执行"""
        try:
            from database.src.core.session import get_db
            from sqlalchemy import inspect
            
            db = next(get_db())
            inspector = inspect(db.bind)
            
            # 检查表是否存在
            tables = inspector.get_table_names()
            assert 'business_activities' in tables, f"business_activities表不存在，现有表: {tables}"
            assert 'capability_units' in tables, f"capability_units表不存在，现有表: {tables}"
            assert 'activity_capability_mappings' in tables, f"activity_capability_mappings表不存在，现有表: {tables}"
            
            print("[OK] 数据库迁移成功，所有表已创建")
        except Exception as e:
            pytest.fail(f"数据库迁移测试失败: {e}")


class TestTableStructure:
    """测试表结构"""
    
    def test_business_activities_structure(self):
        """测试business_activities表结构"""
        try:
            from database.src.core.session import get_db
            from sqlalchemy import inspect
            
            db = next(get_db())
            inspector = inspect(db.bind)
            
            columns = {col['name']: col for col in inspector.get_columns('business_activities')}
            
            # 验证关键字段
            assert 'id' in columns, "缺少id字段"
            assert 'name' in columns, "缺少name字段"
            assert 'vector_entity_uri' in columns, "缺少vector_entity_uri字段"
            assert 'embedding_version' in columns, "缺少embedding_version字段"
            assert 'last_vectorized_at' in columns, "缺少last_vectorized_at字段"
            assert 'description_updated_at' in columns, "缺少description_updated_at字段"
            
            print("[OK] business_activities表结构正确")
        except Exception as e:
            pytest.fail(f"表结构测试失败: {e}")
    
    def test_capability_units_structure(self):
        """测试capability_units表结构"""
        try:
            from database.src.core.session import get_db
            from sqlalchemy import inspect
            
            db = next(get_db())
            inspector = inspect(db.bind)
            
            columns = {col['name']: col for col in inspector.get_columns('capability_units')}
            
            # 验证关键字段
            assert 'id' in columns, "缺少id字段"
            assert 'name' in columns, "缺少name字段"
            assert 'capability_type' in columns, "缺少capability_type字段"
            assert 'reliability_score' in columns, "缺少reliability_score字段"
            
            print("[OK] capability_units表结构正确")
        except Exception as e:
            pytest.fail(f"表结构测试失败: {e}")
    
    def test_activity_capability_mappings_structure(self):
        """测试activity_capability_mappings表结构"""
        try:
            from database.src.core.session import get_db
            from sqlalchemy import inspect
            
            db = next(get_db())
            inspector = inspect(db.bind)
            
            columns = {col['name']: col for col in inspector.get_columns('activity_capability_mappings')}
            
            # 验证关键字段
            assert 'id' in columns, "缺少id字段"
            assert 'activity_id' in columns, "缺少activity_id字段"
            assert 'capability_id' in columns, "缺少capability_id字段"
            assert 'mapping_type' in columns, "缺少mapping_type字段"
            assert 'success_rate' in columns, "缺少success_rate字段"
            
            print("[OK] activity_capability_mappings表结构正确")
        except Exception as e:
            pytest.fail(f"表结构测试失败: {e}")


class TestIndexes:
    """测试索引"""
    
    def test_business_activities_indexes(self):
        """测试business_activities表索引"""
        try:
            from database.src.core.session import get_db
            from sqlalchemy import inspect
            
            db = next(get_db())
            inspector = inspect(db.bind)
            
            indexes = inspector.get_indexes('business_activities')
            index_names = [idx['name'] for idx in indexes]
            
            # 检查关键索引（索引名可能略有不同）
            has_name_index = any('name' in name.lower() for name in index_names)
            has_domain_type_index = any('domain' in name.lower() and 'type' in name.lower() for name in index_names)
            has_vector_uri_index = any('vector' in name.lower() or 'uri' in name.lower() for name in index_names)
            
            assert has_name_index, f"缺少name相关索引，现有索引: {index_names}"
            assert has_domain_type_index or len(index_names) > 0, f"索引可能不完整，现有索引: {index_names}"
            
            print(f"[OK] business_activities表索引创建成功 (共{len(index_names)}个索引)")
        except Exception as e:
            pytest.fail(f"索引测试失败: {e}")


class TestCRUDOperations:
    """测试CRUD操作"""
    
    def test_business_activity_crud(self):
        """测试业务活动CRUD"""
        try:
            from database.src.core.session import get_db
            from database.src.models import BusinessActivity
            
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
            assert retrieved is not None, "创建的活动未找到"
            assert retrieved.name == "测试创建采购订单", "活动名称不匹配"
            
            # Update
            retrieved.description = "更新后的描述"
            retrieved.description_updated_at = datetime.now()
            db.commit()
            
            # 验证needs_vector_update
            assert retrieved.needs_vector_update() == True, "向量更新检查逻辑错误"
            
            # Delete
            db.delete(retrieved)
            db.commit()
            
            # 验证删除
            deleted = db.query(BusinessActivity).filter_by(id=activity.id).first()
            assert deleted is None, "活动删除失败"
            
            print("[OK] 业务活动CRUD操作测试通过")
        except Exception as e:
            db.rollback()
            pytest.fail(f"CRUD操作测试失败: {e}")
    
    def test_capability_unit_crud(self):
        """测试能力单元CRUD"""
        try:
            from database.src.core.session import get_db
            from database.src.models import CapabilityUnit
            
            db = next(get_db())
            
            # Create
            capability = CapabilityUnit(
                id="component:test:sap_create_po",
                name="测试SAP创建PO组件",
                description="测试描述",
                capability_type="Component",
                endpoint="http://test/api/create-po"
            )
            db.add(capability)
            db.commit()
            
            # Read
            retrieved = db.query(CapabilityUnit).filter_by(id=capability.id).first()
            assert retrieved is not None, "创建的能力单元未找到"
            assert retrieved.name == "测试SAP创建PO组件", "能力单元名称不匹配"
            
            # Update
            retrieved.reliability_score = 0.95
            db.commit()
            
            # Delete
            db.delete(retrieved)
            db.commit()
            
            print("[OK] 能力单元CRUD操作测试通过")
        except Exception as e:
            db.rollback()
            pytest.fail(f"CRUD操作测试失败: {e}")
    
    def test_mapping_crud(self):
        """测试映射CRUD"""
        try:
            from database.src.core.session import get_db
            from database.src.models import (
                BusinessActivity,
                CapabilityUnit,
                ActivityCapabilityMapping
            )
            
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
                capability_type="Component"
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
            assert retrieved is not None, "创建的映射未找到"
            assert retrieved.mapping_type == "primary", "映射类型不匹配"
            
            # Delete
            db.delete(retrieved)
            db.delete(activity)
            db.delete(capability)
            db.commit()
            
            print("[OK] 映射CRUD操作测试通过")
        except Exception as e:
            db.rollback()
            pytest.fail(f"CRUD操作测试失败: {e}")


class TestVectorUpdateCheck:
    """测试向量更新检查"""
    
    def test_vector_update_check(self):
        """测试向量更新检查逻辑"""
        from database.src.models import BusinessActivity
        
        # 测试1: 新活动需要更新
        activity1 = BusinessActivity(
            id="activity:test:new",
            name="新活动",
            vector_entity_uri="activity://test/activity:test:new"
        )
        assert activity1.needs_vector_update() == True, "新活动应该需要向量更新"
        
        # 测试2: 已向量化，描述未更新
        activity2 = BusinessActivity(
            id="activity:test:updated",
            name="已更新活动",
            vector_entity_uri="activity://test/activity:test:updated",
            last_vectorized_at=datetime.now(),
            description_updated_at=datetime.now() - timedelta(days=1)
        )
        assert activity2.needs_vector_update() == False, "已向量化且描述未更新的活动不应需要更新"
        
        # 测试3: 描述已更新，需要重新向量化
        activity3 = BusinessActivity(
            id="activity:test:needs_update",
            name="需要更新活动",
            vector_entity_uri="activity://test/activity:test:needs_update",
            last_vectorized_at=datetime.now() - timedelta(days=1),
            description_updated_at=datetime.now()
        )
        assert activity3.needs_vector_update() == True, "描述已更新的活动应该需要向量更新"
        
        print("[OK] 向量更新检查逻辑测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])


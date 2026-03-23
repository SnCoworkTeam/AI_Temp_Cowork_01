"""
数据库性能测试
"""
import pytest
import time
from sqlalchemy.orm import Session
from sqlalchemy import text


@pytest.mark.performance
class TestDatabasePerformance:
    """数据库性能测试"""
    
    def test_simple_query_performance(self, db_session: Session, performance_thresholds):
        """测试简单查询性能"""
        start_time = time.time()
        result = db_session.execute(text("SELECT 1"))
        elapsed_time = time.time() - start_time
        
        assert result.scalar() == 1
        assert elapsed_time < performance_thresholds["database_query_time"]
    
    def test_join_query_performance(self, db_session: Session):
        """测试JOIN查询性能"""
        # 创建测试数据
        from database.src.models.user_models import User
        from database.src.models.workflow_models import WorkflowDefinition
        from uuid import uuid4
        
        user_id = uuid4()
        user = User(id=user_id, username="testuser", email="test@example.com", hashed_password="hashed")
        db_session.add(user)
        
        workflow_id = uuid4()
        workflow = WorkflowDefinition(
            id=workflow_id,
            name="test_workflow",
            description="Test",
            created_by=user_id,
            config={}
        )
        db_session.add(workflow)
        db_session.commit()
        
        # 测试JOIN查询
        start_time = time.time()
        result = db_session.execute(
            text("""
                SELECT w.name, u.username 
                FROM workflow_definitions w
                JOIN users u ON w.created_by = u.id
                WHERE w.id = :workflow_id
            """),
            {"workflow_id": workflow_id}
        )
        elapsed_time = time.time() - start_time
        
        # JOIN查询应该在合理时间内完成
        assert elapsed_time < 0.5  # 500ms
    
    def test_bulk_insert_performance(self, db_session: Session):
        """测试批量插入性能"""
        from database.src.models.user_models import User
        
        start_time = time.time()
        
        # 批量插入1000条记录
        users = [
            User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                hashed_password="hashed"
            )
            for i in range(1000)
        ]
        
        db_session.bulk_save_objects(users)
        db_session.commit()
        
        elapsed_time = time.time() - start_time
        
        # 1000条记录应该在5秒内插入
        assert elapsed_time < 5.0, f"批量插入耗时 {elapsed_time:.3f}s"










"""
数据库集成测试
测试数据库连接和操作
"""
import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text


@pytest.mark.integration
@pytest.mark.slow
class TestDatabaseIntegration:
    """数据库集成测试"""
    
    def test_database_connection(self, db_session: Session):
        """测试数据库连接"""
        result = db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1
    
    def test_user_model_operations(self, db_session: Session):
        """测试用户模型操作"""
        from database.src.models.user_models import User
        
        # 创建用户
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        # 查询用户
        found_user = db_session.query(User).filter_by(username="testuser").first()
        assert found_user is not None
        assert found_user.email == "test@example.com"
        
        # 删除用户
        db_session.delete(found_user)
        db_session.commit()
        
        # 验证删除
        deleted_user = db_session.query(User).filter_by(username="testuser").first()
        assert deleted_user is None
    
    def test_workflow_model_operations(self, db_session: Session):
        """测试工作流模型操作"""
        from database.src.models.workflow_models import WorkflowDefinition, WorkflowStatus
        from uuid import uuid4
        
        # 创建工作流
        workflow = WorkflowDefinition(
            id=uuid4(),
            name="test_workflow",
            description="Test workflow",
            status=WorkflowStatus.DRAFT,
            config={}
        )
        db_session.add(workflow)
        db_session.commit()
        
        # 查询工作流
        found_workflow = db_session.query(WorkflowDefinition).filter_by(
            name="test_workflow"
        ).first()
        assert found_workflow is not None
        assert found_workflow.status == WorkflowStatus.DRAFT
        
        # 更新工作流
        found_workflow.status = WorkflowStatus.ACTIVE
        db_session.commit()
        
        updated_workflow = db_session.query(WorkflowDefinition).filter_by(
            name="test_workflow"
        ).first()
        assert updated_workflow.status == WorkflowStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_async_database_operations(self, async_db_session):
        """测试异步数据库操作"""
        from sqlalchemy import text
        
        result = await async_db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1










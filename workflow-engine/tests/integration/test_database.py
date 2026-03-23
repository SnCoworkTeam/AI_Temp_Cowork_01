"""
Workflow Engine 数据库集成测试
"""
import pytest
from sqlalchemy.orm import Session


@pytest.mark.integration
class TestWorkflowDatabase:
    """工作流数据库测试"""
    
    def test_workflow_crud_operations(self, db_session: Session):
        """测试工作流CRUD操作"""
        from database.src.models.workflow_models import (
            WorkflowDefinition, WorkflowStatus
        )
        from workflow_engine.src.repositories.workflow_repository import WorkflowRepository
        from uuid import uuid4
        
        repo = WorkflowRepository(db_session)
        
        # 创建
        workflow_id = uuid4()
        workflow = WorkflowDefinition(
            id=workflow_id,
            name="test_workflow",
            description="Test",
            status=WorkflowStatus.DRAFT,
            config={}
        )
        db_session.add(workflow)
        db_session.commit()
        
        # 读取
        found = repo.get_by_id(workflow_id)
        assert found is not None
        assert found.name == "test_workflow"
        
        # 更新
        found.status = WorkflowStatus.ACTIVE
        db_session.commit()
        
        updated = repo.get_by_id(workflow_id)
        assert updated.status == WorkflowStatus.ACTIVE
        
        # 删除
        db_session.delete(updated)
        db_session.commit()
        
        deleted = repo.get_by_id(workflow_id)
        assert deleted is None










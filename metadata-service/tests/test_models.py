"""
数据模型测试
测试工作流版本相关的数据模型
"""
import pytest
from datetime import datetime

from src.models.workflow_metadata import WorkflowMetadata
from src.models.workflow_version import WorkflowVersion, WorkflowVersionTag
from tests.factories import WorkflowMetadataFactory, WorkflowVersionFactory


class TestWorkflowVersionModel:
    """工作流版本模型测试"""
    
    def test_create_workflow_version(self, test_session):
        """测试创建工作流版本"""
        # 创建工作流元数据
        workflow_data = WorkflowMetadataFactory.create()
        workflow = WorkflowMetadata(**workflow_data)
        test_session.add(workflow)
        test_session.commit()
        
        # 创建工作流版本
        version_data = WorkflowVersionFactory.create(workflow_id=workflow.workflow_id)
        version = WorkflowVersion(**version_data)
        test_session.add(version)
        test_session.commit()
        
        # 验证数据
        assert version.id is not None
        assert version.workflow_id == workflow.workflow_id
        assert version.version.startswith("v")
        assert version.is_current == True
        assert version.created_at is not None
        
    def test_version_workflow_relationship(self, test_session):
        """测试版本与工作流的关系"""
        # 创建工作流和版本
        workflow_data = WorkflowMetadataFactory.create()
        workflow = WorkflowMetadata(**workflow_data)
        test_session.add(workflow)
        test_session.commit()
        
        version1_data = WorkflowVersionFactory.create(
            workflow_id=workflow.workflow_id,
            version="v1.0",
            version_number=1
        )
        version1 = WorkflowVersion(**version1_data)
        
        version2_data = WorkflowVersionFactory.create(
            workflow_id=workflow.workflow_id,
            version="v1.1",
            version_number=2
        )
        version2 = WorkflowVersion(**version2_data)
        
        test_session.add_all([version1, version2])
        test_session.commit()
        
        # 验证关系
        test_session.refresh(workflow)
        assert len(workflow.versions) == 2
        # 按版本号降序排列
        assert workflow.versions[0].version_number == 2
        assert workflow.versions[1].version_number == 1
        
    def test_version_tags(self, test_session):
        """测试版本标签"""
        # 创建工作流和版本
        workflow_data = WorkflowMetadataFactory.create()
        workflow = WorkflowMetadata(**workflow_data)
        test_session.add(workflow)
        test_session.commit()
        
        version_data = WorkflowVersionFactory.create(workflow_id=workflow.workflow_id)
        version = WorkflowVersion(**version_data)
        test_session.add(version)
        test_session.commit()
        
        # 添加标签
        tag1 = WorkflowVersionTag(version_id=version.id, tag="stable")
        tag2 = WorkflowVersionTag(version_id=version.id, tag="production")
        test_session.add_all([tag1, tag2])
        test_session.commit()
        
        # 验证标签
        test_session.refresh(version)
        assert len(version.tags) == 2
        tag_names = [tag.tag for tag in version.tags]
        assert "stable" in tag_names
        assert "production" in tag_names
        
    def test_version_unique_constraint(self, test_session):
        """测试版本唯一约束"""
        # 创建工作流
        workflow_data = WorkflowMetadataFactory.create()
        workflow = WorkflowMetadata(**workflow_data)
        test_session.add(workflow)
        test_session.commit()
        
        # 创建第一个版本
        version1_data = WorkflowVersionFactory.create(
            workflow_id=workflow.workflow_id,
            version="v1.0",
            version_number=1
        )
        version1 = WorkflowVersion(**version1_data)
        test_session.add(version1)
        test_session.commit()
        
        # 尝试创建相同版本号的版本（应该失败）
        version2_data = WorkflowVersionFactory.create(
            workflow_id=workflow.workflow_id,
            version="v1.0",  # 相同版本号
            version_number=2
        )
        version2 = WorkflowVersion(**version2_data)
        test_session.add(version2)
        
        with pytest.raises(Exception):  # 应该触发唯一约束错误
            test_session.commit()
        
        test_session.rollback()


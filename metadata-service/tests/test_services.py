"""
服务层测试
测试版本管理服务的功能
"""
import pytest

from src.services.version_service import VersionService
from src.models.workflow_version import WorkflowVersionCreate
from src.models.workflow_metadata import WorkflowMetadata
from tests.factories import WorkflowMetadataFactory, WorkflowVersionFactory


class TestVersionService:
    """版本服务测试"""
    
    def test_create_version_success(self, test_session):
        """测试成功创建版本"""
        # 准备工作流
        workflow_data = WorkflowMetadataFactory.create()
        workflow = WorkflowMetadata(**workflow_data)
        test_session.add(workflow)
        test_session.commit()
        
        # 创建版本数据
        version_data = WorkflowVersionCreate(
            workflow_id=workflow.workflow_id,
            version="v2.0",
            version_number=2,
            description="Major update",
            change_summary="Added new features",
            definition={"nodes": [{"id": "node1", "type": "start"}], "connections": []},
            changes={"added_nodes": ["node1"]},
            created_by="test_user"
        )
        
        # 调用服务
        service = VersionService(test_session)
        result = service.create_version(version_data)
        
        # 验证结果
        assert result.version == "v2.0"
        assert result.version_number == 2
        assert result.is_current == True
        assert result.created_by == "test_user"
        
        # 验证工作流版本号已更新
        test_session.refresh(workflow)
        assert workflow.version == "v2.0"
    
    def test_create_version_workflow_not_found(self, test_session):
        """测试创建工作流版本时工作流不存在"""
        version_data = WorkflowVersionCreate(
            workflow_id="nonexistent_workflow",
            version="v1.0",
            version_number=1,
            definition={},
            created_by="test_user"
        )
        
        service = VersionService(test_session)
        
        with pytest.raises(ValueError, match="Workflow nonexistent_workflow not found"):
            service.create_version(version_data)
    
    def test_create_version_duplicate(self, test_session):
        """测试创建重复版本号"""
        workflow_data = WorkflowMetadataFactory.create()
        workflow = WorkflowMetadata(**workflow_data)
        test_session.add(workflow)
        test_session.commit()
        
        # 创建第一个版本
        version_data1 = WorkflowVersionCreate(
            workflow_id=workflow.workflow_id,
            version="v1.0",
            version_number=1,
            definition={},
            created_by="test_user"
        )
        
        service = VersionService(test_session)
        service.create_version(version_data1)
        
        # 尝试创建相同版本号的版本
        version_data2 = WorkflowVersionCreate(
            workflow_id=workflow.workflow_id,
            version="v1.0",  # 相同版本号
            version_number=2,
            definition={},
            created_by="test_user"
        )
        
        with pytest.raises(ValueError, match="Version v1.0 already exists"):
            service.create_version(version_data2)
    
    def test_get_versions_pagination(self, test_session):
        """测试版本列表分页"""
        workflow_data = WorkflowMetadataFactory.create()
        workflow = WorkflowMetadata(**workflow_data)
        test_session.add(workflow)
        test_session.commit()
        
        # 创建多个版本
        service = VersionService(test_session)
        for i in range(5):
            version_data = WorkflowVersionCreate(
                workflow_id=workflow.workflow_id,
                version=f"v1.{i}",
                version_number=i + 1,
                definition={},
                created_by="test_user"
            )
            service.create_version(version_data)
        
        # 测试分页
        result = service.get_versions(workflow.workflow_id, skip=0, limit=3)
        
        assert result["total"] == 5
        assert len(result["items"]) == 3
        assert result["page"] == 1
        assert result["page_size"] == 3
        assert result["total_pages"] == 2
        
        # 验证排序（按版本号降序）
        versions = result["items"]
        assert versions[0].version_number == 5
        assert versions[1].version_number == 4
        assert versions[2].version_number == 3
    
    def test_set_current_version(self, test_session):
        """测试设置当前版本"""
        workflow_data = WorkflowMetadataFactory.create()
        workflow = WorkflowMetadata(**workflow_data)
        test_session.add(workflow)
        test_session.commit()
        
        service = VersionService(test_session)
        
        # 创建多个版本
        version1_data = WorkflowVersionCreate(
            workflow_id=workflow.workflow_id,
            version="v1.0",
            version_number=1,
            definition={},
            created_by="test_user"
        )
        version1 = service.create_version(version1_data)
        
        version2_data = WorkflowVersionCreate(
            workflow_id=workflow.workflow_id,
            version="v2.0",
            version_number=2,
            definition={},
            created_by="test_user"
        )
        version2 = service.create_version(version2_data)
        
        # 默认v2.0是当前版本
        assert version2.is_current == True
        
        # 设置v1.0为当前版本
        result = service.set_current_version(workflow.workflow_id, "v1.0")
        
        assert result.version == "v1.0"
        assert result.is_current == True
        
        # 验证v2.0不再是当前版本
        version2_updated = service.get_version(workflow.workflow_id, "v2.0")
        assert version2_updated.is_current == False
        
        # 验证工作流版本号已更新
        test_session.refresh(workflow)
        assert workflow.version == "v1.0"
    
    def test_restore_version(self, test_session):
        """测试恢复版本"""
        workflow_data = WorkflowMetadataFactory.create()
        workflow = WorkflowMetadata(**workflow_data)
        test_session.add(workflow)
        test_session.commit()
        
        service = VersionService(test_session)
        
        # 创建基础版本
        version1_data = WorkflowVersionCreate(
            workflow_id=workflow.workflow_id,
            version="v1.0",
            version_number=1,
            definition={"nodes": [{"id": "node1", "type": "start"}]},
            created_by="test_user"
        )
        service.create_version(version1_data)
        
        # 恢复v1.0版本
        result = service.restore_version(
            workflow.workflow_id, 
            "v1.0", 
            "Restore stable version"
        )
        
        # 验证新版本创建
        assert result.version == "v2.0"  # 自动生成新版本号
        assert result.version_number == 2
        assert result.description == "Restore stable version"
        assert result.is_current == True
        assert "restored_from" in result.changes
    
    def test_version_tags_operations(self, test_session):
        """测试版本标签操作"""
        workflow_data = WorkflowMetadataFactory.create()
        workflow = WorkflowMetadata(**workflow_data)
        test_session.add(workflow)
        test_session.commit()
        
        service = VersionService(test_session)
        
        # 创建版本
        version_data = WorkflowVersionCreate(
            workflow_id=workflow.workflow_id,
            version="v1.0",
            version_number=1,
            definition={},
            created_by="test_user"
        )
        version = service.create_version(version_data)
        
        # 添加标签
        version_with_tag = service.add_version_tag(
            workflow.workflow_id, "v1.0", "stable"
        )
        
        assert "stable" in version_with_tag.tags
        
        # 添加另一个标签
        version_with_tags = service.add_version_tag(
            workflow.workflow_id, "v1.0", "production"
        )
        
        assert "stable" in version_with_tags.tags
        assert "production" in version_with_tags.tags
        
        # 移除标签
        version_after_remove = service.remove_version_tag(
            workflow.workflow_id, "v1.0", "stable"
        )
        
        assert "stable" not in version_after_remove.tags
        assert "production" in version_after_remove.tags


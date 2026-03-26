"""
API端点测试
测试工作流版本管理的RESTful API
"""
import pytest
import json

from tests.factories import WorkflowMetadataFactory, WorkflowVersionFactory


class TestWorkflowVersionsAPI:
    """工作流版本API测试"""
    
    def test_create_workflow_version_success(self, client):
        """测试成功创建版本API"""
        # 先创建工作流
        workflow_data = WorkflowMetadataFactory.create()
        workflow_response = client.post("/api/workflows", json=workflow_data)
        assert workflow_response.status_code == 200
        
        # 创建版本
        version_data = WorkflowVersionFactory.create(
            workflow_id=workflow_data["workflow_id"],
            version="v1.1",
            version_number=2
        )
        version_data["description"] = "API test version"
        version_data["created_by"] = "api_test_user"
        
        response = client.post(
            f"/api/workflows/{workflow_data['workflow_id']}/versions",
            json=version_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["version"] == "v1.1"
        assert data["is_current"] == True
        assert data["created_by"] == "api_test_user"
    
    def test_create_version_workflow_not_found(self, client):
        """测试为不存在的工作流创建版本"""
        version_data = WorkflowVersionFactory.create(
            workflow_id="nonexistent_workflow",
            version="v1.0",
            version_number=1
        )
        
        response = client.post(
            "/api/workflows/nonexistent_workflow/versions",
            json=version_data
        )
        
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_versions_list(self, client):
        """测试获取版本列表API"""
        # 准备工作流和版本
        workflow_data = WorkflowMetadataFactory.create()
        client.post("/api/workflows", json=workflow_data)
        
        # 创建多个版本
        for i in range(3):
            version_data = WorkflowVersionFactory.create(
                workflow_id=workflow_data["workflow_id"],
                version=f"v1.{i}",
                version_number=i + 1
            )
            client.post(
                f"/api/workflows/{workflow_data['workflow_id']}/versions",
                json=version_data
            )
        
        # 获取版本列表
        response = client.get(
            f"/api/workflows/{workflow_data['workflow_id']}/versions",
            params={"skip": 0, "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
        assert data["items"][0]["version"] == "v1.2"  # 最新版本在前
    
    def test_get_specific_version(self, client):
        """测试获取特定版本API"""
        # 准备工作流和版本
        workflow_data = WorkflowMetadataFactory.create()
        client.post("/api/workflows", json=workflow_data)
        
        version_data = WorkflowVersionFactory.create(
            workflow_id=workflow_data["workflow_id"],
            version="v1.5",
            version_number=5,
            definition={"special": "configuration"}
        )
        client.post(
            f"/api/workflows/{workflow_data['workflow_id']}/versions",
            json=version_data
        )
        
        # 获取特定版本
        response = client.get(
            f"/api/workflows/{workflow_data['workflow_id']}/versions/v1.5"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "v1.5"
        assert data["version_number"] == 5
        assert data["definition"]["special"] == "configuration"
    
    def test_set_current_version(self, client):
        """测试设置当前版本API"""
        # 准备工作流和版本
        workflow_data = WorkflowMetadataFactory.create()
        client.post("/api/workflows", json=workflow_data)
        
        # 创建两个版本
        version1_data = WorkflowVersionFactory.create(
            workflow_id=workflow_data["workflow_id"],
            version="v1.0",
            version_number=1
        )
        client.post(
            f"/api/workflows/{workflow_data['workflow_id']}/versions",
            json=version1_data
        )
        
        version2_data = WorkflowVersionFactory.create(
            workflow_id=workflow_data["workflow_id"],
            version="v2.0",
            version_number=2
        )
        client.post(
            f"/api/workflows/{workflow_data['workflow_id']}/versions",
            json=version2_data
        )
        
        # 设置v1.0为当前版本
        response = client.put(
            f"/api/workflows/{workflow_data['workflow_id']}/versions/v1.0/set-current"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "v1.0"
        assert data["is_current"] == True
    
    def test_restore_version(self, client):
        """测试恢复版本API"""
        # 准备工作流和版本
        workflow_data = WorkflowMetadataFactory.create()
        client.post("/api/workflows", json=workflow_data)
        
        version_data = WorkflowVersionFactory.create(
            workflow_id=workflow_data["workflow_id"],
            version="v1.0",
            version_number=1,
            definition={"original": "configuration"}
        )
        client.post(
            f"/api/workflows/{workflow_data['workflow_id']}/versions",
            json=version_data
        )
        
        # 恢复版本
        restore_data = {
            "version": "v1.0",
            "description": "Restore stable version"
        }
        response = client.post(
            f"/api/workflows/{workflow_data['workflow_id']}/versions/v1.0/restore",
            json=restore_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["version"] == "v2.0"  # 自动生成新版本号
        assert data["description"] == "Restore stable version"
        assert data["is_current"] == True
    
    def test_version_tags_operations(self, client):
        """测试版本标签操作API"""
        # 准备工作流和版本
        workflow_data = WorkflowMetadataFactory.create()
        client.post("/api/workflows", json=workflow_data)
        
        version_data = WorkflowVersionFactory.create(
            workflow_id=workflow_data["workflow_id"],
            version="v1.0",
            version_number=1
        )
        client.post(
            f"/api/workflows/{workflow_data['workflow_id']}/versions",
            json=version_data
        )
        
        # 添加标签
        response = client.post(
            f"/api/workflows/{workflow_data['workflow_id']}/versions/v1.0/tags/stable"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "stable" in data["tags"]
        
        # 添加另一个标签
        client.post(
            f"/api/workflows/{workflow_data['workflow_id']}/versions/v1.0/tags/production"
        )
        
        # 移除标签
        response = client.delete(
            f"/api/workflows/{workflow_data['workflow_id']}/versions/v1.0/tags/stable"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "stable" not in data["tags"]
        assert "production" in data["tags"]


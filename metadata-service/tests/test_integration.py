"""
集成测试
测试与Workflow Engine的集成
"""
import pytest

from tests.factories import WorkflowMetadataFactory, WorkflowVersionFactory


class TestWorkflowEngineIntegration:
    """Workflow Engine集成测试"""
    
    def test_workflow_save_version_creation(self, client):
        """测试工作流保存时版本创建集成"""
        # 模拟Workflow Engine保存工作流
        workflow_id = "integration_test_workflow"
        
        # 1. 创建工作流元数据
        workflow_data = WorkflowMetadataFactory.create(
            workflow_id=workflow_id,
            name="Integration Test Workflow",
            definition={
                "nodes": [
                    {"id": "start", "type": "start", "position": {"x": 100, "y": 100}},
                    {"id": "llm", "type": "llm", "position": {"x": 300, "y": 100}}
                ],
                "connections": [
                    {"from": "start", "to": "llm"}
                ]
            }
        )
        
        workflow_response = client.post("/api/workflows", json=workflow_data)
        assert workflow_response.status_code == 200
        
        # 2. 创建工作流版本（模拟Workflow Engine调用）
        version_data = WorkflowVersionFactory.create(
            workflow_id=workflow_id,
            version="v1.0",
            version_number=1,
            description="Initial version",
            definition=workflow_data["definition"],
            changes={"initial": True},
            created_by="workflow_engine"
        )
        
        version_response = client.post(
            f"/api/workflows/{workflow_id}/versions",
            json=version_data
        )
        assert version_response.status_code == 201
        
        # 3. 验证版本创建成功
        versions_response = client.get(f"/api/workflows/{workflow_id}/versions")
        assert versions_response.status_code == 200
        versions_data = versions_response.json()
        
        assert versions_data["total"] == 1
        assert versions_data["items"][0]["version"] == "v1.0"
        assert versions_data["items"][0]["created_by"] == "workflow_engine"
    
    def test_version_restore_workflow(self, client):
        """测试版本恢复工作流集成"""
        workflow_id = "restore_integration_test"
        
        # 1. 创建初始工作流和版本
        workflow_data = WorkflowMetadataFactory.create(workflow_id=workflow_id)
        client.post("/api/workflows", json=workflow_data)
        
        initial_version = WorkflowVersionFactory.create(
            workflow_id=workflow_id,
            version="v1.0",
            version_number=1,
            definition={"stable": "configuration"}
        )
        client.post(f"/api/workflows/{workflow_id}/versions", json=initial_version)
        
        # 2. 模拟恢复操作
        restore_response = client.post(
            f"/api/workflows/{workflow_id}/versions/v1.0/restore",
            json={
                "version": "v1.0",
                "description": "Restore from production issue"
            }
        )
        assert restore_response.status_code == 201
        
        restore_data = restore_response.json()
        assert restore_data["version"] == "v2.0"
        assert "restored_from" in restore_data["changes"]
        
        # 3. 验证新版本成为当前版本
        versions_response = client.get(f"/api/workflows/{workflow_id}/versions")
        versions_data = versions_response.json()
        
        assert versions_data["total"] == 2
        current_versions = [v for v in versions_data["items"] if v["is_current"]]
        assert len(current_versions) == 1
        assert current_versions[0]["version"] == "v2.0"


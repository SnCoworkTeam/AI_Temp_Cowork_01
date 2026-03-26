"""
Workflow Engine API集成测试
"""
import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "workflow-engine" / "src"))


@pytest.mark.integration
class TestWorkflowEngineAPI:
    """Workflow Engine API测试"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        from src.main import app
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """测试健康检查端点"""
        response = client.get("/api/health")
        assert response.status_code == 200
    
    def test_create_workflow(self, client, sample_workflow_data):
        """测试创建工作流"""
        response = client.post(
            "/api/workflows",
            json=sample_workflow_data
        )
        assert response.status_code in [200, 201]
    
    def test_list_workflows(self, client):
        """测试列出工作流"""
        response = client.get("/api/workflows")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))










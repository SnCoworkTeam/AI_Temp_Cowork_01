"""
健康检查测试
"""
import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "workflow-engine" / "src"))

from src.main import app

client = TestClient(app)


def test_health_check():
    """测试健康检查端点"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "workflow-engine"










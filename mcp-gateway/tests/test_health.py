"""
健康检查测试
"""
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health_check():
    """测试健康检查端点"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "mcp-gateway"


def test_readiness_check():
    """测试就绪检查端点"""
    response = client.get("/api/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


def test_liveness_check():
    """测试存活检查端点"""
    response = client.get("/api/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"










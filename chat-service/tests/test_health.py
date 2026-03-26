"""
健康检查测试
"""
import pytest


def test_health_check(client):
    """测试健康检查端点"""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["service"] == "chat-service"
    assert data["version"] == "1.0.0"


def test_docs_endpoint(client):
    """测试API文档端点"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_endpoint(client):
    """测试OpenAPI规范端点"""
    response = client.get("/openapi.json")

    assert response.status_code == 200
    data = response.json()

    assert data["info"]["title"] == "Chat Service"
    assert data["info"]["version"] == "1.0.0"
    assert "paths" in data

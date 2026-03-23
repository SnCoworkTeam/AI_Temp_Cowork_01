"""
授权安全测试
"""
import pytest
import httpx


@pytest.mark.security
class TestAuthorization:
    """授权测试"""
    
    @pytest.mark.asyncio
    async def test_role_based_access_control(self):
        """测试基于角色的访问控制"""
        async with httpx.AsyncClient() as client:
            # 使用普通用户token
            headers = {"Authorization": "Bearer user_token"}
            
            # 尝试访问管理员端点
            response = await client.get(
                "http://localhost:8000/api/admin/tools",
                headers=headers
            )
            
            # 应该返回403 Forbidden
            assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_permission_based_access(self):
        """测试基于权限的访问控制"""
        async with httpx.AsyncClient() as client:
            # 使用没有特定权限的token
            headers = {"Authorization": "Bearer limited_token"}
            
            # 尝试访问需要特定权限的端点
            response = await client.post(
                "http://localhost:8000/api/admin/users",
                headers=headers,
                json={"username": "newuser"}
            )
            
            # 应该返回403
            assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_resource_ownership(self):
        """测试资源所有权验证"""
        async with httpx.AsyncClient() as client:
            # 使用用户A的token
            headers = {"Authorization": "Bearer user_a_token"}
            
            # 尝试访问用户B的资源
            response = await client.get(
                "http://localhost:8001/api/workflows/user_b_workflow_id",
                headers=headers
            )
            
            # 应该返回403或404
            assert response.status_code in [403, 404]










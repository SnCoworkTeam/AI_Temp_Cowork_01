"""
API性能测试
"""
import pytest
import time
import httpx
from typing import Dict


@pytest.mark.performance
@pytest.mark.slow
class TestAPIPerformance:
    """API性能测试"""
    
    @pytest.fixture
    def base_url(self):
        """API基础URL"""
        return "http://localhost:8000"
    
    @pytest.mark.asyncio
    async def test_health_endpoint_performance(self, base_url, performance_thresholds):
        """测试健康检查端点性能"""
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            response = await client.get(f"{base_url}/api/health")
            elapsed_time = time.time() - start_time
            
            assert response.status_code == 200
            assert elapsed_time < performance_thresholds["api_response_time"], \
                f"响应时间 {elapsed_time:.3f}s 超过阈值 {performance_thresholds['api_response_time']}s"
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, base_url):
        """测试并发请求性能"""
        import asyncio
        
        async def make_request(client):
            return await client.get(f"{base_url}/api/health")
        
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            
            # 并发100个请求
            tasks = [make_request(client) for _ in range(100)]
            responses = await asyncio.gather(*tasks)
            
            elapsed_time = time.time() - start_time
            
            # 所有请求应该成功
            assert all(r.status_code == 200 for r in responses)
            
            # 100个请求应该在5秒内完成
            assert elapsed_time < 5.0, \
                f"100个并发请求耗时 {elapsed_time:.3f}s 超过5秒"
    
    @pytest.mark.asyncio
    async def test_tool_execution_performance(self, base_url, performance_thresholds):
        """测试工具执行性能"""
        async with httpx.AsyncClient() as client:
            # 获取工具列表
            tools_response = await client.get(f"{base_url}/api/tools")
            
            if tools_response.status_code == 200:
                tools = tools_response.json()
                if tools and len(tools) > 0:
                    tool_name = tools[0].get("name")
                    
                    start_time = time.time()
                    execute_response = await client.post(
                        f"{base_url}/api/tools/{tool_name}/execute",
                        json={"parameters": {}}
                    )
                    elapsed_time = time.time() - start_time
                    
                    # 执行时间应该在阈值内
                    assert elapsed_time < performance_thresholds["api_response_time"], \
                        f"工具执行时间 {elapsed_time:.3f}s 超过阈值"


@pytest.mark.performance
class TestDatabasePerformance:
    """数据库性能测试"""
    
    def test_query_performance(self, db_session, performance_thresholds):
        """测试查询性能"""
        from sqlalchemy import text
        
        start_time = time.time()
        result = db_session.execute(text("SELECT 1"))
        elapsed_time = time.time() - start_time
        
        assert result.scalar() == 1
        assert elapsed_time < performance_thresholds["database_query_time"], \
            f"查询时间 {elapsed_time:.3f}s 超过阈值"
    
    def test_bulk_insert_performance(self, db_session):
        """测试批量插入性能"""
        from database.src.models.user_models import User
        
        start_time = time.time()
        
        # 批量插入100条记录
        users = [
            User(
                username=f"testuser{i}",
                email=f"test{i}@example.com",
                hashed_password="hashed"
            )
            for i in range(100)
        ]
        
        db_session.bulk_save_objects(users)
        db_session.commit()
        
        elapsed_time = time.time() - start_time
        
        # 100条记录应该在1秒内插入
        assert elapsed_time < 1.0, \
            f"批量插入100条记录耗时 {elapsed_time:.3f}s 超过1秒"
        
        # 清理
        db_session.query(User).filter(User.username.like("testuser%")).delete()
        db_session.commit()










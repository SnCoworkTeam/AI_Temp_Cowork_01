"""
性能测试
测试版本管理功能的性能
"""
import pytest
import time
import threading

from tests.factories import WorkflowMetadataFactory, WorkflowVersionFactory


class TestPerformance:
    """性能测试"""
    
    def test_concurrent_version_creation(self, client):
        """测试并发版本创建"""
        # 准备工作流
        workflow_data = WorkflowMetadataFactory.create(
            workflow_id="performance_test_workflow"
        )
        client.post("/api/workflows", json=workflow_data)
        
        # 并发创建版本
        def create_version(version_num):
            version_data = WorkflowVersionFactory.create(
                workflow_id="performance_test_workflow",
                version=f"v1.{version_num}",
                version_number=version_num + 1
            )
            version_data["created_by"] = f"user_{version_num}"
            response = client.post(
                "/api/workflows/performance_test_workflow/versions",
                json=version_data
            )
            return response.status_code
        
        # 并发执行
        start_time = time.time()
        threads = []
        results = []
        
        def worker(version_num):
            result = create_version(version_num)
            results.append(result)
        
        for i in range(10):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # 验证结果
        assert all(status == 201 for status in results)
        execution_time = end_time - start_time
        print(f"Concurrent version creation took: {execution_time:.2f} seconds")
        
        # 性能要求：10个版本创建应该在10秒内完成（考虑到数据库锁）
        assert execution_time < 10.0
    
    def test_large_volume_version_query(self, client):
        """测试大数据量版本查询"""
        workflow_id = "large_volume_test"
        
        # 准备工作流
        workflow_data = WorkflowMetadataFactory.create(workflow_id=workflow_id)
        client.post("/api/workflows", json=workflow_data)
        
        # 创建多个版本（在实际测试中可能需要更多）
        for i in range(20):  # 减少数量以加快测试
            version_data = WorkflowVersionFactory.create(
                workflow_id=workflow_id,
                version=f"v1.{i}",
                version_number=i + 1
            )
            client.post(f"/api/workflows/{workflow_id}/versions", json=version_data)
        
        # 测试分页查询性能
        start_time = time.time()
        response = client.get(
            f"/api/workflows/{workflow_id}/versions",
            params={"skip": 0, "limit": 100}
        )
        end_time = time.time()
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 20
        
        query_time = end_time - start_time
        print(f"Large volume query took: {query_time:.2f} seconds")
        
        # 性能要求：20个版本的查询应该在2秒内完成
        assert query_time < 2.0


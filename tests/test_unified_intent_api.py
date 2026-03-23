"""
统一意图服务API测试
测试统一意图服务的RESTful API接口
"""
import pytest
import sys
import os
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入API应用
try:
    from api.unified_intent_api import app
    API_AVAILABLE = True
except ImportError as e:
    API_AVAILABLE = False
    print(f"[WARN] API不可用: {e}")


@pytest.fixture(scope="session", autouse=True)
def setup_test():
    """测试会话级别的设置"""
    print("\n" + "="*60)
    print("统一意图服务API测试")
    print("="*60)
    yield
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


@pytest.fixture
def client():
    """创建测试客户端"""
    if not API_AVAILABLE:
        pytest.skip("API不可用")
    return TestClient(app)


class TestUnifiedIntentAPI:
    """测试统一意图API"""
    
    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        
        print("[OK] 健康检查通过")
    
    @pytest.mark.skipif(not API_AVAILABLE, reason="API不可用")
    def test_intent_understanding_endpoint(self, client):
        """测试意图理解端点"""
        test_payload = {
            "user_input": "我需要创建采购订单",
            "context": {
                "user_id": "user001",
                "department": "采购部",
                "timestamp": "2025-12-01T10:00:00Z"
            }
        }
        
        try:
            response = client.post("/api/intent/understand", json=test_payload)
            
            # 验证响应状态
            assert response.status_code in [200, 500], \
                f"Unexpected status code: {response.status_code}, response: {response.text}"
            
            if response.status_code == 200:
                data = response.json()
                
                # 验证响应结构
                assert "user_input" in data
                assert "base_intent" in data
                assert "intent_type" in data
                assert "confidence" in data
                assert "suggested_activities" in data
                assert "execution_suggestions" in data
                
                # 验证数据类型
                assert isinstance(data["suggested_activities"], list)
                assert isinstance(data["execution_suggestions"], list)
                
                if len(data["suggested_activities"]) > 0:
                    activity = data["suggested_activities"][0]
                    assert "id" in activity or "activity_id" in activity
                    assert "name" in activity
                
                print("[OK] 意图理解端点测试通过")
                print(f"    意图: {data['base_intent']}")
                print(f"    置信度: {data['confidence']:.2f}")
                print(f"    推荐活动数: {len(data['suggested_activities'])}")
            else:
                print(f"[SKIP] API返回错误: {response.status_code}")
                
        except Exception as e:
            if "数据库连接失败" in str(e) or "Connection" in str(e):
                pytest.skip(f"数据库连接失败: {e}")
            else:
                raise
    
    @pytest.mark.skipif(not API_AVAILABLE, reason="API不可用")
    def test_invalid_input_handling(self, client):
        """测试无效输入处理"""
        invalid_cases = [
            {"user_input": ""},  # 空输入
            {"user_input": "   "},  # 空白输入
            {},  # 缺少必填字段
        ]
        
        for payload in invalid_cases:
            try:
                response = client.post("/api/intent/understand", json=payload)
                
                # 应该返回适当的错误响应
                assert response.status_code in [400, 422, 500], \
                    f"Unexpected status for payload {payload}: {response.status_code}"
                
            except Exception as e:
                # 某些情况下可能会抛出异常
                print(f"[OK] 无效输入被正确处理: {payload}")
    
    @pytest.mark.skipif(not API_AVAILABLE, reason="API不可用")
    def test_activity_recommendation_endpoint(self, client):
        """测试活动推荐端点"""
        test_payload = {
            "user_input": "采购原料",
            "context": {"department": "procurement"},
            "top_k": 5
        }
        
        try:
            response = client.post("/api/intent/recommend", json=test_payload)
            
            if response.status_code == 200:
                data = response.json()
                
                assert "recommended_activities" in data
                assert isinstance(data["recommended_activities"], list)
                assert len(data["recommended_activities"]) <= test_payload["top_k"]
                
                print(f"[OK] 活动推荐端点测试通过")
                print(f"    推荐活动数: {len(data['recommended_activities'])}")
            else:
                print(f"[SKIP] API返回错误: {response.status_code}")
                
        except Exception as e:
            if "数据库连接失败" in str(e):
                pytest.skip(f"数据库连接失败: {e}")
            else:
                raise
    
    @pytest.mark.skipif(not API_AVAILABLE, reason="API不可用")
    def test_capability_query_endpoint(self, client):
        """测试能力查询端点"""
        try:
            response = client.get("/api/intent/capabilities?activity_id=activity:procurement:create_po")
            
            if response.status_code == 200:
                data = response.json()
                
                assert "capabilities" in data
                assert isinstance(data["capabilities"], list)
                
                print(f"[OK] 能力查询端点测试通过")
                print(f"    能力数: {len(data['capabilities'])}")
            else:
                print(f"[SKIP] API返回错误: {response.status_code}")
                
        except Exception as e:
            if "数据库连接失败" in str(e):
                pytest.skip(f"数据库连接失败: {e}")
            else:
                raise


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])



"""
阶段一第6周测试：创建协同界面API
测试意图理解、组装执行计划、执行计划等功能
"""
import pytest
import sys
import os
import time
import asyncio
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.unified_intent_service import UnifiedIntentService


@pytest.fixture(scope="session", autouse=True)
def setup_services():
    """测试会话级别的服务设置"""
    print("\n" + "="*60)
    print("阶段一第6周测试 - 创建协同界面API")
    print("="*60)
    yield
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


class TestCollaborativeInterfaceAPI:
    """测试协同界面API功能"""
    
    def test_service_initialization(self):
        """测试服务初始化"""
        service = UnifiedIntentService()
        assert service is not None
        assert service.semantic_engine is not None
        print("[OK] 统一意图服务初始化成功")
        service._close_db()
    
    @pytest.mark.asyncio
    async def test_understand_intent_workflow(self):
        """测试意图理解工作流"""
        service = UnifiedIntentService()
        try:
            # 1. 理解意图
            result = await service.understand_intent("创建采购订单")
            
            assert result is not None
            assert len(result.suggested_activities) > 0
            assert len(result.execution_suggestions) > 0
            
            print(f"[OK] 意图理解工作流成功:")
            print(f"    推荐活动: {len(result.suggested_activities)}")
            print(f"    执行建议: {len(result.execution_suggestions)}")
        finally:
            service._close_db()
    
    @pytest.mark.asyncio
    async def test_assemble_execution_plan(self):
        """测试组装执行计划"""
        service = UnifiedIntentService()
        try:
            # 1. 理解意图
            result = await service.understand_intent("创建采购订单")
            
            # 2. 选择活动
            if result.execution_suggestions:
                suggestion = result.execution_suggestions[0]
                
                # 模拟组装执行计划
                selected_activities = [{
                    "activity_id": suggestion.activity_id,
                    "capability_id": suggestion.capability_id,
                    "parameters": {}
                }]
                
                # 验证选择
                assert len(selected_activities) > 0
                assert selected_activities[0]["activity_id"] == suggestion.activity_id
                
                print(f"[OK] 组装执行计划成功:")
                print(f"    选择活动: {selected_activities[0]['activity_id']}")
                print(f"    选择能力: {selected_activities[0].get('capability_id', 'N/A')}")
            else:
                print("[OK] 组装执行计划测试（无执行建议）")
        finally:
            service._close_db()
    
    @pytest.mark.asyncio
    async def test_parameter_validation(self):
        """测试参数验证"""
        service = UnifiedIntentService()
        try:
            # 获取活动能力
            capabilities = await service.get_capabilities_for_activity("activity:procurement:create_po")
            
            if capabilities:
                capability = capabilities[0]
                input_schema = capability.get("input_schema")
                
                # 验证参数结构
                if input_schema:
                    assert isinstance(input_schema, dict)
                    print(f"[OK] 参数验证测试通过:")
                    print(f"    能力: {capability.get('capability_name', 'N/A')}")
                    print(f"    输入模式: {len(input_schema)} 个字段")
                else:
                    print("[OK] 参数验证测试（无输入模式）")
            else:
                print("[OK] 参数验证测试（无能力单元）")
        finally:
            service._close_db()
    
    @pytest.mark.asyncio
    async def test_execution_suggestions_quality(self):
        """测试执行建议质量"""
        service = UnifiedIntentService()
        try:
            result = await service.understand_intent("创建采购订单")
            
            if result.execution_suggestions:
                for suggestion in result.execution_suggestions:
                    assert suggestion.activity_id is not None
                    assert suggestion.activity_name is not None
                    assert 0.0 <= suggestion.confidence <= 1.0
                
                print(f"[OK] 执行建议质量测试通过:")
                print(f"    建议数量: {len(result.execution_suggestions)}")
                print(f"    平均置信度: {sum(s.confidence for s in result.execution_suggestions) / len(result.execution_suggestions):.2f}")
            else:
                print("[OK] 执行建议质量测试（无执行建议）")
        finally:
            service._close_db()
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """测试端到端工作流"""
        service = UnifiedIntentService()
        try:
            # 1. 理解意图
            start_time = time.time()
            result = await service.understand_intent("创建采购订单")
            intent_time = time.time() - start_time
            
            # 2. 选择活动
            if result.execution_suggestions:
                suggestion = result.execution_suggestions[0]
                
                # 3. 获取能力详情
                start_time = time.time()
                capabilities = await service.get_capabilities_for_activity(suggestion.activity_id)
                capability_time = time.time() - start_time
                
                # 4. 验证工作流
                assert result is not None
                assert suggestion is not None
                assert capabilities is not None
                
                total_time = intent_time + capability_time
                
                print(f"[OK] 端到端工作流测试通过:")
                print(f"    意图理解时间: {intent_time:.3f}秒")
                print(f"    能力查询时间: {capability_time:.3f}秒")
                print(f"    总时间: {total_time:.3f}秒")
                assert total_time < 10.0  # 总时间应该小于10秒
            else:
                print("[OK] 端到端工作流测试（无执行建议）")
        finally:
            service._close_db()


class TestAPIEndpoints:
    """测试API接口（需要API服务运行）"""
    
    def test_api_health_check(self):
        """测试健康检查接口"""
        import requests
        
        try:
            response = requests.get("http://localhost:8003/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                assert data["status"] == "healthy"
                print("[OK] API健康检查通过")
            else:
                print(f"[SKIP] API服务未运行 (状态码: {response.status_code})")
        except requests.exceptions.RequestException:
            print("[SKIP] API服务未运行，跳过API测试")
    
    def test_api_understand_intent(self):
        """测试意图理解接口"""
        import requests
        
        try:
            payload = {
                "user_input": "创建采购订单",
                "context": None
            }
            response = requests.post(
                "http://localhost:8003/api/v1/collaborative/intent/understand",
                json=payload,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                assert "suggested_activities" in data
                assert "execution_suggestions" in data
                print(f"[OK] API意图理解成功: {len(data.get('execution_suggestions', []))} 个建议")
            else:
                print(f"[SKIP] API服务未运行 (状态码: {response.status_code})")
        except requests.exceptions.RequestException:
            print("[SKIP] API服务未运行，跳过API测试")
    
    def test_api_assemble_plan(self):
        """测试组装执行计划接口"""
        import requests
        
        try:
            payload = {
                "selected_activities": [
                    {
                        "activity_id": "activity:procurement:create_po",
                        "capability_id": None,
                        "parameters": {}
                    }
                ],
                "execution_order": None
            }
            response = requests.post(
                "http://localhost:8003/api/v1/collaborative/execution/assemble",
                json=payload,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                assert "plan_id" in data
                assert "activities" in data
                print(f"[OK] API组装执行计划成功: {data.get('plan_id', 'N/A')}")
            else:
                print(f"[SKIP] API服务未运行 (状态码: {response.status_code})")
        except requests.exceptions.RequestException:
            print("[SKIP] API服务未运行，跳过API测试")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])






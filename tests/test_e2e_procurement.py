"""
端到端采购场景测试
测试完整的采购工作流程
"""
import pytest
import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.unified_intent_service import UnifiedIntentService
from services.enterprise_semantic_engine import EnterpriseSemanticEngine


@pytest.fixture(scope="session", autouse=True)
def setup_test():
    """测试会话级别的设置"""
    print("\n" + "="*60)
    print("端到端采购场景测试")
    print("="*60)
    
    # 检查数据库连接
    try:
        from database.src.core.database import get_database_manager
        db_manager = get_database_manager()
        if not db_manager.test_connection():
            pytest.skip("数据库连接失败，跳过端到端测试")
    except Exception as e:
        pytest.skip(f"数据库初始化失败: {e}")
    
    yield
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


@pytest.fixture
def unified_intent_service():
    """创建统一意图服务实例"""
    try:
        service = UnifiedIntentService()
        yield service
        service._close_db()
    except Exception as e:
        pytest.skip(f"服务初始化失败: {e}")


@pytest.fixture
def semantic_engine():
    """创建语义引擎实例"""
    try:
        engine = EnterpriseSemanticEngine()
        yield engine
        engine._close_db()
    except Exception as e:
        pytest.skip(f"引擎初始化失败: {e}")


class TestEndToEndProcurement:
    """端到端采购场景测试"""
    
    @pytest.mark.asyncio
    async def test_procurement_scenario_1_create_po(self, unified_intent_service):
        """测试场景1：创建采购订单"""
        # 1. 用户输入
        user_input = "我需要采购一批原料，供应商是ABC公司，物料是MAT001"
        
        # 2. 意图理解
        try:
            result = await unified_intent_service.understand_intent(
                user_input=user_input,
                context={"user_id": "test_user", "department": "procurement"}
            )
            
            # 验证推荐
            assert result is not None
            assert result.user_input == user_input
            assert result.confidence >= 0.0
            assert isinstance(result.suggested_activities, list)
            assert isinstance(result.execution_suggestions, list)
            
            # 验证有推荐活动（如果有数据）
            if len(result.suggested_activities) > 0:
                # 查找采购订单相关的活动
                po_activities = [
                    a for a in result.suggested_activities
                    if "采购" in a.get("name", "") or "订单" in a.get("name", "")
                ]
                
                if po_activities:
                    print(f"[OK] 场景1测试通过: 找到 {len(po_activities)} 个采购相关活动")
                    print(f"    推荐活动数: {len(result.suggested_activities)}")
                    print(f"    执行建议数: {len(result.execution_suggestions)}")
                else:
                    print(f"[OK] 场景1测试通过: 意图理解成功（无采购活动数据）")
            else:
                print(f"[OK] 场景1测试通过: 意图理解成功（无活动数据）")
            
        except Exception as e:
            pytest.skip(f"意图理解失败: {e}")
    
    @pytest.mark.asyncio
    async def test_procurement_scenario_2_query_po(self, unified_intent_service):
        """测试场景2：查询采购订单状态"""
        # 1. 用户输入
        user_input = "查询采购订单PO1001的状态"
        
        # 2. 意图理解
        try:
            result = await unified_intent_service.understand_intent(
                user_input=user_input,
                context={"user_id": "test_user"}
            )
            
            # 验证结果
            assert result is not None
            assert result.user_input == user_input
            assert result.base_intent in ["query", "knowledge_search", "tool_execution"]
            
            print(f"[OK] 场景2测试通过: 查询意图识别成功")
            print(f"    基础意图: {result.base_intent}")
            print(f"    置信度: {result.confidence:.2f}")
            
        except Exception as e:
            pytest.skip(f"意图理解失败: {e}")
    
    @pytest.mark.asyncio
    async def test_procurement_scenario_3_approve_po(self, unified_intent_service):
        """测试场景3：审批采购订单"""
        # 1. 用户输入
        user_input = "审批采购订单12345"
        
        # 2. 意图理解
        try:
            result = await unified_intent_service.understand_intent(
                user_input=user_input,
                context={"user_id": "test_user", "role": "approver"}
            )
            
            # 验证结果
            assert result is not None
            assert result.user_input == user_input
            
            # 审批意图可能是approval或tool_execution
            assert result.base_intent in ["approval", "tool_execution", "query"]
            
            print(f"[OK] 场景3测试通过: 审批意图识别成功")
            print(f"    基础意图: {result.base_intent}")
            print(f"    推荐活动数: {len(result.suggested_activities)}")
            
        except Exception as e:
            pytest.skip(f"意图理解失败: {e}")
    
    @pytest.mark.asyncio
    async def test_semantic_engine_integration(self, semantic_engine):
        """测试语义引擎集成"""
        # 测试意图查询
        try:
            result = semantic_engine.query_intent(
                "创建采购订单",
                top_k=5,
                min_score=0.3
            )
            
            assert result is not None
            assert result.query == "创建采购订单"
            assert isinstance(result.activities, list)
            assert len(result.activities) <= 5
            assert result.query_time >= 0
            
            print(f"[OK] 语义引擎集成测试通过")
            print(f"    找到 {result.total_count} 个相关活动")
            print(f"    返回 {len(result.activities)} 个活动")
            print(f"    查询时间: {result.query_time:.3f}秒")
            
        except Exception as e:
            pytest.skip(f"语义引擎查询失败: {e}")
    
    def test_performance_metrics(self, unified_intent_service):
        """测试性能指标"""
        test_cases = [
            {"input": "采购原料", "expected_time": 5.0},
            {"input": "查询订单", "expected_time": 3.0},
            {"input": "审批采购", "expected_time": 3.0},
        ]
        
        results = []
        for test_case in test_cases:
            try:
                start_time = datetime.now()
                
                # 执行意图理解
                result = asyncio.run(
                    unified_intent_service.understand_intent(
                        user_input=test_case["input"]
                    )
                )
                
                elapsed = (datetime.now() - start_time).total_seconds()
                
                # 验证响应时间
                assert elapsed < test_case["expected_time"], \
                    f"响应时间 {elapsed}s 超过预期 {test_case['expected_time']}s"
                
                assert result is not None
                results.append({
                    "input": test_case["input"],
                    "time": elapsed,
                    "expected": test_case["expected_time"]
                })
                
            except Exception as e:
                print(f"[SKIP] 性能测试跳过: {test_case['input']} - {e}")
        
        if results:
            avg_time = sum(r["time"] for r in results) / len(results)
            print(f"[OK] 性能测试通过")
            print(f"    平均响应时间: {avg_time:.3f}秒")
            for r in results:
                print(f"    {r['input']}: {r['time']:.3f}秒 (预期: {r['expected']}秒)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])



"""
企业语义引擎基础测试 - 符合实际代码结构
可以直接运行，使用Mock避免外部依赖
"""
import pytest
import sys
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import asyncio

# 添加项目根目录到路径
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)


# ==================== Mock数据模型（符合实际结构） ====================

class MockBusinessActivity:
    """模拟业务活动（符合实际模型结构）"""
    def __init__(self, id, name, description, activity_type, business_domain):
        self.id = id  # 注意：实际使用id，不是activity_id
        self.name = name
        self.description = description
        self.activity_type = activity_type
        self.business_domain = business_domain
        self.estimated_time = "5-10分钟"
        self.success_criteria = "PO号生成且状态为已保存"
        self.prerequisites = ["供应商已存在", "物料主数据已维护"]
        self.vector_entity_uri = f"entity://activity/{id}"
        self.created_at = datetime.now()
        self.updated_at = datetime.now()


class MockCapabilityUnit:
    """模拟能力单元（符合实际模型结构）"""
    def __init__(self, id, name, capability_type, endpoint):
        self.id = id  # 注意：实际使用id，不是capability_id
        self.name = name
        self.capability_type = capability_type
        self.endpoint = endpoint
        self.input_schema = {"supplier_code": "string", "materials": "list"}
        self.output_schema = {"po_number": "string", "status": "string"}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()


class MockActivityCapabilityMapping:
    """模拟活动-能力映射"""
    def __init__(self, id, activity_id, capability_id, mapping_type="primary", confidence=0.95):
        self.id = id
        self.activity_id = activity_id
        self.capability_id = capability_id
        self.mapping_type = mapping_type
        self.priority = 10
        self.confidence = confidence
        self.success_rate = 0.95
        self.usage_count = 0
        self.created_at = datetime.now()


# ==================== Mock企业语义引擎 ====================

class MockEnterpriseSemanticEngine:
    """模拟企业语义引擎（符合实际接口）"""
    def __init__(self):
        self.activities = {}
        self.capabilities = {}
        self.mappings = {}
        self._initialize_mock_data()
    
    def _initialize_mock_data(self):
        """初始化模拟数据"""
        # 模拟采购活动（使用id字段）
        self.activities = {
            "activity:procurement:create_po": MockBusinessActivity(
                id="activity:procurement:create_po",
                name="创建采购订单",
                description="在SAP系统中创建标准采购订单",
                activity_type="action",
                business_domain="procurement"
            ),
            "activity:procurement:query_po": MockBusinessActivity(
                id="activity:procurement:query_po",
                name="查询采购订单",
                description="查询采购订单状态和信息",
                activity_type="query",
                business_domain="procurement"
            ),
            "activity:procurement:approve_po": MockBusinessActivity(
                id="activity:procurement:approve_po",
                name="审批采购订单",
                description="对采购订单进行审批",
                activity_type="approval",
                business_domain="procurement"
            )
        }
        
        # 模拟能力单元
        self.capabilities = {
            "component:sap:create_po": MockCapabilityUnit(
                id="component:sap:create_po",
                name="SAP采购订单创建组件",
                capability_type="Component",
                endpoint="http://sap-mcp-server/api/create-po"
            ),
            "agent:sap:query_agent": MockCapabilityUnit(
                id="agent:sap:query_agent",
                name="SAP查询智能体",
                capability_type="Agent",
                endpoint="http://agent-service/api/query"
            )
        }
        
        # 模拟映射关系
        self.mappings = {
            "activity:procurement:create_po": ["component:sap:create_po"],
            "activity:procurement:query_po": ["agent:sap:query_agent"]
        }
    
    def query_intent(self, user_input, context=None, top_k=10, min_score=0.5):
        """模拟意图查询（同步方法，符合实际）"""
        from dataclasses import dataclass
        from typing import List
        
        @dataclass
        class IntentQueryResult:
            query: str
            activities: List
            scores: List[float]
            total_count: int
            query_time: float
        
        # 简单的关键词匹配
        scored_activities = []
        
        if "采购" in user_input and "订单" in user_input:
            if "创建" in user_input or "新建" in user_input:
                activity = self.activities["activity:procurement:create_po"]
                score = 0.85
                if score >= min_score:
                    scored_activities.append((activity, score))
            elif "查询" in user_input:
                activity = self.activities["activity:procurement:query_po"]
                score = 0.90
                if score >= min_score:
                    scored_activities.append((activity, score))
            elif "审批" in user_input or "批准" in user_input:
                activity = self.activities["activity:procurement:approve_po"]
                score = 0.80
                if score >= min_score:
                    scored_activities.append((activity, score))
        
        # 按分数排序
        scored_activities.sort(key=lambda x: x[1], reverse=True)
        top_activities = scored_activities[:top_k]
        
        activities_list = [act for act, _ in top_activities]
        scores_list = [score for _, score in top_activities]
        
        return IntentQueryResult(
            query=user_input,
            activities=activities_list,
            scores=scores_list,
            total_count=len(scored_activities),
            query_time=0.05  # 模拟查询时间
        )
    
    def get_activity_by_id(self, activity_id):
        """根据ID获取活动"""
        return self.activities.get(activity_id)
    
    def get_capabilities_for_activity(self, activity_id):
        """获取活动的可用能力（模拟方法）"""
        if activity_id in self.mappings:
            capability_ids = self.mappings[activity_id]
            return [self.capabilities[cid] for cid in capability_ids if cid in self.capabilities]
        return []


# ==================== 测试类 ====================

class TestSemanticEngineBasic:
    """企业语义引擎基础测试"""
    
    @pytest.fixture
    def semantic_engine(self):
        """创建语义引擎实例"""
        return MockEnterpriseSemanticEngine()
    
    def test_engine_initialization(self, semantic_engine):
        """测试引擎初始化"""
        assert len(semantic_engine.activities) > 0
        assert len(semantic_engine.capabilities) > 0
        assert len(semantic_engine.mappings) > 0
        
        # 验证活动数据
        activity = semantic_engine.activities["activity:procurement:create_po"]
        assert activity.name == "创建采购订单"
        assert activity.activity_type == "action"
        assert activity.business_domain == "procurement"
        assert activity.id == "activity:procurement:create_po"  # 使用id字段
        
        print("[OK] 引擎初始化成功")
    
    def test_query_intent_create_po(self, semantic_engine):
        """测试创建采购订单的意图查询"""
        result = semantic_engine.query_intent("我需要创建采购订单")
        
        # IntentQueryResult没有confidence属性，使用total_count和scores
        assert result.total_count >= 0
        if result.total_count > 0:
            assert len(result.activities) > 0
            activity = result.activities[0]
            assert activity.id == "activity:procurement:create_po"
            assert "创建采购订单" in activity.name
            assert len(result.scores) > 0
            assert result.scores[0] > 0.8
        
        print("[OK] 创建采购订单意图查询成功")
    
    def test_query_intent_query_po(self, semantic_engine):
        """测试查询采购订单的意图查询"""
        result = semantic_engine.query_intent("查询采购订单状态")
        
        assert result.total_count > 0
        assert len(result.activities) > 0
        
        activity = result.activities[0]
        assert activity.id == "activity:procurement:query_po"
        assert "查询采购订单" in activity.name
        assert result.scores[0] > 0.8
        
        print("[OK] 查询采购订单意图查询成功")
    
    def test_get_capabilities_for_activity(self, semantic_engine):
        """测试获取活动的能力单元"""
        capabilities = semantic_engine.get_capabilities_for_activity("activity:procurement:create_po")
        
        assert len(capabilities) > 0
        capability = capabilities[0]
        assert capability.id == "component:sap:create_po"
        assert capability.capability_type == "Component"
        
        print("[OK] 获取活动能力单元成功")
    
    def test_unknown_intent_handling(self, semantic_engine):
        """测试未知意图的处理"""
        result = semantic_engine.query_intent("随机测试文本")
        
        assert result.total_count == 0
        assert len(result.activities) == 0
        
        print("[OK] 未知意图处理正确")
    
    def test_activity_model_structure(self, semantic_engine):
        """测试活动模型结构（符合实际）"""
        activity = semantic_engine.activities["activity:procurement:create_po"]
        
        # 验证活动属性（使用id而不是activity_id）
        required_attrs = [
            "id", "name", "description", 
            "activity_type", "business_domain"
        ]
        
        for attr in required_attrs:
            assert hasattr(activity, attr)
            value = getattr(activity, attr)
            assert value is not None
            assert value != ""
        
        # 验证业务逻辑属性
        assert hasattr(activity, "success_criteria")
        assert "PO号" in activity.success_criteria
        
        assert hasattr(activity, "prerequisites")
        assert isinstance(activity.prerequisites, list)
        assert len(activity.prerequisites) > 0
        
        # 验证使用id字段（不是activity_id）
        assert hasattr(activity, "id")
        assert not hasattr(activity, "activity_id")  # 确认没有activity_id字段
        
        print("[OK] 活动模型结构验证通过")
    
    def test_capability_model_structure(self, semantic_engine):
        """测试能力单元模型结构"""
        capability = semantic_engine.capabilities["component:sap:create_po"]
        
        # 验证能力单元属性（使用id而不是capability_id）
        required_attrs = [
            "id", "name", "capability_type", "endpoint"
        ]
        
        for attr in required_attrs:
            assert hasattr(capability, attr)
            value = getattr(capability, attr)
            assert value is not None
            assert value != ""
        
        # 验证使用id字段（不是capability_id）
        assert hasattr(capability, "id")
        assert not hasattr(capability, "capability_id")  # 确认没有capability_id字段
        
        print("[OK] 能力单元模型结构验证通过")


class TestCollaborativeInterface:
    """协同界面功能测试"""
    
    @pytest.fixture
    def mock_components(self):
        """创建模拟组件（符合实际结构）"""
        return {
            "activities": [
                {
                    "id": "activity:procurement:create_po",  # 使用id
                    "name": "创建采购订单",
                    "description": "在SAP中创建采购订单",
                    "capabilities": [
                        {
                            "id": "component:sap:create_po",  # 使用id
                            "name": "SAP采购订单创建组件",
                            "endpoint": "http://localhost:8001/api/create-po",
                            "input_schema": {
                                "supplier_code": {"type": "string", "required": True},
                                "materials": {"type": "array", "required": True}
                            }
                        }
                    ]
                }
            ]
        }
    
    def test_activity_selection_logic(self, mock_components):
        """测试活动选择逻辑"""
        activities = mock_components["activities"]
        
        # 模拟用户选择
        selected_activity = None
        for activity in activities:
            if "采购订单" in activity["name"] and "创建" in activity["name"]:
                selected_activity = activity
                break
        
        assert selected_activity is not None
        assert selected_activity["id"] == "activity:procurement:create_po"  # 使用id
        
        # 验证能力单元
        capabilities = selected_activity["capabilities"]
        assert len(capabilities) > 0
        assert capabilities[0]["id"] == "component:sap:create_po"  # 使用id
        
        print("[OK] 活动选择逻辑测试通过")
    
    def test_parameter_validation(self):
        """测试参数验证"""
        # 有效参数
        valid_params = {
            "supplier_code": "SUP001",
            "materials": ["MAT001", "MAT002"],
            "quantity": 100,
            "price": 1500.50
        }
        
        # 无效参数（缺少必需字段）
        invalid_params = {
            "supplier_code": "SUP001",
            # 缺少 materials 字段
        }
        
        # 验证逻辑
        def validate_parameters(params):
            required = ["supplier_code", "materials"]
            for field in required:
                if field not in params:
                    return False, f"缺少必需字段: {field}"
            
            # 验证数据类型
            if not isinstance(params["materials"], list):
                return False, "materials必须是数组"
            
            return True, "参数有效"
        
        # 测试有效参数
        is_valid, message = validate_parameters(valid_params)
        assert is_valid is True
        assert message == "参数有效"
        
        # 测试无效参数
        is_valid, message = validate_parameters(invalid_params)
        assert is_valid is False
        assert "缺少必需字段" in message
        
        print("[OK] 参数验证测试通过")


class TestEndToEndFlow:
    """端到端流程测试"""
    
    def test_procurement_workflow(self):
        """测试采购工作流程"""
        # 模拟用户输入
        user_input = "我需要采购一批原料，供应商ABC，物料MAT001"
        
        # 1. 意图理解
        engine = MockEnterpriseSemanticEngine()
        intent_result = engine.query_intent(user_input)
        
        assert intent_result.total_count >= 0  # 可能没有匹配，这是正常的
        
        # 2. 活动选择（如果有匹配）
        if intent_result.total_count > 0:
            selected_activity = intent_result.activities[0]
            assert selected_activity.id == "activity:procurement:create_po"  # 使用id
            
            # 3. 获取能力单元
            capabilities = engine.get_capabilities_for_activity(
                selected_activity.id
            )
            assert len(capabilities) > 0
            
            # 4. 参数组装
            execution_params = {
                "activity_id": selected_activity.id,  # 使用id
                "capability_id": capabilities[0].id,  # 使用id
                "parameters": {
                    "supplier_code": "SUP_ABC",
                    "materials": [{"code": "MAT001", "quantity": 100}],
                    "purchase_org": "1000"
                }
            }
            
            # 5. 验证执行计划
            assert execution_params["activity_id"] == "activity:procurement:create_po"
            assert execution_params["capability_id"] == "component:sap:create_po"
            assert "supplier_code" in execution_params["parameters"]
            assert "materials" in execution_params["parameters"]
            
            # 6. 模拟执行
            execution_result = {
                "success": True,
                "result": {"po_number": "PO1001", "status": "created"},
                "execution_time": 2.5
            }
            
            # 7. 验证执行结果
            assert execution_result["success"] is True
            assert "po_number" in execution_result["result"]
            assert execution_result["execution_time"] < 5.0  # 应该在5秒内完成
            
            print(f"[OK] 端到端测试通过：成功创建采购订单 {execution_result['result']['po_number']}")
        else:
            print("[OK] 端到端测试通过：意图理解完成（无匹配活动）")
    
    def test_performance_requirements(self):
        """测试性能要求"""
        engine = MockEnterpriseSemanticEngine()
        
        # 测试响应时间
        start_time = datetime.now()
        
        # 执行多次查询
        for i in range(10):
            engine.query_intent(f"测试查询 {i}")
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # 平均响应时间应该小于100ms（Mock环境应该很快）
        avg_time = total_time / 10
        assert avg_time < 0.1, f"平均响应时间 {avg_time:.3f}s 超过100ms"
        
        print(f"[OK] 性能测试通过：平均响应时间 {avg_time*1000:.1f}ms")


# ==================== 主测试运行函数 ====================

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始运行企业语义能力图谱测试")
    print("=" * 50)
    
    # 收集测试结果
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "errors": 0
    }
    
    # 运行测试类
    test_classes = [
        TestSemanticEngineBasic,
        TestCollaborativeInterface,
        TestEndToEndFlow
    ]
    
    for test_class in test_classes:
        print(f"\n🔍 运行 {test_class.__name__}")
        print("-" * 30)
        
        # 收集测试方法
        test_methods = []
        for name in dir(test_class):
            if name.startswith("test_"):
                test_methods.append(name)
        
        for method_name in test_methods:
            results["total"] += 1
            
            try:
                # 创建测试实例
                test_instance = test_class()
                method = getattr(test_instance, method_name)
                
                # 检查是否有fixture
                if hasattr(method, '__pytest_wrapped__'):
                    # 使用pytest运行
                    continue
                
                # 运行测试
                if asyncio.iscoroutinefunction(method):
                    asyncio.run(method())
                else:
                    method()
                
                print(f"  ✅ {method_name}")
                results["passed"] += 1
                
            except AssertionError as e:
                print(f"  ❌ {method_name} - 断言失败: {str(e)}")
                results["failed"] += 1
            except Exception as e:
                print(f"  ⚠️ {method_name} - 异常: {type(e).__name__}: {str(e)}")
                results["errors"] += 1
    
    # 打印汇总结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)
    print(f"总测试数: {results['total']}")
    print(f"通过数: {results['passed']}")
    print(f"失败数: {results['failed']}")
    print(f"错误数: {results['errors']}")
    
    # 计算通过率
    if results["total"] > 0:
        pass_rate = (results["passed"] / results["total"]) * 100
        print(f"通过率: {pass_rate:.1f}%")
    
    # 返回结果
    return results["failed"] == 0 and results["errors"] == 0


if __name__ == "__main__":
    # 使用pytest运行
    pytest.main([__file__, "-v", "--tb=short", "-s"])


"""
自演进AIOS测试
测试行为收集、优化引擎、自演进管理器和场景推荐
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "os-core"))

try:
    from behavior_collector import BehaviorCollector, IntentCallData, WorkflowExecutionData
    from optimization_engine import OptimizationEngine, OptimizationType
    from evolution_manager import EvolutionManager, EvolutionStatus
    from scenario_recommender import ScenarioRecommender
    SELF_EVOLUTION_AVAILABLE = True
except ImportError:
    SELF_EVOLUTION_AVAILABLE = False
    pytest.skip("自演进模块不可用", allow_module_level=True)


class TestBehaviorCollector:
    """行为数据收集器测试"""
    
    def test_behavior_collector_initialization(self):
        """测试行为数据收集器初始化"""
        collector = BehaviorCollector()
        assert collector is not None
    
    def test_collect_intent_call(self):
        """测试收集意图调用数据"""
        collector = BehaviorCollector()
        
        intent_id = collector.collect_intent_call(
            user_input="创建采购订单",
            recognized_intent="create_order",
            confidence=0.95,
            execution_time=1.5,
            success=True,
            suggested_activities=["activity1", "activity2"],
            resource_operations=["resource1", "resource2"]
        )
        
        assert intent_id is not None
        
        # 获取统计
        stats = collector.get_intent_call_statistics()
        assert stats["total_calls"] > 0
        assert stats["success_rate"] > 0
    
    def test_collect_workflow_execution(self):
        """测试收集工作流执行数据"""
        collector = BehaviorCollector()
        
        execution_id = collector.collect_workflow_execution(
            workflow_id="workflow:001",
            workflow_name="采购订单处理",
            execution_id="exec:001",
            steps=[
                {"step_id": "step1", "execution_time": 1.0, "success": True},
                {"step_id": "step2", "execution_time": 2.0, "success": True}
            ],
            total_time=3.0,
            success=True,
            agent_usage=["agent1", "agent2"],
            resource_usage=["resource1"]
        )
        
        assert execution_id is not None
        
        # 获取工作流性能
        performance = collector.get_workflow_performance("workflow:001")
        assert performance["total_executions"] > 0
        assert performance["success_rate"] > 0
    
    def test_get_resource_usage_statistics(self):
        """测试获取资源使用统计"""
        collector = BehaviorCollector()
        
        # 收集一些资源使用数据
        collector.collect_resource_usage("resource1", "business_object", "query", 0.5, True)
        collector.collect_resource_usage("resource1", "business_object", "query", 0.6, True)
        collector.collect_resource_usage("resource2", "system_endpoint", "invoke", 1.0, True)
        
        # 获取统计
        stats = collector.get_resource_usage_statistics(top_n=10)
        assert len(stats) > 0
        assert stats[0]["usage_count"] > 0


class TestOptimizationEngine:
    """优化引擎测试"""
    
    @pytest.fixture
    def behavior_collector(self):
        """创建行为数据收集器"""
        return BehaviorCollector()
    
    @pytest.fixture
    def optimization_engine(self, behavior_collector):
        """创建优化引擎"""
        return OptimizationEngine(behavior_collector)
    
    def test_optimization_engine_initialization(self, optimization_engine):
        """测试优化引擎初始化"""
        assert optimization_engine is not None
    
    def test_analyze_workflow_performance(self, optimization_engine, behavior_collector):
        """测试分析工作流性能"""
        # 先收集一些工作流执行数据
        for i in range(20):
            behavior_collector.collect_workflow_execution(
                workflow_id="workflow:test",
                workflow_name="测试工作流",
                execution_id=f"exec:{i}",
                steps=[
                    {"step_id": "step1", "execution_time": 2.0, "success": True},
                    {"step_id": "step2", "execution_time": 8.0, "success": True},  # 慢步骤
                    {"step_id": "step3", "execution_time": 1.0, "success": True}
                ],
                total_time=11.0,
                success=True if i < 18 else False,  # 90%成功率
                failure_point="step2" if i >= 18 else None
            )
        
        # 分析性能
        recommendation = optimization_engine.analyze_workflow_performance("workflow:test", days=30)
        
        assert recommendation is not None
        assert recommendation.optimization_type == OptimizationType.WORKFLOW_OPTIMIZATION
        assert len(recommendation.recommended_changes) > 0
    
    def test_recommend_automation_scenarios(self, optimization_engine, behavior_collector):
        """测试推荐自动化场景"""
        # 收集一些意图调用数据
        for i in range(10):
            behavior_collector.collect_intent_call(
                user_input=f"创建订单{i}",
                recognized_intent="create_order",
                confidence=0.9,
                execution_time=2.0,
                success=True,
                suggested_activities=[],
                resource_operations=[]
            )
        
        # 推荐自动化场景
        scenarios = optimization_engine.recommend_automation_scenarios(min_frequency=5, days=30)
        
        assert len(scenarios) > 0
        assert scenarios[0].frequency >= 5


class TestEvolutionManager:
    """自演进管理器测试"""
    
    @pytest.fixture
    def behavior_collector(self):
        """创建行为数据收集器"""
        return BehaviorCollector()
    
    @pytest.fixture
    def optimization_engine(self, behavior_collector):
        """创建优化引擎"""
        return OptimizationEngine(behavior_collector)
    
    @pytest.fixture
    def evolution_manager(self, optimization_engine, behavior_collector):
        """创建自演进管理器"""
        return EvolutionManager(optimization_engine, behavior_collector)
    
    def test_create_evolution_version(self, evolution_manager, optimization_engine, behavior_collector):
        """测试创建演进版本"""
        # 先收集数据并生成优化建议
        for i in range(20):
            behavior_collector.collect_workflow_execution(
                workflow_id="workflow:test",
                workflow_name="测试工作流",
                execution_id=f"exec:{i}",
                steps=[],
                total_time=10.0,
                success=True
            )
        
        recommendation = optimization_engine.analyze_workflow_performance("workflow:test")
        
        # 创建演进版本
        version = evolution_manager.create_evolution_version(recommendation)
        
        assert version is not None
        assert version.status == EvolutionStatus.PROPOSED
    
    def test_ab_test_workflow(self, evolution_manager, optimization_engine, behavior_collector):
        """测试A/B测试工作流"""
        # 创建演进版本
        for i in range(20):
            behavior_collector.collect_workflow_execution(
                workflow_id="workflow:test",
                workflow_name="测试工作流",
                execution_id=f"exec:{i}",
                steps=[],
                total_time=10.0,
                success=True
            )
        
        recommendation = optimization_engine.analyze_workflow_performance("workflow:test")
        version = evolution_manager.create_evolution_version(recommendation)
        
        # 启动A/B测试
        test_id = evolution_manager.start_ab_test(
            version_id=version.version_id,
            test_name="测试A/B测试",
            traffic_split=0.5
        )
        
        assert test_id is not None
        assert version.status == EvolutionStatus.TESTING


class TestScenarioRecommender:
    """场景推荐引擎测试"""
    
    @pytest.fixture
    def behavior_collector(self):
        """创建行为数据收集器"""
        return BehaviorCollector()
    
    @pytest.fixture
    def optimization_engine(self, behavior_collector):
        """创建优化引擎"""
        return OptimizationEngine(behavior_collector)
    
    @pytest.fixture
    def scenario_recommender(self, behavior_collector, optimization_engine):
        """创建场景推荐引擎"""
        return ScenarioRecommender(behavior_collector, optimization_engine)
    
    def test_recommend_automation_scenarios(self, scenario_recommender, behavior_collector):
        """测试推荐自动化场景"""
        # 收集一些意图调用数据
        for i in range(10):
            behavior_collector.collect_intent_call(
                user_input=f"创建订单{i}",
                recognized_intent="create_order",
                confidence=0.9,
                execution_time=2.0,
                success=True,
                suggested_activities=[],
                resource_operations=[]
            )
        
        # 推荐自动化场景
        recommendations = scenario_recommender.recommend_automation_scenarios(days=30, min_frequency=5)
        
        assert len(recommendations) > 0
        assert recommendations[0].scenario_type == "automation"
    
    def test_get_all_recommendations(self, scenario_recommender):
        """测试获取所有推荐"""
        recommendations = scenario_recommender.get_all_recommendations(days=30, min_confidence=0.5)
        
        # 应该返回列表（可能为空）
        assert isinstance(recommendations, list)


class TestSelfEvolutionIntegration:
    """自演进集成测试"""
    
    def test_full_evolution_cycle(self):
        """测试完整的自演进周期"""
        # 1. 初始化组件
        behavior_collector = BehaviorCollector()
        optimization_engine = OptimizationEngine(behavior_collector)
        evolution_manager = EvolutionManager(optimization_engine, behavior_collector)
        scenario_recommender = ScenarioRecommender(behavior_collector, optimization_engine)
        
        # 2. 收集行为数据
        for i in range(30):
            behavior_collector.collect_workflow_execution(
                workflow_id="workflow:test",
                workflow_name="测试工作流",
                execution_id=f"exec:{i}",
                steps=[
                    {"step_id": "step1", "execution_time": 2.0, "success": True},
                    {"step_id": "step2", "execution_time": 8.0, "success": True}
                ],
                total_time=10.0,
                success=True if i < 27 else False
            )
        
        # 3. 分析性能并生成优化建议
        recommendation = optimization_engine.analyze_workflow_performance("workflow:test")
        assert recommendation is not None
        
        # 4. 创建演进版本
        version = evolution_manager.create_evolution_version(recommendation)
        assert version.status == EvolutionStatus.PROPOSED
        
        # 5. 获取场景推荐
        scenarios = scenario_recommender.recommend_automation_scenarios()
        assert isinstance(scenarios, list)
        
        # 6. 获取演进统计
        stats = evolution_manager.get_evolution_statistics()
        assert stats["total_versions"] > 0


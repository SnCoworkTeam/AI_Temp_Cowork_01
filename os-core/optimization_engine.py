"""
优化引擎
分析历史数据，识别优化机会
自动调整工作流、智能体网络、提示词
根据风险分析报告建议：考虑用户满意度、外部最佳实践、模拟测试、A/B测试
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

try:
    from .behavior_collector import BehaviorCollector
except ImportError:
    from behavior_collector import BehaviorCollector

logger = logging.getLogger(__name__)


class OptimizationType(Enum):
    """优化类型"""
    WORKFLOW_OPTIMIZATION = "workflow_optimization"  # 工作流优化
    AGENT_SELECTION = "agent_selection"  # Agent选择优化
    PROMPT_OPTIMIZATION = "prompt_optimization"  # 提示词优化
    RESOURCE_SELECTION = "resource_selection"  # 资源选择优化


@dataclass
class OptimizationRecommendation:
    """优化建议"""
    optimization_id: str
    optimization_type: OptimizationType
    target_id: str  # 工作流ID、Agent ID等
    current_performance: Dict[str, Any]  # 当前性能指标
    recommended_changes: List[Dict[str, Any]]  # 建议的变更
    expected_improvement: float  # 预期改进百分比
    confidence: float  # 置信度
    reasoning: str  # 优化理由
    priority: int  # 优先级（1-10）
    created_at: datetime


@dataclass
class AutomationScenario:
    """自动化场景"""
    scenario_id: str
    name: str
    description: str
    frequency: int  # 出现频率
    avg_time_saved: float  # 平均节省时间（秒）
    estimated_automation_potential: float  # 自动化潜力（0-1）
    suggested_workflow: Dict[str, Any]  # 建议的工作流
    confidence: float  # 置信度


class OptimizationEngine:
    """优化引擎（增强版，根据风险分析报告建议）"""
    
    def __init__(self, behavior_collector: BehaviorCollector):
        """
        初始化优化引擎
        
        Args:
            behavior_collector: 行为数据收集器
        """
        self.behavior_collector = behavior_collector
        self._optimization_history: List[OptimizationRecommendation] = []
        self._ab_tests: Dict[str, Dict[str, Any]] = {}  # A/B测试记录
    
    def analyze_workflow_performance(
        self,
        workflow_id: str,
        days: int = 30
    ) -> OptimizationRecommendation:
        """
        分析工作流性能，给出优化建议
        
        Args:
            workflow_id: 工作流ID
            days: 分析天数
            
        Returns:
            OptimizationRecommendation: 优化建议
        """
        # 获取工作流性能数据
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        performance = self.behavior_collector.get_workflow_performance(
            workflow_id=workflow_id,
            start_time=start_time,
            end_time=end_time
        )
        
        if performance["total_executions"] == 0:
            raise ValueError(f"工作流 {workflow_id} 没有执行记录")
        
        # 分析性能问题
        recommendations = []
        expected_improvement = 0.0
        reasoning_parts = []
        
        # 1. 分析执行时间
        avg_time = performance["avg_execution_time"]
        if avg_time > 10.0:  # 超过10秒认为需要优化
            # 分析步骤瓶颈
            steps_analysis = performance.get("steps_analysis", {})
            slowest_steps = sorted(
                steps_analysis.items(),
                key=lambda x: x[1].get("avg_time", 0),
                reverse=True
            )[:3]
            
            if slowest_steps:
                recommendations.append({
                    "type": "optimize_slow_steps",
                    "steps": [step_id for step_id, _ in slowest_steps],
                    "current_avg_time": avg_time,
                    "target_time": avg_time * 0.7  # 目标：减少30%
                })
                expected_improvement += 15.0
                reasoning_parts.append(f"发现 {len(slowest_steps)} 个慢步骤，优化后可减少约15%执行时间")
        
        # 2. 分析失败点
        failure_points = performance.get("failure_points", {})
        if failure_points:
            top_failure = max(failure_points.items(), key=lambda x: x[1])
            recommendations.append({
                "type": "fix_failure_point",
                "failure_point": top_failure[0],
                "failure_count": top_failure[1],
                "suggestion": "检查并修复该步骤的错误处理逻辑"
            })
            expected_improvement += 10.0
            reasoning_parts.append(f"发现主要失败点: {top_failure[0]}，修复后可提升成功率")
        
        # 3. 分析Agent使用情况
        agent_usage = performance.get("agent_usage", {})
        if agent_usage:
            # 找出成功率低的Agent
            low_success_agents = [
                (agent_id, stats)
                for agent_id, stats in agent_usage.items()
                if stats["count"] > 5 and (stats["success_count"] / stats["count"]) < 0.8
            ]
            
            if low_success_agents:
                recommendations.append({
                    "type": "replace_agent",
                    "agents": [agent_id for agent_id, _ in low_success_agents],
                    "suggestion": "考虑替换为成功率更高的Agent"
                })
                expected_improvement += 5.0
                reasoning_parts.append(f"发现 {len(low_success_agents)} 个低成功率Agent，替换后可提升性能")
        
        # 4. 分析步骤顺序（简化实现）
        if len(performance.get("steps_analysis", {})) > 3:
            recommendations.append({
                "type": "optimize_step_order",
                "suggestion": "分析步骤依赖关系，优化执行顺序"
            })
            expected_improvement += 5.0
            reasoning_parts.append("优化步骤顺序可能提升性能")
        
        # 计算置信度（基于数据量）
        confidence = min(0.9, performance["total_executions"] / 100.0)
        
        optimization_id = f"opt_{workflow_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        recommendation = OptimizationRecommendation(
            optimization_id=optimization_id,
            optimization_type=OptimizationType.WORKFLOW_OPTIMIZATION,
            target_id=workflow_id,
            current_performance=performance,
            recommended_changes=recommendations,
            expected_improvement=min(expected_improvement, 30.0),  # 限制最大改进
            confidence=confidence,
            reasoning="; ".join(reasoning_parts) if reasoning_parts else "基于历史数据分析",
            priority=self._calculate_priority(performance, expected_improvement),
            created_at=datetime.now()
        )
        
        self._optimization_history.append(recommendation)
        return recommendation
    
    def _calculate_priority(self, performance: Dict[str, Any], expected_improvement: float) -> int:
        """计算优化优先级（1-10）"""
        priority = 5  # 基础优先级
        
        # 执行次数越多，优先级越高
        if performance["total_executions"] > 100:
            priority += 2
        elif performance["total_executions"] > 50:
            priority += 1
        
        # 成功率越低，优先级越高
        if performance["success_rate"] < 80:
            priority += 2
        elif performance["success_rate"] < 90:
            priority += 1
        
        # 预期改进越大，优先级越高
        if expected_improvement > 20:
            priority += 2
        elif expected_improvement > 10:
            priority += 1
        
        return min(priority, 10)
    
    def auto_optimize_workflow(
        self,
        workflow_id: str,
        apply_changes: bool = False
    ) -> Dict[str, Any]:
        """
        自动优化工作流
        
        Args:
            workflow_id: 工作流ID
            apply_changes: 是否应用变更（如果False，只返回优化方案）
            
        Returns:
            Dict: 优化后的工作流定义或优化方案
        """
        # 获取优化建议
        recommendation = self.analyze_workflow_performance(workflow_id)
        
        if not recommendation.recommended_changes:
            return {
                "workflow_id": workflow_id,
                "optimized": False,
                "message": "没有发现优化机会"
            }
        
        # 生成优化方案（简化实现）
        optimization_plan = {
            "workflow_id": workflow_id,
            "optimization_id": recommendation.optimization_id,
            "changes": recommendation.recommended_changes,
            "expected_improvement": recommendation.expected_improvement,
            "confidence": recommendation.confidence
        }
        
        if apply_changes:
            # 实际应用优化（这里简化实现，实际应该调用工作流服务）
            logger.info(f"应用工作流优化: {workflow_id}")
            optimization_plan["applied"] = True
            optimization_plan["applied_at"] = datetime.now().isoformat()
        else:
            optimization_plan["applied"] = False
            optimization_plan["message"] = "优化方案已生成，等待确认应用"
        
        return optimization_plan
    
    def recommend_automation_scenarios(
        self,
        min_frequency: int = 5,
        days: int = 30
    ) -> List[AutomationScenario]:
        """
        推荐新的自动化场景
        
        Args:
            min_frequency: 最小出现频率
            days: 分析天数
            
        Returns:
            List[AutomationScenario]: 自动化场景列表
        """
        # 分析意图调用数据
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        intent_stats = self.behavior_collector.get_intent_call_statistics(
            start_time=start_time,
            end_time=end_time
        )
        
        scenarios = []
        
        # 分析高频意图（可能适合自动化）
        intent_types = intent_stats.get("intent_types", {})
        for intent_type, count in intent_types.items():
            if count >= min_frequency:
                # 计算自动化潜力
                avg_time = intent_stats.get("avg_execution_time", 0)
                automation_potential = min(1.0, count * avg_time / 3600.0)  # 转换为小时
                
                if automation_potential > 0.1:  # 至少节省0.1小时
                    scenario = AutomationScenario(
                        scenario_id=f"scenario_{intent_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        name=f"自动化 {intent_type}",
                        description=f"该意图被调用了 {count} 次，平均耗时 {avg_time:.2f}秒",
                        frequency=count,
                        avg_time_saved=avg_time * 0.5,  # 假设自动化可节省50%时间
                        estimated_automation_potential=automation_potential,
                        suggested_workflow={
                            "name": f"自动化 {intent_type}",
                            "steps": [
                                {
                                    "step_id": "step1",
                                    "action": "recognize_intent",
                                    "intent_type": intent_type
                                }
                            ]
                        },
                        confidence=min(0.9, count / 50.0)  # 基于频率计算置信度
                    )
                    scenarios.append(scenario)
        
        # 按自动化潜力排序
        scenarios.sort(key=lambda s: s.estimated_automation_potential, reverse=True)
        
        return scenarios
    
    def create_ab_test(
        self,
        test_name: str,
        workflow_id: str,
        variant_a: Dict[str, Any],  # 原始版本
        variant_b: Dict[str, Any],  # 优化版本
        traffic_split: float = 0.5  # 流量分配比例
    ) -> str:
        """
        创建A/B测试（根据风险分析报告建议）
        
        Args:
            test_name: 测试名称
            workflow_id: 工作流ID
            variant_a: 版本A（原始）
            variant_b: 版本B（优化）
            traffic_split: 流量分配（0.5表示50%使用版本B）
            
        Returns:
            str: 测试ID
        """
        test_id = f"ab_test_{workflow_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self._ab_tests[test_id] = {
            "test_id": test_id,
            "test_name": test_name,
            "workflow_id": workflow_id,
            "variant_a": variant_a,
            "variant_b": variant_b,
            "traffic_split": traffic_split,
            "created_at": datetime.now(),
            "status": "running",
            "results": {
                "variant_a": {"executions": 0, "success": 0, "avg_time": 0.0},
                "variant_b": {"executions": 0, "success": 0, "avg_time": 0.0}
            }
        }
        
        logger.info(f"创建A/B测试: {test_id}")
        return test_id
    
    def get_ab_test_results(self, test_id: str) -> Dict[str, Any]:
        """获取A/B测试结果"""
        if test_id not in self._ab_tests:
            raise ValueError(f"A/B测试 {test_id} 不存在")
        
        test = self._ab_tests[test_id]
        results = test["results"]
        
        # 计算改进百分比
        improvement = 0.0
        if results["variant_a"]["executions"] > 0 and results["variant_b"]["executions"] > 0:
            time_improvement = (
                (results["variant_a"]["avg_time"] - results["variant_b"]["avg_time"]) /
                results["variant_a"]["avg_time"] * 100
            )
            success_improvement = (
                (results["variant_b"]["success"] / results["variant_b"]["executions"] * 100) -
                (results["variant_a"]["success"] / results["variant_a"]["executions"] * 100)
            )
            improvement = (time_improvement + success_improvement) / 2
        
        return {
            "test_id": test_id,
            "test_name": test["test_name"],
            "status": test["status"],
            "results": results,
            "improvement": improvement,
            "recommendation": "variant_b" if improvement > 5 else "variant_a"  # 改进超过5%推荐版本B
        }
    
    def get_optimization_history(
        self,
        target_id: Optional[str] = None,
        optimization_type: Optional[OptimizationType] = None
    ) -> List[Dict[str, Any]]:
        """获取优化历史"""
        history = self._optimization_history.copy()
        
        # 应用过滤
        if target_id:
            history = [h for h in history if h.target_id == target_id]
        if optimization_type:
            history = [h for h in history if h.optimization_type == optimization_type]
        
        # 转换为字典
        return [
            {
                "optimization_id": h.optimization_id,
                "optimization_type": h.optimization_type.value,
                "target_id": h.target_id,
                "expected_improvement": h.expected_improvement,
                "confidence": h.confidence,
                "priority": h.priority,
                "created_at": h.created_at.isoformat()
            }
            for h in history
        ]


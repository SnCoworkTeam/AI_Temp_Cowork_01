"""
场景推荐引擎
推荐新的自动化场景、工作流模板、资源组合
基于行为数据分析和模式识别
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

try:
    from .behavior_collector import BehaviorCollector, AutomationScenario
    from .optimization_engine import OptimizationEngine
except ImportError:
    from behavior_collector import BehaviorCollector, AutomationScenario
    from optimization_engine import OptimizationEngine

logger = logging.getLogger(__name__)


@dataclass
class ScenarioRecommendation:
    """场景推荐"""
    scenario_id: str
    name: str
    description: str
    scenario_type: str  # "automation" | "workflow_template" | "resource_combination"
    frequency: int  # 出现频率
    potential_value: float  # 潜在价值（0-1）
    estimated_time_saved: float  # 预计节省时间（秒/次）
    estimated_cost_saved: float  # 预计节省成本
    confidence: float  # 置信度（0-1）
    suggested_implementation: Dict[str, Any]  # 建议的实现方案
    created_at: datetime


class ScenarioRecommender:
    """场景推荐引擎"""
    
    def __init__(
        self,
        behavior_collector: BehaviorCollector,
        optimization_engine: OptimizationEngine
    ):
        """
        初始化场景推荐引擎
        
        Args:
            behavior_collector: 行为数据收集器
            optimization_engine: 优化引擎
        """
        self.behavior_collector = behavior_collector
        self.optimization_engine = optimization_engine
    
    def recommend_automation_scenarios(
        self,
        days: int = 30,
        min_frequency: int = 5
    ) -> List[ScenarioRecommendation]:
        """
        推荐自动化场景
        
        Args:
            days: 分析天数
            min_frequency: 最小出现频率
            
        Returns:
            List[ScenarioRecommendation]: 场景推荐列表
        """
        # 使用优化引擎的推荐功能
        automation_scenarios = self.optimization_engine.recommend_automation_scenarios(
            min_frequency=min_frequency,
            days=days
        )
        
        # 转换为场景推荐
        recommendations = []
        for scenario in automation_scenarios:
            recommendation = ScenarioRecommendation(
                scenario_id=scenario.scenario_id,
                name=scenario.name,
                description=scenario.description,
                scenario_type="automation",
                frequency=scenario.frequency,
                potential_value=scenario.estimated_automation_potential,
                estimated_time_saved=scenario.avg_time_saved,
                estimated_cost_saved=scenario.avg_time_saved * 0.1,  # 简化：假设每秒0.1元成本
                confidence=scenario.confidence,
                suggested_implementation={
                    "workflow": scenario.suggested_workflow,
                    "estimated_development_time": "2-4小时",
                    "estimated_maintenance_cost": "低"
                },
                created_at=datetime.now()
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def recommend_workflow_templates(
        self,
        days: int = 30
    ) -> List[ScenarioRecommendation]:
        """
        推荐工作流模板
        
        基于频繁执行的工作流模式，推荐为可重用模板
        
        Args:
            days: 分析天数
            
        Returns:
            List[ScenarioRecommendation]: 工作流模板推荐列表
        """
        # 分析工作流执行数据
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # 获取所有工作流执行数据（简化实现）
        workflow_patterns = {}
        
        # 分析工作流步骤模式
        # 这里简化实现，实际应该分析步骤组合模式
        
        recommendations = []
        
        # 示例：推荐高频工作流作为模板
        # 实际实现应该分析步骤模式，识别可重用的工作流模板
        
        return recommendations
    
    def recommend_resource_combinations(
        self,
        days: int = 30,
        min_co_occurrence: int = 10
    ) -> List[ScenarioRecommendation]:
        """
        推荐资源组合
        
        基于资源共同使用模式，推荐高效的资源组合
        
        Args:
            days: 分析天数
            min_co_occurrence: 最小共同出现次数
            
        Returns:
            List[ScenarioRecommendation]: 资源组合推荐列表
        """
        # 分析资源使用数据
        resource_usage = self.behavior_collector.get_resource_usage_statistics(top_n=100)
        
        # 分析资源共同使用模式（简化实现）
        # 实际应该分析在同一工作流或意图中共同使用的资源
        
        recommendations = []
        
        # 示例：推荐高频使用的资源组合
        top_resources = resource_usage[:10]
        if len(top_resources) >= 2:
            # 创建资源组合推荐
            combination = [r["resource_id"] for r in top_resources[:3]]
            recommendation = ScenarioRecommendation(
                scenario_id=f"resource_combo_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                name="高频资源组合",
                description=f"这些资源经常一起使用: {', '.join(combination)}",
                scenario_type="resource_combination",
                frequency=sum(r["usage_count"] for r in top_resources[:3]),
                potential_value=0.7,
                estimated_time_saved=5.0,
                estimated_cost_saved=0.5,
                confidence=0.8,
                suggested_implementation={
                    "resources": combination,
                    "suggestion": "考虑将这些资源组合为一个复合操作"
                },
                created_at=datetime.now()
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def get_all_recommendations(
        self,
        days: int = 30,
        min_confidence: float = 0.6
    ) -> List[ScenarioRecommendation]:
        """
        获取所有推荐场景
        
        Args:
            days: 分析天数
            min_confidence: 最小置信度
            
        Returns:
            List[ScenarioRecommendation]: 所有推荐场景
        """
        all_recommendations = []
        
        # 自动化场景推荐
        automation_recs = self.recommend_automation_scenarios(days=days)
        all_recommendations.extend(automation_recs)
        
        # 工作流模板推荐
        template_recs = self.recommend_workflow_templates(days=days)
        all_recommendations.extend(template_recs)
        
        # 资源组合推荐
        resource_recs = self.recommend_resource_combinations(days=days)
        all_recommendations.extend(resource_recs)
        
        # 按置信度和潜在价值排序
        all_recommendations = [
            r for r in all_recommendations
            if r.confidence >= min_confidence
        ]
        all_recommendations.sort(
            key=lambda r: (r.confidence * r.potential_value),
            reverse=True
        )
        
        return all_recommendations
    
    def get_recommendation_details(
        self,
        scenario_id: str
    ) -> Optional[ScenarioRecommendation]:
        """获取推荐场景详情"""
        # 重新生成所有推荐并查找
        all_recs = self.get_all_recommendations()
        for rec in all_recs:
            if rec.scenario_id == scenario_id:
                return rec
        return None


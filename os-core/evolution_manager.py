"""
自演进管理器
管理AIOS的版本演进，记录每次优化的效果
支持A/B测试（对比优化前后的效果）
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

try:
    from .optimization_engine import OptimizationEngine, OptimizationRecommendation
    from .behavior_collector import BehaviorCollector
except ImportError:
    from optimization_engine import OptimizationEngine, OptimizationRecommendation
    from behavior_collector import BehaviorCollector

logger = logging.getLogger(__name__)


class EvolutionStatus(Enum):
    """演进状态"""
    PROPOSED = "proposed"  # 已提出
    TESTING = "testing"  # 测试中
    APPROVED = "approved"  # 已批准
    DEPLOYED = "deployed"  # 已部署
    REJECTED = "rejected"  # 已拒绝
    ROLLED_BACK = "rolled_back"  # 已回滚


@dataclass
class EvolutionVersion:
    """演进版本"""
    version_id: str
    version_name: str
    description: str
    optimization_id: str
    changes: List[Dict[str, Any]]
    status: EvolutionStatus
    created_at: datetime
    deployed_at: Optional[datetime] = None
    performance_before: Dict[str, Any] = field(default_factory=dict)
    performance_after: Dict[str, Any] = field(default_factory=dict)
    improvement: float = 0.0  # 改进百分比
    rollback_reason: Optional[str] = None


@dataclass
class ABTestResult:
    """A/B测试结果"""
    test_id: str
    test_name: str
    variant_a_performance: Dict[str, Any]
    variant_b_performance: Dict[str, Any]
    improvement: float
    statistical_significance: float  # 统计显著性（0-1）
    recommendation: str  # "variant_a" | "variant_b" | "no_difference"
    completed_at: datetime


class EvolutionManager:
    """自演进管理器"""
    
    def __init__(
        self,
        optimization_engine: OptimizationEngine,
        behavior_collector: BehaviorCollector
    ):
        """
        初始化自演进管理器
        
        Args:
            optimization_engine: 优化引擎
            behavior_collector: 行为数据收集器
        """
        self.optimization_engine = optimization_engine
        self.behavior_collector = behavior_collector
        self._versions: Dict[str, EvolutionVersion] = {}  # {version_id: EvolutionVersion}
        self._ab_tests: Dict[str, ABTestResult] = {}  # {test_id: ABTestResult}
        self._version_counter = 0
    
    def create_evolution_version(
        self,
        optimization_recommendation: OptimizationRecommendation,
        version_name: Optional[str] = None
    ) -> EvolutionVersion:
        """
        创建演进版本
        
        Args:
            optimization_recommendation: 优化建议
            version_name: 版本名称（可选）
            
        Returns:
            EvolutionVersion: 演进版本
        """
        self._version_counter += 1
        version_id = f"v{self._version_counter}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if not version_name:
            version_name = f"优化版本 {self._version_counter}"
        
        version = EvolutionVersion(
            version_id=version_id,
            version_name=version_name,
            description=optimization_recommendation.reasoning,
            optimization_id=optimization_recommendation.optimization_id,
            changes=optimization_recommendation.recommended_changes,
            status=EvolutionStatus.PROPOSED,
            created_at=datetime.now(),
            performance_before=optimization_recommendation.current_performance.copy()
        )
        
        self._versions[version_id] = version
        logger.info(f"创建演进版本: {version_id} - {version_name}")
        
        return version
    
    def start_ab_test(
        self,
        version_id: str,
        test_name: str,
        traffic_split: float = 0.5
    ) -> str:
        """
        启动A/B测试
        
        Args:
            version_id: 演进版本ID
            test_name: 测试名称
            traffic_split: 流量分配比例
            
        Returns:
            str: 测试ID
        """
        version = self._versions.get(version_id)
        if not version:
            raise ValueError(f"演进版本 {version_id} 不存在")
        
        # 获取目标ID（工作流ID等）
        target_id = version.optimization_id.split("_")[1] if "_" in version.optimization_id else version_id
        
        # 创建A/B测试
        test_id = self.optimization_engine.create_ab_test(
            test_name=test_name,
            workflow_id=target_id,
            variant_a=version.performance_before,  # 原始版本
            variant_b={"version_id": version_id, "changes": version.changes},  # 优化版本
            traffic_split=traffic_split
        )
        
        # 更新版本状态
        version.status = EvolutionStatus.TESTING
        
        logger.info(f"启动A/B测试: {test_id} for version {version_id}")
        return test_id
    
    def evaluate_ab_test(
        self,
        test_id: str,
        min_executions: int = 50
    ) -> ABTestResult:
        """
        评估A/B测试结果
        
        Args:
            test_id: 测试ID
            min_executions: 最小执行次数（用于统计显著性）
            
        Returns:
            ABTestResult: A/B测试结果
        """
        # 获取测试结果
        test_results = self.optimization_engine.get_ab_test_results(test_id)
        
        variant_a = test_results["results"]["variant_a"]
        variant_b = test_results["results"]["variant_b"]
        
        # 检查是否有足够的数据
        total_executions = variant_a["executions"] + variant_b["executions"]
        if total_executions < min_executions:
            raise ValueError(f"执行次数不足（{total_executions} < {min_executions}），无法得出可靠结论")
        
        # 计算统计显著性（简化实现：基于样本量）
        statistical_significance = min(0.95, total_executions / 100.0)
        
        # 计算改进
        improvement = test_results.get("improvement", 0.0)
        
        # 确定推荐
        if improvement > 5 and statistical_significance > 0.8:
            recommendation = "variant_b"
        elif improvement < -5 and statistical_significance > 0.8:
            recommendation = "variant_a"
        else:
            recommendation = "no_difference"
        
        ab_result = ABTestResult(
            test_id=test_id,
            test_name=test_results["test_name"],
            variant_a_performance={
                "executions": variant_a["executions"],
                "success_rate": (variant_a["success"] / variant_a["executions"] * 100) if variant_a["executions"] > 0 else 0,
                "avg_time": variant_a["avg_time"]
            },
            variant_b_performance={
                "executions": variant_b["executions"],
                "success_rate": (variant_b["success"] / variant_b["executions"] * 100) if variant_b["executions"] > 0 else 0,
                "avg_time": variant_b["avg_time"]
            },
            improvement=improvement,
            statistical_significance=statistical_significance,
            recommendation=recommendation,
            completed_at=datetime.now()
        )
        
        self._ab_tests[test_id] = ab_result
        
        # 更新版本状态
        if recommendation == "variant_b":
            # 找到对应的版本并标记为已批准
            for version in self._versions.values():
                if version.optimization_id in test_id:
                    version.status = EvolutionStatus.APPROVED
                    version.performance_after = variant_b
                    version.improvement = improvement
                    break
        
        logger.info(f"A/B测试评估完成: {test_id}, 推荐: {recommendation}")
        return ab_result
    
    def deploy_version(
        self,
        version_id: str
    ) -> EvolutionVersion:
        """
        部署演进版本
        
        Args:
            version_id: 版本ID
            
        Returns:
            EvolutionVersion: 部署后的版本
        """
        version = self._versions.get(version_id)
        if not version:
            raise ValueError(f"演进版本 {version_id} 不存在")
        
        if version.status != EvolutionStatus.APPROVED:
            raise ValueError(f"版本 {version_id} 状态为 {version.status.value}，不能部署（需要已批准）")
        
        # 应用优化
        target_id = version.optimization_id.split("_")[1] if "_" in version.optimization_id else version_id
        self.optimization_engine.auto_optimize_workflow(target_id, apply_changes=True)
        
        # 更新版本状态
        version.status = EvolutionStatus.DEPLOYED
        version.deployed_at = datetime.now()
        
        logger.info(f"部署演进版本: {version_id}")
        return version
    
    def rollback_version(
        self,
        version_id: str,
        reason: str
    ) -> EvolutionVersion:
        """
        回滚演进版本
        
        Args:
            version_id: 版本ID
            reason: 回滚原因
            
        Returns:
            EvolutionVersion: 回滚后的版本
        """
        version = self._versions.get(version_id)
        if not version:
            raise ValueError(f"演进版本 {version_id} 不存在")
        
        if version.status != EvolutionStatus.DEPLOYED:
            raise ValueError(f"版本 {version_id} 未部署，无法回滚")
        
        # 回滚优化（简化实现）
        target_id = version.optimization_id.split("_")[1] if "_" in version.optimization_id else version_id
        logger.info(f"回滚版本 {version_id} 的优化: {target_id}")
        
        # 更新版本状态
        version.status = EvolutionStatus.ROLLED_BACK
        version.rollback_reason = reason
        
        logger.info(f"回滚演进版本: {version_id}, 原因: {reason}")
        return version
    
    def get_evolution_history(
        self,
        target_id: Optional[str] = None,
        status: Optional[EvolutionStatus] = None
    ) -> List[Dict[str, Any]]:
        """获取演进历史"""
        versions = list(self._versions.values())
        
        # 应用过滤
        if target_id:
            versions = [v for v in versions if target_id in v.optimization_id]
        if status:
            versions = [v for v in versions if v.status == status]
        
        # 转换为字典
        return [
            {
                "version_id": v.version_id,
                "version_name": v.version_name,
                "description": v.description,
                "status": v.status.value,
                "improvement": v.improvement,
                "created_at": v.created_at.isoformat(),
                "deployed_at": v.deployed_at.isoformat() if v.deployed_at else None
            }
            for v in sorted(versions, key=lambda x: x.created_at, reverse=True)
        ]
    
    def get_evolution_statistics(self) -> Dict[str, Any]:
        """获取演进统计信息"""
        total_versions = len(self._versions)
        deployed_versions = sum(1 for v in self._versions.values() if v.status == EvolutionStatus.DEPLOYED)
        rolled_back_versions = sum(1 for v in self._versions.values() if v.status == EvolutionStatus.ROLLED_BACK)
        
        # 计算平均改进
        deployed = [v for v in self._versions.values() if v.status == EvolutionStatus.DEPLOYED]
        avg_improvement = sum(v.improvement for v in deployed) / len(deployed) if deployed else 0.0
        
        return {
            "total_versions": total_versions,
            "deployed_versions": deployed_versions,
            "rolled_back_versions": rolled_back_versions,
            "avg_improvement": avg_improvement,
            "ab_tests_count": len(self._ab_tests)
        }


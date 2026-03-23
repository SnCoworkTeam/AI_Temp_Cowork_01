"""
元数据驱动的执行编排器
使用元数据指导路由决策和执行优化
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .task_classifier import RoutingDecision, ExecutionStrategy
from .conversation_agent import IntentAnalysis
from ..services.metadata_client import metadata_client

logger = logging.getLogger(__name__)


class MetadataDrivenExecutor:
    """元数据驱动的执行编排器"""
    
    def __init__(self):
        self.metadata_client = metadata_client
    
    def _extract_service_recommendations(
        self,
        metadata: Dict[str, Any],
        intent_analysis: IntentAnalysis
    ) -> List[Dict[str, Any]]:
        """
        从元数据中提取服务推荐
        
        Args:
            metadata: 元数据字典
            intent_analysis: 意图分析结果
            
        Returns:
            推荐的服务列表
        """
        recommendations = []
        
        # 从AI模型中提取推荐
        ai_models = metadata.get("ai_models", [])
        for model in ai_models[:3]:  # 取前3个
            recommendations.append({
                "service_id": f"ai_model_{model.get('id')}",
                "service_name": model.get("display_name") or model.get("name", ""),
                "service_type": "ai_model",
                "match_reason": "AI模型匹配",
                "confidence": 0.7,
                "metadata": model
            })
        
        # 从语义服务中提取推荐
        semantic_services = metadata.get("semantic_services", [])
        for service in semantic_services:
            recommendations.append({
                "service_id": service.get("service_id", ""),
                "service_name": service.get("service_name", ""),
                "service_type": service.get("service_type", "unknown"),
                "match_reason": "语义相似度匹配",
                "confidence": service.get("similarity_score", 0.5),
                "metadata": service.get("metadata", {})
            })
        
        # 从工作流中提取推荐（如果意图是工作流任务）
        if intent_analysis.task_type.value == "workflow_task":
            workflows = metadata.get("workflows", [])
            for workflow in workflows[:2]:  # 取前2个
                recommendations.append({
                    "service_id": f"workflow_{workflow.get('id')}",
                    "service_name": workflow.get("display_name") or workflow.get("name", ""),
                    "service_type": "workflow",
                    "match_reason": "工作流匹配",
                    "confidence": 0.8,
                    "metadata": workflow
                })
        
        # 按置信度排序
        recommendations.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        
        return recommendations
    
    def _enhance_routing_decision(
        self,
        routing_decision: RoutingDecision,
        metadata: Dict[str, Any],
        recommendations: List[Dict[str, Any]]
    ) -> RoutingDecision:
        """
        使用元数据增强路由决策
        
        Args:
            routing_decision: 原始路由决策
            metadata: 元数据字典
            recommendations: 服务推荐列表
            
        Returns:
            增强的路由决策
        """
        # 如果有推荐的服务，优先使用
        if recommendations:
            top_recommendation = recommendations[0]
            
            # 根据推荐的服务类型调整路由决策
            service_type = top_recommendation.get("service_type")
            
            if service_type == "ai_model":
                # 如果推荐AI模型，可能需要调整策略
                if routing_decision.strategy == ExecutionStrategy.DIRECT_LLM:
                    # 保持直接LLM策略，但可以添加模型信息
                    routing_decision.execution_params["recommended_model"] = top_recommendation.get("service_id")
                    routing_decision.reasoning += f" 推荐使用AI模型: {top_recommendation.get('service_name')}"
            
            elif service_type == "workflow":
                # 如果推荐工作流，调整策略
                if routing_decision.strategy != ExecutionStrategy.WORKFLOW_EXECUTION:
                    routing_decision.strategy = ExecutionStrategy.WORKFLOW_EXECUTION
                    routing_decision.target_service = "workflow-engine"
                    routing_decision.execution_params["workflow_id"] = top_recommendation.get("metadata", {}).get("id")
                    routing_decision.reasoning = f"根据元数据推荐，使用工作流: {top_recommendation.get('service_name')}"
            
            elif service_type == "data_asset":
                # 如果推荐数据资产，可能需要工具执行
                if "data" in top_recommendation.get("service_name", "").lower():
                    routing_decision.required_tools.append("data_query")
                    routing_decision.reasoning += f" 推荐查询数据资产: {top_recommendation.get('service_name')}"
        
        # 添加元数据信息到执行参数
        routing_decision.execution_params["metadata"] = {
            "recommendations_count": len(recommendations),
            "top_recommendations": recommendations[:3],
            "query_time": metadata.get("query_time", 0)
        }
        
        return routing_decision
    
    async def enhance_with_metadata(
        self,
        user_input: str,
        intent_analysis: IntentAnalysis,
        routing_decision: RoutingDecision,
        context: Dict[str, Any]
    ) -> RoutingDecision:
        """
        使用元数据增强路由决策
        
        Args:
            user_input: 用户输入
            intent_analysis: 意图分析结果
            routing_decision: 原始路由决策
            context: 上下文信息
            
        Returns:
            增强的路由决策
        """
        try:
            # 获取元数据
            metadata_result = await self.metadata_client.get_realtime_metadata(
                user_input=user_input,
                context=context,
                use_cache=True,
                limit_per_type=5
            )
            
            if not metadata_result or not metadata_result.get("success"):
                logger.debug("Failed to get metadata, using original routing decision")
                return routing_decision
            
            metadata = metadata_result.get("metadata", {})
            
            # 提取服务推荐
            recommendations = self._extract_service_recommendations(metadata, intent_analysis)
            
            # 增强路由决策
            enhanced_decision = self._enhance_routing_decision(
                routing_decision,
                metadata,
                recommendations
            )
            
            logger.info(
                f"Enhanced routing decision with {len(recommendations)} recommendations, "
                f"strategy: {enhanced_decision.strategy.value}"
            )
            
            return enhanced_decision
            
        except Exception as e:
            logger.warning(f"Failed to enhance routing decision with metadata: {e}")
            return routing_decision  # 降级：返回原始决策


# 全局实例
metadata_driven_executor = MetadataDrivenExecutor()



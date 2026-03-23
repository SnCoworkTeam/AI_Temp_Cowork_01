"""
学习型工作流设计器
基于执行历史优化智能体网络设计
"""
import logging
from typing import Dict, Any, Optional, List
import json

from .dynamic_workflow_designer import DynamicWorkflowDesigner
from .performance_analyzer import PerformanceAnalyzer, ExecutionRecord
from .protocols import StandardTask

logger = logging.getLogger(__name__)


class LearningWorkflowDesigner(DynamicWorkflowDesigner):
    """学习型工作流设计器 - 基于历史执行数据优化设计"""
    
    def __init__(self, performance_analyzer: Optional[PerformanceAnalyzer] = None):
        super().__init__()
        self.performance_analyzer = performance_analyzer or PerformanceAnalyzer()
    
    async def design_network(
        self,
        user_input: str,
        context: Dict[str, Any],
        analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        设计智能体网络（增强版：基于历史数据优化）
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            analysis: 请求分析结果（可选）
            
        Returns:
            优化的网络设计
        """
        # 1. 查询相似请求的成功执行模式
        best_patterns = self.performance_analyzer.find_best_pattern_for_request(
            user_input,
            limit=3
        )
        
        if best_patterns and best_patterns[0]["similarity"] > 0.5:
            # 找到相似的成功模式，基于它优化设计
            logger.info(f"Found similar successful pattern (similarity: {best_patterns[0]['similarity']:.2f})")
            optimized_design = await self._adapt_best_pattern(
                best_patterns[0]["pattern"],
                user_input,
                context,
                analysis
            )
            
            # 验证和优化设计
            validated_design = await self._validate_design(optimized_design)
            return validated_design
        else:
            # 没有找到相似模式，使用默认设计
            logger.info("No similar pattern found, using default design")
            return await super().design_network(user_input, context, analysis)
    
    async def _adapt_best_pattern(
        self,
        best_pattern: Dict[str, Any],
        user_input: str,
        context: Dict[str, Any],
        analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        适配最佳模式到当前请求
        
        Args:
            best_pattern: 最佳执行模式
            user_input: 用户输入
            context: 上下文信息
            analysis: 请求分析结果
            
        Returns:
            适配后的网络设计
        """
        if not analysis:
            analysis = await self._analyze_request(user_input, context)
        
        agent_pool_desc = self._get_agent_pool_description()
        
        prompt = f"""
基于历史成功模式，为当前请求设计最优的智能体执行路径：

用户请求: "{user_input}"
请求分析: {json.dumps(analysis, ensure_ascii=False, indent=2)}
历史成功模式: {json.dumps(best_pattern, ensure_ascii=False, indent=2)}

可用智能体池:
{agent_pool_desc}

请基于历史成功模式，为当前请求设计执行网络：

**考虑因素**：
1. **模式复用**：尽可能复用历史成功模式中的智能体组合
2. **请求适配**：根据当前请求特点调整智能体配置
3. **性能优化**：选择历史表现最好的智能体组合

**设计输出**：
- 需要哪些智能体？（优先使用历史成功模式中的智能体）
- 执行顺序和并行策略
- 智能体间的数据流和依赖关系
- 预期执行时间和资源分配

返回JSON格式：
{{
    "agents": [
        {{
            "id": "agent_1",
            "agent_type": "metadata_agent",
            "task": "任务描述",
            "input": {{"参数": "值"}},
            "dependencies": [],
            "output_key": "output_key"
        }}
    ],
    "execution_layers": [
        ["agent_1"],
        ["agent_2", "agent_3"],
        ["agent_4"]
    ],
    "estimated_duration": "预计时间",
    "complexity": "simple|medium|complex",
    "parallel_strategy": "full|partial|sequential",
    "based_on_pattern": true,
    "pattern_similarity": 相似度
}}
"""
        
        try:
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            learning_design_prompt = get_system_prompt(
                "learning_workflow_designer",
                fallback="你是一个智能体网络设计专家，擅长基于历史成功模式优化设计。"
            )
            
            response = await self.llm.chat([
                {"role": "system", "content": learning_design_prompt},
                {"role": "user", "content": prompt}
            ])
            
            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    network_design = json.loads(response[json_start:json_end])
                else:
                    network_design = self._create_fallback_design(user_input, analysis)
            else:
                network_design = response
            
            return network_design
            
        except Exception as e:
            logger.error(f"Pattern adaptation failed: {e}", exc_info=True)
            # 降级到默认设计
            return await super().design_network(user_input, context, analysis)
    
    def record_execution(
        self,
        execution_id: str,
        user_input: str,
        network_design: Dict[str, Any],
        agent_results: Dict[str, Any],
        execution_time: float,
        success: bool
    ):
        """
        记录执行结果（用于学习）
        
        Args:
            execution_id: 执行ID
            user_input: 用户输入
            network_design: 网络设计
            agent_results: 智能体结果
            execution_time: 执行时间
            success: 是否成功
        """
        from datetime import datetime
        record = ExecutionRecord(
            execution_id=execution_id,
            user_input=user_input,
            network_design=network_design,
            agent_results=agent_results,
            execution_time=execution_time,
            success=success,
            created_at=datetime.utcnow()
        )
        self.performance_analyzer.add_execution_record(record)



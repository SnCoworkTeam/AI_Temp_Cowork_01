"""
智能体适配器
将旧版IntelligentAgent适配到标准化接口
"""
import logging
from typing import Dict, Any
from datetime import datetime
import uuid

from .base_agent import IntelligentAgent
from .standardized_agent import StandardizedAgent
from .protocols import StandardTask, StandardResult, ExecutionMetadata, Artifact, TaskPriority

logger = logging.getLogger(__name__)


class AgentAdapter(StandardizedAgent):
    """智能体适配器 - 将旧版智能体适配到标准化接口"""
    
    def __init__(self, legacy_agent: IntelligentAgent):
        """
        初始化适配器
        
        Args:
            legacy_agent: 旧版智能体实例
        """
        super().__init__(
            agent_id=legacy_agent.agent_id,
            name=legacy_agent.name,
            description=legacy_agent.description,
            capabilities=legacy_agent.capabilities or {},
            supported_task_types=["legacy_task", "general"],  # 默认支持所有任务
            supported_input_formats=["dict", "json"],
            supported_output_formats=["dict", "json"]
        )
        self.legacy_agent = legacy_agent
    
    async def analyze_task(self, task: StandardTask) -> Dict[str, Any]:
        """分析任务（适配旧接口）"""
        try:
            # 将StandardTask转换为旧接口格式
            task_description = task.description
            context = task.context
            
            # 调用旧版智能体的analyze_task
            result = await self.legacy_agent.analyze_task(task_description, context)
            
            return result
        except Exception as e:
            logger.error(f"Legacy agent analyze_task failed: {e}", exc_info=True)
            return {
                "can_handle": False,
                "error": str(e)
            }
    
    async def execute(self, task: StandardTask) -> StandardResult:
        """执行任务（适配旧接口）"""
        start_time = datetime.utcnow()
        
        try:
            # 将StandardTask转换为旧接口格式
            input_data = task.input_data.copy()
            input_data["task"] = task.description
            context = task.context
            
            # 调用旧版智能体的execute
            legacy_result = await self.legacy_agent.execute(input_data, context)
            
            # 将旧版结果转换为StandardResult
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            standard_result = self._convert_legacy_result(legacy_result, task)
            
            # 添加执行元数据
            if not standard_result.execution_metadata:
                standard_result.execution_metadata = ExecutionMetadata(
                    execution_id=str(uuid.uuid4()),
                    agent_id=self.agent_id,
                    agent_name=self.name,
                    start_time=start_time,
                    end_time=end_time,
                    execution_time=execution_time
                )
            
            return standard_result
            
        except Exception as e:
            logger.error(f"Legacy agent execute failed: {e}", exc_info=True)
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            return StandardResult(
                success=False,
                output=None,
                execution_metadata=ExecutionMetadata(
                    execution_id=str(uuid.uuid4()),
                    agent_id=self.agent_id,
                    agent_name=self.name,
                    start_time=start_time,
                    end_time=end_time,
                    execution_time=execution_time,
                    error_count=1
                ),
                error=str(e),
                error_code="EXECUTION_ERROR"
            )
    
    def _convert_legacy_result(
        self,
        legacy_result: Dict[str, Any],
        task: StandardTask
    ) -> StandardResult:
        """将旧版结果转换为StandardResult"""
        
        # 提取关键信息
        success = legacy_result.get("execution_success", False) or legacy_result.get("success", False)
        output = legacy_result.get("result") or legacy_result.get("output") or legacy_result
        
        # 提取错误信息
        error = legacy_result.get("error")
        error_code = legacy_result.get("error_code")
        
        # 提取质量评分
        quality_score = legacy_result.get("quality_score")
        
        # 提取警告和建议
        warnings = legacy_result.get("warnings", [])
        recommendations = legacy_result.get("recommendations", [])
        
        # 创建Artifacts（如果有）
        artifacts = []
        if isinstance(output, dict):
            # 尝试从输出中提取artifacts
            if "artifacts" in output:
                for artifact_data in output["artifacts"]:
                    artifacts.append(Artifact(
                        artifact_id=str(uuid.uuid4()),
                        artifact_type=artifact_data.get("type", "data"),
                        content=artifact_data.get("content"),
                        metadata=artifact_data.get("metadata", {})
                    ))
        
        return StandardResult(
            success=success,
            output=output,
            artifacts=artifacts,
            error=error,
            error_code=error_code,
            quality_score=quality_score,
            warnings=warnings,
            recommendations=recommendations,
            metadata=legacy_result.get("metadata", {})
        )


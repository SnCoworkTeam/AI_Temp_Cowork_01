"""
智能任务分解器
使用LLM将用户输入分解为DAG执行计划
支持元数据增强的任务分解
"""
import logging
import uuid
from typing import Dict, Any
from ..models.dag_models import DAGPlan, TaskNode, TaskType
from ..services.llm_integration import LLMIntegration
from .metadata_enhanced_decomposer import metadata_enhanced_decomposer

logger = logging.getLogger(__name__)


class TaskDecomposer:
    """任务分解器"""
    
    def __init__(self):
        self.llm_client = LLMIntegration()
    
    async def decompose_task(self, user_input: str, context: Dict[str, Any] = None) -> DAGPlan:
        """
        使用LLM智能分解用户输入为DAG执行计划
        
        Args:
            user_input: 用户输入的任务描述
            context: 上下文信息
            
        Returns:
            DAG执行计划
        """
        context = context or {}
        
        # 尝试获取元数据增强信息
        metadata_enhancement = ""
        try:
            metadata_enhancement = await metadata_enhanced_decomposer.enhance_decomposition_prompt(
                user_input,
                context
            )
        except Exception as e:
            logger.debug(f"Failed to get metadata enhancement: {e}")
        
        decomposition_prompt = f"""
请将以下用户任务分解为可执行的DAG计划：

用户任务: {user_input}

上下文信息: {context}
{metadata_enhancement}

请按以下要求输出：
1. 识别主要子任务（确保每个任务都是原子性的，可以独立执行）
2. 确定任务之间的依赖关系（哪些任务必须先完成，哪些可以并行执行）
3. 为每个任务分配合适的执行服务：
   - mcp_tool: 需要调用外部工具（如GitHub搜索、JIRA查询、文件操作、数据库操作等）
   - workflow: 需要执行已定义的复杂工作流
   - knowledge: 需要从知识库检索信息
   - calculation: 简单的计算或数据处理
   - condition: 条件判断

4. 为每个任务指定：
   - name: 任务名称（简洁明确）
   - description: 任务描述
   - task_type: 任务类型（mcp_tool/workflow/knowledge/calculation/condition）
   - target_service: 目标服务（mcp-gateway/workflow-engine/knowledge-base等）
   - action: 具体操作（如工具名称、工作流名称、搜索查询等）
   - parameters: 任务参数（从用户输入和上下文中提取）
   - dependencies: 依赖的节点ID列表（空列表表示无依赖）

请严格按照以下JSON格式输出，不要添加任何额外的解释文字：
{{
    "task_nodes": {{
        "node_1": {{
            "name": "任务名称",
            "description": "任务描述",
            "task_type": "mcp_tool",
            "target_service": "mcp-gateway",
            "action": "具体操作名称",
            "parameters": {{"key": "value"}},
            "dependencies": []
        }},
        "node_2": {{
            "name": "任务名称",
            "description": "任务描述",
            "task_type": "workflow",
            "target_service": "workflow-engine",
            "action": "工作流名称或ID",
            "parameters": {{"input_data": {{"input": "value"}}}},
            "dependencies": ["node_1"]
        }}
    }},
    "entry_nodes": ["node_1"],
    "exit_nodes": ["node_2"]
}}

注意：
- 确保所有节点ID是唯一的（node_1, node_2, node_3...）
- entry_nodes是没有任何依赖的节点
- exit_nodes是没有任何后续节点的节点
- 参数应该从用户输入中提取，如果用户输入是"搜索Python相关文档"，那么parameters应该是{{"query": "Python"}}
- 如果任务需要工作流，action应该是工作流的名称或ID，parameters应该包含input_data字段
"""
        
        try:
            # 调用LLM进行智能分解
            logger.info(f"Decomposing task: {user_input[:100]}...")
            llm_response = await self.llm_client.analyze(decomposition_prompt)
            
            # 解析LLM响应
            dag_structure = self.llm_client.parse_json_response(llm_response)
            
            # 构建DAGPlan对象
            dag_id = f"dag_{uuid.uuid4().hex[:12]}"
            
            # 转换task_nodes
            task_nodes = {}
            for node_id, node_data in dag_structure.get("task_nodes", {}).items():
                # 处理task_type，确保是有效的枚举值
                task_type_str = node_data.get("task_type", "calculation")
                try:
                    task_type = TaskType(task_type_str)
                except ValueError:
                    # 如果枚举值无效，使用默认值
                    logger.warning(f"Invalid task_type '{task_type_str}', using 'calculation'")
                    task_type = TaskType.CALCULATION
                
                task_nodes[node_id] = TaskNode(
                    node_id=node_id,
                    name=node_data.get("name", ""),
                    description=node_data.get("description", ""),
                    task_type=task_type,
                    target_service=node_data.get("target_service", ""),
                    action=node_data.get("action", ""),
                    parameters=node_data.get("parameters", {}),
                    dependencies=node_data.get("dependencies", [])
                )
            
            # 基于元数据语义关系优化依赖关系
            try:
                suggested_deps = await metadata_enhanced_decomposer.suggest_task_dependencies(
                    {node_id: node_data.model_dump() for node_id, node_data in task_nodes.items()},
                    user_input
                )
                
                # 合并建议的依赖关系（不覆盖已有的依赖）
                for node_id, suggested_dep_list in suggested_deps.items():
                    if node_id in task_nodes:
                        existing_deps = set(task_nodes[node_id].dependencies)
                        new_deps = existing_deps.union(set(suggested_dep_list))
                        task_nodes[node_id].dependencies = list(new_deps)
                        logger.debug(f"Enhanced dependencies for {node_id}: {task_nodes[node_id].dependencies}")
            except Exception as e:
                logger.debug(f"Failed to enhance dependencies with metadata: {e}")
            
            dag_plan = DAGPlan(
                dag_id=dag_id,
                task_nodes=task_nodes,
                entry_nodes=dag_structure.get("entry_nodes", []),
                exit_nodes=dag_structure.get("exit_nodes", []),
                metadata={
                    "user_input": user_input,
                    "context": context,
                    "decomposed_by": "llm"
                }
            )
            
            logger.info(f"DAG plan created: {dag_id} with {len(task_nodes)} nodes")
            return dag_plan
            
        except Exception as e:
            logger.error(f"Task decomposition failed: {str(e)}", exc_info=True)
            # 如果LLM分解失败，返回一个简单的默认计划
            return self._create_fallback_plan(user_input, context)
    
    def _create_fallback_plan(self, user_input: str, context: Dict[str, Any]) -> DAGPlan:
        """
        创建回退计划（当LLM分解失败时）
        
        Args:
            user_input: 用户输入
            context: 上下文
            
        Returns:
            简单的DAG计划
        """
        logger.warning("Using fallback plan due to decomposition failure")
        
        dag_id = f"dag_{uuid.uuid4().hex[:12]}"
        
        # 创建一个简单的单节点计划
        task_node = TaskNode(
            node_id="node_1",
            name="处理用户请求",
            description=f"处理用户输入: {user_input}",
            task_type=TaskType.KNOWLEDGE,
            target_service="knowledge-base",
            action="search",
            parameters={"query": user_input},
            dependencies=[]
        )
        
        return DAGPlan(
            dag_id=dag_id,
            task_nodes={"node_1": task_node},
            entry_nodes=["node_1"],
            exit_nodes=["node_1"],
            metadata={
                "user_input": user_input,
                "context": context,
                "decomposed_by": "fallback"
            }
        )


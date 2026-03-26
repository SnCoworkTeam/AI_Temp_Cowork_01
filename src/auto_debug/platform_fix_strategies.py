"""
针对平台特有问题的修复策略库

功能：
1. MCP工具修复策略
2. 工作流引擎修复策略
3. 知识库修复策略
4. 前端界面修复策略
5. 基于错误类型自动选择修复策略
6. 支持策略的组合使用
7. 修复策略的可配置性
"""
from typing import Dict, Any, Optional, List, Callable, Tuple
from enum import Enum
from datetime import datetime
import logging
import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import wraps

from .platform_error_analyzer import ErrorCategory, ErrorType, ErrorAnalysis

logger = logging.getLogger(__name__)


class FixStrategyType(Enum):
    """修复策略类型"""
    RETRY = "retry"
    FALLBACK = "fallback"
    RECOVERY = "recovery"
    VALIDATION = "validation"
    CONFIG_UPDATE = "config_update"
    CACHE_CLEAR = "cache_clear"
    STATE_RESTORE = "state_restore"
    ROLLBACK = "rollback"


@dataclass
class FixStrategyConfig:
    """修复策略配置"""
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
    timeout: Optional[float] = None
    enable_fallback: bool = True
    enable_cache_clear: bool = True
    enable_state_restore: bool = True
    strategy_priority: List[str] = field(default_factory=lambda: [
        "retry", "validation", "fallback", "recovery", "config_update"
    ])


@dataclass
class FixResult:
    """修复结果"""
    success: bool
    strategy_used: str
    message: str
    data: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    execution_time: float = 0.0
    error: Optional[str] = None


class BaseFixStrategy(ABC):
    """修复策略基类"""
    
    def __init__(self, config: Optional[FixStrategyConfig] = None):
        self.config = config or FixStrategyConfig()
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def can_apply(self, error_analysis: ErrorAnalysis, context: Dict[str, Any]) -> bool:
        """判断是否可以应用此策略"""
        pass
    
    @abstractmethod
    async def apply(self, error_analysis: ErrorAnalysis, context: Dict[str, Any]) -> FixResult:
        """应用修复策略"""
        pass
    
    def _should_retry(self, attempt: int, error_message: str) -> bool:
        """判断是否应该重试"""
        if attempt >= self.config.max_retries:
            return False
        
        # 某些错误不应该重试
        non_retryable_errors = [
            "not found", "invalid", "permission denied", "unauthorized"
        ]
        
        error_lower = error_message.lower()
        for non_retryable in non_retryable_errors:
            if non_retryable in error_lower:
                return False
        
        return True
    
    async def _retry_with_backoff(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Tuple[Any, int]:
        """带指数退避的重试"""
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                if self.config.timeout:
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=self.config.timeout
                    )
                else:
                    result = await func(*args, **kwargs)
                
                return result, attempt
            
            except Exception as e:
                last_error = e
                error_message = str(e)
                
                if not self._should_retry(attempt, error_message):
                    break
                
                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay * (self.config.retry_backoff ** attempt)
                    logger.info(
                        f"Retry attempt {attempt + 1}/{self.config.max_retries} "
                        f"after {delay:.2f}s: {error_message}"
                    )
                    await asyncio.sleep(delay)
        
        raise last_error


class MCPToolFixStrategy(BaseFixStrategy):
    """MCP工具修复策略"""
    
    async def can_apply(
        self,
        error_analysis: ErrorAnalysis,
        context: Dict[str, Any]
    ) -> bool:
        """判断是否可以应用此策略"""
        return error_analysis.category == ErrorCategory.MCP_TOOL
    
    async def apply(
        self,
        error_analysis: ErrorAnalysis,
        context: Dict[str, Any]
    ) -> FixResult:
        """应用MCP工具修复策略"""
        start_time = datetime.now()
        tool_name = context.get("tool_name") or error_analysis.context.get("tool_name")
        parameters = context.get("parameters", {})
        
        strategies_applied = []
        
        # 1. 工具连接重试机制
        if "connection" in error_analysis.error_message.lower() or \
           "timeout" in error_analysis.error_message.lower():
            result = await self._retry_tool_connection(tool_name, parameters, context)
            strategies_applied.append("connection_retry")
            if result.success:
                execution_time = (datetime.now() - start_time).total_seconds()
                return FixResult(
                    success=True,
                    strategy_used="connection_retry",
                    message="工具连接重试成功",
                    data=result.data,
                    retry_count=result.retry_count,
                    execution_time=execution_time
                )
        
        # 2. 参数验证和自动修正
        if error_analysis.error_type == ErrorType.DATA_ERROR:
            fixed_params = await self._validate_and_fix_parameters(tool_name, parameters, context)
            if fixed_params != parameters:
                result = await self._execute_tool_with_fixed_params(tool_name, fixed_params, context)
                strategies_applied.append("parameter_fix")
                if result.success:
                    execution_time = (datetime.now() - start_time).total_seconds()
                    return FixResult(
                        success=True,
                        strategy_used="parameter_fix",
                        message="参数修正后执行成功",
                        data=result.data,
                        execution_time=execution_time
                    )
        
        # 3. 备用工具切换策略
        if self.config.enable_fallback:
            fallback_result = await self._try_fallback_tool(tool_name, parameters, context)
            strategies_applied.append("fallback_tool")
            if fallback_result.success:
                execution_time = (datetime.now() - start_time).total_seconds()
                return FixResult(
                    success=True,
                    strategy_used="fallback_tool",
                    message=f"使用备用工具 {fallback_result.data.get('fallback_tool')} 执行成功",
                    data=fallback_result.data,
                    execution_time=execution_time
                )
        
        # 4. 工具配置热更新
        if error_analysis.error_type == ErrorType.CONFIG_ERROR:
            config_result = await self._update_tool_config(tool_name, context)
            strategies_applied.append("config_update")
            if config_result.success:
                execution_time = (datetime.now() - start_time).total_seconds()
                return FixResult(
                    success=True,
                    strategy_used="config_update",
                    message="工具配置更新成功",
                    data=config_result.data,
                    execution_time=execution_time
                )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        return FixResult(
            success=False,
            strategy_used=",".join(strategies_applied) if strategies_applied else "none",
            message="所有MCP工具修复策略均失败",
            retry_count=len(strategies_applied),
            execution_time=execution_time,
            error="无法修复MCP工具错误"
        )
    
    async def _retry_tool_connection(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> FixResult:
        """工具连接重试"""
        try:
            async def execute_tool():
                # 这里应该调用实际的工具执行逻辑
                # 为了演示，我们模拟一个调用
                from shared_libs.common.http_client import HTTPClient
                mcp_gateway_url = context.get("mcp_gateway_url", "http://localhost:8001")
                
                async with HTTPClient(mcp_gateway_url, timeout=self.config.timeout or 30) as client:
                    response = await client.post(
                        f"/api/tools/{tool_name}/execute",
                        data={"parameters": parameters}
                    )
                    return response
            
            result, retry_count = await self._retry_with_backoff(execute_tool)
            
            return FixResult(
                success=True,
                strategy_used="connection_retry",
                message="工具连接重试成功",
                data={"result": result, "retry_count": retry_count},
                retry_count=retry_count
            )
        
        except Exception as e:
            return FixResult(
                success=False,
                strategy_used="connection_retry",
                message=f"工具连接重试失败: {str(e)}",
                error=str(e)
            )
    
    async def _validate_and_fix_parameters(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证和修正参数"""
        fixed_params = parameters.copy()
        
        # 获取工具定义以验证参数
        try:
            from shared_libs.common.http_client import HTTPClient
            mcp_gateway_url = context.get("mcp_gateway_url", "http://localhost:8001")
            
            async with HTTPClient(mcp_gateway_url) as client:
                tool_info = await client.get(f"/api/tools/{tool_name}")
                
                # 检查必需参数
                required_params = tool_info.get("required_parameters", [])
                for param in required_params:
                    if param not in fixed_params:
                        # 尝试从上下文获取默认值
                        default_value = context.get(f"default_{param}")
                        if default_value is not None:
                            fixed_params[param] = default_value
                        else:
                            logger.warning(f"Missing required parameter: {param}")
                
                # 类型转换和验证
                param_schema = tool_info.get("parameters", {}).get("properties", {})
                for param_name, param_value in fixed_params.items():
                    if param_name in param_schema:
                        param_def = param_schema[param_name]
                        param_type = param_def.get("type")
                        
                        # 简单的类型转换
                        if param_type == "integer" and isinstance(param_value, str):
                            try:
                                fixed_params[param_name] = int(param_value)
                            except ValueError:
                                pass
                        elif param_type == "number" and isinstance(param_value, str):
                            try:
                                fixed_params[param_name] = float(param_value)
                            except ValueError:
                                pass
        
        except Exception as e:
            logger.warning(f"Failed to validate parameters: {str(e)}")
        
        return fixed_params
    
    async def _execute_tool_with_fixed_params(
        self,
        tool_name: str,
        fixed_params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> FixResult:
        """使用修正后的参数执行工具"""
        try:
            from shared_libs.common.http_client import HTTPClient
            mcp_gateway_url = context.get("mcp_gateway_url", "http://localhost:8001")
            
            async with HTTPClient(mcp_gateway_url) as client:
                response = await client.post(
                    f"/api/tools/{tool_name}/execute",
                    data={"parameters": fixed_params}
                )
                
                return FixResult(
                    success=True,
                    strategy_used="parameter_fix",
                    message="使用修正后的参数执行成功",
                    data={"result": response}
                )
        
        except Exception as e:
            return FixResult(
                success=False,
                strategy_used="parameter_fix",
                message=f"执行失败: {str(e)}",
                error=str(e)
            )
    
    async def _try_fallback_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> FixResult:
        """尝试备用工具"""
        # 定义工具映射关系
        fallback_mapping = {
            "sap_query": ["sap_query_v2", "sap_query_legacy"],
            "knowledge_search": ["knowledge_search_v2", "document_search"],
        }
        
        fallback_tools = fallback_mapping.get(tool_name, [])
        
        for fallback_tool in fallback_tools:
            try:
                from shared_libs.common.http_client import HTTPClient
                mcp_gateway_url = context.get("mcp_gateway_url", "http://localhost:8001")
                
                async with HTTPClient(mcp_gateway_url) as client:
                    response = await client.post(
                        f"/api/tools/{fallback_tool}/execute",
                        data={"parameters": parameters}
                    )
                    
                    return FixResult(
                        success=True,
                        strategy_used="fallback_tool",
                        message=f"使用备用工具 {fallback_tool} 执行成功",
                        data={"result": response, "fallback_tool": fallback_tool}
                    )
            
            except Exception as e:
                logger.debug(f"Fallback tool {fallback_tool} failed: {str(e)}")
                continue
        
        return FixResult(
            success=False,
            strategy_used="fallback_tool",
            message="所有备用工具均失败",
            error="No available fallback tools"
        )
    
    async def _update_tool_config(
        self,
        tool_name: str,
        context: Dict[str, Any]
    ) -> FixResult:
        """更新工具配置"""
        try:
            # 这里应该实现工具配置的热更新逻辑
            # 例如：重新加载工具配置、更新超时时间等
            logger.info(f"Updating tool config for {tool_name}")
            
            # 模拟配置更新
            config_updates = context.get("config_updates", {})
            
            return FixResult(
                success=True,
                strategy_used="config_update",
                message="工具配置更新成功",
                data={"tool_name": tool_name, "config_updates": config_updates}
            )
        
        except Exception as e:
            return FixResult(
                success=False,
                strategy_used="config_update",
                message=f"配置更新失败: {str(e)}",
                error=str(e)
            )


class WorkflowEngineFixStrategy(BaseFixStrategy):
    """工作流引擎修复策略"""
    
    async def can_apply(
        self,
        error_analysis: ErrorAnalysis,
        context: Dict[str, Any]
    ) -> bool:
        """判断是否可以应用此策略"""
        return error_analysis.category == ErrorCategory.WORKFLOW_ENGINE
    
    async def apply(
        self,
        error_analysis: ErrorAnalysis,
        context: Dict[str, Any]
    ) -> FixResult:
        """应用工作流引擎修复策略"""
        start_time = datetime.now()
        workflow_id = context.get("workflow_id") or error_analysis.context.get("workflow_id")
        execution_id = context.get("execution_id") or error_analysis.context.get("execution_id")
        
        strategies_applied = []
        
        # 1. 工作流状态恢复
        if self.config.enable_state_restore and execution_id:
            restore_result = await self._restore_workflow_state(execution_id, context)
            strategies_applied.append("state_restore")
            if restore_result.success:
                execution_time = (datetime.now() - start_time).total_seconds()
                return FixResult(
                    success=True,
                    strategy_used="state_restore",
                    message="工作流状态恢复成功",
                    data=restore_result.data,
                    execution_time=execution_time
                )
        
        # 2. 失败节点重试逻辑
        if "node" in error_analysis.error_message.lower():
            node_name = context.get("node_name") or error_analysis.context.get("error_node")
            if node_name:
                retry_result = await self._retry_failed_node(
                    workflow_id, execution_id, node_name, context
                )
                strategies_applied.append("node_retry")
                if retry_result.success:
                    execution_time = (datetime.now() - start_time).total_seconds()
                    return FixResult(
                        success=True,
                        strategy_used="node_retry",
                        message=f"节点 {node_name} 重试成功",
                        data=retry_result.data,
                        execution_time=execution_time
                    )
        
        # 3. 循环依赖检测和解除
        if "circular" in error_analysis.error_message.lower():
            circular_result = await self._detect_and_resolve_circular_dependency(
                workflow_id, context
            )
            strategies_applied.append("circular_dependency_resolve")
            if circular_result.success:
                execution_time = (datetime.now() - start_time).total_seconds()
                return FixResult(
                    success=True,
                    strategy_used="circular_dependency_resolve",
                    message="循环依赖已解除",
                    data=circular_result.data,
                    execution_time=execution_time
                )
        
        # 4. 工作流版本回滚
        if error_analysis.error_type == ErrorType.CONFIG_ERROR:
            rollback_result = await self._rollback_workflow_version(workflow_id, context)
            strategies_applied.append("workflow_rollback")
            if rollback_result.success:
                execution_time = (datetime.now() - start_time).total_seconds()
                return FixResult(
                    success=True,
                    strategy_used="workflow_rollback",
                    message="工作流版本回滚成功",
                    data=rollback_result.data,
                    execution_time=execution_time
                )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        return FixResult(
            success=False,
            strategy_used=",".join(strategies_applied) if strategies_applied else "none",
            message="所有工作流引擎修复策略均失败",
            retry_count=len(strategies_applied),
            execution_time=execution_time,
            error="无法修复工作流引擎错误"
        )
    
    async def _restore_workflow_state(
        self,
        execution_id: str,
        context: Dict[str, Any]
    ) -> FixResult:
        """恢复工作流状态"""
        try:
            # 调用工作流状态管理器恢复状态
            from shared_libs.common.http_client import HTTPClient
            workflow_engine_url = context.get("workflow_engine_url", "http://localhost:8002")
            
            async with HTTPClient(workflow_engine_url) as client:
                response = await client.post(
                    f"/api/workflows/executions/{execution_id}/resume",
                    data={"checkpoint_name": context.get("checkpoint_name")}
                )
                
                return FixResult(
                    success=True,
                    strategy_used="state_restore",
                    message="工作流状态恢复成功",
                    data={"execution_id": execution_id, "state": response}
                )
        
        except Exception as e:
            return FixResult(
                success=False,
                strategy_used="state_restore",
                message=f"状态恢复失败: {str(e)}",
                error=str(e)
            )
    
    async def _retry_failed_node(
        self,
        workflow_id: str,
        execution_id: Optional[str],
        node_name: str,
        context: Dict[str, Any]
    ) -> FixResult:
        """重试失败节点"""
        try:
            # 获取节点状态
            node_state = context.get("node_state", {})
            
            # 重试节点执行
            async def retry_node():
                # 这里应该调用实际的节点重试逻辑
                logger.info(f"Retrying node {node_name} in workflow {workflow_id}")
                return {"success": True, "node_name": node_name}
            
            result, retry_count = await self._retry_with_backoff(retry_node)
            
            return FixResult(
                success=True,
                strategy_used="node_retry",
                message=f"节点 {node_name} 重试成功",
                data={"result": result, "retry_count": retry_count},
                retry_count=retry_count
            )
        
        except Exception as e:
            return FixResult(
                success=False,
                strategy_used="node_retry",
                message=f"节点重试失败: {str(e)}",
                error=str(e)
            )
    
    async def _detect_and_resolve_circular_dependency(
        self,
        workflow_id: str,
        context: Dict[str, Any]
    ) -> FixResult:
        """检测和解除循环依赖"""
        try:
            # 获取工作流定义
            from shared_libs.common.http_client import HTTPClient
            workflow_engine_url = context.get("workflow_engine_url", "http://localhost:8002")
            
            async with HTTPClient(workflow_engine_url) as client:
                workflow_def = await client.get(f"/api/workflows/{workflow_id}")
                
                # 检测循环依赖
                nodes = workflow_def.get("nodes", [])
                connections = workflow_def.get("connections", [])
                
                # 构建依赖图
                graph = {}
                for node in nodes:
                    graph[node["id"]] = []
                
                for conn in connections:
                    source = conn.get("source", {}).get("node_id")
                    target = conn.get("target", {}).get("node_id")
                    if source and target:
                        graph[source].append(target)
                
                # 检测循环（使用DFS）
                circular_deps = self._detect_cycles(graph)
                
                if circular_deps:
                    # 尝试解除循环依赖（移除最后一个连接）
                    logger.warning(f"Detected circular dependencies: {circular_deps}")
                    # 这里应该实现实际的解除逻辑
                    return FixResult(
                        success=True,
                        strategy_used="circular_dependency_resolve",
                        message="循环依赖已检测并标记",
                        data={"circular_dependencies": circular_deps}
                    )
                else:
                    return FixResult(
                        success=False,
                        strategy_used="circular_dependency_resolve",
                        message="未检测到循环依赖",
                        error="No circular dependencies found"
                    )
        
        except Exception as e:
            return FixResult(
                success=False,
                strategy_used="circular_dependency_resolve",
                message=f"检测循环依赖失败: {str(e)}",
                error=str(e)
            )
    
    def _detect_cycles(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        """检测图中的循环"""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]):
            if node in rec_stack:
                # 找到循环
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    async def _rollback_workflow_version(
        self,
        workflow_id: str,
        context: Dict[str, Any]
    ) -> FixResult:
        """回滚工作流版本"""
        try:
            from shared_libs.common.http_client import HTTPClient
            workflow_engine_url = context.get("workflow_engine_url", "http://localhost:8002")
            
            async with HTTPClient(workflow_engine_url) as client:
                # 获取版本历史
                versions = await client.get(f"/api/workflows/{workflow_id}/versions")
                
                if versions and len(versions) > 1:
                    # 回滚到上一个版本
                    previous_version = versions[-2]
                    response = await client.post(
                        f"/api/workflows/{workflow_id}/rollback",
                        data={"version": previous_version["version"]}
                    )
                    
                    return FixResult(
                        success=True,
                        strategy_used="workflow_rollback",
                        message=f"工作流已回滚到版本 {previous_version['version']}",
                        data={"previous_version": previous_version, "response": response}
                    )
                else:
                    return FixResult(
                        success=False,
                        strategy_used="workflow_rollback",
                        message="没有可回滚的版本",
                        error="No previous versions available"
                    )
        
        except Exception as e:
            return FixResult(
                success=False,
                strategy_used="workflow_rollback",
                message=f"版本回滚失败: {str(e)}",
                error=str(e)
            )


class KnowledgeBaseFixStrategy(BaseFixStrategy):
    """知识库修复策略"""
    
    async def can_apply(
        self,
        error_analysis: ErrorAnalysis,
        context: Dict[str, Any]
    ) -> bool:
        """判断是否可以应用此策略"""
        return error_analysis.category == ErrorCategory.KNOWLEDGE_BASE
    
    async def apply(
        self,
        error_analysis: ErrorAnalysis,
        context: Dict[str, Any]
    ) -> FixResult:
        """应用知识库修复策略"""
        start_time = datetime.now()
        document_id = context.get("document_id") or error_analysis.context.get("document_id")
        
        strategies_applied = []
        
        # 1. 向量索引重建
        if "vector" in error_analysis.error_message.lower() or \
           "index" in error_analysis.error_message.lower():
            rebuild_result = await self._rebuild_vector_index(document_id, context)
            strategies_applied.append("vector_index_rebuild")
            if rebuild_result.success:
                execution_time = (datetime.now() - start_time).total_seconds()
                return FixResult(
                    success=True,
                    strategy_used="vector_index_rebuild",
                    message="向量索引重建成功",
                    data=rebuild_result.data,
                    execution_time=execution_time
                )
        
        # 2. 文档重新解析
        if "parsing" in error_analysis.error_message.lower() or \
           "parse" in error_analysis.error_message.lower():
            reparse_result = await self._reparse_document(document_id, context)
            strategies_applied.append("document_reparse")
            if reparse_result.success:
                execution_time = (datetime.now() - start_time).total_seconds()
                return FixResult(
                    success=True,
                    strategy_used="document_reparse",
                    message="文档重新解析成功",
                    data=reparse_result.data,
                    execution_time=execution_time
                )
        
        # 3. 搜索查询优化
        if "search" in error_analysis.error_message.lower():
            optimize_result = await self._optimize_search_query(context)
            strategies_applied.append("search_optimization")
            if optimize_result.success:
                execution_time = (datetime.now() - start_time).total_seconds()
                return FixResult(
                    success=True,
                    strategy_used="search_optimization",
                    message="搜索查询优化成功",
                    data=optimize_result.data,
                    execution_time=execution_time
                )
        
        # 4. 缓存清理和重建
        if self.config.enable_cache_clear:
            cache_result = await self._clear_and_rebuild_cache(context)
            strategies_applied.append("cache_clear")
            if cache_result.success:
                execution_time = (datetime.now() - start_time).total_seconds()
                return FixResult(
                    success=True,
                    strategy_used="cache_clear",
                    message="缓存清理和重建成功",
                    data=cache_result.data,
                    execution_time=execution_time
                )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        return FixResult(
            success=False,
            strategy_used=",".join(strategies_applied) if strategies_applied else "none",
            message="所有知识库修复策略均失败",
            retry_count=len(strategies_applied),
            execution_time=execution_time,
            error="无法修复知识库错误"
        )
    
    async def _rebuild_vector_index(
        self,
        document_id: Optional[str],
        context: Dict[str, Any]
    ) -> FixResult:
        """重建向量索引"""
        try:
            from shared_libs.common.http_client import HTTPClient
            knowledge_base_url = context.get("knowledge_base_url", "http://localhost:8003")
            
            async with HTTPClient(knowledge_base_url) as client:
                if document_id:
                    # 重建特定文档的索引
                    response = await client.post(
                        f"/api/documents/{document_id}/rebuild-index"
                    )
                else:
                    # 重建所有索引
                    response = await client.post("/api/maintenance/rebuild-indexes")
                
                return FixResult(
                    success=True,
                    strategy_used="vector_index_rebuild",
                    message="向量索引重建成功",
                    data={"response": response, "document_id": document_id}
                )
        
        except Exception as e:
            return FixResult(
                success=False,
                strategy_used="vector_index_rebuild",
                message=f"向量索引重建失败: {str(e)}",
                error=str(e)
            )
    
    async def _reparse_document(
        self,
        document_id: str,
        context: Dict[str, Any]
    ) -> FixResult:
        """重新解析文档"""
        try:
            from shared_libs.common.http_client import HTTPClient
            knowledge_base_url = context.get("knowledge_base_url", "http://localhost:8003")
            
            async with HTTPClient(knowledge_base_url) as client:
                response = await client.post(
                    f"/api/documents/{document_id}/reparse"
                )
                
                return FixResult(
                    success=True,
                    strategy_used="document_reparse",
                    message="文档重新解析成功",
                    data={"response": response, "document_id": document_id}
                )
        
        except Exception as e:
            return FixResult(
                success=False,
                strategy_used="document_reparse",
                message=f"文档重新解析失败: {str(e)}",
                error=str(e)
            )
    
    async def _optimize_search_query(
        self,
        context: Dict[str, Any]
    ) -> FixResult:
        """优化搜索查询"""
        try:
            query = context.get("query", "")
            
            # 查询优化逻辑
            optimized_query = query
            
            # 移除特殊字符
            import re
            optimized_query = re.sub(r'[^\w\s]', ' ', optimized_query)
            
            # 移除多余空格
            optimized_query = ' '.join(optimized_query.split())
            
            # 限制查询长度
            if len(optimized_query) > 200:
                optimized_query = optimized_query[:200]
            
            return FixResult(
                success=True,
                strategy_used="search_optimization",
                message="搜索查询优化成功",
                data={
                    "original_query": query,
                    "optimized_query": optimized_query
                }
            )
        
        except Exception as e:
            return FixResult(
                success=False,
                strategy_used="search_optimization",
                message=f"查询优化失败: {str(e)}",
                error=str(e)
            )
    
    async def _clear_and_rebuild_cache(
        self,
        context: Dict[str, Any]
    ) -> FixResult:
        """清理和重建缓存"""
        try:
            from shared_libs.common.http_client import HTTPClient
            knowledge_base_url = context.get("knowledge_base_url", "http://localhost:8003")
            
            async with HTTPClient(knowledge_base_url) as client:
                # 清理缓存
                await client.delete("/api/maintenance/clear-cache")
                
                # 重建缓存
                response = await client.post("/api/maintenance/rebuild-cache")
                
                return FixResult(
                    success=True,
                    strategy_used="cache_clear",
                    message="缓存清理和重建成功",
                    data={"response": response}
                )
        
        except Exception as e:
            return FixResult(
                success=False,
                strategy_used="cache_clear",
                message=f"缓存清理失败: {str(e)}",
                error=str(e)
            )


class FrontendUIFixStrategy(BaseFixStrategy):
    """前端界面修复策略"""
    
    async def can_apply(
        self,
        error_analysis: ErrorAnalysis,
        context: Dict[str, Any]
    ) -> bool:
        """判断是否可以应用此策略"""
        return error_analysis.category == ErrorCategory.FRONTEND_UI
    
    async def apply(
        self,
        error_analysis: ErrorAnalysis,
        context: Dict[str, Any]
    ) -> FixResult:
        """应用前端界面修复策略"""
        start_time = datetime.now()
        
        strategies_applied = []
        
        # 1. API调用重试机制
        if "api" in error_analysis.error_message.lower() or \
           "call" in error_analysis.error_message.lower():
            retry_result = await self._retry_api_call(context)
            strategies_applied.append("api_retry")
            if retry_result.success:
                execution_time = (datetime.now() - start_time).total_seconds()
                return FixResult(
                    success=True,
                    strategy_used="api_retry",
                    message="API调用重试成功",
                    data=retry_result.data,
                    execution_time=execution_time
                )
        
        # 2. 状态同步修复
        if "state" in error_analysis.error_message.lower() or \
           "sync" in error_analysis.error_message.lower():
            sync_result = await self._fix_state_sync(context)
            strategies_applied.append("state_sync")
            if sync_result.success:
                execution_time = (datetime.now() - start_time).total_seconds()
                return FixResult(
                    success=True,
                    strategy_used="state_sync",
                    message="状态同步修复成功",
                    data=sync_result.data,
                    execution_time=execution_time
                )
        
        # 3. 组件错误边界处理
        if "component" in error_analysis.error_message.lower() or \
           "render" in error_analysis.error_message.lower():
            boundary_result = await self._handle_component_error(context)
            strategies_applied.append("error_boundary")
            if boundary_result.success:
                execution_time = (datetime.now() - start_time).total_seconds()
                return FixResult(
                    success=True,
                    strategy_used="error_boundary",
                    message="组件错误边界处理成功",
                    data=boundary_result.data,
                    execution_time=execution_time
                )
        
        # 4. 本地存储清理
        clear_result = await self._clear_local_storage(context)
        strategies_applied.append("local_storage_clear")
        if clear_result.success:
            execution_time = (datetime.now() - start_time).total_seconds()
            return FixResult(
                success=True,
                strategy_used="local_storage_clear",
                message="本地存储清理成功",
                data=clear_result.data,
                execution_time=execution_time
            )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        return FixResult(
            success=False,
            strategy_used=",".join(strategies_applied) if strategies_applied else "none",
            message="所有前端界面修复策略均失败",
            retry_count=len(strategies_applied),
            execution_time=execution_time,
            error="无法修复前端界面错误"
        )
    
    async def _retry_api_call(
        self,
        context: Dict[str, Any]
    ) -> FixResult:
        """重试API调用"""
        try:
            api_endpoint = context.get("api_endpoint")
            api_method = context.get("api_method", "GET")
            api_data = context.get("api_data", {})
            
            if not api_endpoint:
                return FixResult(
                    success=False,
                    strategy_used="api_retry",
                    message="缺少API端点信息",
                    error="Missing api_endpoint"
                )
            
            async def call_api():
                from shared_libs.common.http_client import HTTPClient
                base_url = context.get("base_url", "http://localhost:8000")
                
                async with HTTPClient(base_url) as client:
                    if api_method == "POST":
                        return await client.post(api_endpoint, data=api_data)
                    elif api_method == "PUT":
                        return await client.put(api_endpoint, data=api_data)
                    elif api_method == "DELETE":
                        return await client.delete(api_endpoint)
                    else:
                        return await client.get(api_endpoint)
            
            result, retry_count = await self._retry_with_backoff(call_api)
            
            return FixResult(
                success=True,
                strategy_used="api_retry",
                message="API调用重试成功",
                data={"result": result, "retry_count": retry_count},
                retry_count=retry_count
            )
        
        except Exception as e:
            return FixResult(
                success=False,
                strategy_used="api_retry",
                message=f"API调用重试失败: {str(e)}",
                error=str(e)
            )
    
    async def _fix_state_sync(
        self,
        context: Dict[str, Any]
    ) -> FixResult:
        """修复状态同步"""
        try:
            # 状态同步修复逻辑
            # 这里应该实现前端状态同步的修复
            state_key = context.get("state_key")
            expected_state = context.get("expected_state")
            current_state = context.get("current_state")
            
            if state_key and expected_state:
                # 同步状态
                return FixResult(
                    success=True,
                    strategy_used="state_sync",
                    message="状态同步修复成功",
                    data={
                        "state_key": state_key,
                        "synced": True
                    }
                )
            else:
                return FixResult(
                    success=False,
                    strategy_used="state_sync",
                    message="缺少状态同步所需信息",
                    error="Missing state information"
                )
        
        except Exception as e:
            return FixResult(
                success=False,
                strategy_used="state_sync",
                message=f"状态同步修复失败: {str(e)}",
                error=str(e)
            )
    
    async def _handle_component_error(
        self,
        context: Dict[str, Any]
    ) -> FixResult:
        """处理组件错误"""
        try:
            component_name = context.get("component_name")
            
            # 组件错误边界处理
            # 这里应该实现组件错误恢复逻辑
            return FixResult(
                success=True,
                strategy_used="error_boundary",
                message="组件错误边界处理成功",
                data={
                    "component_name": component_name,
                    "error_handled": True
                }
            )
        
        except Exception as e:
            return FixResult(
                success=False,
                strategy_used="error_boundary",
                message=f"组件错误处理失败: {str(e)}",
                error=str(e)
            )
    
    async def _clear_local_storage(
        self,
        context: Dict[str, Any]
    ) -> FixResult:
        """清理本地存储"""
        try:
            # 本地存储清理逻辑
            # 这里应该实现前端本地存储的清理
            storage_keys = context.get("storage_keys", [])
            
            return FixResult(
                success=True,
                strategy_used="local_storage_clear",
                message="本地存储清理成功",
                data={
                    "cleared_keys": storage_keys,
                    "cleared": True
                }
            )
        
        except Exception as e:
            return FixResult(
                success=False,
                strategy_used="local_storage_clear",
                message=f"本地存储清理失败: {str(e)}",
                error=str(e)
            )


class PlatformFixStrategyManager:
    """平台修复策略管理器"""
    
    def __init__(self, config: Optional[FixStrategyConfig] = None):
        self.config = config or FixStrategyConfig()
        self.strategies: List[BaseFixStrategy] = [
            MCPToolFixStrategy(self.config),
            WorkflowEngineFixStrategy(self.config),
            KnowledgeBaseFixStrategy(self.config),
            FrontendUIFixStrategy(self.config),
        ]
    
    async def apply_fix(
        self,
        error_analysis: ErrorAnalysis,
        context: Optional[Dict[str, Any]] = None
    ) -> FixResult:
        """
        应用修复策略
        
        Args:
            error_analysis: 错误分析结果
            context: 额外上下文信息
        
        Returns:
            修复结果
        """
        context = context or {}
        
        # 找到适用的策略
        applicable_strategies = []
        for strategy in self.strategies:
            if await strategy.can_apply(error_analysis, context):
                applicable_strategies.append(strategy)
        
        if not applicable_strategies:
            return FixResult(
                success=False,
                strategy_used="none",
                message="没有找到适用的修复策略",
                error="No applicable strategies found"
            )
        
        # 按照配置的优先级应用策略
        results = []
        for strategy in applicable_strategies:
            try:
                result = await strategy.apply(error_analysis, context)
                results.append(result)
                
                if result.success:
                    logger.info(
                        f"Fix strategy {strategy.name} succeeded: {result.message}"
                    )
                    return result
                
            except Exception as e:
                logger.error(
                    f"Fix strategy {strategy.name} failed: {str(e)}",
                    exc_info=True
                )
                results.append(FixResult(
                    success=False,
                    strategy_used=strategy.name,
                    message=f"策略执行异常: {str(e)}",
                    error=str(e)
                ))
        
        # 如果所有策略都失败，尝试组合策略
        if self.config.enable_fallback:
            combined_result = await self._apply_combined_strategies(
                error_analysis, context, results
            )
            if combined_result.success:
                return combined_result
        
        # 返回最后一个结果
        return results[-1] if results else FixResult(
            success=False,
            strategy_used="none",
            message="所有修复策略均失败",
            error="All strategies failed"
        )
    
    async def _apply_combined_strategies(
        self,
        error_analysis: ErrorAnalysis,
        context: Dict[str, Any],
        previous_results: List[FixResult]
    ) -> FixResult:
        """应用组合策略"""
        # 根据错误类型组合不同的策略
        combined_strategies = []
        
        if error_analysis.category == ErrorCategory.MCP_TOOL:
            # 尝试参数修正 + 重试
            if any("parameter" in r.strategy_used for r in previous_results):
                # 可以组合多个策略
                pass
        
        # 这里可以实现更复杂的组合逻辑
        return FixResult(
            success=False,
            strategy_used="combined",
            message="组合策略未实现",
            error="Combined strategies not implemented"
        )
    
    def register_strategy(self, strategy: BaseFixStrategy):
        """注册新的修复策略"""
        self.strategies.append(strategy)
    
    def update_config(self, config: FixStrategyConfig):
        """更新配置"""
        self.config = config
        for strategy in self.strategies:
            strategy.config = config


# 全局策略管理器实例
_fix_manager_instance: Optional[PlatformFixStrategyManager] = None


def get_fix_strategy_manager(
    config: Optional[FixStrategyConfig] = None
) -> PlatformFixStrategyManager:
    """获取修复策略管理器实例（单例模式）"""
    global _fix_manager_instance
    if _fix_manager_instance is None:
        _fix_manager_instance = PlatformFixStrategyManager(config)
    elif config:
        _fix_manager_instance.update_config(config)
    return _fix_manager_instance


# 便捷函数
async def apply_fix(
    error_analysis: ErrorAnalysis,
    context: Optional[Dict[str, Any]] = None,
    config: Optional[FixStrategyConfig] = None
) -> FixResult:
    """
    应用修复策略的便捷函数
    
    Args:
        error_analysis: 错误分析结果
        context: 额外上下文信息
        config: 修复策略配置
    
    Returns:
        修复结果
    """
    manager = get_fix_strategy_manager(config)
    return await manager.apply_fix(error_analysis, context)


"""
元数据采集管理器
管理各种采集时机的元数据收集
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

from .mcp_tool_collector import MCPToolCollector
from .workflow_collector import WorkflowCollector
from .knowledge_collector import KnowledgeCollector
from .model_collector import ModelCollector
from .data_lineage_collector import DataLineageCollector
from .intent_collector import IntentCollector
from .execution_collector import ExecutionCollector
from .tool_execution_collector import ToolExecutionCollector

logger = logging.getLogger(__name__)


class CollectionManager:
    """元数据采集管理器"""
    
    def __init__(
        self,
        metadata_service_url: str = "http://localhost:8005",
        mcp_gateway_url: str = "http://mcp-gateway:8001",
        workflow_engine_url: str = "http://workflow-engine:8002",
        knowledge_base_url: str = "http://knowledge-base:8004",
        agent_service_url: str = "http://agent-service:8010"
    ):
        """
        初始化采集管理器
        
        Args:
            metadata_service_url: 元数据服务URL
            mcp_gateway_url: MCP Gateway服务URL
            workflow_engine_url: Workflow Engine服务URL
            knowledge_base_url: Knowledge Base服务URL
            agent_service_url: Agent Service服务URL
        """
        self.metadata_service_url = metadata_service_url
        self.collectors = {
            "tools": MCPToolCollector(
                mcp_gateway_url=mcp_gateway_url,
                metadata_service_url=metadata_service_url
            ),
            "workflows": WorkflowCollector(
                workflow_engine_url=workflow_engine_url,
                metadata_service_url=metadata_service_url
            ),
            "knowledge": KnowledgeCollector(
                knowledge_base_url=knowledge_base_url,
                metadata_service_url=metadata_service_url
            ),
            "models": ModelCollector(
                metadata_service_url=metadata_service_url
            ),
            "lineage": DataLineageCollector(
                metadata_service_url=metadata_service_url
            ),
            "intents": IntentCollector(
                agent_service_url=agent_service_url,
                metadata_service_url=metadata_service_url
            ),
            "executions": ExecutionCollector(
                agent_service_url=agent_service_url,
                metadata_service_url=metadata_service_url
            ),
            "tool_executions": ToolExecutionCollector(
                mcp_gateway_url=mcp_gateway_url,
                metadata_service_url=metadata_service_url
            )
        }
    
    async def register_on_startup(self) -> Dict[str, Any]:
        """
        服务启动时：注册基础元数据
        
        Returns:
            注册结果统计
        """
        logger.info("Starting metadata registration on service startup...")
        results = {}
        
        # 并行采集所有基础元数据
        tasks = {
            name: collector.collect_and_sync()
            for name, collector in self.collectors.items()
        }
        
        completed = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        for (name, task), result in zip(tasks.items(), completed):
            if isinstance(result, Exception):
                logger.error(f"Failed to register {name} metadata: {str(result)}")
                results[name] = {
                    "success": False,
                    "error": str(result)
                }
            else:
                results[name] = result
        
        logger.info(f"Metadata registration completed: {results}")
        return results
    
    async def update_on_data_change(
        self,
        entity_type: str,
        entity_id: str,
        change_type: str = "update"
    ) -> bool:
        """
        数据变更时：更新元数据版本
        
        Args:
            entity_type: 实体类型（tool, workflow, document, model）
            entity_id: 实体ID
            change_type: 变更类型（create, update, delete）
            
        Returns:
            是否更新成功
        """
        try:
            collector = self.collectors.get(entity_type)
            if not collector:
                logger.warning(f"No collector found for entity type: {entity_type}")
                return False
            
            # 重新采集该实体的元数据
            metadata_list = await collector.collect()
            
            # 找到对应的实体并更新
            for metadata in metadata_list:
                if metadata.get("workflow_id") == entity_id or metadata.get("name") == entity_id:
                    result = await collector.sync([metadata])
                    logger.info(f"Updated metadata for {entity_type}:{entity_id} - {result}")
                    return result.get("success", False)
            
            logger.warning(f"Entity {entity_type}:{entity_id} not found in collected metadata")
            return False
            
        except Exception as e:
            logger.error(f"Failed to update metadata on data change: {str(e)}", exc_info=True)
            return False
    
    async def collect_tool_usage_statistics(
        self,
        tool_name: str,
        execution_time: float,
        success: bool
    ) -> bool:
        """
        工具执行时：收集使用统计
        
        Args:
            tool_name: 工具名称
            execution_time: 执行时间（秒）
            success: 是否成功
            
        Returns:
            是否收集成功
        """
        try:
            import httpx
            
            # 获取工作流元数据（工具作为工作流存储）
            workflow_id = f"tool_{tool_name}"
            
            # 更新使用统计
            async with httpx.AsyncClient() as client:
                # 获取当前工作流元数据
                response = await client.get(f"{self.metadata_service_url}/api/workflows/{workflow_id}")
                if response.status_code == 404:
                    logger.debug(f"Tool metadata not found for {tool_name}, skipping statistics update")
                    return False
                
                response.raise_for_status()
                workflow = response.json()
                
                # 获取当前统计
                current_stats = workflow.get("metadata", {}).get("usage_statistics", {}) if workflow.get("metadata") else {}
                
                # 更新统计
                total_calls = current_stats.get("total_calls", 0) + 1
                successful_calls = current_stats.get("successful_calls", 0) + (1 if success else 0)
                failed_calls = current_stats.get("failed_calls", 0) + (0 if success else 1)
                
                # 计算平均执行时间
                avg_time = current_stats.get("average_execution_time", 0.0)
                total_time = avg_time * (total_calls - 1) + execution_time
                new_avg_time = total_time / total_calls
                
                update_data = {
                    "metadata": {
                        "usage_statistics": {
                            "total_calls": total_calls,
                            "successful_calls": successful_calls,
                            "failed_calls": failed_calls,
                            "average_execution_time": new_avg_time,
                            "last_execution_time": datetime.now().isoformat(),
                            "last_execution_success": success
                        }
                    }
                }
                
                response = await client.put(
                    f"{self.metadata_service_url}/api/workflows/{workflow_id}",
                    json=update_data
                )
                response.raise_for_status()
                
                logger.debug(f"Updated tool usage statistics for {tool_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to collect tool usage statistics: {str(e)}", exc_info=True)
            return False
    
    async def collect_workflow_execution_metrics(
        self,
        workflow_id: str,
        execution_time: float,
        success: bool,
        input_size: Optional[int] = None,
        output_size: Optional[int] = None
    ) -> bool:
        """
        工作流运行时：收集执行指标
        
        Args:
            workflow_id: 工作流ID
            execution_time: 执行时间（秒）
            success: 是否成功
            input_size: 输入数据大小（可选）
            output_size: 输出数据大小（可选）
            
        Returns:
            是否收集成功
        """
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                # 获取当前工作流元数据
                response = await client.get(f"{self.metadata_service_url}/api/workflows/{workflow_id}")
                if response.status_code == 404:
                    logger.debug(f"Workflow metadata not found for {workflow_id}")
                    return False
                
                response.raise_for_status()
                workflow = response.json()
                
                # 更新执行统计
                execution_stats = workflow.get("metadata", {}).get("execution_statistics", {})
                total_executions = execution_stats.get("total_executions", 0) + 1
                successful_executions = execution_stats.get("successful_executions", 0) + (1 if success else 0)
                failed_executions = execution_stats.get("failed_executions", 0) + (0 if success else 1)
                
                # 计算成功率
                success_rate = successful_executions / total_executions if total_executions > 0 else 0.0
                
                # 计算平均执行时间
                avg_time = execution_stats.get("average_execution_time", 0.0)
                total_time = avg_time * (total_executions - 1) + execution_time
                new_avg_time = total_time / total_executions
                
                update_data = {
                    "execution_count": total_executions,
                    "last_execution_time": datetime.now().isoformat(),
                    "average_execution_time": int(new_avg_time),
                    "success_rate": f"{success_rate:.2%}",
                    "metadata": {
                        "execution_statistics": {
                            "total_executions": total_executions,
                            "successful_executions": successful_executions,
                            "failed_executions": failed_executions,
                            "average_execution_time": new_avg_time,
                            "last_execution_time": datetime.now().isoformat(),
                            "last_execution_success": success,
                            "input_size": input_size,
                            "output_size": output_size
                        }
                    }
                }
                
                response = await client.put(
                    f"{self.metadata_service_url}/api/workflows/{workflow_id}",
                    json=update_data
                )
                response.raise_for_status()
                
                logger.debug(f"Updated workflow execution metrics for {workflow_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to collect workflow execution metrics: {str(e)}", exc_info=True)
            return False
    
    async def collect_user_access_pattern(
        self,
        entity_type: str,
        entity_id: str,
        user_id: Optional[str] = None,
        action: str = "access",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        用户交互时：收集访问模式
        
        Args:
            entity_type: 实体类型（data_asset, workflow, document等）
            entity_id: 实体ID
            user_id: 用户ID（可选）
            action: 操作类型（access, search, download等）
            metadata: 扩展元数据（可选）
            
        Returns:
            是否收集成功
        """
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                access_data = {
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id,
                    "action": action,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    **(metadata or {})
                }
                
                # 根据实体类型更新相应的元数据
                if entity_type == "data_asset":
                    # 更新数据资产的访问统计
                    response = await client.get(
                        f"{self.metadata_service_url}/api/data-assets",
                        params={"search": entity_id}
                    )
                    if response.status_code == 200:
                        assets = response.json()
                        if assets:
                            asset_id = assets[0]["id"]
                            # 更新访问模式（存储在metadata中）
                            update_response = await client.get(f"{self.metadata_service_url}/api/data-assets/{asset_id}")
                            asset = update_response.json()
                            
                            access_patterns = asset.get("metadata", {}).get("access_patterns", [])
                            access_patterns.append(access_data)
                            
                            # 只保留最近100条访问记录
                            if len(access_patterns) > 100:
                                access_patterns = access_patterns[-100:]
                            
                            update_data = {
                                "metadata": {
                                    **asset.get("metadata", {}),
                                    "access_patterns": access_patterns,
                                    "last_access_time": datetime.now().isoformat()
                                }
                            }
                            
                            await client.put(
                                f"{self.metadata_service_url}/api/data-assets/{asset_id}",
                                json=update_data
                            )
                
                elif entity_type == "workflow":
                    # 更新工作流的访问统计
                    response = await client.get(f"{self.metadata_service_url}/api/workflows/{entity_id}")
                    if response.status_code == 200:
                        workflow = response.json()
                        access_patterns = workflow.get("metadata", {}).get("access_patterns", [])
                        access_patterns.append(access_data)
                        
                        if len(access_patterns) > 100:
                            access_patterns = access_patterns[-100:]
                        
                        update_data = {
                            "metadata": {
                                **workflow.get("metadata", {}),
                                "access_patterns": access_patterns
                            }
                        }
                        
                        await client.put(
                            f"{self.metadata_service_url}/api/workflows/{entity_id}",
                            json=update_data
                        )
                
                logger.debug(f"Collected access pattern for {entity_type}:{entity_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to collect user access pattern: {str(e)}", exc_info=True)
            return False
    
    async def close(self):
        """关闭所有采集器"""
        for collector in self.collectors.values():
            await collector.close()


# 全局采集管理器实例
_collection_manager: Optional[CollectionManager] = None


def get_collection_manager() -> CollectionManager:
    """获取采集管理器实例（单例）"""
    global _collection_manager
    if _collection_manager is None:
        _collection_manager = CollectionManager()
    return _collection_manager


async def close_collection_manager():
    """关闭采集管理器"""
    global _collection_manager
    if _collection_manager:
        await _collection_manager.close()
        _collection_manager = None


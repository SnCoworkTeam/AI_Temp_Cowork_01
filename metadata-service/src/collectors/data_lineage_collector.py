"""
数据血缘采集器
从各个服务采集数据血缘关系
"""
import logging
from typing import Dict, Any, List
from datetime import datetime
import httpx

from .base_collector import BaseCollector
from .workflow_collector import WorkflowCollector
from .mcp_tool_collector import MCPToolCollector

logger = logging.getLogger(__name__)


class DataLineageCollector(BaseCollector):
    """数据血缘采集器"""
    
    def __init__(self, **kwargs):
        """
        初始化数据血缘采集器
        
        Args:
            **kwargs: 参数传递给BaseCollector
        """
        # 数据血缘采集器需要访问多个服务
        super().__init__(
            source_service_url="http://localhost:8000",  # 占位符
            **kwargs
        )
    
    async def collect(self) -> List[Dict[str, Any]]:
        """
        采集数据血缘关系
        
        从多个来源采集：
        1. 工作流中的数据流
        2. 工具的数据输入输出
        3. 文档的依赖关系
        
        Returns:
            血缘关系列表
        """
        lineage_list = []
        
        # 方法1: 从工作流中提取数据流
        try:
            workflow_collector = WorkflowCollector(
                workflow_engine_url="http://workflow-engine:8002",
                metadata_service_url=self.metadata_service_url
            )
            workflows = await workflow_collector.collect()
            
            for workflow in workflows:
                workflow_id = workflow.get("workflow_id")
                data_sources = workflow.get("data_sources", [])
                data_sinks = workflow.get("data_sinks", [])
                dependencies = workflow.get("dependencies", {})
                
                # 工作流读取数据源
                for source in data_sources:
                    lineage = {
                        "source_asset": f"data_asset:{source}",
                        "target_asset": f"workflow:{workflow_id}",
                        "source_type": "data_asset",
                        "source_id": source,
                        "target_type": "workflow",
                        "target_id": workflow_id,
                        "relation_type": "reads",
                        "lineage_type": "data_flow",
                        "transformation": f"Workflow {workflow.get('name', '')} Data Input",
                        "transformation_logic": f"Workflow {workflow.get('name', '')} reads from {source}",
                        "business_rules": [],
                        "data_quality_impact": {},
                        "metadata": {
                            "workflow_name": workflow.get("name"),
                            "collected_at": datetime.now().isoformat()
                        }
                    }
                    lineage_list.append(lineage)
                
                # 工作流写入数据输出
                for sink in data_sinks:
                    lineage = {
                        "source_asset": f"workflow:{workflow_id}",
                        "target_asset": f"data_asset:{sink}",
                        "source_type": "workflow",
                        "source_id": workflow_id,
                        "target_type": "data_asset",
                        "target_id": sink,
                        "relation_type": "writes",
                        "lineage_type": "data_flow",
                        "transformation": f"Workflow {workflow.get('name', '')} Data Output",
                        "transformation_logic": f"Workflow {workflow.get('name', '')} writes to {sink}",
                        "business_rules": [],
                        "data_quality_impact": {},
                        "metadata": {
                            "workflow_name": workflow.get("name"),
                            "collected_at": datetime.now().isoformat()
                        }
                    }
                    lineage_list.append(lineage)
                
                # 工作流使用的AI模型
                ai_models = dependencies.get("ai_models", [])
                for model in ai_models:
                    lineage = {
                        "source_asset": f"ai_model:{model}",
                        "target_asset": f"workflow:{workflow_id}",
                        "source_type": "ai_model",
                        "source_id": model,
                        "target_type": "workflow",
                        "target_id": workflow_id,
                        "relation_type": "depends_on",
                        "lineage_type": "dependency",
                        "transformation": f"Model Dependency",
                        "transformation_logic": f"Workflow {workflow.get('name', '')} depends on model {model}",
                        "business_rules": [],
                        "data_quality_impact": {},
                        "metadata": {
                            "workflow_name": workflow.get("name"),
                            "collected_at": datetime.now().isoformat()
                        }
                    }
                    lineage_list.append(lineage)
        except Exception as e:
            logger.warning(f"Failed to collect lineage from workflows: {str(e)}")
        
        # 方法2: 从工具中提取数据依赖
        try:
            tool_collector = MCPToolCollector(
                mcp_gateway_url="http://mcp-gateway:8001",
                metadata_service_url=self.metadata_service_url
            )
            tools = await tool_collector.collect()
            
            for tool in tools:
                tool_name = tool.get("name", "")
                workflow_id = tool.get("workflow_id", f"tool_{tool_name}")
                dependencies = tool.get("dependencies", {})
                dependent_tools = dependencies.get("tools", [])
                
                # 工具依赖其他工具
                for dep_tool in dependent_tools:
                    lineage = {
                        "source_asset": f"workflow:tool_{dep_tool}",
                        "target_asset": f"workflow:{workflow_id}",
                        "source_type": "workflow",
                        "source_id": f"tool_{dep_tool}",
                        "target_type": "workflow",
                        "target_id": workflow_id,
                        "relation_type": "depends_on",
                        "lineage_type": "dependency",
                        "transformation": f"Tool Dependency",
                        "transformation_logic": f"Tool {tool_name} depends on tool {dep_tool}",
                        "business_rules": [],
                        "data_quality_impact": {},
                        "metadata": {
                            "tool_name": tool_name,
                            "collected_at": datetime.now().isoformat()
                        }
                    }
                    lineage_list.append(lineage)
        except Exception as e:
            logger.warning(f"Failed to collect lineage from tools: {str(e)}")
        
        return lineage_list
    
    async def sync(self, metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        同步血缘关系到元数据服务
        
        Args:
            metadata_list: 血缘关系列表
            
        Returns:
            同步结果统计
        """
        client = await self._get_metadata_client()
        synced = 0
        errors = 0
        skipped = 0
        
        for lineage in metadata_list:
            try:
                # 检查是否已存在相同的血缘关系
                check_response = await client.get(
                    "/api/lineage",
                    params={
                        "source_type": lineage.get("source_type"),
                        "source_id": lineage.get("source_id"),
                        "target_type": lineage.get("target_type"),
                        "target_id": lineage.get("target_id"),
                        "relation_type": lineage.get("relation_type")
                    }
                )
                check_response.raise_for_status()
                existing = check_response.json()
                
                if existing and len(existing) > 0:
                    # 已存在，更新最后发现时间
                    lineage_id = existing[0]["id"]
                    update_response = await client.put(
                        f"/api/lineage/{lineage_id}",
                        json={"last_seen": datetime.now().isoformat()}
                    )
                    update_response.raise_for_status()
                    skipped += 1
                else:
                    # 创建新血缘关系
                    response = await client.post("/api/lineage", json=lineage)
                    response.raise_for_status()
                    synced += 1
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to sync lineage: {e.response.status_code} - {e.response.text}")
                errors += 1
            except Exception as e:
                logger.error(f"Error syncing lineage: {str(e)}")
                errors += 1
        
        return {
            "success": errors == 0,
            "collected": len(metadata_list),
            "synced": synced,
            "skipped": skipped,
            "errors": errors,
            "message": f"Synced {synced} new, updated {skipped} existing lineage relationships"
        }


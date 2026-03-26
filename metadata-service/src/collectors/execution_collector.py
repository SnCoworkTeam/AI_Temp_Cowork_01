"""
任务执行元数据采集器
从agent-service采集任务执行、路由决策和执行路径元数据
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class ExecutionCollector(BaseCollector):
    """任务执行元数据采集器"""
    
    def __init__(self, agent_service_url: str = "http://agent-service:8010", **kwargs):
        """
        初始化执行采集器
        
        Args:
            agent_service_url: Agent Service服务URL
            **kwargs: 其他参数传递给BaseCollector
        """
        super().__init__(
            source_service_url=agent_service_url,
            **kwargs
        )
    
    async def collect(self) -> List[Dict[str, Any]]:
        """
        从Agent Service采集执行元数据
        
        Returns:
            执行元数据列表
        """
        try:
            client = await self._get_source_client()
            
            # 获取执行模式
            response = await client.get("/api/v1/executions/patterns")
            if response.status_code == 200:
                patterns = response.json()
                
                metadata_list = []
                for pattern in patterns:
                    metadata_list.append({
                        "execution_pattern_id": pattern.get("pattern_id", ""),
                        "pattern_name": pattern.get("pattern_name", ""),
                        "task_type": pattern.get("task_type", ""),
                        "execution_strategy": pattern.get("execution_strategy", ""),
                        "execution_path": pattern.get("execution_path", []),
                        "used_services": pattern.get("used_services", []),
                        "usage_count": pattern.get("usage_count", 0),
                        "average_execution_time": pattern.get("average_execution_time", 0.0),
                        "success_rate": pattern.get("success_rate", 0.0),
                        "metadata": {
                            "task_type": pattern.get("task_type"),
                            "execution_strategy": pattern.get("execution_strategy"),
                            "execution_path": pattern.get("execution_path", []),
                            "used_services": pattern.get("used_services", [])
                        }
                    })
                
                logger.info(f"Collected {len(metadata_list)} execution pattern metadata records")
                return metadata_list
            else:
                logger.warning(f"Failed to get execution patterns from agent-service: {response.status_code}")
                return []
            
        except Exception as e:
            logger.error(f"Error collecting execution metadata: {str(e)}", exc_info=True)
            return []
    
    async def sync(self, metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        同步执行元数据到元数据服务
        
        Args:
            metadata_list: 执行元数据列表
            
        Returns:
            同步结果统计
        """
        # 执行元数据可以作为工作流元数据存储（执行模式）
        client = await self._get_metadata_client()
        synced = 0
        errors = 0
        
        for metadata in metadata_list:
            try:
                # 创建或更新工作流元数据（执行模式）
                workflow_data = {
                    "workflow_id": metadata.get("execution_pattern_id", f"pattern_{metadata.get('task_type', 'unknown')}"),
                    "name": metadata.get("pattern_name", f"执行模式: {metadata.get('task_type', 'unknown')}"),
                    "display_name": metadata.get("pattern_name", ""),
                    "description": f"任务类型 {metadata.get('task_type')} 的执行模式",
                    "version": "1.0.0",
                    "category": "execution_pattern",
                    "workflow_type": "execution_pattern",
                    "execution_count": metadata.get("usage_count", 0),
                    "tags": ["execution_pattern", metadata.get("task_type", "")],
                    "metadata": {
                        "task_type": metadata.get("task_type"),
                        "execution_strategy": metadata.get("execution_strategy"),
                        "execution_path": metadata.get("execution_path", []),
                        "used_services": metadata.get("used_services", []),
                        "average_execution_time": metadata.get("average_execution_time", 0.0),
                        "success_rate": metadata.get("success_rate", 0.0),
                        **metadata.get("metadata", {})
                    }
                }
                
                # 检查是否已存在
                workflow_id = workflow_data["workflow_id"]
                check_response = await client.get(f"/api/workflows/{workflow_id}")
                
                if check_response.status_code == 200:
                    # 更新
                    response = await client.put(
                        f"/api/workflows/{workflow_id}",
                        json=workflow_data
                    )
                else:
                    # 创建
                    response = await client.post(
                        "/api/workflows",
                        json=workflow_data
                    )
                
                if response.status_code in [200, 201]:
                    synced += 1
                else:
                    errors += 1
                    logger.warning(f"Failed to sync execution metadata: {response.status_code}")
                    
            except Exception as e:
                errors += 1
                logger.error(f"Error syncing execution metadata: {str(e)}")
        
        return {
            "success": errors == 0,
            "synced": synced,
            "errors": errors,
            "total": len(metadata_list)
        }


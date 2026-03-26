"""
血缘采集器
在各个服务中追踪数据血缘关系
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx
from httpx import AsyncClient, Timeout

from ..core.config import settings

logger = logging.getLogger(__name__)


class NodeExecution:
    """节点执行信息"""
    def __init__(
        self,
        node_id: str,
        node_type: str,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        execution_time: Optional[float] = None,
        success: bool = True
    ):
        self.node_id = node_id
        self.node_type = node_type
        self.input_data = input_data or {}
        self.output_data = output_data or {}
        self.execution_time = execution_time
        self.success = success


class ProcessingStep:
    """处理步骤信息"""
    def __init__(
        self,
        step_name: str,
        step_type: str,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        processing_time: Optional[float] = None
    ):
        self.step_name = step_name
        self.step_type = step_type
        self.input_data = input_data or {}
        self.output_data = output_data or {}
        self.processing_time = processing_time


class LineageCollector:
    """血缘采集器"""
    
    def __init__(
        self,
        metadata_service_url: Optional[str] = None,
        timeout: float = 10.0
    ):
        """
        初始化血缘采集器
        
        Args:
            metadata_service_url: 元数据服务URL
            timeout: 请求超时时间（秒）
        """
        self.metadata_service_url = metadata_service_url or getattr(
            settings, 'METADATA_SERVICE_URL', 'http://metadata-service:8005'
        )
        self.timeout = Timeout(timeout)
        self._client: Optional[AsyncClient] = None
    
    async def _get_client(self) -> AsyncClient:
        """获取HTTP客户端（懒加载）"""
        if self._client is None:
            self._client = AsyncClient(
                base_url=self.metadata_service_url,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
        return self._client
    
    async def close(self):
        """关闭HTTP客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def _create_lineage(
        self,
        source_asset: str,
        target_asset: str,
        source_type: str,
        source_id: str,
        target_type: str,
        target_id: str,
        relation_type: str,
        lineage_type: str,
        transformation: Optional[str] = None,
        transformation_logic: Optional[str] = None,
        business_rules: Optional[List[str]] = None,
        data_quality_impact: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        创建血缘关系
        
        Args:
            source_asset: 源资产（格式：type:id）
            target_asset: 目标资产（格式：type:id）
            source_type: 源类型
            source_id: 源ID
            target_type: 目标类型
            target_id: 目标ID
            relation_type: 关系类型
            lineage_type: 血缘类型
            transformation: 转换过程名称
            transformation_logic: 转换逻辑
            business_rules: 业务规则
            data_quality_impact: 数据质量影响
            metadata: 扩展元数据
            
        Returns:
            是否创建成功
        """
        try:
            client = await self._get_client()
            
            lineage_data = {
                "source_asset": source_asset,
                "target_asset": target_asset,
                "source_type": source_type,
                "source_id": source_id,
                "target_type": target_type,
                "target_id": target_id,
                "relation_type": relation_type,
                "lineage_type": lineage_type,
                "transformation": transformation,
                "transformation_logic": transformation_logic,
                "business_rules": business_rules or [],
                "data_quality_impact": data_quality_impact or {},
                "metadata": metadata or {},
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat()
            }
            
            # 检查是否已存在
            check_response = await client.get(
                "/api/lineage",
                params={
                    "source_type": source_type,
                    "source_id": source_id,
                    "target_type": target_type,
                    "target_id": target_id,
                    "relation_type": relation_type
                }
            )
            
            if check_response.status_code == 200:
                existing = check_response.json()
                if existing and len(existing) > 0:
                    # 更新最后发现时间
                    lineage_id = existing[0]["id"]
                    await client.put(
                        f"/api/lineage/{lineage_id}",
                        json={"last_seen": datetime.now().isoformat()}
                    )
                    return True
            
            # 创建新血缘关系
            response = await client.post("/api/lineage", json=lineage_data)
            response.raise_for_status()
            
            logger.debug(f"Created lineage: {source_asset} -> {target_asset}")
            return True
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to create lineage: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Error creating lineage: {str(e)}", exc_info=True)
            return False
    
    async def track_mcp_tool_execution(
        self,
        tool_name: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        execution_id: Optional[str] = None,
        execution_time: Optional[float] = None
    ) -> bool:
        """
        追踪MCP工具执行血缘
        
        Args:
            tool_name: 工具名称
            input_data: 输入数据
            output_data: 输出数据
            execution_id: 执行ID（可选）
            execution_time: 执行时间（秒，可选）
            
        Returns:
            是否追踪成功
        """
        try:
            # 提取输入数据源
            input_sources = self._extract_data_sources(input_data)
            # 提取输出数据目标
            output_targets = self._extract_data_targets(output_data)
            
            tool_asset = f"workflow:tool_{tool_name}"
            
            # 创建输入血缘：数据源 -> 工具
            for source in input_sources:
                await self._create_lineage(
                    source_asset=source["asset"],
                    target_asset=tool_asset,
                    source_type=source["type"],
                    source_id=source["id"],
                    target_type="workflow",
                    target_id=f"tool_{tool_name}",
                    relation_type="reads",
                    lineage_type="data_flow",
                    transformation=f"Tool {tool_name} Input",
                    transformation_logic=f"Tool {tool_name} reads from {source['id']}",
                    metadata={
                        "execution_id": execution_id,
                        "execution_time": execution_time,
                        "input_keys": list(input_data.keys()) if input_data else []
                    }
                )
            
            # 创建输出血缘：工具 -> 数据目标
            for target in output_targets:
                await self._create_lineage(
                    source_asset=tool_asset,
                    target_asset=target["asset"],
                    source_type="workflow",
                    source_id=f"tool_{tool_name}",
                    target_type=target["type"],
                    target_id=target["id"],
                    relation_type="writes",
                    lineage_type="data_flow",
                    transformation=f"Tool {tool_name} Output",
                    transformation_logic=f"Tool {tool_name} writes to {target['id']}",
                    metadata={
                        "execution_id": execution_id,
                        "execution_time": execution_time,
                        "output_keys": list(output_data.keys()) if output_data else []
                    }
                )
            
            logger.info(f"Tracked MCP tool execution lineage for {tool_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track MCP tool execution lineage: {str(e)}", exc_info=True)
            return False
    
    async def track_workflow_execution(
        self,
        workflow_id: str,
        node_executions: List[NodeExecution],
        execution_id: Optional[str] = None
    ) -> bool:
        """
        追踪工作流执行血缘
        
        Args:
            workflow_id: 工作流ID
            node_executions: 节点执行列表
            execution_id: 执行ID（可选）
            
        Returns:
            是否追踪成功
        """
        try:
            workflow_asset = f"workflow:{workflow_id}"
            
            # 追踪节点之间的数据流
            for i, node_exec in enumerate(node_executions):
                node_asset = f"workflow_node:{workflow_id}:{node_exec.node_id}"
                
                # 节点从工作流读取
                await self._create_lineage(
                    source_asset=workflow_asset,
                    target_asset=node_asset,
                    source_type="workflow",
                    source_id=workflow_id,
                    target_type="workflow_node",
                    target_id=f"{workflow_id}:{node_exec.node_id}",
                    relation_type="contains",
                    lineage_type="dependency",
                    transformation=f"Workflow Node {node_exec.node_id}",
                    transformation_logic=f"Workflow {workflow_id} contains node {node_exec.node_id}",
                    metadata={
                        "execution_id": execution_id,
                        "node_type": node_exec.node_type,
                        "execution_time": node_exec.execution_time,
                        "success": node_exec.success
                    }
                )
                
                # 节点输入数据源
                input_sources = self._extract_data_sources(node_exec.input_data)
                for source in input_sources:
                    await self._create_lineage(
                        source_asset=source["asset"],
                        target_asset=node_asset,
                        source_type=source["type"],
                        source_id=source["id"],
                        target_type="workflow_node",
                        target_id=f"{workflow_id}:{node_exec.node_id}",
                        relation_type="reads",
                        lineage_type="data_flow",
                        transformation=f"Node {node_exec.node_id} Input",
                        transformation_logic=f"Node {node_exec.node_id} reads from {source['id']}",
                        metadata={
                            "execution_id": execution_id,
                            "node_type": node_exec.node_type
                        }
                    )
                
                # 节点输出数据目标
                output_targets = self._extract_data_targets(node_exec.output_data)
                for target in output_targets:
                    await self._create_lineage(
                        source_asset=node_asset,
                        target_asset=target["asset"],
                        source_type="workflow_node",
                        source_id=f"{workflow_id}:{node_exec.node_id}",
                        target_type=target["type"],
                        target_id=target["id"],
                        relation_type="writes",
                        lineage_type="data_flow",
                        transformation=f"Node {node_exec.node_id} Output",
                        transformation_logic=f"Node {node_exec.node_id} writes to {target['id']}",
                        metadata={
                            "execution_id": execution_id,
                            "node_type": node_exec.node_type
                        }
                    )
                
                # 节点之间的依赖关系（如果存在）
                if i > 0:
                    prev_node = node_executions[i - 1]
                    prev_node_asset = f"workflow_node:{workflow_id}:{prev_node.node_id}"
                    await self._create_lineage(
                        source_asset=prev_node_asset,
                        target_asset=node_asset,
                        source_type="workflow_node",
                        source_id=f"{workflow_id}:{prev_node.node_id}",
                        target_type="workflow_node",
                        target_id=f"{workflow_id}:{node_exec.node_id}",
                        relation_type="depends_on",
                        lineage_type="dependency",
                        transformation=f"Node Dependency",
                        transformation_logic=f"Node {node_exec.node_id} depends on {prev_node.node_id}",
                        metadata={
                            "execution_id": execution_id
                        }
                    )
            
            logger.info(f"Tracked workflow execution lineage for {workflow_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track workflow execution lineage: {str(e)}", exc_info=True)
            return False
    
    async def track_knowledge_processing(
        self,
        document_id: str,
        processing_steps: List[ProcessingStep],
        processing_id: Optional[str] = None
    ) -> bool:
        """
        追踪知识处理血缘
        
        Args:
            document_id: 文档ID
            processing_steps: 处理步骤列表
            processing_id: 处理ID（可选）
            
        Returns:
            是否追踪成功
        """
        try:
            document_asset = f"data_asset:{document_id}"
            
            # 追踪处理步骤之间的数据流
            for i, step in enumerate(processing_steps):
                step_asset = f"processing_step:{document_id}:{step.step_name}"
                
                # 处理步骤从文档读取
                await self._create_lineage(
                    source_asset=document_asset,
                    target_asset=step_asset,
                    source_type="data_asset",
                    source_id=document_id,
                    target_type="processing_step",
                    target_id=f"{document_id}:{step.step_name}",
                    relation_type="reads",
                    lineage_type="data_flow",
                    transformation=f"Processing Step {step.step_name}",
                    transformation_logic=f"Step {step.step_name} processes document {document_id}",
                    metadata={
                        "processing_id": processing_id,
                        "step_type": step.step_type,
                        "processing_time": step.processing_time
                    }
                )
                
                # 处理步骤之间的依赖关系
                if i > 0:
                    prev_step = processing_steps[i - 1]
                    prev_step_asset = f"processing_step:{document_id}:{prev_step.step_name}"
                    await self._create_lineage(
                        source_asset=prev_step_asset,
                        target_asset=step_asset,
                        source_type="processing_step",
                        source_id=f"{document_id}:{prev_step.step_name}",
                        target_type="processing_step",
                        target_id=f"{document_id}:{step.step_name}",
                        relation_type="depends_on",
                        lineage_type="dependency",
                        transformation=f"Processing Pipeline",
                        transformation_logic=f"Step {step.step_name} depends on {prev_step.step_name}",
                        metadata={
                            "processing_id": processing_id
                        }
                    )
                
                # 处理步骤的输出（如向量嵌入、摘要等）
                output_targets = self._extract_data_targets(step.output_data)
                for target in output_targets:
                    await self._create_lineage(
                        source_asset=step_asset,
                        target_asset=target["asset"],
                        source_type="processing_step",
                        source_id=f"{document_id}:{step.step_name}",
                        target_type=target["type"],
                        target_id=target["id"],
                        relation_type="writes",
                        lineage_type="data_flow",
                        transformation=f"Step {step.step_name} Output",
                        transformation_logic=f"Step {step.step_name} produces {target['id']}",
                        metadata={
                            "processing_id": processing_id,
                            "step_type": step.step_type
                        }
                    )
            
            logger.info(f"Tracked knowledge processing lineage for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track knowledge processing lineage: {str(e)}", exc_info=True)
            return False
    
    async def track_model_inference(
        self,
        model_id: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        inference_id: Optional[str] = None,
        inference_time: Optional[float] = None
    ) -> bool:
        """
        追踪模型推理血缘
        
        Args:
            model_id: 模型ID
            input_data: 输入数据
            output_data: 输出数据
            inference_id: 推理ID（可选）
            inference_time: 推理时间（秒，可选）
            
        Returns:
            是否追踪成功
        """
        try:
            model_asset = f"ai_model:{model_id}"
            
            # 提取输入数据源
            input_sources = self._extract_data_sources(input_data)
            # 提取输出数据目标
            output_targets = self._extract_data_targets(output_data)
            
            # 创建输入血缘：数据源 -> 模型
            for source in input_sources:
                await self._create_lineage(
                    source_asset=source["asset"],
                    target_asset=model_asset,
                    source_type=source["type"],
                    source_id=source["id"],
                    target_type="ai_model",
                    target_id=model_id,
                    relation_type="reads",
                    lineage_type="data_flow",
                    transformation=f"Model {model_id} Inference Input",
                    transformation_logic=f"Model {model_id} processes {source['id']}",
                    metadata={
                        "inference_id": inference_id,
                        "inference_time": inference_time,
                        "input_keys": list(input_data.keys()) if input_data else []
                    }
                )
            
            # 创建输出血缘：模型 -> 数据目标
            for target in output_targets:
                await self._create_lineage(
                    source_asset=model_asset,
                    target_asset=target["asset"],
                    source_type="ai_model",
                    source_id=model_id,
                    target_type=target["type"],
                    target_id=target["id"],
                    relation_type="writes",
                    lineage_type="data_flow",
                    transformation=f"Model {model_id} Inference Output",
                    transformation_logic=f"Model {model_id} produces {target['id']}",
                    metadata={
                        "inference_id": inference_id,
                        "inference_time": inference_time,
                        "output_keys": list(output_data.keys()) if output_data else []
                    }
                )
            
            logger.info(f"Tracked model inference lineage for {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track model inference lineage: {str(e)}", exc_info=True)
            return False
    
    def _extract_data_sources(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        从数据中提取数据源
        
        Args:
            data: 数据字典
            
        Returns:
            数据源列表，每个元素包含 type, id, asset
        """
        sources = []
        
        # 检查常见的数据源标识
        if isinstance(data, dict):
            # 检查是否有明确的 source_id 或 data_source
            if "source_id" in data:
                source_type = data.get("source_type", "data_asset")
                source_id = data["source_id"]
                sources.append({
                    "type": source_type,
                    "id": source_id,
                    "asset": f"{source_type}:{source_id}"
                })
            
            if "data_source" in data:
                source = data["data_source"]
                if isinstance(source, str):
                    # 格式：type:id
                    parts = source.split(":", 1)
                    if len(parts) == 2:
                        sources.append({
                            "type": parts[0],
                            "id": parts[1],
                            "asset": source
                        })
            
            # 检查是否有引用其他实体的字段
            for key, value in data.items():
                if key.endswith("_id") and isinstance(value, str):
                    # 尝试推断类型
                    entity_type = key.replace("_id", "")
                    sources.append({
                        "type": entity_type,
                        "id": value,
                        "asset": f"{entity_type}:{value}"
                    })
        
        return sources
    
    def _extract_data_targets(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        从数据中提取数据目标
        
        Args:
            data: 数据字典
            
        Returns:
            数据目标列表，每个元素包含 type, id, asset
        """
        targets = []
        
        # 检查常见的数据目标标识
        if isinstance(data, dict):
            # 检查是否有明确的 target_id 或 data_target
            if "target_id" in data:
                target_type = data.get("target_type", "data_asset")
                target_id = data["target_id"]
                targets.append({
                    "type": target_type,
                    "id": target_id,
                    "asset": f"{target_type}:{target_id}"
                })
            
            if "data_target" in data:
                target = data["data_target"]
                if isinstance(target, str):
                    # 格式：type:id
                    parts = target.split(":", 1)
                    if len(parts) == 2:
                        targets.append({
                            "type": parts[0],
                            "id": parts[1],
                            "asset": target
                        })
            
            # 检查是否有输出ID字段
            if "output_id" in data:
                target_type = data.get("output_type", "data_asset")
                target_id = data["output_id"]
                targets.append({
                    "type": target_type,
                    "id": target_id,
                    "asset": f"{target_type}:{target_id}"
                })
        
        return targets


# 全局血缘采集器实例
_lineage_collector: Optional[LineageCollector] = None


def get_lineage_collector() -> LineageCollector:
    """获取血缘采集器实例（单例）"""
    global _lineage_collector
    if _lineage_collector is None:
        _lineage_collector = LineageCollector()
    return _lineage_collector


async def close_lineage_collector():
    """关闭血缘采集器"""
    global _lineage_collector
    if _lineage_collector:
        await _lineage_collector.close()
        _lineage_collector = None


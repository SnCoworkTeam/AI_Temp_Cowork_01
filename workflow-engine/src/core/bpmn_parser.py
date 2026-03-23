"""
BPMN 2.0解析器 - 支持AI节点扩展
解析BPMN XML文件，提取流程定义，支持LuminaOS AI扩展
"""
from typing import Dict, Any, List, Optional, Set
from xml.etree import ElementTree as ET
from dataclasses import dataclass
import logging
from enum import Enum

from ..models.workflow_models import WorkflowDefinition, WorkflowNode, WorkflowConnection, ConnectionPoint
from shared_libs.luminaos_common.schemas.workflow_schemas import NodeType
from ..config import settings

logger = logging.getLogger(__name__)

# BPMN命名空间
BPMN_NS = {
    'bpmn2': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
    'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
    'dc': 'http://www.omg.org/spec/DD/20100524/DC',
    'di': 'http://www.omg.org/spec/DD/20100524/DI',
    'lumina': 'http://luminaos.ai/schema/bpmn-extension'
}


class AINodeType(str, Enum):
    """AI节点类型"""
    LLM = "llm"  # 大语言模型节点
    AGENT = "agent"  # 智能体节点
    DECISION = "decision"  # 智能决策节点
    VALIDATION = "validation"  # 智能验证节点
    ANALYSIS = "analysis"  # 智能分析节点
    RECOMMENDATION = "recommendation"  # 智能推荐节点


@dataclass
class AIWorkflowConfig:
    """AI工作流配置"""
    workflow_id: str
    agents: List[Dict[str, Any]]
    fallback: Optional[str] = None
    threshold: Optional[float] = None


@dataclass
class AINodeConfig:
    """AI节点配置"""
    agent_id: str
    agent_type: str
    capabilities: Optional[List[str]] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    prompt_template: Optional[str] = None
    system_message: Optional[str] = None
    timeout: Optional[int] = None
    retry_count: Optional[int] = None


class BPMNParser:
    """BPMN 2.0解析器"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self._node_id_map: Dict[str, str] = {}  # BPMN ID -> WorkflowNode ID映射
    
    def parse(self, bpmn_xml: str) -> WorkflowDefinition:
        """
        解析BPMN XML文件
        
        Args:
            bpmn_xml: BPMN XML字符串
        
        Returns:
            WorkflowDefinition对象
        
        Raises:
            ValueError: 如果BPMN文件无效
        """
        self.errors.clear()
        self.warnings.clear()
        self._node_id_map.clear()
        
        try:
            root = ET.fromstring(bpmn_xml)
        except ET.ParseError as e:
            raise ValueError(f"Invalid BPMN XML: {str(e)}")
        
        # 查找流程定义
        process = root.find('.//bpmn2:process', BPMN_NS)
        if process is None:
            raise ValueError("No process definition found in BPMN file")
        
        # 解析流程基本信息
        process_id = process.get('id', '')
        process_name = process.get('name', process_id)
        is_executable = process.get('isExecutable', 'true').lower() == 'true'
        
        if not is_executable:
            self.warnings.append("Process is not marked as executable")
        
        # 解析所有节点
        nodes = []
        start_nodes = []
        end_nodes = []
        
        # 解析开始事件
        for start_event in process.findall('.//bpmn2:startEvent', BPMN_NS):
            node = self._parse_start_event(start_event)
            nodes.append(node)
            start_nodes.append(node.id)
        
        # 解析任务节点（包括AI任务）
        for task in process.findall('.//bpmn2:task', BPMN_NS):
            node = self._parse_task(task)
            nodes.append(node)
        
        # 解析服务任务（可能包含AI节点）
        for service_task in process.findall('.//bpmn2:serviceTask', BPMN_NS):
            node = self._parse_service_task(service_task)
            nodes.append(node)
        
        # 解析用户任务
        for user_task in process.findall('.//bpmn2:userTask', BPMN_NS):
            node = self._parse_user_task(user_task)
            nodes.append(node)
        
        # 解析网关
        for gateway in process.findall('.//bpmn2:exclusiveGateway', BPMN_NS):
            node = self._parse_gateway(gateway)
            nodes.append(node)
        
        for gateway in process.findall('.//bpmn2:parallelGateway', BPMN_NS):
            node = self._parse_parallel_gateway(gateway)
            nodes.append(node)
        
        # 解析结束事件
        for end_event in process.findall('.//bpmn2:endEvent', BPMN_NS):
            node = self._parse_end_event(end_event)
            nodes.append(node)
            end_nodes.append(node.id)
        
        # 解析连接线
        connections = []
        for sequence_flow in process.findall('.//bpmn2:sequenceFlow', BPMN_NS):
            connection = self._parse_sequence_flow(sequence_flow)
            if connection:
                connections.append(connection)
        
        # 验证流程结构
        self._validate_process_structure(nodes, connections, start_nodes, end_nodes)
        
        if self.errors:
            raise ValueError(f"BPMN validation failed: {', '.join(self.errors)}")
        
        # 构建WorkflowDefinition
        workflow_def = WorkflowDefinition(
            name=process_name,
            description=process.get('documentation', ''),
            version="1.0.0",
            status="active",
            nodes=nodes,
            connections=connections,
            start_node_id=start_nodes[0] if start_nodes else nodes[0].id,
            end_node_ids=end_nodes if end_nodes else self._find_end_nodes(nodes, connections),
            variables={},
            metadata={
                "bpmn_process_id": process_id,
                "source": "bpmn",
                "warnings": self.warnings
            }
        )
        
        logger.info(f"Parsed BPMN process: {process_name} ({len(nodes)} nodes, {len(connections)} connections)")
        
        return workflow_def
    
    def _parse_start_event(self, element: ET.Element) -> WorkflowNode:
        """解析开始事件"""
        node_id = element.get('id', '')
        name = element.get('name', 'Start')
        
        return WorkflowNode(
            id=node_id,
            name=name,
            node_type=NodeType.START,
            config={},
            inputs=[],
            outputs=[],
            next_nodes=[]
        )
    
    def _parse_task(self, element: ET.Element) -> WorkflowNode:
        """解析任务节点"""
        node_id = element.get('id', '')
        name = element.get('name', 'Task')
        
        # 检查是否是AI任务
        ai_config = self._extract_ai_config(element)
        if ai_config:
            node_type = NodeType.AGENT if ai_config.agent_type == "agent" else NodeType.LLM
            # 如果BPMN中没有指定模型，或者模型是占位符，使用配置中心的默认模型
            model = ai_config.model
            if not model or model in ['gpt-4', 'gpt-3.5-turbo', 'placeholder', 'default']:
                # 使用配置中心的默认模型
                model = settings.LLM_MODEL
                logger.info(f"Node {node_id}: Using default model from config: {model} (BPMN specified: {ai_config.model})")
            
            config = {
                "agent_id": ai_config.agent_id,
                "agent_type": ai_config.agent_type,
                "capabilities": ai_config.capabilities or [],
                "model": model,
                "temperature": ai_config.temperature,
                "max_tokens": ai_config.max_tokens,
                "prompt_template": ai_config.prompt_template,
                "system_message": ai_config.system_message,
                "timeout": ai_config.timeout,
                "retry_count": ai_config.retry_count
            }
        else:
            node_type = NodeType.TASK
            config = {}
        
        return WorkflowNode(
            id=node_id,
            name=name,
            node_type=node_type,
            config=config,
            inputs=[],
            outputs=[],
            next_nodes=[]
        )
    
    def _parse_service_task(self, element: ET.Element) -> WorkflowNode:
        """解析服务任务（可能包含AI节点）"""
        node_id = element.get('id', '')
        name = element.get('name', 'Service Task')
        
        # 检查是否是AI服务任务
        ai_config = self._extract_ai_config(element)
        if ai_config:
            node_type = NodeType.AGENT if ai_config.agent_type == "agent" else NodeType.LLM
            # 如果BPMN中没有指定模型，或者模型是占位符，使用配置中心的默认模型
            model = ai_config.model
            if not model or model in ['gpt-4', 'gpt-3.5-turbo', 'placeholder', 'default']:
                # 使用配置中心的默认模型
                model = settings.LLM_MODEL
                logger.info(f"Node {node_id}: Using default model from config: {model} (BPMN specified: {ai_config.model})")
            
            config = {
                "agent_id": ai_config.agent_id,
                "agent_type": ai_config.agent_type,
                "capabilities": ai_config.capabilities or [],
                "model": model,
                "temperature": ai_config.temperature,
                "max_tokens": ai_config.max_tokens,
                "prompt_template": ai_config.prompt_template,
                "system_message": ai_config.system_message,
                "timeout": ai_config.timeout,
                "retry_count": ai_config.retry_count
            }
        else:
            # 检查实现类型
            implementation = element.get('implementation', '')
            if implementation == '##WebService' or element.get('type') == 'http':
                node_type = NodeType.HTTP
                config = {
                    "url": element.get('url', ''),
                    "method": element.get('method', 'GET')
                }
            else:
                node_type = NodeType.TASK
                config = {}
        
        return WorkflowNode(
            id=node_id,
            name=name,
            node_type=node_type,
            config=config,
            inputs=[],
            outputs=[],
            next_nodes=[]
        )
    
    def _parse_user_task(self, element: ET.Element) -> WorkflowNode:
        """解析用户任务"""
        node_id = element.get('id', '')
        name = element.get('name', 'User Task')
        
        return WorkflowNode(
            id=node_id,
            name=name,
            node_type=NodeType.TASK,
            config={
                "assignee": element.get('assignee'),
                "candidate_users": element.get('candidateUsers', '').split(',') if element.get('candidateUsers') else [],
                "candidate_groups": element.get('candidateGroups', '').split(',') if element.get('candidateGroups') else []
            },
            inputs=[],
            outputs=[],
            next_nodes=[]
        )
    
    def _parse_gateway(self, element: ET.Element) -> WorkflowNode:
        """解析排他网关"""
        node_id = element.get('id', '')
        name = element.get('name', 'Gateway')
        gateway_direction = element.get('gatewayDirection', 'Diverging')
        
        return WorkflowNode(
            id=node_id,
            name=name,
            node_type=NodeType.CONDITION,
            config={
                "gateway_type": "exclusive",
                "direction": gateway_direction
            },
            inputs=[],
            outputs=[],
            next_nodes=[],
            condition=None
        )
    
    def _parse_parallel_gateway(self, element: ET.Element) -> WorkflowNode:
        """解析并行网关"""
        node_id = element.get('id', '')
        name = element.get('name', 'Parallel Gateway')
        gateway_direction = element.get('gatewayDirection', 'Diverging')
        
        return WorkflowNode(
            id=node_id,
            name=name,
            node_type=NodeType.PARALLEL if gateway_direction == 'Diverging' else NodeType.MERGE,
            config={
                "gateway_type": "parallel",
                "direction": gateway_direction
            },
            inputs=[],
            outputs=[],
            next_nodes=[]
        )
    
    def _parse_end_event(self, element: ET.Element) -> WorkflowNode:
        """解析结束事件"""
        node_id = element.get('id', '')
        name = element.get('name', 'End')
        
        return WorkflowNode(
            id=node_id,
            name=name,
            node_type=NodeType.END,
            config={},
            inputs=[],
            outputs=[],
            next_nodes=[]
        )
    
    def _parse_sequence_flow(self, element: ET.Element) -> Optional[WorkflowConnection]:
        """解析序列流（连接线）"""
        flow_id = element.get('id', '')
        source_ref = element.get('sourceRef', '')
        target_ref = element.get('targetRef', '')
        name = element.get('name', '')
        
        if not source_ref or not target_ref:
            self.warnings.append(f"Sequence flow {flow_id} missing source or target")
            return None
        
        # 查找条件表达式
        condition_expr = element.find('.//bpmn2:conditionExpression', BPMN_NS)
        condition = None
        if condition_expr is not None:
            condition = condition_expr.text
        
        return WorkflowConnection(
            id=flow_id,
            source=ConnectionPoint(node_id=source_ref, port="output"),
            target=ConnectionPoint(node_id=target_ref, port="input"),
            condition=condition,
            label=name
        )
    
    def _extract_ai_config(self, element: ET.Element) -> Optional[AINodeConfig]:
        """提取AI节点配置"""
        extension_elements = element.find('.//bpmn2:extensionElements', BPMN_NS)
        if extension_elements is None:
            return None
        
        # 查找LuminaOS AI配置
        ai_config_elem = extension_elements.find('.//lumina:aiWorkflowConfig', BPMN_NS)
        if ai_config_elem is None:
            return None
        
        # 查找agent配置
        agent_elem = ai_config_elem.find('.//lumina:agent', BPMN_NS)
        if agent_elem is None:
            return None
        
        agent_id = agent_elem.get('id', '')
        agent_type = agent_elem.get('type', 'agent')
        capabilities_str = agent_elem.get('capabilities', '')
        capabilities = capabilities_str.split(',') if capabilities_str else []
        
        # 提取其他配置属性
        model = agent_elem.get('model')
        temperature = agent_elem.get('temperature')
        max_tokens = agent_elem.get('max_tokens')
        prompt_template = agent_elem.get('prompt_template')
        system_message = agent_elem.get('system_message')
        timeout = agent_elem.get('timeout')
        retry_count = agent_elem.get('retry_count')
        
        return AINodeConfig(
            agent_id=agent_id,
            agent_type=agent_type,
            capabilities=capabilities,
            model=model,
            temperature=float(temperature) if temperature else None,
            max_tokens=int(max_tokens) if max_tokens else None,
            prompt_template=prompt_template,
            system_message=system_message,
            timeout=int(timeout) if timeout else None,
            retry_count=int(retry_count) if retry_count else None
        )
    
    def _validate_process_structure(
        self,
        nodes: List[WorkflowNode],
        connections: List[WorkflowConnection],
        start_nodes: List[str],
        end_nodes: List[str]
    ):
        """验证流程结构"""
        if not nodes:
            self.errors.append("Process must have at least one node")
            return
        
        if not start_nodes:
            self.errors.append("Process must have at least one start event")
        
        if not end_nodes:
            self.warnings.append("Process has no end events")
        
        # 检查节点ID唯一性
        node_ids = [node.id for node in nodes]
        if len(node_ids) != len(set(node_ids)):
            self.errors.append("Duplicate node IDs found")
        
        # 检查连接线的源和目标节点是否存在
        all_node_ids = set(node_ids)
        for conn in connections:
            if conn.source.node_id not in all_node_ids:
                self.errors.append(f"Connection {conn.id} references unknown source node: {conn.source.node_id}")
            if conn.target.node_id not in all_node_ids:
                self.errors.append(f"Connection {conn.id} references unknown target node: {conn.target.node_id}")
        
        # 检查孤立节点
        connected_nodes = set()
        for conn in connections:
            connected_nodes.add(conn.source.node_id)
            connected_nodes.add(conn.target.node_id)
        
        isolated_nodes = all_node_ids - connected_nodes
        if len(isolated_nodes) > 1:  # 允许一个孤立节点（可能是单个任务）
            self.warnings.append(f"Isolated nodes found: {isolated_nodes}")
    
    def _find_end_nodes(
        self,
        nodes: List[WorkflowNode],
        connections: List[WorkflowConnection]
    ) -> List[str]:
        """查找结束节点（没有出边的节点）"""
        nodes_with_outgoing = set()
        for conn in connections:
            nodes_with_outgoing.add(conn.source.node_id)
        
        end_nodes = [
            node.id for node in nodes
            if node.id not in nodes_with_outgoing and node.node_type != NodeType.START
        ]
        
        return end_nodes


class BPMNValidator:
    """BPMN流程验证器"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate(self, workflow_def: WorkflowDefinition) -> bool:
        """
        验证工作流定义
        
        Args:
            workflow_def: 工作流定义
        
        Returns:
            是否有效
        """
        self.errors.clear()
        self.warnings.clear()
        
        # 验证基本结构
        if not workflow_def.nodes:
            self.errors.append("Workflow must have at least one node")
        
        # 验证起始节点存在
        start_node = next((n for n in workflow_def.nodes if n.id == workflow_def.start_node_id), None)
        if not start_node:
            self.errors.append(f"Start node '{workflow_def.start_node_id}' not found")
        elif start_node.node_type != NodeType.START:
            self.errors.append(f"Start node '{workflow_def.start_node_id}' is not a start node type")
        
        # 验证结束节点
        for end_node_id in workflow_def.end_node_ids:
            end_node = next((n for n in workflow_def.nodes if n.id == end_node_id), None)
            if not end_node:
                self.errors.append(f"End node '{end_node_id}' not found")
            elif end_node.node_type != NodeType.END:
                self.warnings.append(f"End node '{end_node_id}' is not an end node type")
        
        # 验证AI节点配置
        for node in workflow_def.nodes:
            if node.node_type in [NodeType.AGENT, NodeType.LLM]:
                self._validate_ai_node(node)
        
        # 验证连接线
        all_node_ids = {node.id for node in workflow_def.nodes}
        for conn in workflow_def.connections:
            if conn.source.node_id not in all_node_ids:
                self.errors.append(f"Connection references unknown source node: {conn.source.node_id}")
            if conn.target.node_id not in all_node_ids:
                self.errors.append(f"Connection references unknown target node: {conn.target.node_id}")
        
        return len(self.errors) == 0
    
    def _validate_ai_node(self, node: WorkflowNode):
        """验证AI节点配置"""
        config = node.config
        
        # 检查必需的配置
        if node.node_type == NodeType.AGENT:
            if 'agent_id' not in config:
                self.errors.append(f"AI node '{node.id}' missing agent_id")
            if 'agent_type' not in config:
                self.warnings.append(f"AI node '{node.id}' missing agent_type")
        
        # 检查LLM配置
        if node.node_type == NodeType.LLM:
            if 'model' not in config and 'agent_id' not in config:
                self.warnings.append(f"LLM node '{node.id}' missing model or agent_id")
        
        # 检查超时配置
        if 'timeout' in config:
            timeout = config['timeout']
            if not isinstance(timeout, int) or timeout <= 0:
                self.errors.append(f"AI node '{node.id}' has invalid timeout: {timeout}")
        
        # 检查重试配置
        if 'retry_count' in config:
            retry_count = config['retry_count']
            if not isinstance(retry_count, int) or retry_count < 0:
                self.errors.append(f"AI node '{node.id}' has invalid retry_count: {retry_count}")
    
    def get_errors(self) -> List[str]:
        """获取验证错误"""
        return self.errors
    
    def get_warnings(self) -> List[str]:
        """获取验证警告"""
        return self.warnings


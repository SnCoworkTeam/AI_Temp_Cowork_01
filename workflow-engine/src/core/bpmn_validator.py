"""
BPMN流程验证器
提供详细的验证规则和错误报告
"""
from typing import List, Dict, Any, Set
from ..models.workflow_models import WorkflowDefinition, WorkflowNode, WorkflowConnection
from shared_libs.luminaos_common.schemas.workflow_schemas import NodeType
import logging

logger = logging.getLogger(__name__)


class ValidationRule:
    """验证规则"""
    
    def __init__(self, name: str, severity: str = "error"):
        self.name = name
        self.severity = severity  # "error" or "warning"
    
    def check(self, workflow_def: WorkflowDefinition) -> List[str]:
        """执行验证规则，返回错误/警告列表"""
        raise NotImplementedError


class StructureValidationRule(ValidationRule):
    """结构验证规则"""
    
    def __init__(self):
        super().__init__("structure_validation", "error")
    
    def check(self, workflow_def: WorkflowDefinition) -> List[str]:
        """验证流程结构"""
        errors = []
        
        if not workflow_def.nodes:
            errors.append("工作流必须至少包含一个节点")
            return errors
        
        # 检查节点ID唯一性
        node_ids = [node.id for node in workflow_def.nodes]
        if len(node_ids) != len(set(node_ids)):
            errors.append("存在重复的节点ID")
        
        # 检查起始节点
        start_node = next((n for n in workflow_def.nodes if n.id == workflow_def.start_node_id), None)
        if not start_node:
            errors.append(f"起始节点 '{workflow_def.start_node_id}' 不存在")
        elif start_node.node_type != NodeType.START:
            errors.append(f"起始节点 '{workflow_def.start_node_id}' 类型不正确")
        
        # 检查结束节点
        if not workflow_def.end_node_ids:
            errors.append("工作流必须至少包含一个结束节点")
        else:
            for end_node_id in workflow_def.end_node_ids:
                end_node = next((n for n in workflow_def.nodes if n.id == end_node_id), None)
                if not end_node:
                    errors.append(f"结束节点 '{end_node_id}' 不存在")
        
        return errors


class ConnectionValidationRule(ValidationRule):
    """连接验证规则"""
    
    def __init__(self):
        super().__init__("connection_validation", "error")
    
    def check(self, workflow_def: WorkflowDefinition) -> List[str]:
        """验证连接线"""
        errors = []
        warnings = []
        
        all_node_ids = {node.id for node in workflow_def.nodes}
        
        for conn in workflow_def.connections:
            # 检查源节点
            if conn.source.node_id not in all_node_ids:
                errors.append(f"连接线 '{conn.id}' 引用了不存在的源节点: {conn.source.node_id}")
            
            # 检查目标节点
            if conn.target.node_id not in all_node_ids:
                errors.append(f"连接线 '{conn.id}' 引用了不存在目标节点: {conn.target.node_id}")
            
            # 检查自循环
            if conn.source.node_id == conn.target.node_id:
                warnings.append(f"连接线 '{conn.id}' 存在自循环")
        
        # 检查孤立节点
        connected_nodes = set()
        for conn in workflow_def.connections:
            connected_nodes.add(conn.source.node_id)
            connected_nodes.add(conn.target.node_id)
        
        isolated_nodes = all_node_ids - connected_nodes
        if len(isolated_nodes) > 1:
            warnings.append(f"发现孤立节点: {isolated_nodes}")
        
        return errors + warnings


class AINodeValidationRule(ValidationRule):
    """AI节点验证规则"""
    
    def __init__(self):
        super().__init__("ai_node_validation", "error")
    
    def check(self, workflow_def: WorkflowDefinition) -> List[str]:
        """验证AI节点配置"""
        errors = []
        warnings = []
        
        ai_nodes = [node for node in workflow_def.nodes if node.node_type in [NodeType.AGENT, NodeType.LLM]]
        
        for node in ai_nodes:
            config = node.config
            
            # 验证Agent节点
            if node.node_type == NodeType.AGENT:
                if 'agent_id' not in config:
                    errors.append(f"AI节点 '{node.id}' 缺少必需的 agent_id 配置")
                if 'agent_type' not in config:
                    warnings.append(f"AI节点 '{node.id}' 缺少 agent_type 配置")
            
            # 验证LLM节点
            if node.node_type == NodeType.LLM:
                if 'model' not in config and 'agent_id' not in config:
                    warnings.append(f"LLM节点 '{node.id}' 缺少 model 或 agent_id 配置")
            
            # 验证超时配置
            if 'timeout' in config:
                timeout = config['timeout']
                if not isinstance(timeout, (int, float)) or timeout <= 0:
                    errors.append(f"AI节点 '{node.id}' 的 timeout 配置无效: {timeout}")
            
            # 验证重试配置
            if 'retry_count' in config:
                retry_count = config['retry_count']
                if not isinstance(retry_count, int) or retry_count < 0:
                    errors.append(f"AI节点 '{node.id}' 的 retry_count 配置无效: {retry_count}")
            
            # 验证温度配置
            if 'temperature' in config:
                temp = config['temperature']
                if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                    warnings.append(f"AI节点 '{node.id}' 的 temperature 配置超出合理范围: {temp}")
            
            # 验证最大token数
            if 'max_tokens' in config:
                max_tokens = config['max_tokens']
                if not isinstance(max_tokens, int) or max_tokens <= 0:
                    errors.append(f"AI节点 '{node.id}' 的 max_tokens 配置无效: {max_tokens}")
        
        return errors + warnings


class BPMNValidator:
    """BPMN流程验证器（完整版）"""
    
    def __init__(self):
        self.rules: List[ValidationRule] = [
            StructureValidationRule(),
            ConnectionValidationRule(),
            AINodeValidationRule()
        ]
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
        
        # 执行所有验证规则
        for rule in self.rules:
            issues = rule.check(workflow_def)
            for issue in issues:
                if rule.severity == "error":
                    self.errors.append(issue)
                else:
                    self.warnings.append(issue)
        
        # 记录验证结果
        if self.errors:
            logger.error(f"Workflow validation failed with {len(self.errors)} errors")
            for error in self.errors:
                logger.error(f"  - {error}")
        
        if self.warnings:
            logger.warning(f"Workflow validation has {len(self.warnings)} warnings")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")
        
        return len(self.errors) == 0
    
    def get_errors(self) -> List[str]:
        """获取验证错误"""
        return self.errors
    
    def get_warnings(self) -> List[str]:
        """获取验证警告"""
        return self.warnings
    
    def get_validation_report(self) -> Dict[str, Any]:
        """获取验证报告"""
        return {
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings)
        }





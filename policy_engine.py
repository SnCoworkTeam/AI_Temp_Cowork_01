"""
策略引擎
定义和执行企业策略（权限、合规、风险控制）
根据风险分析报告建议：增加策略语言层和可视化配置
"""
import logging
from typing import Dict, Any, List, Optional, Callable, Protocol
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, time
import json
import yaml

try:
    from .resource_operations import ResourceOperation, ResourceOperationType
    from .resource_model import ResourceType
except ImportError:
    from resource_operations import ResourceOperation, ResourceOperationType
    from resource_model import ResourceType

logger = logging.getLogger(__name__)


class PolicyAction(Enum):
    """策略动作"""
    ALLOW = "allow"  # 允许
    DENY = "deny"  # 拒绝
    REQUIRE_APPROVAL = "require_approval"  # 需要审批
    LOG_ONLY = "log_only"  # 仅记录日志
    RESTRICT = "restrict"  # 限制（部分允许）


@dataclass
class PolicyContext:
    """策略评估上下文"""
    user: str  # 用户ID
    role: str  # 用户角色
    resource_id: str  # 资源ID
    resource_type: str  # 资源类型
    operation: str  # 操作类型
    timestamp: datetime  # 时间戳
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据


@dataclass
class PolicyEvaluationResult:
    """策略评估结果"""
    allowed: bool  # 是否允许
    action: PolicyAction  # 策略动作
    reason: str  # 原因说明
    required_approvals: List[str] = field(default_factory=list)  # 需要的审批人
    restrictions: List[str] = field(default_factory=list)  # 限制条件
    policy_rule_name: Optional[str] = None  # 匹配的策略规则名称


@dataclass
class PolicyRule:
    """策略规则"""
    name: str  # 规则名称
    description: str  # 规则描述
    condition: Callable[[PolicyContext], bool]  # 条件函数
    action: PolicyAction  # 动作
    priority: int = 1  # 优先级（数字越大优先级越高）
    enabled: bool = True  # 是否启用
    
    def evaluate(self, context: PolicyContext) -> Optional[PolicyAction]:
        """
        评估规则是否匹配
        
        Returns:
            如果匹配返回动作，否则返回None
        """
        if not self.enabled:
            return None
        
        try:
            if self.condition(context):
                return self.action
        except Exception as e:
            logger.error(f"策略规则 {self.name} 评估失败: {e}")
        
        return None


class PolicyLanguage:
    """策略定义语言（根据风险分析报告建议）"""
    
    @staticmethod
    def create_rule(
        name: str,
        description: str,
        condition: Callable[[PolicyContext], bool],
        action: PolicyAction,
        priority: int = 1
    ) -> PolicyRule:
        """创建策略规则"""
        return PolicyRule(
            name=name,
            description=description,
            condition=condition,
            action=action,
            priority=priority
        )
    
    @staticmethod
    def composite_rule(
        name: str,
        description: str,
        rules: List[PolicyRule],
        operator: str = "AND"  # "AND" | "OR"
    ) -> PolicyRule:
        """组合多个规则"""
        def composite_condition(context: PolicyContext) -> bool:
            if operator == "AND":
                return all(rule.condition(context) for rule in rules if rule.enabled)
            else:  # OR
                return any(rule.condition(context) for rule in rules if rule.enabled)
        
        # 使用最高优先级
        max_priority = max(rule.priority for rule in rules) if rules else 1
        
        return PolicyRule(
            name=name,
            description=description,
            condition=composite_condition,
            action=rules[0].action if rules else PolicyAction.DENY,
            priority=max_priority
        )
    
    @staticmethod
    def time_based_rule(
        name: str,
        description: str,
        time_range: tuple,  # (start_hour, end_hour)
        action: PolicyAction,
        priority: int = 1
    ) -> PolicyRule:
        """基于时间的规则"""
        def time_condition(context: PolicyContext) -> bool:
            hour = context.timestamp.hour
            return time_range[0] <= hour < time_range[1]
        
        return PolicyRule(
            name=name,
            description=description,
            condition=time_condition,
            action=action,
            priority=priority
        )
    
    @staticmethod
    def role_based_rule(
        name: str,
        description: str,
        allowed_roles: List[str],
        action: PolicyAction,
        priority: int = 1
    ) -> PolicyRule:
        """基于角色的规则"""
        def role_condition(context: PolicyContext) -> bool:
            return context.role in allowed_roles
        
        return PolicyRule(
            name=name,
            description=description,
            condition=role_condition,
            action=action,
            priority=priority
        )
    
    @staticmethod
    def resource_type_rule(
        name: str,
        description: str,
        resource_types: List[str],
        action: PolicyAction,
        priority: int = 1
    ) -> PolicyRule:
        """基于资源类型的规则"""
        def resource_condition(context: PolicyContext) -> bool:
            return context.resource_type in resource_types
        
        return PolicyRule(
            name=name,
            description=description,
            condition=resource_condition,
            action=action,
            priority=priority
        )
    
    @staticmethod
    def operation_rule(
        name: str,
        description: str,
        operations: List[str],
        action: PolicyAction,
        priority: int = 1
    ) -> PolicyRule:
        """基于操作的规则"""
        def operation_condition(context: PolicyContext) -> bool:
            return context.operation in operations
        
        return PolicyRule(
            name=name,
            description=description,
            condition=operation_condition,
            action=action,
            priority=priority
        )


class PolicyEngine:
    """策略引擎（增强版，根据风险分析报告建议）"""
    
    def __init__(self):
        """初始化策略引擎"""
        self.rules: List[PolicyRule] = []
        self.policy_language = PolicyLanguage()
        self._load_default_policies()
    
    def _load_default_policies(self):
        """加载默认策略"""
        # 默认策略：拒绝所有未明确允许的操作
        default_deny = PolicyRule(
            name="default_deny",
            description="默认拒绝所有操作",
            condition=lambda ctx: True,
            action=PolicyAction.DENY,
            priority=0  # 最低优先级
        )
        self.add_rule(default_deny)
    
    def add_rule(self, rule: PolicyRule):
        """添加策略规则"""
        self.rules.append(rule)
        # 按优先级排序（高优先级在前）
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        logger.info(f"添加策略规则: {rule.name} (优先级: {rule.priority})")
    
    def remove_rule(self, rule_name: str) -> bool:
        """移除策略规则"""
        original_count = len(self.rules)
        self.rules = [r for r in self.rules if r.name != rule_name]
        removed = len(self.rules) < original_count
        if removed:
            logger.info(f"移除策略规则: {rule_name}")
        return removed
    
    def enable_rule(self, rule_name: str) -> bool:
        """启用策略规则"""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = True
                logger.info(f"启用策略规则: {rule_name}")
                return True
        return False
    
    def disable_rule(self, rule_name: str) -> bool:
        """禁用策略规则"""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = False
                logger.info(f"禁用策略规则: {rule_name}")
                return True
        return False
    
    def load_policies_from_config(self, config_path: str):
        """从配置文件加载策略（YAML/JSON）"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)
            
            policies = config.get('policies', [])
            for policy_config in policies:
                rule = self._create_rule_from_config(policy_config)
                if rule:
                    self.add_rule(rule)
            
            logger.info(f"从配置文件加载了 {len(policies)} 个策略规则")
        except Exception as e:
            logger.error(f"加载策略配置失败: {e}")
    
    def _create_rule_from_config(self, config: Dict[str, Any]) -> Optional[PolicyRule]:
        """从配置创建策略规则"""
        try:
            name = config.get('name', 'unnamed')
            description = config.get('description', '')
            action_str = config.get('action', 'deny')
            priority = config.get('priority', 1)
            
            action = PolicyAction[action_str.upper()] if action_str.upper() in PolicyAction.__members__ else PolicyAction.DENY
            
            # 根据条件类型创建规则
            condition_type = config.get('condition_type', 'custom')
            
            if condition_type == 'role':
                allowed_roles = config.get('allowed_roles', [])
                return self.policy_language.role_based_rule(
                    name=name,
                    description=description,
                    allowed_roles=allowed_roles,
                    action=action,
                    priority=priority
                )
            elif condition_type == 'resource_type':
                resource_types = config.get('resource_types', [])
                return self.policy_language.resource_type_rule(
                    name=name,
                    description=description,
                    resource_types=resource_types,
                    action=action,
                    priority=priority
                )
            elif condition_type == 'operation':
                operations = config.get('operations', [])
                return self.policy_language.operation_rule(
                    name=name,
                    description=description,
                    operations=operations,
                    action=action,
                    priority=priority
                )
            elif condition_type == 'time':
                time_range = tuple(config.get('time_range', [0, 24]))
                return self.policy_language.time_based_rule(
                    name=name,
                    description=description,
                    time_range=time_range,
                    action=action,
                    priority=priority
                )
            else:
                # 自定义条件（需要实现）
                logger.warning(f"不支持的条件类型: {condition_type}")
                return None
        except Exception as e:
            logger.error(f"从配置创建策略规则失败: {e}")
            return None
    
    def evaluate(
        self,
        operation: ResourceOperation,
        context: Dict[str, Any]
    ) -> PolicyEvaluationResult:
        """
        评估操作是否符合策略
        
        Args:
            operation: 资源操作
            context: 上下文信息（用户、角色、时间等）
            
        Returns:
            PolicyEvaluationResult: 评估结果
        """
        # 构建策略上下文
        # 处理resource_type（可能是字符串或ResourceType枚举）
        resource_type_str = operation.resource_type
        if hasattr(operation.resource_type, 'value'):
            resource_type_str = operation.resource_type.value
        elif isinstance(operation.resource_type, ResourceType):
            resource_type_str = operation.resource_type.value
        
        # 处理operation_type（可能是字符串或ResourceOperationType枚举）
        operation_str = operation.operation_type
        if hasattr(operation.operation_type, 'value'):
            operation_str = operation.operation_type.value
        elif isinstance(operation.operation_type, ResourceOperationType):
            operation_str = operation.operation_type.value
        
        policy_context = PolicyContext(
            user=context.get('user', 'unknown'),
            role=context.get('role', 'guest'),
            resource_id=operation.resource_id,
            resource_type=resource_type_str,
            operation=operation_str,
            timestamp=context.get('timestamp', datetime.now()),
            metadata=context.get('metadata', {})
        )
        
        # 遍历所有规则（按优先级）
        for rule in self.rules:
            action = rule.evaluate(policy_context)
            if action:
                # 匹配到规则，返回结果
                allowed = action in [PolicyAction.ALLOW, PolicyAction.LOG_ONLY]
                
                # 处理需要审批的情况
                required_approvals = []
                if action == PolicyAction.REQUIRE_APPROVAL:
                    # 从元数据或规则中获取审批人
                    required_approvals = context.get('required_approvals', [])
                    allowed = False  # 需要审批时暂时不允许
                
                # 处理限制情况
                restrictions = []
                if action == PolicyAction.RESTRICT:
                    restrictions = context.get('restrictions', [])
                
                return PolicyEvaluationResult(
                    allowed=allowed,
                    action=action,
                    reason=rule.description,
                    required_approvals=required_approvals,
                    restrictions=restrictions,
                    policy_rule_name=rule.name
                )
        
        # 没有匹配的规则，使用默认策略（拒绝）
        return PolicyEvaluationResult(
            allowed=False,
            action=PolicyAction.DENY,
            reason="No matching policy rule",
            policy_rule_name="default_deny"
        )
    
    def apply_policy(
        self,
        operation: ResourceOperation,
        evaluation: PolicyEvaluationResult
    ) -> ResourceOperation:
        """
        应用策略（添加审批、限制等）
        
        Args:
            operation: 原始操作
            evaluation: 策略评估结果
            
        Returns:
            ResourceOperation: 修改后的操作（可能添加了审批节点、限制等）
        """
        # 如果被拒绝，直接返回
        if not evaluation.allowed and evaluation.action == PolicyAction.DENY:
            return operation
        
        # 如果需要审批，在操作元数据中添加审批信息
        if evaluation.required_approvals:
            if not hasattr(operation, 'metadata') or operation.metadata is None:
                operation.metadata = {}
            operation.metadata['required_approvals'] = evaluation.required_approvals
            operation.metadata['approval_status'] = 'pending'
        
        # 如果有限制，在操作元数据中添加限制信息
        if evaluation.restrictions:
            if not hasattr(operation, 'metadata') or operation.metadata is None:
                operation.metadata = {}
            operation.metadata['restrictions'] = evaluation.restrictions
        
        return operation
    
    def get_all_rules(self) -> List[Dict[str, Any]]:
        """获取所有策略规则（用于配置界面）"""
        return [
            {
                "name": rule.name,
                "description": rule.description,
                "action": rule.action.value,
                "priority": rule.priority,
                "enabled": rule.enabled
            }
            for rule in self.rules
        ]
    
    def get_rule(self, rule_name: str) -> Optional[Dict[str, Any]]:
        """获取指定策略规则"""
        for rule in self.rules:
            if rule.name == rule_name:
                return {
                    "name": rule.name,
                    "description": rule.description,
                    "action": rule.action.value,
                    "priority": rule.priority,
                    "enabled": rule.enabled
                }
        return None

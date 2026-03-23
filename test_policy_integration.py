"""
策略引擎集成测试
测试策略引擎、审计日志和统一意图服务的集成
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime

# 添加路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "os-core"))
sys.path.insert(0, str(PROJECT_ROOT / "services"))

try:
    from policy_engine import PolicyEngine, PolicyLanguage, PolicyAction
    from audit_logger import AuditLogger, AuditEventType
    from resource_operations import ResourceOperation, ResourceOperationType
    from resource_model import ResourceType
    POLICY_AVAILABLE = True
except ImportError:
    POLICY_AVAILABLE = False
    pytest.skip("策略引擎模块不可用", allow_module_level=True)


class TestPolicyEngine:
    """策略引擎测试"""
    
    def test_policy_engine_initialization(self):
        """测试策略引擎初始化"""
        engine = PolicyEngine()
        assert engine is not None
        assert len(engine.rules) > 0  # 至少应该有默认规则
    
    def test_role_based_rule(self):
        """测试基于角色的规则"""
        engine = PolicyEngine()
        policy_lang = PolicyLanguage()
        
        # 创建角色规则
        rule = policy_lang.role_based_rule(
            name="高管访问",
            description="高管可以访问",
            allowed_roles=["CEO", "CTO"],
            action=PolicyAction.ALLOW,
            priority=100
        )
        engine.add_rule(rule)
        
        # 创建测试操作
        operation = ResourceOperation(
            operation_type=ResourceOperationType.QUERY,
            resource_id="resource:001",
            resource_type=ResourceType.BUSINESS_OBJECT,
            action="query",
            parameters={}
        )
        
        # 测试CEO角色
        context = {
            "user": "ceo_user",
            "role": "CEO",
            "timestamp": datetime.now()
        }
        evaluation = engine.evaluate(operation, context)
        assert evaluation.allowed is True
        assert evaluation.action == PolicyAction.ALLOW
        
        # 测试普通用户
        context["role"] = "guest"
        evaluation = engine.evaluate(operation, context)
        assert evaluation.allowed is False  # 默认拒绝
    
    def test_resource_type_rule(self):
        """测试基于资源类型的规则"""
        engine = PolicyEngine()
        policy_lang = PolicyLanguage()
        
        # 创建资源类型规则
        rule = policy_lang.resource_type_rule(
            name="数据实体限制",
            description="数据实体只能查询",
            resource_types=["data_entity"],
            action=PolicyAction.RESTRICT,
            priority=60
        )
        engine.add_rule(rule)
        
        # 测试数据实体操作
        operation = ResourceOperation(
            operation_type=ResourceOperationType.QUERY,
            resource_id="data:001",
            resource_type="data_entity",
            action="query",
            parameters={}
        )
        
        context = {
            "user": "user1",
            "role": "user",
            "timestamp": datetime.now()
        }
        evaluation = engine.evaluate(operation, context)
        assert evaluation.action == PolicyAction.RESTRICT
    
    def test_time_based_rule(self):
        """测试基于时间的规则"""
        engine = PolicyEngine()
        policy_lang = PolicyLanguage()
        
        # 创建时间规则（非工作时间需要审批）
        rule = policy_lang.time_based_rule(
            name="非工作时间审批",
            description="非工作时间需要审批",
            time_range=(18, 9),  # 18:00-09:00
            action=PolicyAction.REQUIRE_APPROVAL,
            priority=50
        )
        engine.add_rule(rule)
        
        operation = ResourceOperation(
            operation_type=ResourceOperationType.CREATE,
            resource_id="resource:001",
            resource_type=ResourceType.BUSINESS_OBJECT,
            action="create",
            parameters={}
        )
        
        # 测试非工作时间（20:00）
        context = {
            "user": "user1",
            "role": "user",
            "timestamp": datetime.now().replace(hour=20)
        }
        evaluation = engine.evaluate(operation, context)
        assert evaluation.action == PolicyAction.REQUIRE_APPROVAL
        assert evaluation.allowed is False  # 需要审批时暂时不允许


class TestAuditLogger:
    """审计日志测试"""
    
    def test_audit_logger_initialization(self):
        """测试审计日志初始化"""
        logger = AuditLogger()
        assert logger is not None
    
    def test_log_intent_recognition(self):
        """测试记录意图识别"""
        logger = AuditLogger()
        
        event_id = logger.log_intent_recognition(
            user="user1",
            role="user",
            intent="创建采购订单",
            recognized_intent={"intent": "create_order", "confidence": 0.95},
            success=True
        )
        
        assert event_id is not None
        
        # 查询事件
        events = logger.query_events(user="user1", limit=10)
        assert len(events) > 0
        assert events[0].event_type == AuditEventType.INTENT_RECOGNITION
    
    def test_log_resource_operation(self):
        """测试记录资源操作"""
        logger = AuditLogger()
        
        event_id = logger.log_resource_operation(
            user="user1",
            role="user",
            resource_id="order:001",
            resource_type="business_object",
            operation="create",
            success=True
        )
        
        assert event_id is not None
        
        # 查询事件
        events = logger.query_events(
            resource_id="order:001",
            limit=10
        )
        assert len(events) > 0
        assert events[0].event_type == AuditEventType.RESOURCE_OPERATION
    
    def test_log_policy_evaluation(self):
        """测试记录策略评估"""
        logger = AuditLogger()
        
        event_id = logger.log_policy_evaluation(
            user="user1",
            role="user",
            resource_id="resource:001",
            operation="create",
            evaluation_result={"allowed": True, "action": "allow"},
            allowed=True
        )
        
        assert event_id is not None
        
        # 查询事件
        events = logger.query_events(
            event_type=AuditEventType.POLICY_EVALUATION,
            limit=10
        )
        assert len(events) > 0
    
    def test_generate_audit_report(self):
        """测试生成审计报告"""
        logger = AuditLogger()
        
        # 记录一些事件
        logger.log_intent_recognition("user1", "user", "test", {}, True)
        logger.log_resource_operation("user1", "user", "res1", "type1", "op1", True)
        
        # 生成报告
        from datetime import timedelta
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        
        report = logger.generate_audit_report(start_time, end_time)
        
        assert "summary" in report
        assert "total_events" in report["summary"]
        assert report["summary"]["total_events"] >= 2


class TestPolicyIntegration:
    """策略集成测试"""
    
    def test_policy_with_audit(self):
        """测试策略评估和审计日志集成"""
        engine = PolicyEngine()
        logger = AuditLogger()
        
        # 添加规则
        policy_lang = PolicyLanguage()
        rule = policy_lang.role_based_rule(
            name="测试规则",
            description="测试规则",
            allowed_roles=["admin"],
            action=PolicyAction.ALLOW,
            priority=100
        )
        engine.add_rule(rule)
        
        # 创建操作
        operation = ResourceOperation(
            operation_type=ResourceOperationType.QUERY,
            resource_id="resource:001",
            resource_type=ResourceType.BUSINESS_OBJECT,
            action="query",
            parameters={}
        )
        
        # 评估策略
        context = {
            "user": "admin_user",
            "role": "admin",
            "timestamp": datetime.now()
        }
        evaluation = engine.evaluate(operation, context)
        
        # 记录审计日志
        logger.log_policy_evaluation(
            user=context["user"],
            role=context["role"],
            resource_id=operation.resource_id,
            operation=operation.operation_type.value,
            evaluation_result={
                "allowed": evaluation.allowed,
                "action": evaluation.action.value,
                "reason": evaluation.reason
            },
            allowed=evaluation.allowed
        )
        
        # 验证
        assert evaluation.allowed is True
        events = logger.query_events(user="admin_user", limit=10)
        assert len(events) > 0


class TestPolicyConfiguration:
    """策略配置测试"""
    
    def test_load_policies_from_config(self):
        """测试从配置文件加载策略"""
        engine = PolicyEngine()
        
        # 加载配置文件
        config_path = PROJECT_ROOT / "config" / "policies.yaml"
        if config_path.exists():
            engine.load_policies_from_config(str(config_path))
            
            # 验证规则已加载
            rules = engine.get_all_rules()
            assert len(rules) > 1  # 至少应该有默认规则和加载的规则

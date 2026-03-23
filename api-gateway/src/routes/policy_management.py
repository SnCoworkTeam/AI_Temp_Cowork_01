"""
策略配置管理API
提供策略规则的CRUD操作和配置管理
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "os-core"))

try:
    from policy_engine import PolicyEngine, PolicyRule, PolicyAction, PolicyLanguage
    POLICY_ENGINE_AVAILABLE = True
except ImportError:
    POLICY_ENGINE_AVAILABLE = False

router = APIRouter(prefix="/api/policies", tags=["策略管理"])

# 全局策略引擎实例（实际应该通过依赖注入）
_policy_engine: Optional[PolicyEngine] = None


def get_policy_engine() -> PolicyEngine:
    """获取策略引擎实例"""
    global _policy_engine
    if _policy_engine is None:
        if not POLICY_ENGINE_AVAILABLE:
            raise HTTPException(status_code=503, detail="策略引擎不可用")
        _policy_engine = PolicyEngine()
    return _policy_engine


# Pydantic模型
class PolicyRuleCreate(BaseModel):
    """创建策略规则请求"""
    name: str
    description: str
    condition_type: str  # "role" | "resource_type" | "operation" | "time" | "custom"
    action: str  # "allow" | "deny" | "require_approval" | "log_only" | "restrict"
    priority: int = 1
    enabled: bool = True
    # 条件参数（根据condition_type不同而不同）
    allowed_roles: Optional[List[str]] = None
    resource_types: Optional[List[str]] = None
    operations: Optional[List[str]] = None
    time_range: Optional[List[int]] = None  # [start_hour, end_hour]
    custom_condition: Optional[str] = None  # 自定义条件（JSON字符串）


class PolicyRuleResponse(BaseModel):
    """策略规则响应"""
    name: str
    description: str
    action: str
    priority: int
    enabled: bool


class PolicyRuleUpdate(BaseModel):
    """更新策略规则请求"""
    description: Optional[str] = None
    action: Optional[str] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None


@router.get("/rules", response_model=List[PolicyRuleResponse])
async def list_policies(engine: PolicyEngine = Depends(get_policy_engine)):
    """获取所有策略规则"""
    try:
        rules = engine.get_all_rules()
        return rules
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略规则失败: {str(e)}")


@router.get("/rules/{rule_name}", response_model=PolicyRuleResponse)
async def get_policy(rule_name: str, engine: PolicyEngine = Depends(get_policy_engine)):
    """获取指定策略规则"""
    try:
        rule = engine.get_rule(rule_name)
        if not rule:
            raise HTTPException(status_code=404, detail=f"策略规则 {rule_name} 不存在")
        return rule
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略规则失败: {str(e)}")


@router.post("/rules", response_model=PolicyRuleResponse)
async def create_policy(
    rule_data: PolicyRuleCreate,
    engine: PolicyEngine = Depends(get_policy_engine)
):
    """创建策略规则"""
    try:
        # 检查是否已存在
        existing = engine.get_rule(rule_data.name)
        if existing:
            raise HTTPException(status_code=400, detail=f"策略规则 {rule_data.name} 已存在")
        
        # 根据条件类型创建规则
        policy_lang = PolicyLanguage()
        action = PolicyAction[rule_data.action.upper()]
        
        if rule_data.condition_type == "role":
            if not rule_data.allowed_roles:
                raise HTTPException(status_code=400, detail="角色规则需要指定allowed_roles")
            rule = policy_lang.role_based_rule(
                name=rule_data.name,
                description=rule_data.description,
                allowed_roles=rule_data.allowed_roles,
                action=action,
                priority=rule_data.priority
            )
        elif rule_data.condition_type == "resource_type":
            if not rule_data.resource_types:
                raise HTTPException(status_code=400, detail="资源类型规则需要指定resource_types")
            rule = policy_lang.resource_type_rule(
                name=rule_data.name,
                description=rule_data.description,
                resource_types=rule_data.resource_types,
                action=action,
                priority=rule_data.priority
            )
        elif rule_data.condition_type == "operation":
            if not rule_data.operations:
                raise HTTPException(status_code=400, detail="操作规则需要指定operations")
            rule = policy_lang.operation_rule(
                name=rule_data.name,
                description=rule_data.description,
                operations=rule_data.operations,
                action=action,
                priority=rule_data.priority
            )
        elif rule_data.condition_type == "time":
            if not rule_data.time_range or len(rule_data.time_range) != 2:
                raise HTTPException(status_code=400, detail="时间规则需要指定time_range [start_hour, end_hour]")
            rule = policy_lang.time_based_rule(
                name=rule_data.name,
                description=rule_data.description,
                time_range=tuple(rule_data.time_range),
                action=action,
                priority=rule_data.priority
            )
        else:
            raise HTTPException(status_code=400, detail=f"不支持的条件类型: {rule_data.condition_type}")
        
        rule.enabled = rule_data.enabled
        engine.add_rule(rule)
        
        return PolicyRuleResponse(
            name=rule.name,
            description=rule.description,
            action=rule.action.value,
            priority=rule.priority,
            enabled=rule.enabled
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建策略规则失败: {str(e)}")


@router.put("/rules/{rule_name}", response_model=PolicyRuleResponse)
async def update_policy(
    rule_name: str,
    rule_data: PolicyRuleUpdate,
    engine: PolicyEngine = Depends(get_policy_engine)
):
    """更新策略规则"""
    try:
        # 获取现有规则（这里简化实现，实际应该支持更新规则内容）
        rule = engine.get_rule(rule_name)
        if not rule:
            raise HTTPException(status_code=404, detail=f"策略规则 {rule_name} 不存在")
        
        # 更新启用状态
        if rule_data.enabled is not None:
            if rule_data.enabled:
                engine.enable_rule(rule_name)
            else:
                engine.disable_rule(rule_name)
        
        # 获取更新后的规则
        updated_rule = engine.get_rule(rule_name)
        return updated_rule
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新策略规则失败: {str(e)}")


@router.delete("/rules/{rule_name}")
async def delete_policy(rule_name: str, engine: PolicyEngine = Depends(get_policy_engine)):
    """删除策略规则"""
    try:
        if rule_name == "default_deny":
            raise HTTPException(status_code=400, detail="不能删除默认拒绝规则")
        
        success = engine.remove_rule(rule_name)
        if not success:
            raise HTTPException(status_code=404, detail=f"策略规则 {rule_name} 不存在")
        
        return {"message": f"策略规则 {rule_name} 已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除策略规则失败: {str(e)}")


@router.post("/rules/{rule_name}/enable")
async def enable_policy(rule_name: str, engine: PolicyEngine = Depends(get_policy_engine)):
    """启用策略规则"""
    try:
        success = engine.enable_rule(rule_name)
        if not success:
            raise HTTPException(status_code=404, detail=f"策略规则 {rule_name} 不存在")
        return {"message": f"策略规则 {rule_name} 已启用"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启用策略规则失败: {str(e)}")


@router.post("/rules/{rule_name}/disable")
async def disable_policy(rule_name: str, engine: PolicyEngine = Depends(get_policy_engine)):
    """禁用策略规则"""
    try:
        success = engine.disable_rule(rule_name)
        if not success:
            raise HTTPException(status_code=404, detail=f"策略规则 {rule_name} 不存在")
        return {"message": f"策略规则 {rule_name} 已禁用"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"禁用策略规则失败: {str(e)}")


@router.post("/load-from-config")
async def load_policies_from_config(
    config_path: str,
    engine: PolicyEngine = Depends(get_policy_engine)
):
    """从配置文件加载策略"""
    try:
        engine.load_policies_from_config(config_path)
        return {"message": f"已从 {config_path} 加载策略配置"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加载策略配置失败: {str(e)}")


@router.get("/statistics")
async def get_policy_statistics(engine: PolicyEngine = Depends(get_policy_engine)):
    """获取策略统计信息"""
    try:
        rules = engine.get_all_rules()
        total_rules = len(rules)
        enabled_rules = sum(1 for r in rules if r.get("enabled", True))
        disabled_rules = total_rules - enabled_rules
        
        # 按动作类型统计
        action_counts = {}
        for rule in rules:
            action = rule.get("action", "deny")
            action_counts[action] = action_counts.get(action, 0) + 1
        
        return {
            "total_rules": total_rules,
            "enabled_rules": enabled_rules,
            "disabled_rules": disabled_rules,
            "action_distribution": action_counts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略统计失败: {str(e)}")


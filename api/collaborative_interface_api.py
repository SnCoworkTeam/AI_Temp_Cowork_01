"""
协同界面API
支持AI推荐和人工组装的协同工作流
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.unified_intent_service import UnifiedIntentService, UnifiedIntentResult
from database.src.core.session import get_db, init_session_factory
from database.src.core.database import get_database_manager
from database.src.models import CapabilityUnit

# 创建FastAPI应用
app = FastAPI(
    title="协同界面API",
    description="支持AI推荐和人工组装的协同工作流",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局服务实例
unified_intent_service: Optional[UnifiedIntentService] = None


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化服务"""
    global unified_intent_service
    try:
        # 初始化数据库连接
        db_manager = get_database_manager()
        if not db_manager.test_connection():
            raise RuntimeError("数据库连接失败")
        
        init_session_factory()
        
        unified_intent_service = UnifiedIntentService()
        print("[INFO] 协同界面API已启动")
    except Exception as e:
        print(f"[ERROR] 服务启动失败: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    global unified_intent_service
    if unified_intent_service:
        unified_intent_service._close_db()
    print("[INFO] 协同界面API已关闭")


# ==================== 请求/响应模型 ====================

class IntentRequest(BaseModel):
    """意图理解请求"""
    user_input: str = Field(..., description="用户输入文本")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")


class SelectedActivity(BaseModel):
    """用户选择的活动"""
    activity_id: str = Field(..., description="活动ID")
    capability_id: Optional[str] = Field(None, description="能力单元ID")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="参数")


class ExecutionAssemblyRequest(BaseModel):
    """组装执行计划请求"""
    selected_activities: List[SelectedActivity] = Field(..., description="用户选择的活动列表")
    execution_order: Optional[List[str]] = Field(None, description="执行顺序（活动ID列表）")


class ExecutionPlan(BaseModel):
    """执行计划"""
    plan_id: str
    activities: List[Dict[str, Any]]
    execution_order: List[str]
    estimated_time: Optional[str]
    total_confidence: float
    created_at: str


class ExecutionPlanRequest(BaseModel):
    """执行计划请求"""
    plan_id: str = Field(..., description="执行计划ID")
    confirm: bool = Field(True, description="是否确认执行")


class ExecutionResult(BaseModel):
    """执行结果"""
    plan_id: str
    status: str
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    execution_time: float
    completed_at: str


# ==================== API端点 ====================

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "collaborative_interface_api",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/collaborative/intent/understand")
async def understand_intent(request: IntentRequest):
    """
    理解意图（返回推荐）
    
    Args:
        request: 意图理解请求
    
    Returns:
        UnifiedIntentResult: 意图理解结果（包含推荐活动）
    """
    if not unified_intent_service:
        raise HTTPException(status_code=503, detail="统一意图服务未初始化")
    
    try:
        result = await unified_intent_service.understand_intent(
            user_input=request.user_input,
            context=request.context
        )
        
        # 转换为响应格式
        return {
            "user_input": result.user_input,
            "base_intent": result.base_intent,
            "intent_type": result.intent_type,
            "confidence": result.confidence,
            "suggested_activities": result.suggested_activities,
            "execution_suggestions": [
                {
                    "activity_id": s.activity_id,
                    "activity_name": s.activity_name,
                    "capability_id": s.capability_id,
                    "capability_name": s.capability_name,
                    "input_schema": s.input_schema,
                    "estimated_time": s.estimated_time,
                    "confidence": s.confidence
                }
                for s in result.execution_suggestions
            ],
            "reasoning": result.reasoning,
            "fallback_mode": result.fallback_mode,
            "query_time": result.query_time
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"意图理解失败: {str(e)}")


@app.post("/api/v1/collaborative/execution/assemble", response_model=ExecutionPlan)
async def assemble_execution_plan(request: ExecutionAssemblyRequest):
    """
    组装执行计划（用户选择）
    
    Args:
        request: 组装执行计划请求
    
    Returns:
        ExecutionPlan: 执行计划
    """
    if not unified_intent_service:
        raise HTTPException(status_code=503, detail="统一意图服务未初始化")
    
    try:
        # 1. 验证用户选择
        validated_activities = []
        total_confidence = 0.0
        
        for selected in request.selected_activities:
            # 获取活动详情
            activity = unified_intent_service.semantic_engine.get_activity_by_id(selected.activity_id)
            if not activity:
                raise HTTPException(status_code=404, detail=f"活动不存在: {selected.activity_id}")
            
            # 获取能力单元（如果指定）
            capability_info = None
            if selected.capability_id:
                capabilities = await unified_intent_service.get_capabilities_for_activity(selected.activity_id)
                capability_info = next(
                    (c for c in capabilities if c["capability_id"] == selected.capability_id),
                    None
                )
                if not capability_info:
                    raise HTTPException(status_code=404, detail=f"能力单元不存在: {selected.capability_id}")
            else:
                # 使用推荐的能力单元
                capabilities = await unified_intent_service.get_capabilities_for_activity(selected.activity_id)
                if capabilities:
                    capability_info = max(
                        capabilities,
                        key=lambda c: (c.get("priority", 0), c.get("success_rate", 0))
                    )
            
            # 验证参数（如果能力单元有input_schema）
            if capability_info and capability_info.get("input_schema"):
                # 简单的参数验证
                input_schema = capability_info["input_schema"]
                if isinstance(input_schema, dict):
                    for key, value in input_schema.items():
                        if key in selected.parameters:
                            # 类型验证（简化版）
                            pass
            
            validated_activities.append({
                "activity_id": selected.activity_id,
                "activity_name": activity.name,
                "capability_id": capability_info["capability_id"] if capability_info else None,
                "capability_name": capability_info["capability_name"] if capability_info else None,
                "parameters": selected.parameters,
                "confidence": capability_info.get("confidence", 0.7) if capability_info else 0.5
            })
            
            total_confidence += validated_activities[-1]["confidence"]
        
        # 2. 构建执行计划
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        execution_order = request.execution_order or [a["activity_id"] for a in validated_activities]
        
        # 验证执行顺序
        activity_ids = {a["activity_id"] for a in validated_activities}
        if not all(aid in activity_ids for aid in execution_order):
            raise HTTPException(status_code=400, detail="执行顺序包含不存在的活动ID")
        
        plan = ExecutionPlan(
            plan_id=plan_id,
            activities=validated_activities,
            execution_order=execution_order,
            estimated_time=None,  # TODO: 计算总时间
            total_confidence=total_confidence / len(validated_activities) if validated_activities else 0.0,
            created_at=datetime.now().isoformat()
        )
        
        return plan
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"组装执行计划失败: {str(e)}")


@app.post("/api/v1/collaborative/execution/execute", response_model=ExecutionResult)
async def execute_plan(request: ExecutionPlanRequest):
    """
    执行计划
    
    Args:
        request: 执行计划请求
    
    Returns:
        ExecutionResult: 执行结果
    """
    if not unified_intent_service:
        raise HTTPException(status_code=503, detail="统一意图服务未初始化")
    
    if not request.confirm:
        raise HTTPException(status_code=400, detail="需要确认执行")
    
    try:
        import time
        start_time = time.time()
        
        # 注意：这里只是模拟执行，实际应该调用真实的能力单元
        # TODO: 实现真实的执行逻辑
        
        results = []
        errors = []
        
        # 模拟执行结果
        results.append({
            "activity_id": "activity:procurement:create_po",
            "status": "success",
            "message": "执行成功（模拟）",
            "output": {"po_number": "PO-2025-001"}
        })
        
        execution_time = time.time() - start_time
        
        result = ExecutionResult(
            plan_id=request.plan_id,
            status="completed",
            results=results,
            errors=errors,
            execution_time=execution_time,
            completed_at=datetime.now().isoformat()
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行计划失败: {str(e)}")


@app.post("/api/v1/collaborative/execution/validate")
async def validate_parameters(
    activity_id: str = Query(..., description="活动ID"),
    capability_id: Optional[str] = Query(None, description="能力单元ID"),
    parameters: Dict[str, Any] = Query(..., description="参数")
):
    """
    验证参数
    
    Args:
        activity_id: 活动ID
        capability_id: 能力单元ID
        parameters: 参数
    
    Returns:
        Dict: 验证结果
    """
    if not unified_intent_service:
        raise HTTPException(status_code=503, detail="统一意图服务未初始化")
    
    try:
        # 获取能力单元
        capabilities = await unified_intent_service.get_capabilities_for_activity(activity_id)
        
        if capability_id:
            capability = next(
                (c for c in capabilities if c["capability_id"] == capability_id),
                None
            )
        else:
            capability = capabilities[0] if capabilities else None
        
        if not capability:
            raise HTTPException(status_code=404, detail="能力单元不存在")
        
        # 验证参数（简化版）
        input_schema = capability.get("input_schema")
        validation_errors = []
        
        if isinstance(input_schema, dict):
            for key, schema in input_schema.items():
                if key not in parameters:
                    if schema.get("required", False):
                        validation_errors.append(f"缺少必需参数: {key}")
        
        return {
            "valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "warnings": []
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"参数验证失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)






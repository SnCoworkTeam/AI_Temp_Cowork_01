"""
统一意图服务API接口
提供RESTful API用于意图理解、活动推荐、能力查询等
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

from services.unified_intent_service import (
    UnifiedIntentService,
    UnifiedIntentResult,
    ExecutionSuggestion
)

# 创建FastAPI应用
app = FastAPI(
    title="统一意图服务API",
    description="提供意图理解、活动推荐、能力查询等功能",
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
        unified_intent_service = UnifiedIntentService()
        print("[INFO] 统一意图服务已启动")
    except Exception as e:
        print(f"[ERROR] 服务启动失败: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    global unified_intent_service
    if unified_intent_service:
        unified_intent_service._close_db()
    print("[INFO] 统一意图服务已关闭")


# ==================== 请求/响应模型 ====================

class IntentRequest(BaseModel):
    """意图理解请求"""
    user_input: str = Field(..., description="用户输入文本")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")


class IntentResponse(BaseModel):
    """意图理解响应"""
    user_input: str
    base_intent: str
    intent_type: str
    confidence: float
    suggested_activities: List[Dict[str, Any]]
    related_entities: List[Dict[str, Any]]
    available_capabilities: List[Dict[str, Any]]
    execution_suggestions: List[Dict[str, Any]]
    reasoning: str
    fallback_mode: bool
    query_time: float


class ActivityRecommendationRequest(BaseModel):
    """活动推荐请求"""
    user_input: str = Field(..., description="用户输入文本")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")
    top_k: int = Field(5, ge=1, le=20, description="返回前k个推荐")


# ==================== API端点 ====================

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "unified_intent_service",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/intent/understand", response_model=IntentResponse)
async def understand_intent(request: IntentRequest):
    """
    理解用户意图
    
    Args:
        request: 意图理解请求
    
    Returns:
        IntentResponse: 意图理解结果
    """
    if not unified_intent_service:
        raise HTTPException(status_code=503, detail="统一意图服务未初始化")
    
    try:
        result = await unified_intent_service.understand_intent(
            user_input=request.user_input,
            context=request.context
        )
        
        # 转换为响应格式
        execution_suggestions_data = []
        for suggestion in result.execution_suggestions:
            execution_suggestions_data.append({
                "activity_id": suggestion.activity_id,
                "activity_name": suggestion.activity_name,
                "capability_id": suggestion.capability_id,
                "capability_name": suggestion.capability_name,
                "input_schema": suggestion.input_schema,
                "estimated_time": suggestion.estimated_time,
                "confidence": suggestion.confidence
            })
        
        return IntentResponse(
            user_input=result.user_input,
            base_intent=result.base_intent,
            intent_type=result.intent_type,
            confidence=result.confidence,
            suggested_activities=result.suggested_activities,
            related_entities=result.related_entities,
            available_capabilities=result.available_capabilities,
            execution_suggestions=execution_suggestions_data,
            reasoning=result.reasoning,
            fallback_mode=result.fallback_mode,
            query_time=result.query_time
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"意图理解失败: {str(e)}")


@app.post("/api/v1/intent/recommendations")
async def recommend_activities(request: ActivityRecommendationRequest):
    """
    推荐相关业务活动
    
    Args:
        request: 活动推荐请求
    
    Returns:
        List[Dict]: 推荐的活动列表
    """
    if not unified_intent_service:
        raise HTTPException(status_code=503, detail="统一意图服务未初始化")
    
    try:
        recommendations = await unified_intent_service.recommend_activities(
            user_input=request.user_input,
            context=request.context,
            top_k=request.top_k
        )
        
        return {
            "total": len(recommendations),
            "recommendations": recommendations
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"活动推荐失败: {str(e)}")


@app.get("/api/v1/intent/activities/{activity_id}/capabilities")
async def get_activity_capabilities(activity_id: str):
    """
    获取活动的能力单元
    
    Args:
        activity_id: 活动ID
    
    Returns:
        List[Dict]: 能力单元列表
    """
    if not unified_intent_service:
        raise HTTPException(status_code=503, detail="统一意图服务未初始化")
    
    try:
        capabilities = await unified_intent_service.get_capabilities_for_activity(activity_id)
        
        return {
            "activity_id": activity_id,
            "total": len(capabilities),
            "capabilities": capabilities
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取活动能力失败: {str(e)}")


@app.get("/api/v1/intent/cache/stats")
async def get_cache_stats():
    """
    获取缓存统计信息
    
    Returns:
        Dict: 缓存统计信息
    """
    if not unified_intent_service:
        raise HTTPException(status_code=503, detail="统一意图服务未初始化")
    
    try:
        stats = unified_intent_service.get_cache_stats()
        return stats
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取缓存统计失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)






"""
企业语义引擎API接口
提供RESTful API用于查询意图、搜索活动、推荐活动等
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

from services.enterprise_semantic_engine import (
    EnterpriseSemanticEngine,
    IntentQueryResult,
    ActivityRecommendation
)
from services.vector_sync_service import VectorSyncService

# 创建FastAPI应用
app = FastAPI(
    title="企业语义引擎API",
    description="提供意图查询、活动搜索、活动推荐等功能",
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
semantic_engine: Optional[EnterpriseSemanticEngine] = None
vector_sync_service: Optional[VectorSyncService] = None


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化服务"""
    global semantic_engine, vector_sync_service
    try:
        semantic_engine = EnterpriseSemanticEngine()
        vector_sync_service = VectorSyncService()
        print("[INFO] 企业语义引擎服务已启动")
    except Exception as e:
        print(f"[ERROR] 服务启动失败: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    global semantic_engine, vector_sync_service
    if semantic_engine:
        semantic_engine._close_db()
    if vector_sync_service:
        vector_sync_service._close_db()
    print("[INFO] 企业语义引擎服务已关闭")


# ==================== 请求/响应模型 ====================

class IntentQueryRequest(BaseModel):
    """意图查询请求"""
    query: str = Field(..., description="用户查询文本")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")
    top_k: int = Field(10, ge=1, le=50, description="返回前k个结果")
    min_score: float = Field(0.5, ge=0.0, le=1.0, description="最小相似度分数")


class IntentQueryResponse(BaseModel):
    """意图查询响应"""
    query: str
    activities: List[Dict[str, Any]]
    scores: List[float]
    total_count: int
    query_time: float


class ActivityRecommendationRequest(BaseModel):
    """活动推荐请求"""
    activity_id: str = Field(..., description="源活动ID")
    top_k: int = Field(5, ge=1, le=20, description="返回前k个推荐")
    min_similarity: float = Field(0.6, ge=0.0, le=1.0, description="最小相似度")


class ActivityRecommendationResponse(BaseModel):
    """活动推荐响应"""
    source_activity_id: str
    recommended_activities: List[Dict[str, Any]]
    similarity_scores: List[float]
    recommendation_reason: str


class VectorSyncResponse(BaseModel):
    """向量同步响应"""
    total: int
    updated: int
    failed: int
    failed_ids: List[str]
    message: str


class SyncStatusResponse(BaseModel):
    """同步状态响应"""
    total: int
    needs_update: int
    up_to_date: int
    update_percentage: float


# ==================== API端点 ====================

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "enterprise_semantic_engine",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/intent/query", response_model=IntentQueryResponse)
async def query_intent(request: IntentQueryRequest):
    """
    查询意图，返回相关业务活动
    
    Args:
        request: 意图查询请求
    
    Returns:
        IntentQueryResponse: 查询结果
    """
    if not semantic_engine:
        raise HTTPException(status_code=503, detail="语义引擎服务未初始化")
    
    try:
        result = semantic_engine.query_intent(
            user_input=request.query,
            context=request.context,
            top_k=request.top_k,
            min_score=request.min_score
        )
        
        # 转换为响应格式
        activities_data = []
        for activity in result.activities:
            activities_data.append({
                "id": activity.id,
                "name": activity.name,
                "description": activity.description,
                "activity_type": activity.activity_type,
                "business_domain": activity.business_domain,
                "vector_entity_uri": activity.vector_entity_uri
            })
        
        return IntentQueryResponse(
            query=result.query,
            activities=activities_data,
            scores=result.scores,
            total_count=result.total_count,
            query_time=result.query_time
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@app.get("/api/v1/activities/{activity_id}")
async def get_activity(activity_id: str):
    """
    根据ID获取业务活动
    
    Args:
        activity_id: 活动ID
    
    Returns:
        Dict: 活动信息
    """
    if not semantic_engine:
        raise HTTPException(status_code=503, detail="语义引擎服务未初始化")
    
    try:
        activity = semantic_engine.get_activity_by_id(activity_id)
        if not activity:
            raise HTTPException(status_code=404, detail=f"活动不存在: {activity_id}")
        
        return {
            "id": activity.id,
            "name": activity.name,
            "description": activity.description,
            "activity_type": activity.activity_type,
            "business_domain": activity.business_domain,
            "success_criteria": activity.success_criteria,
            "prerequisites": activity.prerequisites,
            "vector_entity_uri": activity.vector_entity_uri,
            "embedding_version": activity.embedding_version
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取活动失败: {str(e)}")


@app.get("/api/v1/activities")
async def list_activities(
    domain: Optional[str] = Query(None, description="业务领域过滤"),
    activity_type: Optional[str] = Query(None, description="活动类型过滤")
):
    """
    获取活动列表
    
    Args:
        domain: 业务领域
        activity_type: 活动类型
    
    Returns:
        List[Dict]: 活动列表
    """
    if not semantic_engine:
        raise HTTPException(status_code=503, detail="语义引擎服务未初始化")
    
    try:
        if domain:
            activities = semantic_engine.get_activities_by_domain(domain)
        else:
            activities = semantic_engine.get_activities_by_domain("procurement")
        
        # 应用活动类型过滤
        if activity_type:
            activities = [a for a in activities if a.activity_type == activity_type]
        
        activities_data = []
        for activity in activities:
            activities_data.append({
                "id": activity.id,
                "name": activity.name,
                "description": activity.description,
                "activity_type": activity.activity_type,
                "business_domain": activity.business_domain,
                "vector_entity_uri": activity.vector_entity_uri
            })
        
        return {
            "total": len(activities_data),
            "activities": activities_data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取活动列表失败: {str(e)}")


@app.post("/api/v1/recommendations", response_model=ActivityRecommendationResponse)
async def recommend_activities(request: ActivityRecommendationRequest):
    """
    推荐相关业务活动
    
    Args:
        request: 推荐请求
    
    Returns:
        ActivityRecommendationResponse: 推荐结果
    """
    if not semantic_engine:
        raise HTTPException(status_code=503, detail="语义引擎服务未初始化")
    
    try:
        recommendation = semantic_engine.recommend_activities(
            activity_id=request.activity_id,
            top_k=request.top_k,
            min_similarity=request.min_similarity
        )
        
        # 转换为响应格式
        recommended_activities_data = []
        for activity in recommendation.recommended_activities:
            recommended_activities_data.append({
                "id": activity.id,
                "name": activity.name,
                "description": activity.description,
                "activity_type": activity.activity_type,
                "business_domain": activity.business_domain
            })
        
        return ActivityRecommendationResponse(
            source_activity_id=recommendation.source_activity_id,
            recommended_activities=recommended_activities_data,
            similarity_scores=recommendation.similarity_scores,
            recommendation_reason=recommendation.recommendation_reason
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推荐失败: {str(e)}")


@app.get("/api/v1/vector/sync/status", response_model=SyncStatusResponse)
async def get_sync_status(domain: Optional[str] = Query(None, description="业务领域过滤")):
    """
    获取向量同步状态
    
    Args:
        domain: 业务领域
    
    Returns:
        SyncStatusResponse: 同步状态
    """
    if not vector_sync_service:
        raise HTTPException(status_code=503, detail="向量同步服务未初始化")
    
    try:
        status = vector_sync_service.get_sync_status(domain)
        return SyncStatusResponse(**status)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取同步状态失败: {str(e)}")


@app.post("/api/v1/vector/sync", response_model=VectorSyncResponse)
async def sync_vectors(
    domain: Optional[str] = Query(None, description="业务领域过滤"),
    batch_size: int = Query(10, ge=1, le=100, description="批处理大小")
):
    """
    同步向量
    
    Args:
        domain: 业务领域
        batch_size: 批处理大小
    
    Returns:
        VectorSyncResponse: 同步结果
    """
    if not vector_sync_service:
        raise HTTPException(status_code=503, detail="向量同步服务未初始化")
    
    try:
        result = vector_sync_service.sync_vectors(domain, batch_size)
        return VectorSyncResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步向量失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)






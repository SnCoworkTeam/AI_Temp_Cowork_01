"""
知识图谱监控API路由
"""
from fastapi import APIRouter, HTTPException
from ..services.knowledge_graph_monitor import KnowledgeGraphMonitor
import logging

router = APIRouter(prefix="/api/monitor", tags=["Monitor"])
logger = logging.getLogger(__name__)


@router.get("/knowledge-graph/stats", summary="获取知识图谱统计信息")
async def get_knowledge_graph_stats():
    """
    获取统一的知识图谱统计信息
    
    返回knowledge-base、metadata-service和实体映射的统计信息
    """
    try:
        monitor = KnowledgeGraphMonitor()
        stats = await monitor.get_unified_stats()
        await monitor.close()
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))









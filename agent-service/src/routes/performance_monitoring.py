"""
意图识别性能监控API
提供性能指标查询接口
"""
from fastapi import APIRouter, Query
from typing import Optional
import logging

from ..core.intent_performance_monitor import get_performance_monitor

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/metrics")
async def get_performance_metrics():
    """获取性能指标"""
    monitor = get_performance_monitor()
    return monitor.get_metrics()


@router.get("/metrics/summary")
async def get_performance_summary():
    """获取性能摘要"""
    monitor = get_performance_monitor()
    return {
        "summary": monitor.get_summary(),
        "metrics": monitor.get_metrics()
    }


@router.get("/metrics/recent")
async def get_recent_requests(limit: int = Query(10, ge=1, le=100)):
    """获取最近的请求记录"""
    monitor = get_performance_monitor()
    return {
        "recent_requests": monitor.get_recent_requests(limit=limit)
    }


@router.post("/metrics/reset")
async def reset_metrics():
    """重置性能指标"""
    monitor = get_performance_monitor()
    monitor.reset()
    return {"message": "Metrics reset successfully"}



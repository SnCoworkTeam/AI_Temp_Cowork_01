"""
业务场景API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Optional
from pydantic import BaseModel, Field
import logging

from ..services.business_scenario_service import BusinessScenarioService
import os

router = APIRouter(prefix="/api/scenarios", tags=["Business Scenarios"])
logger = logging.getLogger(__name__)


class PurchaseOrderQueryRequest(BaseModel):
    po_number: str = Field(..., description="采购订单号")


# 创建业务场景服务实例
business_scenario_service = BusinessScenarioService(
    sap_mcp_url=os.getenv("SAP_MCP_URL", "http://sap-odata-mcp-server:8000")
)


@router.post("/purchase-order/query", summary="查询采购订单状态和关联信息")
async def query_purchase_order(
    request: PurchaseOrderQueryRequest
):
    """
    查询采购订单状态和关联信息
    
    端到端业务场景，返回：
    - 📋 订单基本信息（供应商、金额、日期）
    - 📦 收货状态（已收货数量、待收货数量）
    - 🧾 发票校验状态
    - ⚠️ 异常预警（如有）
    - 🔗 相关文档（合同、技术规格书）
    
    Args:
        request: 采购订单查询请求
    
    Returns:
        结构化结果
    """
    try:
        result = await business_scenario_service.handle_purchase_order_query(
            request.po_number
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Failed to query purchase order: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.on_event("shutdown")
async def shutdown_event():
    """关闭时清理资源"""
    await business_scenario_service.close()


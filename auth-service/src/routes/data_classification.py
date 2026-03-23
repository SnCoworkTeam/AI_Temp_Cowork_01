"""
数据分类API路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..dependencies.database import get_db
from ..services.data_classifier import DataClassifier
from shared_libs.luminaos_common.common.logger import setup_logger

router = APIRouter(prefix="/api/data", tags=["Data Classification"])
logger = setup_logger(__name__)


def get_data_classifier(db: Session = Depends(get_db)) -> DataClassifier:
    """获取数据分类器"""
    return DataClassifier(db)


@router.post("/classification", summary="分类数据资产")
async def classify_data_assets(
    classifier: DataClassifier = Depends(get_data_classifier)
):
    """
    从metadata-service获取数据资产，基于敏感度和业务价值分类
    
    Returns:
        分类结果和分类图谱
    """
    try:
        result = await classifier.classify_data_assets()
        return result
    except Exception as e:
        logger.error(f"Failed to classify data assets: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await classifier.close()


@router.get("/classification", summary="获取数据分类图谱")
async def get_classification_graph(
    classifier: DataClassifier = Depends(get_data_classifier)
):
    """获取数据分类图谱"""
    try:
        result = await classifier.classify_data_assets(persist=False)
        return {
            "success": True,
            "classification_graph": result.get("classification_graph", {})
        }
    except Exception as e:
        logger.error(f"Failed to get classification graph: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await classifier.close()


@router.get("/classification/history/{asset_id}", summary="获取资产分类历史")
async def get_classification_history(
    asset_id: int,
    limit: int = 10,
    classifier: DataClassifier = Depends(get_data_classifier)
):
    """获取指定资产的分类历史"""
    try:
        history = classifier.get_classification_history(asset_id, limit)
        return {
            "success": True,
            "asset_id": asset_id,
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        logger.error(f"Failed to get classification history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await classifier.close()


@router.get("/classification/latest", summary="获取最新分类结果")
async def get_latest_classifications(
    sensitivity: Optional[str] = None,
    business_value: Optional[str] = None,
    limit: int = 100,
    classifier: DataClassifier = Depends(get_data_classifier)
):
    """获取最新分类结果（支持过滤）"""
    try:
        results = classifier.get_latest_classifications(sensitivity, business_value, limit)
        return {
            "success": True,
            "results": results,
            "count": len(results),
            "filters": {
                "sensitivity": sensitivity,
                "business_value": business_value
            }
        }
    except Exception as e:
        logger.error(f"Failed to get latest classifications: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await classifier.close()


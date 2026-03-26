"""
BPMN相关API路由
支持BPMN文件上传、解析、验证和转换
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import Optional
import logging

from ..core.bpmn_converter import BPMNConverter
from ..core.bpmn_validator import BPMNValidator
from ..models.workflow_models import WorkflowDefinition
from shared_libs.luminaos_common.common.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.post("/bpmn/parse", response_model=WorkflowDefinition, tags=["BPMN"])
async def parse_bpmn(bpmn_xml: str):
    """
    解析BPMN XML文件
    
    Args:
        bpmn_xml: BPMN XML字符串
    
    Returns:
        工作流定义
    """
    try:
        converter = BPMNConverter()
        workflow_def = converter.convert_from_xml(bpmn_xml, validate=True)
        return workflow_def
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to parse BPMN: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to parse BPMN: {str(e)}")


@router.post("/bpmn/upload", response_model=WorkflowDefinition, tags=["BPMN"])
async def upload_bpmn(file: UploadFile = File(...)):
    """
    上传并解析BPMN文件
    
    Args:
        file: BPMN文件
    
    Returns:
        工作流定义
    """
    try:
        # 读取文件内容
        content = await file.read()
        bpmn_xml = content.decode('utf-8')
        
        # 解析
        converter = BPMNConverter()
        workflow_def = converter.convert_from_xml(bpmn_xml, validate=True)
        
        return workflow_def
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to upload and parse BPMN: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to upload BPMN: {str(e)}")


@router.post("/bpmn/validate", tags=["BPMN"])
async def validate_bpmn(bpmn_xml: str):
    """
    验证BPMN文件
    
    Args:
        bpmn_xml: BPMN XML字符串
    
    Returns:
        验证报告
    """
    try:
        converter = BPMNConverter()
        workflow_def = converter.convert_from_xml(bpmn_xml, validate=True)
        report = converter.get_validation_report()
        return report
    except ValueError as e:
        # 即使验证失败，也返回报告
        converter = BPMNConverter()
        try:
            workflow_def = converter.convert_from_xml(bpmn_xml, validate=False)
            converter.validator.validate(workflow_def)
            report = converter.get_validation_report()
            return report
        except:
            return {
                "valid": False,
                "errors": [str(e)],
                "warnings": [],
                "error_count": 1,
                "warning_count": 0
            }
    except Exception as e:
        logger.error(f"Failed to validate BPMN: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to validate BPMN: {str(e)}")





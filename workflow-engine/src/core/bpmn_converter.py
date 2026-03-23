"""
BPMN到工作流定义的转换器
将BPMN流程转换为LuminaOS工作流定义格式
"""
from typing import Dict, Any, List
from .bpmn_parser import BPMNParser
from .bpmn_validator import BPMNValidator
from ..models.workflow_models import WorkflowDefinition
import logging

logger = logging.getLogger(__name__)


class BPMNConverter:
    """BPMN转换器"""
    
    def __init__(self):
        self.parser = BPMNParser()
        self.validator = BPMNValidator()
    
    def convert_from_xml(self, bpmn_xml: str, validate: bool = True) -> WorkflowDefinition:
        """
        从BPMN XML转换为工作流定义
        
        Args:
            bpmn_xml: BPMN XML字符串
            validate: 是否进行验证
        
        Returns:
            WorkflowDefinition对象
        
        Raises:
            ValueError: 如果BPMN无效或验证失败
        """
        # 解析BPMN
        workflow_def = self.parser.parse(bpmn_xml)
        
        # 验证（如果需要）
        if validate:
            if not self.validator.validate(workflow_def):
                errors = self.validator.get_errors()
                raise ValueError(f"BPMN validation failed: {', '.join(errors)}")
            
            warnings = self.validator.get_warnings()
            if warnings:
                logger.warning(f"BPMN validation warnings: {', '.join(warnings)}")
        
        return workflow_def
    
    def convert_from_file(self, file_path: str, validate: bool = True) -> WorkflowDefinition:
        """
        从BPMN文件转换为工作流定义
        
        Args:
            file_path: BPMN文件路径
            validate: 是否进行验证
        
        Returns:
            WorkflowDefinition对象
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            bpmn_xml = f.read()
        
        return self.convert_from_xml(bpmn_xml, validate)
    
    def get_validation_report(self) -> Dict[str, Any]:
        """获取验证报告"""
        return self.validator.get_validation_report()





"""
SAP业务流程分析器
分析SAP业务流程和数据血缘关系
"""
import logging
from typing import List, Dict, Any, Optional

from ..models.sap_metadata_models import (
    SAPBusinessProcess,
    SAPBusinessDomain
)

logger = logging.getLogger(__name__)


class SAPBusinessProcessAnalyzer:
    """SAP业务流程分析器"""
    
    def __init__(self):
        """初始化业务流程分析器"""
        self.process_templates = self._init_process_templates()
    
    def _init_process_templates(self) -> Dict[str, Dict[str, Any]]:
        """初始化业务流程模板"""
        return {
            "order_to_cash": {
                "name": "order_to_cash",
                "display_name": "订单到现金流程",
                "description": "从销售订单创建到收款完成的完整业务流程",
                "domain": SAPBusinessDomain.SALES,
                "steps": [
                    {
                        "step": 1,
                        "description": "创建销售订单",
                        "sap_transaction": "VA01",
                        "data_objects": ["VBAK", "VBAP", "KNA1", "MARA"],
                        "output": "销售订单"
                    },
                    {
                        "step": 2,
                        "description": "创建交货单",
                        "sap_transaction": "VL01N",
                        "data_objects": ["LIKP", "LIPS", "VBAK", "MARD"],
                        "output": "交货单"
                    },
                    {
                        "step": 3,
                        "description": "过账发货",
                        "sap_transaction": "VL02N",
                        "data_objects": ["MSEG", "BKPF", "LIKP"],
                        "output": "物料凭证、会计凭证"
                    },
                    {
                        "step": 4,
                        "description": "创建发票",
                        "sap_transaction": "VF01",
                        "data_objects": ["VBRK", "VBRP", "LIKP"],
                        "output": "发票"
                    },
                    {
                        "step": 5,
                        "description": "收款过账",
                        "sap_transaction": "F-28",
                        "data_objects": ["BKPF", "BSAD", "BSID"],
                        "output": "会计凭证"
                    }
                ],
                "involved_tables": ["VBAK", "VBAP", "LIKP", "LIPS", "VBRK", "VBRP", "KNA1", "MARA"],
                "sap_transactions": ["VA01", "VL01N", "VL02N", "VF01", "F-28"]
            },
            "procure_to_pay": {
                "name": "procure_to_pay",
                "display_name": "采购到付款流程",
                "description": "从采购需求到付款完成的完整业务流程",
                "domain": SAPBusinessDomain.MATERIAL_MANAGEMENT,
                "steps": [
                    {
                        "step": 1,
                        "description": "创建采购申请",
                        "sap_transaction": "ME51N",
                        "data_objects": ["EBAN", "MARA", "LFA1"],
                        "output": "采购申请"
                    },
                    {
                        "step": 2,
                        "description": "创建采购订单",
                        "sap_transaction": "ME21N",
                        "data_objects": ["EKKO", "EKPO", "EBAN", "LFA1"],
                        "output": "采购订单"
                    },
                    {
                        "step": 3,
                        "description": "收货",
                        "sap_transaction": "MIGO",
                        "data_objects": ["MSEG", "EKBE", "MARD"],
                        "output": "物料凭证"
                    },
                    {
                        "step": 4,
                        "description": "发票校验",
                        "sap_transaction": "MIRO",
                        "data_objects": ["RSEG", "BKPF", "EKKO"],
                        "output": "发票凭证"
                    },
                    {
                        "step": 5,
                        "description": "付款",
                        "sap_transaction": "F-53",
                        "data_objects": ["BKPF", "BSAK", "BSIK"],
                        "output": "会计凭证"
                    }
                ],
                "involved_tables": ["EBAN", "EKKO", "EKPO", "MSEG", "RSEG", "LFA1", "MARA"],
                "sap_transactions": ["ME51N", "ME21N", "MIGO", "MIRO", "F-53"]
            },
            "record_to_report": {
                "name": "record_to_report",
                "display_name": "记录到报告流程",
                "description": "从业务交易记录到财务报表的完整流程",
                "domain": SAPBusinessDomain.FINANCE,
                "steps": [
                    {
                        "step": 1,
                        "description": "业务交易过账",
                        "sap_transaction": "FB01",
                        "data_objects": ["BKPF", "BSEG"],
                        "output": "会计凭证"
                    },
                    {
                        "step": 2,
                        "description": "期末调整",
                        "sap_transaction": "F-02",
                        "data_objects": ["BKPF", "BSEG"],
                        "output": "调整凭证"
                    },
                    {
                        "step": 3,
                        "description": "成本中心分配",
                        "sap_transaction": "KB11N",
                        "data_objects": ["COEP", "CSKS"],
                        "output": "成本凭证"
                    },
                    {
                        "step": 4,
                        "description": "财务报表生成",
                        "sap_transaction": "F.01",
                        "data_objects": ["GLT0", "BSIS", "BSAS"],
                        "output": "财务报表"
                    }
                ],
                "involved_tables": ["BKPF", "BSEG", "COEP", "CSKS", "GLT0"],
                "sap_transactions": ["FB01", "F-02", "KB11N", "F.01"]
            }
        }
    
    async def analyze_processes(
        self,
        assets: List[Dict[str, Any]]
    ) -> List[SAPBusinessProcess]:
        """
        分析业务流程
        
        Args:
            assets: 数据资产列表
            
        Returns:
            业务流程列表
        """
        processes = []
        
        # 获取所有表名
        table_names = {asset.get('sap_table_name') for asset in assets if asset.get('sap_table_name')}
        
        # 基于模板和实际数据资产匹配流程
        for process_name, template in self.process_templates.items():
            # 检查流程涉及的表是否存在
            involved_tables = template.get('involved_tables', [])
            existing_tables = [t for t in involved_tables if t in table_names]
            
            if len(existing_tables) >= len(involved_tables) * 0.5:  # 至少50%的表存在
                process = SAPBusinessProcess(
                    name=template['name'],
                    display_name=template['display_name'],
                    description=template['description'],
                    domain=template['domain'],
                    steps=template['steps'],
                    involved_data_assets=[
                        f"sap_table_{t.lower()}" for t in existing_tables
                    ],
                    sap_transactions=template.get('sap_transactions', []),
                    metadata={
                        "coverage": len(existing_tables) / len(involved_tables),
                        "missing_tables": [t for t in involved_tables if t not in table_names],
                        "analysis_method": "template_matching"
                    }
                )
                processes.append(process)
        
        logger.info(f"Analyzed {len(processes)} business processes")
        return processes
    
    async def analyze_data_lineage(
        self,
        assets: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """
        分析数据血缘关系
        
        Args:
            assets: 数据资产列表
            
        Returns:
            数据血缘关系映射 {table_name: [downstream_tables]}
        """
        lineage = {}
        
        for asset in assets:
            table_name = asset.get('sap_table_name')
            if not table_name:
                continue
            
            schema_info = asset.get('schema_info', {})
            foreign_keys = schema_info.get('foreign_keys', [])
            
            # 收集下游表（通过外键关系）
            downstream = []
            for fk in foreign_keys:
                referred_table = fk.get('referred_table')
                if referred_table:
                    downstream.append(referred_table)
            
            if downstream:
                lineage[table_name] = downstream
        
        return lineage



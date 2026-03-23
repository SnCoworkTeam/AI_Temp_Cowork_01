"""
SAP模块推断器
基于服务名称和实体名称推断SAP模块和子模块
"""
import logging
from typing import Dict, Tuple, Optional
import re

logger = logging.getLogger(__name__)


class SAPModuleInference:
    """SAP模块推断器"""
    
    def __init__(self):
        """初始化模块推断器，定义模块模式"""
        self.module_patterns = {
            "FI": {
                "patterns": [
                    "GLACCOUNT", "JOURNALENTRY", "ACCOUNTDOCUMENT", 
                    "BANK", "FINANCIAL", "ACCOUNTING", "LEDGER",
                    "TRIALBALANCE", "BALANCESHEET", "INCOMESTMT",
                    "ACCOUNTRECEIVABLE", "ACCOUNTSPAYABLE", "ASSET"
                ],
                "sub_modules": {
                    "GeneralLedger": ["GLACCOUNT", "JOURNALENTRY", "LEDGER", "TRIALBALANCE"],
                    "Banking": ["BANK", "CASH", "PAYMENT"],
                    "AccountsReceivable": ["RECEIVABLE", "CUSTOMER", "AR"],
                    "AccountsPayable": ["PAYABLE", "VENDOR", "AP"],
                    "AssetAccounting": ["ASSET", "FIXEDASSET", "DEPRECIATION"]
                },
                "display_name": "财务会计"
            },
            "CO": {
                "patterns": [
                    "COSTCENTER", "PROFITCENTER", "WBS", "INTERNALORDER",
                    "COST", "PROFIT", "COSTOBJECT", "COSTELEMENT"
                ],
                "sub_modules": {
                    "CostAccounting": ["COSTCENTER", "INTERNALORDER", "COSTELEMENT"],
                    "ProfitAccounting": ["PROFITCENTER"],
                    "ProjectAccounting": ["WBS", "PROJECT"]
                },
                "display_name": "管理会计"
            },
            "SD": {
                "patterns": [
                    "SALES", "ORDER", "DELIVERY", "INVOICE", "CUSTOMER",
                    "BILLING", "PRICING", "QUOTATION", "SHIPMENT"
                ],
                "sub_modules": {
                    "SalesOrder": ["SALES", "ORDER", "QUOTATION"],
                    "Delivery": ["DELIVERY", "SHIPMENT"],
                    "Billing": ["INVOICE", "BILLING"]
                },
                "display_name": "销售与分销"
            },
            "MM": {
                "patterns": [
                    "MATERIAL", "PURCHASE", "INVENTORY", "VENDOR", "SUPPLIER",
                    "PROCUREMENT", "STOCK", "WAREHOUSE", "PURCHASING"
                ],
                "sub_modules": {
                    "MaterialManagement": ["MATERIAL", "PRODUCT"],
                    "Procurement": ["PURCHASE", "PROCUREMENT", "VENDOR", "SUPPLIER"],
                    "InventoryManagement": ["INVENTORY", "STOCK", "WAREHOUSE"]
                },
                "display_name": "物料管理"
            },
            "PP": {
                "patterns": [
                    "PRODUCTION", "PLANNING", "WORKCENTER", "ROUTING",
                    "BOM", "OPERATION", "CAPACITY", "MANUFACTURING"
                ],
                "sub_modules": {
                    "ProductionPlanning": ["PLANNING", "BOM"],
                    "ProductionExecution": ["PRODUCTION", "WORKCENTER", "ROUTING", "MANUFACTURING"]
                },
                "display_name": "生产计划"
            },
            "HR": {
                "patterns": [
                    "EMPLOYEE", "PAYROLL", "ORGANIZATION", "PERSONNEL",
                    "TIME", "ATTENDANCE", "BENEFIT", "HUMANRESOURCE"
                ],
                "sub_modules": {
                    "PersonnelManagement": ["EMPLOYEE", "PERSONNEL", "HUMANRESOURCE"],
                    "Payroll": ["PAYROLL", "SALARY"],
                    "TimeManagement": ["TIME", "ATTENDANCE"]
                },
                "display_name": "人力资源管理"
            }
        }
    
    def infer_module_with_confidence(
        self,
        service_name: str,
        entity_name: Optional[str] = None
    ) -> Tuple[str, str, float]:
        """
        推断模块和子模块，返回置信度
        
        Args:
            service_name: OData服务名称
            entity_name: 实体名称（可选）
            
        Returns:
            (module, sub_module, confidence) 元组
        """
        service_upper = service_name.upper()
        entity_upper = (entity_name or "").upper()
        combined_text = f"{service_upper} {entity_upper}"
        
        best_match = ("OTHER", "General", 0.0)
        
        for module_code, config in self.module_patterns.items():
            # 检查服务名称模式
            module_score = 0.0
            matched_pattern = None
            
            for pattern in config["patterns"]:
                if pattern in service_upper:
                    # 计算匹配度（基于模式长度和位置）
                    pattern_length = len(pattern)
                    pattern_pos = service_upper.find(pattern)
                    
                    # 模式在开头或中间位置得分更高
                    if pattern_pos == 0:
                        score = (pattern_length / len(service_upper)) * 1.0
                    elif pattern_pos < len(service_upper) / 2:
                        score = (pattern_length / len(service_upper)) * 0.8
                    else:
                        score = (pattern_length / len(service_upper)) * 0.6
                    
                    if score > module_score:
                        module_score = score
                        matched_pattern = pattern
            
            # 检查实体名称模式（如果提供）
            if entity_upper:
                for pattern in config["patterns"]:
                    if pattern in entity_upper:
                        entity_score = (len(pattern) / len(entity_upper)) * 0.3
                        module_score += entity_score
            
            # 推断子模块
            sub_module = "General"
            sub_module_score = 0.0
            
            if module_score > 0:
                for sub_module_name, sub_patterns in config["sub_modules"].items():
                    for sub_pattern in sub_patterns:
                        if sub_pattern in combined_text:
                            sub_score = (len(sub_pattern) / len(combined_text)) * 0.2
                            if sub_score > sub_module_score:
                                sub_module_score = sub_score
                                sub_module = sub_module_name
                                break
            
            # 计算总置信度
            total_confidence = min(module_score + sub_module_score, 1.0)
            
            if total_confidence > best_match[2]:
                best_match = (module_code, sub_module, total_confidence)
        
        # 如果置信度太低，返回OTHER
        if best_match[2] < 0.3:
            return ("OTHER", "General", 0.1)
        
        return best_match
    
    def infer_module(self, service_name: str, entity_name: Optional[str] = None) -> str:
        """
        推断模块（简化版）
        
        Args:
            service_name: OData服务名称
            entity_name: 实体名称（可选）
            
        Returns:
            模块代码（FI, CO, SD等）
        """
        module, _, _ = self.infer_module_with_confidence(service_name, entity_name)
        return module
    
    def infer_sub_module(self, service_name: str, entity_name: Optional[str] = None) -> str:
        """
        推断子模块（简化版）
        
        Args:
            service_name: OData服务名称
            entity_name: 实体名称（可选）
            
        Returns:
            子模块名称
        """
        _, sub_module, _ = self.infer_module_with_confidence(service_name, entity_name)
        return sub_module
    
    def get_module_display_name(self, module_code: str) -> str:
        """
        获取模块显示名称
        
        Args:
            module_code: 模块代码
            
        Returns:
            模块显示名称
        """
        if module_code in self.module_patterns:
            return self.module_patterns[module_code]["display_name"]
        return module_code


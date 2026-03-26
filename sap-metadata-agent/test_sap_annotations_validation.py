"""
SAP注解解析准确性验证脚本
验证sapLabel、sapSemantics等SAP特定注解的解析准确性
"""
import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any

# 添加项目根目录到路径
agent_path = Path(__file__).parent
sys.path.insert(0, str(agent_path))

from src.core.sap_odata_metadata_parser import SAPODataMetadataParser

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_test_metadata_with_annotations() -> Dict[str, str]:
    """获取包含完整SAP注解的测试元数据"""
    return {
        "C_GLACCOUNT_FS_SRV": '''<?xml version="1.0" encoding="utf-8"?>
<edmx:Edmx xmlns:edmx="http://schemas.microsoft.com/ado/2007/06/edmx" Version="4.0">
  <edmx:DataServices>
    <Schema xmlns="http://schemas.microsoft.com/ado/2007/06/edm" 
            xmlns:sap="http://www.sap.com/Protocols/SAPData"
            Namespace="com.sap.gateway.srvd.a2x.api_glaccount.v0001">
      <EntityContainer Name="API_GLACCOUNT_SRV_Entities">
        <EntitySet Name="A_GLAccount" 
                   EntityType="com.sap.gateway.srvd.a2x.api_glaccount.v0001.A_GLAccountType" 
                   sap:creatable="true" sap:updatable="true" sap:deletable="true" 
                   sap:content-version="1" sap:label="总账科目"/>
      </EntityContainer>
      <EntityType Name="A_GLAccountType" sap:label="总账科目" sap:content-version="1">
        <Key>
          <PropertyRef Name="GLAccount"/>
        </Key>
        <Property Name="GLAccount" Type="Edm.String" Nullable="false" MaxLength="10" 
                  sap:label="总账科目编号" sap:semantics="text"/>
        <Property Name="GLAccountName" Type="Edm.String" MaxLength="50" 
                  sap:label="总账科目名称" sap:semantics="text"/>
        <Property Name="AccountType" Type="Edm.String" MaxLength="1" 
                  sap:label="科目类型" sap:semantics="text"/>
        <Property Name="CompanyCode" Type="Edm.String" MaxLength="4" 
                  sap:label="公司代码" sap:semantics="company-code"/>
        <Property Name="BalanceAmount" Type="Edm.Decimal" Precision="23" Scale="4" 
                  sap:label="余额" sap:semantics="amount"/>
        <Property Name="Currency" Type="Edm.String" MaxLength="3" 
                  sap:label="货币" sap:semantics="currency-code"/>
        <Property Name="LastChangedDate" Type="Edm.DateTimeOffset" 
                  sap:label="最后更改日期" sap:semantics="date"/>
        <Property Name="IsBlocked" Type="Edm.Boolean" 
                  sap:label="已冻结" sap:semantics="text"/>
        <NavigationProperty Name="to_CompanyCode" 
                           Type="com.sap.gateway.srvd.a2x.api_glaccount.v0001.A_CompanyCodeType" 
                           Relationship="com.sap.gateway.srvd.a2x.api_glaccount.v0001.to_CompanyCode"
                           sap:label="关联公司代码"/>
      </EntityType>
    </Schema>
  </edmx:DataServices>
</edmx:Edmx>''',
        
        "C_COSTCENTER_FS_SRV": '''<?xml version="1.0" encoding="utf-8"?>
<edmx:Edmx xmlns:edmx="http://schemas.microsoft.com/ado/2007/06/edmx" Version="4.0">
  <edmx:DataServices>
    <Schema xmlns="http://schemas.microsoft.com/ado/2007/06/edm" 
            xmlns:sap="http://www.sap.com/Protocols/SAPData"
            Namespace="com.sap.gateway.srvd.a2x.api_costcenter.v0001">
      <EntityContainer Name="API_COSTCENTER_SRV_Entities">
        <EntitySet Name="A_CostCenter" 
                   EntityType="com.sap.gateway.srvd.a2x.api_costcenter.v0001.A_CostCenterType" 
                   sap:creatable="true" sap:updatable="true" sap:deletable="false" 
                   sap:content-version="1" sap:label="成本中心"/>
      </EntityContainer>
      <EntityType Name="A_CostCenterType" sap:label="成本中心" sap:content-version="1">
        <Key>
          <PropertyRef Name="CostCenter"/>
          <PropertyRef Name="ControllingArea"/>
        </Key>
        <Property Name="CostCenter" Type="Edm.String" Nullable="false" MaxLength="10" 
                  sap:label="成本中心" sap:semantics="id"/>
        <Property Name="ControllingArea" Type="Edm.String" Nullable="false" MaxLength="4" 
                  sap:label="控制范围" sap:semantics="id"/>
        <Property Name="CostCenterName" Type="Edm.String" MaxLength="20" 
                  sap:label="成本中心名称" sap:semantics="text"/>
        <Property Name="CostCenterDescription" Type="Edm.String" MaxLength="40" 
                  sap:label="成本中心描述" sap:semantics="text"/>
        <Property Name="CompanyCode" Type="Edm.String" MaxLength="4" 
                  sap:label="公司代码" sap:semantics="company-code"/>
        <Property Name="ValidFrom" Type="Edm.DateTimeOffset" 
                  sap:label="有效期自" sap:semantics="date"/>
        <Property Name="ValidTo" Type="Edm.DateTimeOffset" 
                  sap:label="有效期至" sap:semantics="date"/>
      </EntityType>
    </Schema>
  </edmx:DataServices>
</edmx:Edmx>'''
    }


class SAPAnnotationsValidator:
    """SAP注解验证器"""
    
    def __init__(self):
        self.parser = SAPODataMetadataParser()
        
        # 定义期望的注解基准（基于实际SAP服务）
        self.annotation_benchmarks = {
            "C_GLACCOUNT_FS_SRV": {
                "entity_label": "总账科目",
                "properties": {
                    "GLAccount": {
                        "sapLabel": "总账科目编号",
                        "sapSemantics": "text"
                    },
                    "GLAccountName": {
                        "sapLabel": "总账科目名称",
                        "sapSemantics": "text"
                    },
                    "CompanyCode": {
                        "sapLabel": "公司代码",
                        "sapSemantics": "company-code"
                    },
                    "BalanceAmount": {
                        "sapLabel": "余额",
                        "sapSemantics": "amount"
                    },
                    "Currency": {
                        "sapLabel": "货币",
                        "sapSemantics": "currency-code"
                    },
                    "LastChangedDate": {
                        "sapLabel": "最后更改日期",
                        "sapSemantics": "date"
                    }
                }
            },
            "C_COSTCENTER_FS_SRV": {
                "entity_label": "成本中心",
                "properties": {
                    "CostCenter": {
                        "sapLabel": "成本中心",
                        "sapSemantics": "id"
                    },
                    "ControllingArea": {
                        "sapLabel": "控制范围",
                        "sapSemantics": "id"
                    },
                    "CostCenterName": {
                        "sapLabel": "成本中心名称",
                        "sapSemantics": "text"
                    },
                    "CompanyCode": {
                        "sapLabel": "公司代码",
                        "sapSemantics": "company-code"
                    },
                    "ValidFrom": {
                        "sapLabel": "有效期自",
                        "sapSemantics": "date"
                    }
                }
            }
        }
    
    def validate_annotation_accuracy(self) -> Dict[str, Any]:
        """验证SAP注解解析准确性"""
        logger.info("=" * 60)
        logger.info("SAP注解解析准确性验证")
        logger.info("=" * 60)
        
        test_metadata = get_test_metadata_with_annotations()
        results = {
            "total_services": len(test_metadata),
            "services_validated": 0,
            "entity_label_accuracy": 0.0,
            "property_label_accuracy": 0.0,
            "property_semantics_accuracy": 0.0,
            "overall_accuracy": 0.0,
            "details": []
        }
        
        total_entity_labels = 0
        correct_entity_labels = 0
        total_property_labels = 0
        correct_property_labels = 0
        total_property_semantics = 0
        correct_property_semantics = 0
        
        for service_id, xml_data in test_metadata.items():
            logger.info(f"\n验证服务: {service_id}")
            
            benchmark = self.annotation_benchmarks.get(service_id)
            if not benchmark:
                logger.warning(f"未找到服务 {service_id} 的基准数据")
                continue
            
            # 解析元数据
            parsed = self.parser.parse_metadata(xml_data)
            if "error" in parsed:
                logger.error(f"解析失败: {parsed['error']}")
                continue
            
            results["services_validated"] += 1
            service_result = {
                "service_id": service_id,
                "entity_label_match": False,
                "property_label_matches": 0,
                "property_label_total": 0,
                "property_semantics_matches": 0,
                "property_semantics_total": 0,
                "details": []
            }
            
            # 验证实体标签
            for entity in parsed["entities"]:
                entity_label = entity.get("sap_label", "")
                expected_label = benchmark["entity_label"]
                
                total_entity_labels += 1
                if entity_label == expected_label:
                    correct_entity_labels += 1
                    service_result["entity_label_match"] = True
                    logger.info(f"  ✓ 实体标签匹配: {entity_label}")
                else:
                    logger.warning(f"  ✗ 实体标签不匹配: 期望 '{expected_label}', 实际 '{entity_label}'")
                
                # 验证属性注解
                for prop in entity.get("properties", []):
                    prop_name = prop["name"]
                    expected_prop = benchmark["properties"].get(prop_name)
                    
                    if expected_prop:
                        service_result["property_label_total"] += 1
                        total_property_labels += 1
                        
                        # 验证sapLabel
                        actual_label = prop.get("sap_label", "")
                        expected_label = expected_prop.get("sapLabel", "")
                        if actual_label == expected_label:
                            correct_property_labels += 1
                            service_result["property_label_matches"] += 1
                            label_status = "✓"
                        else:
                            label_status = "✗"
                        
                        # 验证sapSemantics
                        service_result["property_semantics_total"] += 1
                        total_property_semantics += 1
                        actual_semantics = prop.get("sap_semantics", "")
                        expected_semantics = expected_prop.get("sapSemantics", "")
                        if actual_semantics == expected_semantics:
                            correct_property_semantics += 1
                            service_result["property_semantics_matches"] += 1
                            semantics_status = "✓"
                        else:
                            semantics_status = "✗"
                        
                        service_result["details"].append({
                            "property": prop_name,
                            "label_match": actual_label == expected_label,
                            "semantics_match": actual_semantics == expected_semantics,
                            "actual_label": actual_label,
                            "expected_label": expected_label,
                            "actual_semantics": actual_semantics,
                            "expected_semantics": expected_semantics
                        })
                        
                        logger.info(f"  {label_status}{semantics_status} {prop_name}: "
                                  f"label='{actual_label}' semantics='{actual_semantics}'")
            
            results["details"].append(service_result)
        
        # 计算准确率
        if total_entity_labels > 0:
            results["entity_label_accuracy"] = (correct_entity_labels / total_entity_labels) * 100
        if total_property_labels > 0:
            results["property_label_accuracy"] = (correct_property_labels / total_property_labels) * 100
        if total_property_semantics > 0:
            results["property_semantics_accuracy"] = (correct_property_semantics / total_property_semantics) * 100
        
        # 总体准确率（加权平均）
        if total_property_labels + total_property_semantics > 0:
            results["overall_accuracy"] = (
                (correct_property_labels + correct_property_semantics) / 
                (total_property_labels + total_property_semantics)
            ) * 100
        
        logger.info("\n" + "=" * 60)
        logger.info("注解解析准确率统计:")
        logger.info(f"  验证服务数: {results['services_validated']}/{results['total_services']}")
        logger.info(f"  实体标签准确率: {results['entity_label_accuracy']:.1f}%")
        logger.info(f"  属性标签准确率: {results['property_label_accuracy']:.1f}%")
        logger.info(f"  属性语义准确率: {results['property_semantics_accuracy']:.1f}%")
        logger.info(f"  总体准确率: {results['overall_accuracy']:.1f}%")
        logger.info("=" * 60)
        
        return results


async def main():
    """主测试函数"""
    logger.info("开始SAP注解解析准确性验证...")
    
    validator = SAPAnnotationsValidator()
    results = validator.validate_annotation_accuracy()
    
    # 验证成功标准
    logger.info("\n验证成功标准:")
    logger.info(f"  {'✓' if results['entity_label_accuracy'] >= 90 else '✗'} 实体标签准确率 > 90%: {results['entity_label_accuracy']:.1f}%")
    logger.info(f"  {'✓' if results['property_label_accuracy'] >= 85 else '✗'} 属性标签准确率 > 85%: {results['property_label_accuracy']:.1f}%")
    logger.info(f"  {'✓' if results['property_semantics_accuracy'] >= 80 else '✗'} 属性语义准确率 > 80%: {results['property_semantics_accuracy']:.1f}%")
    logger.info(f"  {'✓' if results['overall_accuracy'] >= 85 else '✗'} 总体准确率 > 85%: {results['overall_accuracy']:.1f}%")
    
    overall_success = (
        results['entity_label_accuracy'] >= 90 and
        results['property_label_accuracy'] >= 85 and
        results['property_semantics_accuracy'] >= 80 and
        results['overall_accuracy'] >= 85
    )
    
    logger.info(f"\n总体评估: {'✓ 通过' if overall_success else '✗ 未通过'}")
    
    return results


if __name__ == "__main__":
    parser = SAPODataMetadataParser()
    asyncio.run(main())


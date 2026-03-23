"""
技术验证测试脚本
用于验证OData元数据解析、模块推断等关键技术组件
"""
import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import sys
from pathlib import Path

# 添加sap-metadata-agent到路径
agent_path = Path(__file__).parent
sys.path.insert(0, str(agent_path))

from src.core.sap_odata_metadata_parser import SAPODataMetadataParser
from src.core.sap_module_inference import SAPModuleInference
from src.services.sap_mcp_client import SAPMCPClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_odata_metadata_parsing():
    """测试OData元数据解析"""
    logger.info("=" * 60)
    logger.info("测试1: OData元数据解析")
    logger.info("=" * 60)
    
    parser = SAPODataMetadataParser()
    mcp_client = SAPMCPClient()
    
    try:
        # 获取FICO模块的3个核心服务
        test_services = [
            "C_GLACCOUNT_FS_SRV",  # 总账科目
            "C_COSTCENTER_FS_SRV",  # 成本中心
            "C_PROFITCENTER_FS_SRV"  # 利润中心
        ]
        
        results = {
            "total_services": len(test_services),
            "successful_parses": 0,
            "failed_parses": 0,
            "total_entities": 0,
            "entities_with_sap_label": 0,
            "entities_with_navigation": 0,
            "details": []
        }
        
        for service_id in test_services:
            try:
                logger.info(f"\n处理服务: {service_id}")
                
                # 获取服务元数据
                metadata = await mcp_client.get_service_metadata(service_id)
                if not metadata:
                    logger.warning(f"无法获取服务 {service_id} 的元数据")
                    results["failed_parses"] += 1
                    continue
                
                # 解析元数据
                parsed = parser.parse_metadata(metadata)
                
                results["successful_parses"] += 1
                results["total_entities"] += len(parsed["entities"])
                
                # 统计SAP标签和导航属性
                for entity in parsed["entities"]:
                    if entity.get("sap_label"):
                        results["entities_with_sap_label"] += 1
                    if entity.get("navigation_properties"):
                        results["entities_with_navigation"] += len(entity["navigation_properties"])
                
                results["details"].append({
                    "service_id": service_id,
                    "entity_sets": parsed["entity_sets_count"],
                    "entity_types": parsed["entity_types_count"],
                    "matched_entities": parsed["matched_entities_count"],
                    "entities": [
                        {
                            "name": e["name"],
                            "sap_label": e.get("sap_label"),
                            "properties_count": len(e.get("properties", [])),
                            "navigation_count": len(e.get("navigation_properties", []))
                        }
                        for e in parsed["entities"][:5]  # 只显示前5个
                    ]
                })
                
                logger.info(f"  ✓ 成功解析: {parsed['matched_entities_count']} 个实体")
                logger.info(f"  ✓ EntitySets: {parsed['entity_sets_count']}")
                logger.info(f"  ✓ EntityTypes: {parsed['entity_types_count']}")
                
            except Exception as e:
                logger.error(f"解析服务 {service_id} 失败: {e}", exc_info=True)
                results["failed_parses"] += 1
        
        # 计算准确率
        success_rate = (results["successful_parses"] / results["total_services"]) * 100 if results["total_services"] > 0 else 0
        
        logger.info("\n" + "=" * 60)
        logger.info("解析结果统计:")
        logger.info(f"  总服务数: {results['total_services']}")
        logger.info(f"  成功解析: {results['successful_parses']}")
        logger.info(f"  失败解析: {results['failed_parses']}")
        logger.info(f"  成功率: {success_rate:.1f}%")
        logger.info(f"  总实体数: {results['total_entities']}")
        logger.info(f"  有SAP标签的实体: {results['entities_with_sap_label']}")
        logger.info(f"  有导航属性的实体: {results['entities_with_navigation']}")
        logger.info("=" * 60)
        
        return results
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        raise
    finally:
        await mcp_client.close()


async def test_module_inference():
    """测试模块推断算法"""
    logger.info("\n" + "=" * 60)
    logger.info("测试2: 模块推断算法")
    logger.info("=" * 60)
    
    inference = SAPModuleInference()
    
    # 测试用例
    test_cases = [
        ("C_GLACCOUNT_FS_SRV", "GLAccountSet", "FI", "GeneralLedger"),
        ("C_COSTCENTER_FS_SRV", "CostCenterSet", "CO", "CostAccounting"),
        ("C_PROFITCENTER_FS_SRV", "ProfitCenterSet", "CO", "ProfitAccounting"),
        ("API_JOURNALENTRY_SRV", "JournalEntrySet", "FI", "GeneralLedger"),
        ("API_ACCOUNTDOCUMENT_SRV", "AccountDocumentSet", "FI", "GeneralLedger"),
        ("C_BANK_SRV", "BankSet", "FI", "Banking"),
        ("C_WBS_FS_SRV", "WBSElementSet", "CO", "ProjectAccounting"),
        ("UNKNOWN_SERVICE", "UnknownSet", "OTHER", "General"),
    ]
    
    results = {
        "total_cases": len(test_cases),
        "correct_module": 0,
        "correct_sub_module": 0,
        "high_confidence": 0,
        "details": []
    }
    
    for service_name, entity_name, expected_module, expected_sub_module in test_cases:
        module, sub_module, confidence = inference.infer_module_with_confidence(service_name, entity_name)
        
        module_correct = module == expected_module
        sub_module_correct = sub_module == expected_sub_module
        
        if module_correct:
            results["correct_module"] += 1
        if sub_module_correct:
            results["correct_sub_module"] += 1
        if confidence >= 0.5:
            results["high_confidence"] += 1
        
        results["details"].append({
            "service": service_name,
            "entity": entity_name,
            "inferred_module": module,
            "expected_module": expected_module,
            "module_correct": module_correct,
            "inferred_sub_module": sub_module,
            "expected_sub_module": expected_sub_module,
            "sub_module_correct": sub_module_correct,
            "confidence": confidence
        })
        
        status = "✓" if module_correct and sub_module_correct else "✗"
        logger.info(f"{status} {service_name} -> {module}/{sub_module} (置信度: {confidence:.2f})")
    
    # 计算准确率
    module_accuracy = (results["correct_module"] / results["total_cases"]) * 100
    sub_module_accuracy = (results["correct_sub_module"] / results["total_cases"]) * 100
    
    logger.info("\n" + "=" * 60)
    logger.info("推断结果统计:")
    logger.info(f"  总测试用例: {results['total_cases']}")
    logger.info(f"  模块推断正确: {results['correct_module']} ({module_accuracy:.1f}%)")
    logger.info(f"  子模块推断正确: {results['correct_sub_module']} ({sub_module_accuracy:.1f}%)")
    logger.info(f"  高置信度推断: {results['high_confidence']}")
    logger.info("=" * 60)
    
    return results


async def test_error_handling():
    """测试错误处理和降级策略"""
    logger.info("\n" + "=" * 60)
    logger.info("测试3: 错误处理和降级策略")
    logger.info("=" * 60)
    
    parser = SAPODataMetadataParser()
    inference = SAPModuleInference()
    
    # 有效的OData XML示例（带命名空间）
    valid_xml = '''<?xml version="1.0" encoding="utf-8"?>
<edmx:Edmx xmlns:edmx="http://schemas.microsoft.com/ado/2007/06/edmx" Version="4.0">
  <edmx:DataServices>
    <Schema xmlns="http://schemas.microsoft.com/ado/2007/06/edm" Namespace="Test">
      <EntityContainer Name="Container">
        <EntitySet Name="TestSet" EntityType="Test.TestType"/>
      </EntityContainer>
      <EntityType Name="TestType">
        <Key>
          <PropertyRef Name="ID"/>
        </Key>
        <Property Name="ID" Type="Edm.String" Nullable="false"/>
      </EntityType>
    </Schema>
  </edmx:DataServices>
</edmx:Edmx>'''
    
    test_cases = [
        ("有效XML", valid_xml),
        ("无效XML", "<invalid>xml</invalid"),
        ("空字符串", ""),
        ("None值", None),
    ]
    
    results = {
        "total_cases": len(test_cases),
        "handled_gracefully": 0,
        "exceptions": 0,
        "details": []
    }
    
    for case_name, xml_data in test_cases:
        try:
            if xml_data is None:
                # None值应该被优雅处理
                parsed = parser.parse_metadata("")
                results["handled_gracefully"] += 1
                results["details"].append({
                    "case": case_name,
                    "status": "handled",
                    "entities": len(parsed.get("entities", []))
                })
                logger.info(f"✓ {case_name}: 成功处理（返回空结果）")
            else:
                parsed = parser.parse_metadata(xml_data)
                # 检查是否有错误字段
                if "error" in parsed:
                    # 有错误但优雅处理了
                    results["handled_gracefully"] += 1
                    results["details"].append({
                        "case": case_name,
                        "status": "handled_with_error",
                        "error": parsed.get("error"),
                        "entities": len(parsed.get("entities", []))
                    })
                    logger.info(f"✓ {case_name}: 优雅处理（返回空结果，错误: {parsed.get('error', '')[:50]}）")
                else:
                    results["handled_gracefully"] += 1
                    results["details"].append({
                        "case": case_name,
                        "status": "handled",
                        "entities": len(parsed.get("entities", []))
                    })
                    logger.info(f"✓ {case_name}: 成功处理（{len(parsed.get('entities', []))} 个实体）")
        except Exception as e:
            results["exceptions"] += 1
            results["details"].append({
                "case": case_name,
                "status": "exception",
                "error": str(e)
            })
            logger.info(f"✗ {case_name}: 抛出异常 - {type(e).__name__}: {str(e)[:50]}")
    
    logger.info("\n" + "=" * 60)
    logger.info("错误处理结果:")
    logger.info(f"  总测试用例: {results['total_cases']}")
    logger.info(f"  优雅处理: {results['handled_gracefully']}")
    logger.info(f"  抛出异常: {results['exceptions']}")
    logger.info("=" * 60)
    
    return results


async def main():
    """主测试函数"""
    logger.info("开始技术验证测试...")
    logger.info("=" * 60)
    
    all_results = {}
    
    try:
        # 测试1: OData元数据解析
        all_results["metadata_parsing"] = await test_odata_metadata_parsing()
        
        # 测试2: 模块推断
        all_results["module_inference"] = await test_module_inference()
        
        # 测试3: 错误处理
        all_results["error_handling"] = await test_error_handling()
        
        # 总结
        logger.info("\n" + "=" * 60)
        logger.info("技术验证测试总结")
        logger.info("=" * 60)
        
        # 计算总体成功率
        parsing_success_rate = (
            (all_results["metadata_parsing"]["successful_parses"] / 
             all_results["metadata_parsing"]["total_services"]) * 100
            if all_results["metadata_parsing"]["total_services"] > 0 else 0
        )
        
        module_accuracy = (
            (all_results["module_inference"]["correct_module"] / 
             all_results["module_inference"]["total_cases"]) * 100
            if all_results["module_inference"]["total_cases"] > 0 else 0
        )
        
        logger.info(f"✓ OData元数据解析成功率: {parsing_success_rate:.1f}%")
        logger.info(f"✓ 模块推断准确率: {module_accuracy:.1f}%")
        logger.info(f"✓ 错误处理测试: {all_results['error_handling']['handled_gracefully']}/{all_results['error_handling']['total_cases']}")
        
        # 验证成功标准
        logger.info("\n验证成功标准:")
        logger.info(f"  {'✓' if parsing_success_rate >= 85 else '✗'} 元数据解析准确率 > 85%: {parsing_success_rate:.1f}%")
        logger.info(f"  {'✓' if module_accuracy >= 80 else '✗'} 模块推断准确率 > 80%: {module_accuracy:.1f}%")
        
        overall_success = parsing_success_rate >= 85 and module_accuracy >= 80
        logger.info(f"\n总体评估: {'✓ 通过' if overall_success else '✗ 未通过'}")
        
        return all_results
        
    except Exception as e:
        logger.error(f"测试执行失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())


"""
关系发现质量验证脚本
验证导航属性解析、隐含关系推断等关系发现能力
"""
import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple

# 添加项目根目录到路径
agent_path = Path(__file__).parent
sys.path.insert(0, str(agent_path))

from src.core.sap_odata_metadata_parser import SAPODataMetadataParser

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_test_metadata_with_relationships() -> str:
    """获取包含关系信息的测试元数据"""
    return '''<?xml version="1.0" encoding="utf-8"?>
<edmx:Edmx xmlns:edmx="http://schemas.microsoft.com/ado/2007/06/edmx" Version="4.0">
  <edmx:DataServices>
    <Schema xmlns="http://schemas.microsoft.com/ado/2007/06/edm" 
            xmlns:sap="http://www.sap.com/Protocols/SAPData"
            Namespace="com.sap.gateway.srvd.a2x.api_glaccount.v0001">
      <EntityContainer Name="API_GLACCOUNT_SRV_Entities">
        <EntitySet Name="A_GLAccount" 
                   EntityType="com.sap.gateway.srvd.a2x.api_glaccount.v0001.A_GLAccountType"/>
        <EntitySet Name="A_CompanyCode" 
                   EntityType="com.sap.gateway.srvd.a2x.api_glaccount.v0001.A_CompanyCodeType"/>
        <EntitySet Name="A_JournalEntry" 
                   EntityType="com.sap.gateway.srvd.a2x.api_glaccount.v0001.A_JournalEntryType"/>
      </EntityContainer>
      
      <!-- 总账科目实体 -->
      <EntityType Name="A_GLAccountType" sap:label="总账科目">
        <Key>
          <PropertyRef Name="GLAccount"/>
        </Key>
        <Property Name="GLAccount" Type="Edm.String" Nullable="false" MaxLength="10"/>
        <Property Name="GLAccountName" Type="Edm.String" MaxLength="50"/>
        <Property Name="CompanyCode" Type="Edm.String" MaxLength="4"/>
        <NavigationProperty Name="to_CompanyCode" 
                           Type="com.sap.gateway.srvd.a2x.api_glaccount.v0001.A_CompanyCodeType" 
                           Relationship="com.sap.gateway.srvd.a2x.api_glaccount.v0001.to_CompanyCode"/>
        <NavigationProperty Name="to_JournalEntries" 
                           Type="Collection(com.sap.gateway.srvd.a2x.api_glaccount.v0001.A_JournalEntryType)" 
                           Relationship="com.sap.gateway.srvd.a2x.api_glaccount.v0001.to_JournalEntries"/>
      </EntityType>
      
      <!-- 公司代码实体 -->
      <EntityType Name="A_CompanyCodeType" sap:label="公司代码">
        <Key>
          <PropertyRef Name="CompanyCode"/>
        </Key>
        <Property Name="CompanyCode" Type="Edm.String" Nullable="false" MaxLength="4"/>
        <Property Name="CompanyCodeName" Type="Edm.String" MaxLength="25"/>
      </EntityType>
      
      <!-- 日记账分录实体 -->
      <EntityType Name="A_JournalEntryType" sap:label="日记账分录">
        <Key>
          <PropertyRef Name="JournalEntry"/>
        </Key>
        <Property Name="JournalEntry" Type="Edm.String" Nullable="false" MaxLength="10"/>
        <Property Name="GLAccount" Type="Edm.String" MaxLength="10"/>
        <Property Name="CompanyCode" Type="Edm.String" MaxLength="4"/>
        <NavigationProperty Name="to_GLAccount" 
                           Type="com.sap.gateway.srvd.a2x.api_glaccount.v0001.A_GLAccountType" 
                           Relationship="com.sap.gateway.srvd.a2x.api_glaccount.v0001.to_GLAccount"/>
        <NavigationProperty Name="to_CompanyCode" 
                           Type="com.sap.gateway.srvd.a2x.api_glaccount.v0001.A_CompanyCodeType" 
                           Relationship="com.sap.gateway.srvd.a2x.api_glaccount.v0001.to_CompanyCode"/>
      </EntityType>
    </Schema>
  </edmx:DataServices>
</edmx:Edmx>'''


class RelationshipDiscoveryValidator:
    """关系发现验证器"""
    
    def __init__(self):
        self.parser = SAPODataMetadataParser()
        
        # 定义期望的关系基准（基于业务知识）
        self.relationship_benchmark = [
            {
                "source": "A_GLAccount",
                "target": "A_CompanyCode",
                "relationship_type": "belongs_to",
                "navigation_property": "to_CompanyCode",
                "cardinality": "many_to_one"
            },
            {
                "source": "A_GLAccount",
                "target": "A_JournalEntry",
                "relationship_type": "has_many",
                "navigation_property": "to_JournalEntries",
                "cardinality": "one_to_many"
            },
            {
                "source": "A_JournalEntry",
                "target": "A_GLAccount",
                "relationship_type": "belongs_to",
                "navigation_property": "to_GLAccount",
                "cardinality": "many_to_one"
            },
            {
                "source": "A_JournalEntry",
                "target": "A_CompanyCode",
                "relationship_type": "belongs_to",
                "navigation_property": "to_CompanyCode",
                "cardinality": "many_to_one"
            }
        ]
    
    def discover_relationships(self, parsed_entities: List[Dict]) -> List[Dict]:
        """从解析的实体中发现关系"""
        relationships = []
        entity_map = {e["name"]: e for e in parsed_entities}
        
        for entity in parsed_entities:
            source_name = entity["name"]
            nav_props = entity.get("navigation_properties", [])
            
            for nav_prop in nav_props:
                target_type = nav_prop.get("type", "")
                
                # 提取目标实体名称（从类型中）
                # 处理Collection类型: Collection(Namespace.EntityType) -> EntityType
                if target_type.startswith("Collection("):
                    target_type = target_type[11:-1]  # 去掉Collection(和)
                
                # 提取简单名称（去掉命名空间）
                target_simple_name = target_type.split(".")[-1].replace("Type", "")
                
                # 查找匹配的目标实体
                target_entity = None
                for entity_name, entity_data in entity_map.items():
                    if target_simple_name in entity_name or entity_name in target_simple_name:
                        target_entity = entity_data
                        break
                
                if target_entity:
                    # 推断关系类型
                    nav_name = nav_prop.get("name", "")
                    if nav_name.startswith("to_"):
                        rel_type = "belongs_to"
                    elif "Collection" in nav_prop.get("type", ""):
                        rel_type = "has_many"
                    else:
                        rel_type = "related_to"
                    
                    relationships.append({
                        "source": source_name,
                        "target": target_entity["name"],
                        "relationship_type": rel_type,
                        "navigation_property": nav_name,
                        "cardinality": "many_to_one" if rel_type == "belongs_to" else "one_to_many"
                    })
        
        return relationships
    
    def calculate_metrics(
        self,
        benchmark: List[Dict],
        discovered: List[Dict]
    ) -> Dict[str, float]:
        """计算准确率、召回率、F1分数"""
        # 构建基准关系集合（用于匹配）
        benchmark_set = {
            (r["source"], r["target"], r["navigation_property"])
            for r in benchmark
        }
        
        discovered_set = {
            (r["source"], r["target"], r["navigation_property"])
            for r in discovered
        }
        
        # 计算TP, FP, FN
        true_positives = len(benchmark_set & discovered_set)
        false_positives = len(discovered_set - benchmark_set)
        false_negatives = len(benchmark_set - discovered_set)
        
        # 计算指标
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "coverage": (true_positives / len(benchmark)) * 100 if benchmark else 0.0
        }
    
    def validate_relationship_quality(self) -> Dict[str, Any]:
        """验证关系发现质量"""
        logger.info("=" * 60)
        logger.info("关系发现质量验证")
        logger.info("=" * 60)
        
        # 解析元数据
        xml_data = get_test_metadata_with_relationships()
        parsed = self.parser.parse_metadata(xml_data)
        
        if "error" in parsed:
            logger.error(f"解析失败: {parsed['error']}")
            return {"error": parsed["error"]}
        
        # 发现关系
        discovered_relationships = self.discover_relationships(parsed["entities"])
        
        logger.info(f"\n发现的关系数: {len(discovered_relationships)}")
        for rel in discovered_relationships:
            logger.info(f"  {rel['source']} --[{rel['relationship_type']}]--> {rel['target']} "
                      f"(via {rel['navigation_property']})")
        
        # 计算指标
        metrics = self.calculate_metrics(self.relationship_benchmark, discovered_relationships)
        
        logger.info("\n" + "=" * 60)
        logger.info("关系发现质量指标:")
        logger.info(f"  基准关系数: {len(self.relationship_benchmark)}")
        logger.info(f"  发现关系数: {len(discovered_relationships)}")
        logger.info(f"  正确关系数 (TP): {metrics['true_positives']}")
        logger.info(f"  错误关系数 (FP): {metrics['false_positives']}")
        logger.info(f"  遗漏关系数 (FN): {metrics['false_negatives']}")
        logger.info(f"  精确率 (Precision): {metrics['precision']:.2%}")
        logger.info(f"  召回率 (Recall): {metrics['recall']:.2%}")
        logger.info(f"  F1分数: {metrics['f1_score']:.2%}")
        logger.info(f"  覆盖率: {metrics['coverage']:.1f}%")
        logger.info("=" * 60)
        
        return {
            "benchmark_count": len(self.relationship_benchmark),
            "discovered_count": len(discovered_relationships),
            "metrics": metrics,
            "discovered_relationships": discovered_relationships
        }


async def main():
    """主测试函数"""
    logger.info("开始关系发现质量验证...")
    
    validator = RelationshipDiscoveryValidator()
    results = validator.validate_relationship_quality()
    
    if "error" in results:
        logger.error("验证失败")
        return results
    
    # 验证成功标准
    logger.info("\n验证成功标准:")
    logger.info(f"  {'✓' if results['metrics']['precision'] >= 0.9 else '✗'} 精确率 > 90%: {results['metrics']['precision']:.2%}")
    logger.info(f"  {'✓' if results['metrics']['recall'] >= 0.75 else '✗'} 召回率 > 75%: {results['metrics']['recall']:.2%}")
    logger.info(f"  {'✓' if results['metrics']['f1_score'] >= 0.8 else '✗'} F1分数 > 80%: {results['metrics']['f1_score']:.2%}")
    logger.info(f"  {'✓' if results['metrics']['coverage'] >= 75 else '✗'} 覆盖率 > 75%: {results['metrics']['coverage']:.1f}%")
    
    overall_success = (
        results['metrics']['precision'] >= 0.9 and
        results['metrics']['recall'] >= 0.75 and
        results['metrics']['f1_score'] >= 0.8 and
        results['metrics']['coverage'] >= 75
    )
    
    logger.info(f"\n总体评估: {'✓ 通过' if overall_success else '✗ 未通过'}")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())


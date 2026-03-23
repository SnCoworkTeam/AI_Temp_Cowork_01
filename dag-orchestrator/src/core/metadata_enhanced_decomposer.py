"""
元数据增强的任务分解器
利用SAP元数据的语义关系来优化任务分解和依赖关系构建
"""
import logging
from typing import Dict, Any, Optional, List
import httpx
import os

logger = logging.getLogger(__name__)


class MetadataEnhancedDecomposer:
    """元数据增强的任务分解器"""
    
    def __init__(self, metadata_service_url: Optional[str] = None):
        """
        初始化元数据增强分解器
        
        Args:
            metadata_service_url: 元数据服务URL
        """
        self.metadata_service_url = metadata_service_url or os.getenv(
            "METADATA_SERVICE_URL",
            "http://metadata-service:8005"
        )
        self.http_client = httpx.AsyncClient(timeout=5.0)
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()
    
    async def enhance_decomposition_prompt(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> str:
        """
        增强任务分解提示词，包含元数据信息
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            
        Returns:
            增强的提示词
        """
        try:
            # 1. 提取业务术语
            business_terms = self._extract_business_terms(user_input)
            
            if not business_terms:
                return ""
            
            # 2. 查询相关资产和语义关系
            related_assets = await self._search_assets_by_terms(business_terms)
            semantic_relationships = await self._get_semantic_relationships(business_terms)
            
            if not related_assets and not semantic_relationships:
                return ""
            
            # 3. 构建增强提示词部分
            enhancement = "\n\n# 元数据增强信息（基于SAP业务术语和语义关系）\n"
            
            if business_terms:
                enhancement += f"检测到的业务术语: {', '.join(business_terms)}\n\n"
            
            if related_assets:
                enhancement += "相关的技术资产:\n"
                for asset in related_assets[:5]:
                    asset_name = asset.get('name', '')
                    display_name = asset.get('display_name', '')
                    classification = asset.get('classification', '')
                    sap_table = asset.get('metadata', {}).get('sap_table_name', '')
                    
                    enhancement += f"- {display_name or asset_name}"
                    if sap_table:
                        enhancement += f" (SAP表: {sap_table})"
                    if classification:
                        enhancement += f" [分类: {classification}]"
                    enhancement += "\n"
            
            if semantic_relationships:
                enhancement += "\n语义关系（用于构建任务依赖）:\n"
                for rel in semantic_relationships[:5]:
                    source = rel.get('source', '').split(':')[-1]
                    target = rel.get('target', '').split(':')[-1]
                    rel_type = rel.get('relationship_type', '')
                    enhancement += f"- {source} → {target} ({rel_type})\n"
            
            enhancement += """
# 使用元数据指导任务分解
- 利用语义关系确定任务之间的依赖顺序
- 如果任务涉及多个相关资产，考虑按依赖关系分解为多个子任务
- 优先使用SAP相关的工具和服务（如OData查询、MCP工具）
- 根据业务术语推荐合适的技术资产和工具
"""
            
            return enhancement
            
        except Exception as e:
            logger.debug(f"Failed to enhance decomposition prompt: {e}")
            return ""
    
    def _extract_business_terms(self, user_input: str) -> List[str]:
        """从用户输入中提取业务术语"""
        terms = []
        input_lower = user_input.lower()
        
        sap_terms = {
            "客户": ["客户", "customer", "kunde", "客户主数据"],
            "供应商": ["供应商", "vendor", "supplier", "lieferant"],
            "物料": ["物料", "material", "产品", "product"],
            "销售订单": ["销售订单", "sales order", "verkaufsauftrag", "订单"],
            "采购订单": ["采购订单", "purchase order", "einkaufsauftrag", "采购单"],
            "交货单": ["交货单", "delivery", "lieferung", "发货单"],
            "发票": ["发票", "invoice", "rechnung", "账单"]
        }
        
        for term_key, keywords in sap_terms.items():
            for keyword in keywords:
                if keyword.lower() in input_lower:
                    if term_key not in terms:
                        terms.append(term_key)
                    break
        
        return terms
    
    async def _search_assets_by_terms(
        self,
        business_terms: List[str]
    ) -> List[Dict[str, Any]]:
        """根据业务术语搜索相关的技术资产"""
        assets = []
        
        try:
            search_query = " OR ".join(business_terms)
            response = await self.http_client.get(
                f"{self.metadata_service_url}/api/search",
                params={
                    "q": search_query,
                    "limit": 10,
                    "entity_types": "data_asset"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                assets = data.get("results", [])
                
        except Exception as e:
            logger.debug(f"Failed to search assets: {e}")
        
        return assets
    
    async def _get_semantic_relationships(
        self,
        business_terms: List[str]
    ) -> List[Dict[str, Any]]:
        """获取语义关系"""
        relationships = []
        
        try:
            # 通过搜索相关资产，然后从资产元数据中提取语义关系
            assets = await self._search_assets_by_terms(business_terms)
            
            for asset in assets:
                metadata = asset.get('metadata', {})
                semantic_rels = metadata.get('semantic_relationships', [])
                relationships.extend(semantic_rels)
                
        except Exception as e:
            logger.debug(f"Failed to get semantic relationships: {e}")
        
        return relationships
    
    async def suggest_task_dependencies(
        self,
        task_nodes: Dict[str, Any],
        user_input: str
    ) -> Dict[str, List[str]]:
        """
        基于语义关系建议任务依赖
        
        Args:
            task_nodes: 任务节点字典
            user_input: 用户输入
            
        Returns:
            建议的依赖关系字典 {node_id: [依赖的node_ids]}
        """
        dependencies = {}
        
        try:
            # 提取业务术语
            business_terms = self._extract_business_terms(user_input)
            
            if not business_terms:
                return dependencies
            
            # 获取语义关系
            semantic_relationships = await self._get_semantic_relationships(business_terms)
            
            # 分析任务节点，匹配语义关系
            for node_id, node_data in task_nodes.items():
                node_deps = []
                node_action = node_data.get('action', '').lower()
                node_description = node_data.get('description', '').lower()
                
                # 查找与当前节点相关的语义关系
                for rel in semantic_relationships:
                    source = rel.get('source', '').split(':')[-1].lower()
                    target = rel.get('target', '').split(':')[-1].lower()
                    rel_type = rel.get('relationship_type', '')
                    
                    # 如果当前节点涉及target，且存在source节点，则添加依赖
                    if target in node_action or target in node_description:
                        # 查找涉及source的节点
                        for other_node_id, other_node_data in task_nodes.items():
                            if other_node_id == node_id:
                                continue
                            
                            other_action = other_node_data.get('action', '').lower()
                            other_description = other_node_data.get('description', '').lower()
                            
                            if source in other_action or source in other_description:
                                if other_node_id not in node_deps:
                                    node_deps.append(other_node_id)
                
                if node_deps:
                    dependencies[node_id] = node_deps
                    
        except Exception as e:
            logger.debug(f"Failed to suggest task dependencies: {e}")
        
        return dependencies


# 全局实例
metadata_enhanced_decomposer = MetadataEnhancedDecomposer()



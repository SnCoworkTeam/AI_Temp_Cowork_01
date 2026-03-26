"""
元数据增强的提示词构建器
利用SAP元数据（业务术语、分类、语义关系）增强意图识别提示词
"""
import logging
from typing import Dict, Any, Optional, List
import httpx
import os

from ..models.prompt_models import PromptContext

logger = logging.getLogger(__name__)


class MetadataEnhancedPromptBuilder:
    """元数据增强的提示词构建器"""
    
    def __init__(self, metadata_service_url: Optional[str] = None):
        """
        初始化元数据增强提示词构建器
        
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
    
    async def build_enhanced_prompt(
        self,
        user_input: str,
        context: PromptContext
    ) -> Optional[str]:
        """
        构建元数据增强的系统提示词
        
        Args:
            user_input: 用户输入
            context: 提示词上下文
            
        Returns:
            增强的系统提示词（如果可用），否则返回None
        """
        try:
            # 1. 从用户输入中提取业务术语
            business_terms = self._extract_business_terms(user_input)
            
            if not business_terms:
                return None
            
            # 2. 查询元数据服务，获取相关的技术资产
            related_assets = await self._search_assets_by_terms(business_terms)
            
            if not related_assets:
                return None
            
            # 3. 构建增强的系统提示词
            enhanced_prompt = self._build_prompt_with_metadata(
                user_input,
                business_terms,
                related_assets
            )
            
            return enhanced_prompt
            
        except Exception as e:
            logger.debug(f"Failed to build metadata-enhanced prompt: {e}")
            return None
    
    def _extract_business_terms(self, user_input: str) -> List[str]:
        """
        从用户输入中提取业务术语
        
        Args:
            user_input: 用户输入
            
        Returns:
            业务术语列表
        """
        terms = []
        input_lower = user_input.lower()
        
        # SAP业务术语关键词
        sap_terms = {
            "客户": ["客户", "customer", "kunde", "客户主数据", "客户信息"],
            "供应商": ["供应商", "vendor", "supplier", "lieferant", "供应商主数据"],
            "物料": ["物料", "material", "产品", "product", "物料主数据"],
            "销售订单": ["销售订单", "sales order", "verkaufsauftrag", "订单", "销售单"],
            "采购订单": ["采购订单", "purchase order", "einkaufsauftrag", "采购单", "po"],
            "交货单": ["交货单", "delivery", "lieferung", "发货单", "交货"],
            "发票": ["发票", "invoice", "rechnung", "账单", "开票"],
            "库存": ["库存", "stock", "inventory", "lager", "库存数据"],
            "价格": ["价格", "price", "preis", "定价", "价格信息"],
            "成本": ["成本", "cost", "kosten", "成本数据", "成本信息"]
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
        """
        根据业务术语搜索相关的技术资产
        
        Args:
            business_terms: 业务术语列表
            
        Returns:
            相关的技术资产列表
        """
        assets = []
        
        try:
            # 构建搜索查询（使用业务术语）
            search_query = " OR ".join(business_terms)
            
            # 调用元数据服务的搜索API
            response = await self.http_client.get(
                f"{self.metadata_service_url}/api/search",
                params={
                    "q": search_query,
                    "limit": 10,
                    "asset_type": "data_asset"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                assets = data.get("results", [])
                
        except Exception as e:
            logger.debug(f"Failed to search assets by terms: {e}")
        
        return assets
    
    def _build_prompt_with_metadata(
        self,
        user_input: str,
        business_terms: List[str],
        related_assets: List[Dict[str, Any]]
    ) -> str:
        """
        构建包含元数据的系统提示词
        
        Args:
            user_input: 用户输入
            business_terms: 业务术语列表
            related_assets: 相关的技术资产列表
            
        Returns:
            增强的系统提示词
        """
        base_prompt = """你是一个专业的对话理解智能体，负责精准分析用户意图。

# 角色定位
- 你是LuminaOS系统的对话理解模块
- 你需要理解用户真实需求，识别隐含意图
- 你需要准确分类任务类型，提取关键信息

# 任务类型定义
1. simple_query - 简单问答、知识查询、闲聊对话
2. tool_execution - 需要调用工具、API、执行命令
3. workflow_task - 涉及业务流程、工作流执行
4. complex_analysis - 复杂分析、多步骤推理任务
5. knowledge_search - 需要搜索知识库、文档
6. data_analysis - 数据分析、统计、可视化任务

# 分析要求
- 仔细分析用户query的深层意图
- 识别query中的实体、参数、约束条件
- 考虑对话历史和上下文
- 评估任务复杂度"""
        
        # 添加元数据增强部分
        if business_terms and related_assets:
            metadata_section = f"""

# 元数据增强信息（基于SAP业务术语）
检测到的业务术语: {', '.join(business_terms)}

相关的技术资产:
"""
            for asset in related_assets[:5]:  # 限制显示数量
                asset_name = asset.get('name', '')
                display_name = asset.get('display_name', '')
                classification = asset.get('classification', '')
                description = asset.get('description', '')
                
                metadata_section += f"""
- {display_name or asset_name}
  - 分类: {classification}
  - 描述: {description[:100]}...
"""
            
            metadata_section += """
# 使用元数据增强分析
- 利用业务术语和技术资产的映射关系，更准确地理解用户意图
- 识别用户提到的业务术语对应的技术资产
- 在提取实体时，优先考虑SAP相关的业务实体（客户、供应商、物料、订单等）
- 在识别required_tools时，如果涉及SAP数据，考虑使用SAP相关的工具（如OData查询、MCP工具等）
"""
            
            base_prompt += metadata_section
        
        base_prompt += """
# 输出格式
请返回严格的JSON格式：
{
    "task_type": "任务类型",
    "confidence": 0.0-1.0的置信度,
    "extracted_context": {
        "entities": ["实体1", "实体2"],
        "parameters": {"参数名": "参数值"},
        "intent": "用户真实意图描述",
        "complexity": "low|medium|high"
    },
    "required_tools": ["工具列表"],
    "required_services": ["服务列表"],
    "reasoning": "详细的分析推理过程"
}

请确保分析准确，置信度评估合理。"""
        
        return base_prompt


# 全局实例
metadata_enhanced_prompt_builder = MetadataEnhancedPromptBuilder()

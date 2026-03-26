"""
关系发现LLM增强服务
使用LLM识别复杂和隐含的关系
"""
import logging
import httpx
import os
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class RelationshipLLMDiscovery:
    """关系发现LLM增强服务"""
    
    def __init__(self, db: Session):
        """
        初始化LLM关系发现服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.llm_base_url = os.getenv("LLM_BASE_URL", "http://chat-service:8006")
        self.llm_api_key = os.getenv("OPENAI_API_KEY", "")
        self.http_client = httpx.AsyncClient(timeout=60.0)
        self.enabled = os.getenv("LLM_RELATIONSHIP_DISCOVERY_ENABLED", "true").lower() == "true"
    
    async def discover_relationships_batch(
        self,
        entity_pairs: List[tuple],
        batch_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        批量LLM识别关系
        
        Args:
            entity_pairs: 实体对列表 [(entity1, entity2), ...]
            batch_size: 批量大小
        
        Returns:
            关系列表
        """
        if not self.enabled:
            logger.info("LLM relationship discovery is disabled")
            return []
        
        relationships = []
        
        # 分批处理
        logger.info(f"LLM discovery enabled: {self.enabled}, processing {len(entity_pairs)} entity pairs")
        for i in range(0, len(entity_pairs), batch_size):
            batch = entity_pairs[i:i + batch_size]
            logger.info(f"Processing LLM batch {i//batch_size + 1}/{(len(entity_pairs) + batch_size - 1)//batch_size} ({len(batch)} pairs)...")
            batch_relationships = await self._process_batch(batch)
            relationships.extend(batch_relationships)
            logger.info(f"Batch {i//batch_size + 1} discovered {len(batch_relationships)} relationships")
        
        logger.info(f"LLM discovered {len(relationships)} relationships from {len(entity_pairs)} pairs")
        return relationships
    
    async def _process_batch(
        self,
        entity_pairs: List[tuple]
    ) -> List[Dict[str, Any]]:
        """处理一批实体对"""
        relationships = []
        
        for entity1, entity2 in entity_pairs:
            try:
                relationship = await self._discover_relationship(entity1, entity2)
                if relationship:
                    confidence = relationship.get("confidence", 0)
                    if confidence > 0.7:
                        relationships.append(relationship)
                        logger.debug(f"Discovered relationship: {entity1.get('name')} -> {entity2.get('name')} (confidence: {confidence})")
                    else:
                        logger.debug(f"Skipped low confidence relationship: {entity1.get('name')} -> {entity2.get('name')} (confidence: {confidence})")
                else:
                    logger.debug(f"No relationship discovered for: {entity1.get('name')} -> {entity2.get('name')}")
            except Exception as e:
                logger.warning(f"Failed to discover relationship for pair ({entity1.get('name', 'unknown')}, {entity2.get('name', 'unknown')}): {e}", exc_info=True)
                continue
        
        return relationships
    
    async def _discover_relationship(
        self,
        entity1: Dict[str, Any],
        entity2: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """使用LLM发现两个实体之间的关系"""
        try:
            prompt = self._build_prompt(entity1, entity2)
            
            # 调用LLM API
            # 尝试多个可能的端点（按优先级排序）
            endpoints = [
                f"{self.llm_base_url}/v1/chat/completions",  # DeepSeek标准端点
                f"{self.llm_base_url}/chat/completions",
                f"{self.llm_base_url}/api/v1/chat/completions",
                f"{self.llm_base_url}/api/chat/completions"
            ]
            
            response = None
            last_error = None
            for endpoint in endpoints:
                try:
                    headers = {
                        "Content-Type": "application/json"
                    }
                    if self.llm_api_key:
                        headers["Authorization"] = f"Bearer {self.llm_api_key}"
                    
                    # DeepSeek API格式
                    request_data = {
                        "model": "deepseek-chat",
                        "messages": [
                            {
                                "role": "system",
                                "content": "你是一个业务实体关系分析专家。分析两个业务实体之间的关系，返回JSON格式。"
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.3
                    }
                    
                    # 尝试添加response_format（如果API支持）
                    # DeepSeek可能不支持response_format，先不添加
                    
                    response = await self.http_client.post(
                        endpoint,
                        headers=headers,
                        json=request_data
                    )
                    if response.status_code == 200:
                        break  # 成功则退出循环
                    else:
                        logger.warning(f"LLM API endpoint {endpoint} returned {response.status_code}")
                except Exception as e:
                    last_error = e
                    logger.debug(f"Failed to call LLM endpoint {endpoint}: {e}")
                    continue
            
            if not response or response.status_code != 200:
                logger.warning(f"All LLM API endpoints failed. Last error: {last_error}")
                return None
            
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            
            # 清理响应内容（移除markdown代码块标记）
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()
            
            # 解析JSON响应
            try:
                relationship_data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM response as JSON: {e}, content: {content[:200]}")
                # 尝试提取JSON部分
                import re
                json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
                if json_match:
                    try:
                        relationship_data = json.loads(json_match.group())
                    except:
                        return None
                else:
                    return None
            
            return {
                "source": str(entity1.get("id")),
                "target": str(entity2.get("id")),
                "relationship_type": relationship_data.get("relationship_type", "related_to"),
                "confidence": float(relationship_data.get("confidence", 0.5)),
                "rule": "llm_discovery",
                "reason": relationship_data.get("reason", ""),
                "properties": {
                    "source_type": "concept",
                    "target_type": "concept",
                    "llm_reason": relationship_data.get("reason", "")
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to discover relationship with LLM: {e}", exc_info=True)
            return None
    
    def _build_prompt(
        self,
        entity1: Dict[str, Any],
        entity2: Dict[str, Any]
    ) -> str:
        """构建LLM提示词"""
        return f"""
分析以下两个业务实体之间的关系：

实体1:
- 名称: {entity1.get('name', '')}
- 显示名称: {entity1.get('display_name', '')}
- 类型: {entity1.get('entity_type', '')}
- 描述: {entity1.get('description', '')}
- 业务定义: {entity1.get('business_definition', '')}

实体2:
- 名称: {entity2.get('name', '')}
- 显示名称: {entity2.get('display_name', '')}
- 类型: {entity2.get('entity_type', '')}
- 描述: {entity2.get('description', '')}
- 业务定义: {entity2.get('business_definition', '')}

请分析它们之间的关系，返回JSON格式：
{{
    "relationship_type": "parent_of|child_of|related_to|depends_on|transforms_to|...",
    "confidence": 0.0-1.0,
    "reason": "关系原因说明"
}}

关系类型说明：
- parent_of: 父子关系（实体1是实体2的父）
- child_of: 子父关系（实体1是实体2的子）
- related_to: 相关关系
- depends_on: 依赖关系
- transforms_to: 转换关系
"""
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()

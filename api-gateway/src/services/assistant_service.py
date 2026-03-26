"""
智能助手服务
提供上下文感知的智能助手能力
"""
import logging
import httpx
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class AssistantService:
    """智能助手服务"""
    
    def __init__(self):
        """
        初始化智能助手服务
        """
        self.llm_base_url = os.getenv("LLM_BASE_URL", "http://chat-service:8006")
        self.llm_api_key = os.getenv("OPENAI_API_KEY", "")
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.enabled = os.getenv("ASSISTANT_ENABLED", "true").lower() == "true"
    
    async def chat(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        智能助手对话
        
        Args:
            message: 用户消息
            context: 上下文信息（当前操作、实体等）
            conversation_history: 对话历史
        
        Returns:
            助手响应
        """
        if not self.enabled:
            return {
                "response": "智能助手功能未启用",
                "suggestions": []
            }
        
        try:
            # 构建系统提示词
            system_prompt = self._build_system_prompt(context)
            
            # 构建消息列表
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                }
            ]
            
            # 添加对话历史
            if conversation_history:
                messages.extend(conversation_history)
            
            # 添加当前消息
            messages.append({
                "role": "user",
                "content": message
            })
            
            # 调用LLM API
            response = await self.http_client.post(
                f"{self.llm_base_url}/api/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.llm_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 500
                }
            )
            
            if response.status_code != 200:
                logger.warning(f"LLM API returned {response.status_code}")
                return {
                    "response": "抱歉，我暂时无法回答您的问题。",
                    "suggestions": []
                }
            
            result = response.json()
            assistant_message = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # 生成建议操作
            suggestions = await self._generate_suggestions(message, context)
            
            return {
                "response": assistant_message,
                "suggestions": suggestions,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to chat with assistant: {e}", exc_info=True)
            return {
                "response": "抱歉，处理您的请求时出现了错误。",
                "suggestions": []
            }
    
    def _build_system_prompt(self, context: Optional[Dict[str, Any]]) -> str:
        """构建系统提示词"""
        base_prompt = """你是一个企业AI平台的智能助手。你的任务是帮助用户：
1. 理解和使用平台功能
2. 查找和分析数据
3. 提供操作建议
4. 回答系统相关问题

请用友好、专业的语气回答用户问题。"""
        
        if context:
            context_str = json.dumps(context, indent=2, ensure_ascii=False)
            base_prompt += f"\n\n当前上下文:\n{context_str}"
        
        return base_prompt
    
    async def _generate_suggestions(
        self,
        message: str,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """生成建议操作"""
        suggestions = []
        
        # 基于消息内容生成建议
        message_lower = message.lower()
        
        if "搜索" in message or "查找" in message or "search" in message_lower:
            suggestions.append({
                "type": "action",
                "label": "执行搜索",
                "action": "search",
                "description": "在平台中搜索相关内容"
            })
        
        if "推荐" in message or "recommend" in message_lower:
            suggestions.append({
                "type": "action",
                "label": "查看推荐",
                "action": "recommend",
                "description": "查看相关推荐"
            })
        
        if "图谱" in message or "关系" in message or "graph" in message_lower:
            suggestions.append({
                "type": "action",
                "label": "查看知识图谱",
                "action": "view_graph",
                "description": "查看知识图谱可视化"
            })
        
        # 基于上下文生成建议
        if context:
            if context.get("entity_id"):
                suggestions.append({
                    "type": "action",
                    "label": "查看实体详情",
                    "action": "view_entity",
                    "entity_id": context.get("entity_id"),
                    "description": "查看当前实体的详细信息"
                })
            
            if context.get("entity_id"):
                suggestions.append({
                    "type": "action",
                    "label": "查看相关实体",
                    "action": "view_related",
                    "entity_id": context.get("entity_id"),
                    "description": "查看与当前实体相关的其他实体"
                })
        
        return suggestions[:5]  # 最多5个建议
    
    async def answer_question(
        self,
        question: str,
        knowledge_base: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        回答问题
        
        Args:
            question: 问题
            knowledge_base: 知识库上下文（可选）
        
        Returns:
            答案和相关信息
        """
        try:
            kb_context = ""
            if knowledge_base:
                kb_context = f"知识库上下文:\n{json.dumps(knowledge_base, indent=2, ensure_ascii=False)}\n"
            
            prompt = f"""
用户问题: {question}

{kb_context}请基于知识库上下文回答问题。如果知识库中没有相关信息，请说明。
"""
            
            response = await self.http_client.post(
                f"{self.llm_base_url}/api/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.llm_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一个知识库问答专家。基于提供的知识库上下文回答问题。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 500
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                return {
                    "answer": answer,
                    "confidence": 0.8,  # 简化实现
                    "sources": knowledge_base.get("sources", []) if knowledge_base else []
                }
            
            return {
                "answer": "抱歉，无法回答您的问题。",
                "confidence": 0.0,
                "sources": []
            }
            
        except Exception as e:
            logger.error(f"Failed to answer question: {e}", exc_info=True)
            return {
                "answer": "抱歉，处理问题时出现了错误。",
                "confidence": 0.0,
                "sources": []
            }
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()


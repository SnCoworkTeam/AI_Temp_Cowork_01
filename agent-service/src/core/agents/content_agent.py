"""
内容生成智能体
专门处理内容生成和结构化
"""
import logging
from typing import Dict, Any, Optional, List
import json
import re

from .base_agent import IntelligentAgent
from ..llm_integration import deepseek_llm
from ..platform_introduction import get_platform_introduction

logger = logging.getLogger(__name__)


class ContentAgent(IntelligentAgent):
    """内容生成智能体 - 专门处理内容生成和结构化"""
    
    def __init__(self):
        super().__init__(
            agent_id="content_agent",
            name="内容生成智能体",
            description="专门处理内容生成和结构化，包括报告生成、文档生成、内容创作",
            capabilities={
                "content_generation": "内容生成",
                "structuring": "结构化",
                "report_writing": "报告撰写"
            }
        )
        self.llm = deepseek_llm
    
    async def analyze_task(
        self,
        task_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析内容生成需求
        
        Args:
            task_description: 任务描述
            context: 上下文信息
            
        Returns:
            内容生成计划
        """
        try:
            # 清理上下文，移除不能序列化的对象
            clean_context = self._clean_context_for_json(context)
            
            prompt = f"""
作为内容生成专家，分析以下内容生成需求：

任务: {task_description}
上下文: {json.dumps(clean_context, ensure_ascii=False, indent=2)}

请分析：
1. **内容类型**：报告、文档、摘要、邮件、其他
2. **内容结构**：需要什么结构？
3. **内容风格**：正式、非正式、技术性、业务性
4. **目标受众**：谁将阅读这个内容？
5. **内容长度**：简短、中等、详细

返回JSON格式：
{{
    "needs_content": true/false,
    "content_type": "report|document|summary|email|other",
    "content_structure": ["章节1", "章节2"],
    "content_style": "formal|informal|technical|business",
    "target_audience": "受众描述",
    "content_length": "short|medium|detailed"
}}
"""
            
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            system_prompt = get_system_prompt(
                "content_agent",
                fallback="你是一个内容生成专家，擅长分析内容生成需求。"
            )
            
            response = await self.llm.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])
            
            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    content_plan = json.loads(response[json_start:json_end])
                else:
                    content_plan = {"needs_content": True, "content_type": "other"}
            else:
                content_plan = response
            
            return content_plan
            
        except Exception as e:
            logger.error(f"Content planning failed: {e}", exc_info=True)
            return {
                "needs_content": True,
                "content_type": "other",
                "error": str(e)
            }
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成内容
        
        Args:
            input_data: 输入数据（包含task、data、insights等）
            context: 上下文信息
            
        Returns:
            生成的内容
        """
        try:
            task_description = input_data.get("task", "")
            user_input = context.get("user_input", "") or task_description
            
            # 检查是否是平台介绍请求
            if self._is_platform_intro_request(user_input, task_description):
                logger.info("Detected platform introduction request, returning platform introduction")
                platform_intro = get_platform_introduction()
                return {
                    "agent_type": "content",
                    "execution_success": True,
                    "content_type": "platform_introduction",
                    "generated_content": platform_intro,
                    "content_plan": {
                        "needs_content": True,
                        "content_type": "platform_introduction"
                    }
                }
            
            content_plan = input_data.get("content_plan")
            
            # 收集所有可用的数据
            available_data = {
                "query_result": input_data.get("query_result"),
                "analysis_result": input_data.get("analysis_result"),
                "insights": input_data.get("insights"),
                "business_context": input_data.get("business_context"),
                "metadata": input_data.get("metadata")
            }
            
            # 过滤掉None值
            available_data = {k: v for k, v in available_data.items() if v is not None}
            
            if not content_plan:
                content_plan = await self.analyze_task(task_description, context)
            
            # 生成内容
            generated_content = await self._generate_content(
                task_description,
                available_data,
                content_plan,
                context
            )
            
            return {
                "agent_type": "content",
                "execution_success": True,
                "content_type": content_plan.get("content_type", "other"),
                "generated_content": generated_content,
                "content_plan": content_plan
            }
            
        except Exception as e:
            logger.error(f"Content agent execution failed: {e}", exc_info=True)
            raise
    
    def _is_platform_intro_request(self, user_input: str, task_description: str) -> bool:
        """判断是否是平台介绍请求"""
        text = (user_input + " " + task_description).lower()
        
        # 匹配模式
        intro_patterns = [
            r'介绍.*你.*自己',
            r'你.*是.*什么',
            r'你.*能.*做.*什么',
            r'关于.*我们',
            r'平台.*介绍',
            r'系统.*介绍',
            r'产品.*介绍',
            r'功能.*介绍',
            r'能力.*介绍',
            r'what.*are.*you',
            r'who.*are.*you',
            r'about.*us',
            r'platform.*intro',
            r'system.*intro'
        ]
        
        for pattern in intro_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    async def _generate_content(
        self,
        task_description: str,
        available_data: Dict[str, Any],
        content_plan: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成具体内容"""
        
        content_type = content_plan.get("content_type", "report")
        content_structure = content_plan.get("content_structure", [])
        content_style = content_plan.get("content_style", "business")
        target_audience = content_plan.get("target_audience", "管理层")
        
        # 准备数据摘要（避免提示词过长）
        data_summary = {}
        for key, value in available_data.items():
            if isinstance(value, dict):
                data_summary[key] = {
                    "type": "dict",
                    "keys": list(value.keys())[:10],
                    "summary": str(value)[:500]
                }
            elif isinstance(value, list):
                data_summary[key] = {
                    "type": "list",
                    "count": len(value),
                    "sample": value[:3] if value else []
                }
            else:
                data_summary[key] = {"type": "other", "content": str(value)[:500]}
        
        prompt = f"""
作为内容生成专家，基于以下信息生成内容：

任务描述: {task_description}
内容类型: {content_type}
内容结构: {json.dumps(content_structure, ensure_ascii=False)}
内容风格: {content_style}
目标受众: {target_audience}

可用数据: {json.dumps(data_summary, ensure_ascii=False, indent=2)}

请生成高质量的内容，要求：
1. **结构清晰**：按照内容结构组织
2. **内容准确**：基于提供的数据，不要编造
3. **风格合适**：符合目标受众和内容风格
4. **逻辑连贯**：内容逻辑清晰，易于理解
5. **重点突出**：突出重要信息和关键发现

返回JSON格式：
{{
    "title": "内容标题",
    "sections": [
        {{
            "section_title": "章节标题",
            "content": "章节内容"
        }}
    ],
    "summary": "内容摘要",
    "key_points": ["要点1", "要点2"],
    "formatted_text": "完整格式化的文本内容（Markdown格式）"
}}
"""
        
        try:
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            execute_system_prompt = get_system_prompt(
                "content_agent_execute",
                fallback="你是一个专业的内容生成专家，擅长生成高质量的结构化内容。"
            )
            
            response = await self.llm.chat([
                {"role": "system", "content": execute_system_prompt},
                {"role": "user", "content": prompt}
            ])
            
            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    return json.loads(response[json_start:json_end])
                else:
                    # 如果没有JSON，直接使用文本作为内容
                    return {
                        "title": task_description,
                        "sections": [{"section_title": "内容", "content": response}],
                        "formatted_text": response
                    }
            else:
                return response
            
        except Exception as e:
            logger.warning(f"LLM content generation failed: {e}")
            return {
                "title": task_description,
                "sections": [{"section_title": "内容", "content": "内容生成失败"}],
                "formatted_text": "内容生成失败，请重试"
            }
    
    def _clean_context_for_json(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理上下文，移除不能JSON序列化的对象（如StandardResult）
        
        Args:
            context: 原始上下文
            
        Returns:
            清理后的上下文
        """
        from ..agents.protocols import StandardResult
        
        clean_context = {}
        for key, value in context.items():
            try:
                # 尝试序列化以检查是否可序列化
                if isinstance(value, StandardResult):
                    # 转换StandardResult为字典
                    clean_context[key] = value.to_dict()
                elif isinstance(value, dict):
                    # 递归清理字典
                    clean_context[key] = self._clean_context_for_json(value)
                elif isinstance(value, list):
                    # 清理列表中的元素
                    clean_context[key] = [
                        item.to_dict() if isinstance(item, StandardResult) else item
                        for item in value
                    ]
                else:
                    # 尝试序列化检查
                    json.dumps(value, ensure_ascii=False)
                    clean_context[key] = value
            except (TypeError, ValueError):
                # 如果不能序列化，转换为字符串
                clean_context[key] = str(value)
        
        return clean_context



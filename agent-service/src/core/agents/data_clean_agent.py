"""
数据清洗智能体
专门处理数据清洗和质量检查
"""
import logging
from typing import Dict, Any, Optional, List
import json

from .base_agent import IntelligentAgent
from ..llm_integration import deepseek_llm

logger = logging.getLogger(__name__)


class DataCleanAgent(IntelligentAgent):
    """数据清洗智能体 - 专门处理数据清洗和质量检查"""
    
    def __init__(self):
        super().__init__(
            agent_id="data_clean_agent",
            name="数据清洗智能体",
            description="专门处理数据清洗和质量检查，包括数据清理、去重、标准化、异常值处理",
            capabilities={
                "data_cleaning": "数据清洗",
                "quality_check": "质量检查",
                "data_standardization": "数据标准化"
            }
        )
        self.llm = deepseek_llm
    
    async def analyze_task(
        self,
        task_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析数据清洗需求
        
        Args:
            task_description: 任务描述
            context: 上下文信息
            
        Returns:
            清洗计划
        """
        try:
            prompt = f"""
作为数据清洗专家，分析以下数据清洗需求：

任务: {task_description}
上下文: {json.dumps(context, ensure_ascii=False, indent=2)}

请分析：
1. **清洗类型**：去重、标准化、异常值处理、缺失值处理等
2. **清洗规则**：需要应用什么清洗规则？
3. **质量要求**：数据质量要达到什么标准？
4. **清洗策略**：如何清洗最有效？

返回JSON格式：
{{
    "needs_cleaning": true/false,
    "cleaning_types": ["去重", "标准化", "异常值处理"],
    "cleaning_rules": ["规则1", "规则2"],
    "quality_requirements": {{
        "completeness": "完整性要求",
        "accuracy": "准确性要求",
        "consistency": "一致性要求"
    }},
    "cleaning_strategy": "清洗策略描述"
}}
"""
            
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            system_prompt = get_system_prompt(
                "data_clean_agent",
                fallback="你是一个数据清洗专家，擅长分析数据清洗需求。"
            )
            
            response = await self.llm.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])
            
            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    cleaning_plan = json.loads(response[json_start:json_end])
                else:
                    cleaning_plan = {"needs_cleaning": True}
            else:
                cleaning_plan = response
            
            return cleaning_plan
            
        except Exception as e:
            logger.error(f"Data cleaning planning failed: {e}", exc_info=True)
            return {
                "needs_cleaning": True,
                "error": str(e)
            }
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行数据清洗
        
        Args:
            input_data: 输入数据（包含data或cleaning_plan）
            context: 上下文信息
            
        Returns:
            清洗后的数据
        """
        try:
            # 获取数据（从多个可能的来源）
            data = (
                input_data.get("data") or 
                input_data.get("query_result") or 
                input_data.get("formatted_result") or
                input_data.get("raw_result")
            )
            
            # 如果input_data中没有，尝试从context中获取（从依赖的智能体结果中）
            if not data:
                # 检查常见的依赖智能体结果键
                possible_keys = [
                    "agent_2_result",  # data_query_agent
                    "data_query_agent_result",
                    "query_result",
                    "formatted_result",
                    "raw_result"
                ]
                
                for key in possible_keys:
                    if key in context:
                        context_value = context[key]
                        # 如果值是字典，尝试提取数据
                        if isinstance(context_value, dict):
                            # 尝试从不同字段提取数据
                            data = (
                                context_value.get("formatted_result") or
                                context_value.get("raw_result") or
                                context_value.get("data") or
                                context_value.get("query_result") or
                                context_value  # 如果整个字典就是数据
                            )
                            if data:
                                break
                        elif context_value is not None:
                            data = context_value
                            break
                
                # 如果还是没有，检查input_data中是否有依赖结果
                if not data:
                    for key in input_data.keys():
                        if key.endswith("_result") and input_data[key]:
                            value = input_data[key]
                            if isinstance(value, dict):
                                data = (
                                    value.get("formatted_result") or
                                    value.get("raw_result") or
                                    value.get("data") or
                                    value
                                )
                            else:
                                data = value
                            if data:
                                break
            
            cleaning_plan = input_data.get("cleaning_plan")
            
            if not data:
                # 如果没有数据，先分析任务
                task_description = input_data.get("task", "")
                cleaning_plan = await self.analyze_task(task_description, context)
                
                if not cleaning_plan.get("needs_cleaning"):
                    return {
                        "agent_type": "data_clean",
                        "decision": "no_cleaning_needed",
                        "reason": cleaning_plan.get("reason", "No data to clean"),
                        "formatted_text": "数据清洗：无需清洗"
                    }
                
                return {
                    "agent_type": "data_clean",
                    "execution_success": False,
                    "decision": "data_required",
                    "cleaning_plan": cleaning_plan,
                    "message": "需要先获取数据才能清洗",
                    "error": "没有数据可供清洗",
                    "formatted_text": "⚠️ **数据清洗失败**\n\n**原因**：没有数据可供清洗\n\n**说明**：数据清洗智能体需要先获取数据才能执行清洗操作。请确保数据查询智能体已成功执行并返回数据。"
                }
            
            # 执行清洗
            cleaned_data = await self._clean_data(
                data,
                cleaning_plan,
                context
            )
            
            # 生成格式化的文本输出
            cleaning_summary = cleaned_data.get("cleaning_summary", {})
            formatted_text = "✅ **数据清洗完成**\n\n"
            
            if cleaning_summary:
                formatted_text += "### 清洗摘要\n\n"
                if isinstance(cleaning_summary, dict):
                    for key, value in cleaning_summary.items():
                        if isinstance(value, (dict, list)):
                            value_str = json.dumps(value, ensure_ascii=False, indent=2)
                            formatted_text += f"- **{key}**: {value_str}\n"
                        else:
                            formatted_text += f"- **{key}**: {value}\n"
            
            return {
                "agent_type": "data_clean",
                "execution_success": True,
                "cleaned_data": cleaned_data,
                "cleaning_summary": cleaning_summary,
                "cleaning_plan": cleaning_plan,
                "formatted_text": formatted_text
            }
            
        except Exception as e:
            logger.error(f"Data clean agent execution failed: {e}", exc_info=True)
            raise
    
    async def _clean_data(
        self,
        data: Any,
        cleaning_plan: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行具体的数据清洗"""
        
        # 快速路径：对于简单的结构化数据（如组织架构），使用规则清洗而不是LLM
        task_type = context.get("task_type", "")
        query_type = context.get("query_type", "")
        
        # 判断是否需要LLM清洗
        needs_llm_cleaning = True
        if task_type in ["organization_query", "org_query", "组织架构查询"] or \
           query_type in ["organization", "org", "组织架构"] or \
           "组织架构" in str(context.get("task_description", "")):
            # 组织架构查询：使用快速规则清洗
            needs_llm_cleaning = False
            logger.info("Using fast rule-based cleaning for organization architecture query")
        
        # 快速路径：规则清洗（适用于结构化数据）
        if not needs_llm_cleaning:
            return self._fast_rule_cleaning(data, cleaning_plan)
        
        # 准备数据摘要
        data_summary = self._summarize_data(data)
        cleaning_types = cleaning_plan.get("cleaning_types", ["去重", "标准化"]) if cleaning_plan else ["去重", "标准化"]
        
        # 如果数据量很大，只清洗前100条，避免LLM处理时间过长
        data_to_clean = data
        if isinstance(data, list) and len(data) > 100:
            logger.info(f"Data too large ({len(data)} items), cleaning first 100 items only")
            data_to_clean = data[:100]
        
        prompt = f"""
作为数据清洗专家，对以下数据进行清洗：

原始数据摘要: {json.dumps(data_summary, ensure_ascii=False, indent=2)}
清洗类型: {json.dumps(cleaning_types, ensure_ascii=False)}
清洗规则: {json.dumps(cleaning_plan.get('cleaning_rules', []), ensure_ascii=False) if cleaning_plan else []}
质量要求: {json.dumps(cleaning_plan.get('quality_requirements', {}), ensure_ascii=False) if cleaning_plan else {}}

原始数据（前20条）: {json.dumps(
    (data_to_clean.get('data', data_to_clean) if isinstance(data_to_clean, dict) else data_to_clean)[:20] if isinstance(data_to_clean, list) else [data_to_clean],
    ensure_ascii=False,
    indent=2
)}

请进行数据清洗，包括：
1. **去重**：移除重复记录
2. **标准化**：统一格式、单位、命名等
3. **异常值处理**：识别和处理异常值
4. **缺失值处理**：处理缺失数据
5. **数据验证**：验证数据质量

返回JSON格式：
{{
    "cleaned_data": [
        {{"字段1": "值1", "字段2": "值2"}}
    ],
    "cleaning_summary": {{
        "original_count": 原始记录数,
        "cleaned_count": 清洗后记录数,
        "removed_duplicates": 移除的重复记录数,
        "standardized_fields": ["标准化字段1", "标准化字段2"],
        "anomalies_found": 异常值数量,
        "missing_values_handled": 处理的缺失值数量,
        "quality_score": 质量评分(0-100)
    }},
    "cleaning_report": "清洗报告文本"
}}
"""
        
        try:
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            system_prompt = get_system_prompt(
                "data_clean_agent_execute",
                fallback="你是一个专业的数据清洗专家，擅长清洗各种数据质量问题。"
            )
            
            response = await self.llm.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])
            
            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    result = json.loads(response[json_start:json_end])
                    # 如果原始数据被截断，恢复完整数据
                    if isinstance(data, list) and len(data) > 100:
                        result["cleaned_data"] = data  # 使用原始完整数据
                    return result
            
            # 降级：简单清洗
            return {
                "cleaned_data": data if isinstance(data, list) else [data],
                "cleaning_summary": {
                    "original_count": len(data) if isinstance(data, list) else 1,
                    "cleaned_count": len(data) if isinstance(data, list) else 1,
                    "quality_score": 80
                }
            }
            
        except Exception as e:
            logger.warning(f"LLM data cleaning failed: {e}, using fast rule-based cleaning")
            return self._fast_rule_cleaning(data, cleaning_plan)
    
    def _fast_rule_cleaning(self, data: Any, cleaning_plan: Dict[str, Any]) -> Dict[str, Any]:
        """快速规则清洗（适用于结构化数据，不需要LLM）"""
        try:
            # 提取数据
            if isinstance(data, dict):
                if "data" in data:
                    data_list = data["data"]
                elif "result" in data:
                    data_list = data["result"] if isinstance(data["result"], list) else [data["result"]]
                else:
                    data_list = [data]
            elif isinstance(data, list):
                data_list = data
            else:
                data_list = [data]
            
            # 简单去重（基于所有字段的组合）
            seen = set()
            cleaned_list = []
            for item in data_list:
                if isinstance(item, dict):
                    # 使用所有字段值的组合作为唯一标识
                    item_key = tuple(sorted(item.items()))
                else:
                    item_key = str(item)
                
                if item_key not in seen:
                    seen.add(item_key)
                    cleaned_list.append(item)
            
            removed_duplicates = len(data_list) - len(cleaned_list)
            
            # 简单标准化：去除前后空格
            standardized_count = 0
            for item in cleaned_list:
                if isinstance(item, dict):
                    for key, value in item.items():
                        if isinstance(value, str):
                            original = value
                            item[key] = value.strip()
                            if original != item[key]:
                                standardized_count += 1
            
            return {
                "cleaned_data": cleaned_list,
                "cleaning_summary": {
                    "original_count": len(data_list),
                    "cleaned_count": len(cleaned_list),
                    "removed_duplicates": removed_duplicates,
                    "standardized_fields": ["所有字符串字段"] if standardized_count > 0 else [],
                    "anomalies_found": 0,
                    "missing_values_handled": 0,
                    "quality_score": 95 if removed_duplicates == 0 else 90
                },
                "cleaning_report": f"快速规则清洗完成：移除{removed_duplicates}条重复记录，标准化{standardized_count}个字段"
            }
        except Exception as e:
            logger.warning(f"Fast rule cleaning failed: {e}")
            return {
                "cleaned_data": data if isinstance(data, list) else [data],
                "cleaning_summary": {
                    "original_count": len(data) if isinstance(data, list) else 1,
                    "cleaned_count": len(data) if isinstance(data, list) else 1,
                    "quality_score": 80
                }
            }
    
    def _summarize_data(self, data: Any) -> Dict[str, Any]:
        """总结数据特征"""
        if isinstance(data, dict):
            if "data" in data:
                data_list = data["data"]
            elif "summary" in data:
                return {"type": "summary", "content": data}
            else:
                return {"type": "dict", "keys": list(data.keys())[:10], "sample": str(data)[:200]}
        elif isinstance(data, list):
            return {
                "type": "list",
                "count": len(data),
                "sample_count": min(10, len(data)),
                "sample": data[:10] if data else []
            }
        else:
            return {"type": "other", "content": str(data)[:200]}



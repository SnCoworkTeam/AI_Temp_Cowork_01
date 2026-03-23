# LLM使用详细分析：代码层面的改进建议

## 一、当前代码中应该使用LLM但没有使用的地方

### 1. 多步骤任务识别（`metadata_first_intent_recognizer.py`）

**位置**：`_llm_understanding_with_metadata` 方法（第529-658行）

**当前问题**：
- LLM提示词没有明确说明如何识别多步骤任务
- 没有要求LLM返回步骤列表和依赖关系

**应该改进**：
```python
# 当前提示词（第542-564行）
system_prompt = f"""你是一个企业业务助手，基于以下业务元数据理解用户需求：

# 业务上下文
{metadata_context}

用户输入: "{user_input}"

请基于以上业务元数据，分析用户的真实业务意图...
"""

# 应该改为：
system_prompt = f"""你是一个企业业务助手，基于以下业务元数据理解用户需求：

# 业务上下文
{metadata_context}

用户输入: "{user_input}"

请基于以上业务元数据，分析用户的真实业务意图。

**重要：如果用户输入包含多个动作（如"分析...然后...发送..."、"查询...形成报告...发送..."），
必须识别为多步骤任务，并返回详细的步骤列表。**

返回JSON格式：
{{
    "entities": ["实体1", "实体2"],
    "operation": "操作类型（如果是多步骤，使用'multi_step_task'）",
    "required_services": ["服务1", "服务2"],
    "required_tools": ["工具1", "工具2"],
    "business_scenario": "业务场景描述",
    "parameters": {{
        "table": "SAP表名（如果是SAP查询）",
        "query": "查询条件（可选）",
        "其他参数": "参数值"
    }},
    "steps": [
        {{
            "step": 1,
            "action": "query",
            "description": "查询销售订单数据",
            "tool": "sap_query",
            "parameters": {{"table": "I_SalesOrder", "query": "分析一下销售订单"}},
            "depends_on": []
        }},
        {{
            "step": 2,
            "action": "analyze",
            "description": "分析查询结果",
            "llm": true,
            "llm_prompt": "基于查询结果进行数据分析",
            "depends_on": [1]
        }},
        {{
            "step": 3,
            "action": "generate_report",
            "description": "生成分析报告",
            "llm": true,
            "llm_prompt": "基于分析结果生成结构化报告",
            "depends_on": [2]
        }},
        {{
            "step": 4,
            "action": "send_email",
            "description": "发送报告邮件",
            "tool": "send_email",
            "parameters": {{
                "to_emails": ["yubin.liu@pcitc.com"],
                "subject": "销售订单分析报告",
                "body": "{{step3_result}}"
            }},
            "depends_on": [3]
        }}
    ],
    "confidence": 0.0-1.0
}}

**步骤说明**：
- 如果用户输入包含"然后"、"接着"、"之后"等连接词，表示多步骤任务
- 每个步骤应该包含：action（动作）、tool或llm（执行方式）、depends_on（依赖的步骤）
- LLM步骤应该包含llm_prompt，说明如何使用LLM处理
"""
```

### 2. 工具执行后的处理（`orchestration_engine.py`）

**位置**：`_handle_tool_execution` 方法（第560-692行）

**当前问题**：
- 只在用户输入包含"分析"关键词时才使用LLM分析
- 没有检查任务上下文是否需要分析
- 没有生成报告的功能
- 没有多步骤编排

**应该改进**：
```python
async def _handle_tool_execution(
    self,
    user_input: str,
    context: Dict[str, Any],
    decision: RoutingDecision,
    intent_analysis: Optional[IntentAnalysis] = None,
    prompt_context: Optional[PromptContext] = None
) -> Dict[str, Any]:
    # ... 现有代码 ...
    
    # 执行工具
    result = await self.service_clients.mcp_gateway.execute_tool(
        tool_id, parameters, context
    )
    
    # 处理工具执行结果
    raw_result = result.get("result") or result.get("output") or {}
    success = result.get("success", False)
    
    if not success:
        # ... 错误处理 ...
    else:
        formatted_result = self._format_tool_result(raw_result, tool_id)
        
        # 检查是否是多步骤任务
        steps = intent_analysis.extracted_context.get("steps", []) if intent_analysis else []
        if steps:
            # 多步骤任务：执行后续步骤
            return await self._execute_multi_step_task(
                steps=steps,
                current_step_result=formatted_result,
                context=context,
                user_input=user_input
            )
        
        # 单步骤任务：检查是否需要分析
        needs_analysis = self._should_analyze(user_input, intent_analysis, context)
        if needs_analysis and deepseek_llm.llm:
            analysis = await self._analyze_with_llm(formatted_result, user_input)
            
            # 检查是否需要生成报告
            needs_report = self._should_generate_report(user_input, intent_analysis, context)
            if needs_report:
                report = await self._generate_report_with_llm(analysis, formatted_result, user_input)
                
                # 检查是否需要发送邮件
                if self._should_send_email(user_input, intent_analysis):
                    email_result = await self._send_email_with_report(
                        report, user_input, intent_analysis, context
                    )
                    return {
                        "success": True,
                        "output": f"✅ 数据分析完成\n\n{formatted_result}\n\n---\n\n## 📊 数据分析\n\n{analysis}\n\n---\n\n## 📄 分析报告\n\n{report}\n\n---\n\n## 📧 邮件发送\n\n{email_result.get('message', '邮件已发送')}",
                        "response": f"✅ 已完成：数据分析、报告生成和邮件发送",
                        "tool_id": tool_id,
                        "raw_result": result
                    }
                
                return {
                    "success": True,
                    "output": f"{formatted_result}\n\n---\n\n## 📊 数据分析\n\n{analysis}\n\n---\n\n## 📄 分析报告\n\n{report}",
                    "response": f"✅ 已完成：数据分析和报告生成",
                    "tool_id": tool_id,
                    "raw_result": result
                }
            
            return {
                "success": True,
                "output": f"{formatted_result}\n\n---\n\n## 📊 数据分析\n\n{analysis}",
                "response": f"✅ 已完成：数据分析",
                "tool_id": tool_id,
                "raw_result": result
            }
        
        # 不需要分析，直接返回
        return {
            "success": True,
            "output": formatted_result,
            "response": formatted_result,
            "tool_id": tool_id,
            "raw_result": result
        }
```

### 3. 多步骤任务执行器（新建）

**新建文件**：`agent-service/src/core/multi_step_executor.py`

```python
"""
多步骤任务执行器
支持执行包含多个步骤的复杂任务，步骤可以是工具调用或LLM处理
"""
import logging
from typing import Dict, Any, List, Optional
from .llm_integration import deepseek_llm

logger = logging.getLogger(__name__)


class MultiStepExecutor:
    """多步骤任务执行器"""
    
    def __init__(self, service_clients):
        self.service_clients = service_clients
    
    async def execute_multi_step_task(
        self,
        steps: List[Dict[str, Any]],
        initial_context: Dict[str, Any],
        user_input: str
    ) -> Dict[str, Any]:
        """
        执行多步骤任务
        
        Args:
            steps: 步骤列表，每个步骤包含：
                - step: 步骤编号
                - action: 动作类型（query, analyze, generate_report, send_email等）
                - tool: 工具名称（如果是工具步骤）
                - llm: 是否使用LLM（如果是LLM步骤）
                - llm_prompt: LLM提示词（如果是LLM步骤）
                - parameters: 参数（如果是工具步骤）
                - depends_on: 依赖的步骤编号列表
            initial_context: 初始上下文
            user_input: 用户输入
            
        Returns:
            执行结果
        """
        results = {}
        context = initial_context.copy()
        
        # 按步骤编号排序
        sorted_steps = sorted(steps, key=lambda x: x.get("step", 0))
        
        for step in sorted_steps:
            step_id = step.get("step", 0)
            action = step.get("action", "")
            depends_on = step.get("depends_on", [])
            
            logger.info(f"Executing step {step_id}: {action}")
            
            # 等待依赖步骤完成
            if depends_on:
                dependencies = {}
                for dep_id in depends_on:
                    if dep_id in results:
                        dependencies[f"step_{dep_id}_result"] = results[dep_id]
                    else:
                        logger.warning(f"Dependency step {dep_id} not found")
                context.update(dependencies)
            
            # 执行步骤
            try:
                if step.get("llm"):
                    # 使用LLM执行
                    result = await self._execute_llm_step(step, context, user_input)
                else:
                    # 使用工具执行
                    result = await self._execute_tool_step(step, context, user_input)
                
                results[step_id] = result
                context[f"step_{step_id}_result"] = result
                context[f"step_{step_id}_output"] = result.get("output", result.get("response", ""))
                
            except Exception as e:
                logger.error(f"Step {step_id} failed: {e}", exc_info=True)
                results[step_id] = {
                    "success": False,
                    "error": str(e),
                    "output": f"步骤 {step_id} 执行失败: {str(e)}"
                }
                # 如果关键步骤失败，停止执行
                if step.get("critical", True):
                    break
        
        # 返回最终结果
        final_output = self._format_final_output(results, sorted_steps)
        return {
            "success": all(r.get("success", False) for r in results.values()),
            "output": final_output,
            "response": final_output,
            "steps": results
        }
    
    async def _execute_llm_step(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any],
        user_input: str
    ) -> Dict[str, Any]:
        """执行LLM步骤"""
        action = step.get("action", "")
        llm_prompt = step.get("llm_prompt", "")
        depends_on = step.get("depends_on", [])
        
        # 构建LLM输入
        if depends_on:
            # 使用依赖步骤的结果
            dependency_results = []
            for dep_id in depends_on:
                dep_result = context.get(f"step_{dep_id}_result", {})
                dep_output = dep_result.get("output", dep_result.get("response", ""))
                dependency_results.append(f"步骤 {dep_id} 的结果：\n{dep_output}")
            
            llm_input = f"""{llm_prompt}

用户请求：{user_input}

依赖步骤的结果：
{chr(10).join(dependency_results)}

请基于以上信息完成任务。"""
        else:
            llm_input = f"""{llm_prompt}

用户请求：{user_input}

请完成任务。"""
        
        # 根据动作类型选择不同的系统提示词
        system_prompts = {
            "analyze": "你是一个专业的业务数据分析师，擅长从数据中提取洞察并提供有价值的建议。",
            "generate_report": "你是一个专业的业务报告撰写专家，擅长将数据分析结果转化为有价值的业务洞察。",
            "summarize": "你是一个专业的总结专家，擅长将复杂信息提炼为简洁明了的总结。",
        }
        
        system_prompt = system_prompts.get(action, "你是一个专业的AI助手，擅长理解和处理各种任务。")
        
        # 调用LLM
        try:
            response = await deepseek_llm.chat(
                messages=[{"role": "user", "content": llm_input}],
                system_prompt=system_prompt,
                temperature=0.7
            )
            
            return {
                "success": True,
                "output": response,
                "response": response,
                "action": action
            }
        except Exception as e:
            logger.error(f"LLM step execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "output": f"LLM处理失败: {str(e)}"
            }
    
    async def _execute_tool_step(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any],
        user_input: str
    ) -> Dict[str, Any]:
        """执行工具步骤"""
        tool_name = step.get("tool", "")
        parameters = step.get("parameters", {})
        depends_on = step.get("depends_on", [])
        
        # 如果参数中包含步骤结果占位符，替换为实际结果
        if depends_on:
            for dep_id in depends_on:
                dep_result = context.get(f"step_{dep_id}_result", {})
                dep_output = dep_result.get("output", dep_result.get("response", ""))
                
                # 替换参数中的占位符
                for key, value in parameters.items():
                    if isinstance(value, str) and f"{{step{dep_id}_result}}" in value:
                        parameters[key] = value.replace(f"{{step{dep_id}_result}}", dep_output)
        
        # 调用工具
        try:
            result = await self.service_clients.mcp_gateway.execute_tool(
                tool_name, parameters, context
            )
            
            return {
                "success": result.get("success", False),
                "output": result.get("result", result.get("output", "")),
                "response": result.get("result", result.get("output", "")),
                "tool": tool_name,
                "raw_result": result
            }
        except Exception as e:
            logger.error(f"Tool step execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "output": f"工具执行失败: {str(e)}"
            }
    
    def _format_final_output(
        self,
        results: Dict[int, Dict[str, Any]],
        steps: List[Dict[str, Any]]
    ) -> str:
        """格式化最终输出"""
        output_parts = []
        
        for step in steps:
            step_id = step.get("step", 0)
            action = step.get("action", "")
            description = step.get("description", action)
            
            if step_id in results:
                result = results[step_id]
                if result.get("success", False):
                    output_parts.append(f"✅ **步骤 {step_id}: {description}**\n\n{result.get('output', '')}\n")
                else:
                    output_parts.append(f"❌ **步骤 {step_id}: {description}**\n\n执行失败: {result.get('error', '未知错误')}\n")
        
        return "\n---\n\n".join(output_parts)
```

### 4. 集成多步骤执行器到编排引擎

**修改文件**：`agent-service/src/core/orchestration_engine.py`

```python
# 在 __init__ 方法中添加
from .multi_step_executor import MultiStepExecutor

class OrchestrationEngine:
    def __init__(self):
        # ... 现有代码 ...
        self.multi_step_executor = MultiStepExecutor(self.service_clients)
    
    # 在 _handle_tool_execution 方法中使用
    async def _handle_tool_execution(...):
        # ... 执行工具 ...
        
        if success:
            formatted_result = self._format_tool_result(raw_result, tool_id)
            
            # 检查是否是多步骤任务
            steps = intent_analysis.extracted_context.get("steps", []) if intent_analysis else []
            if steps:
                # 将当前工具执行结果作为第一步的结果
                step_results = {1: {
                    "success": True,
                    "output": formatted_result,
                    "response": formatted_result
                }}
                
                # 执行后续步骤
                multi_step_result = await self.multi_step_executor.execute_multi_step_task(
                    steps=steps[1:],  # 跳过第一步（已执行）
                    initial_context={
                        **context,
                        "step_1_result": step_results[1],
                        "step_1_output": formatted_result
                    },
                    user_input=user_input
                )
                
                return {
                    "success": multi_step_result.get("success", True),
                    "output": multi_step_result.get("output", ""),
                    "response": multi_step_result.get("response", ""),
                    "steps": {1: step_results[1], **multi_step_result.get("steps", {})}
                }
            
            # ... 单步骤处理 ...
```

## 二、总结

### 应该使用LLM但没有使用的地方

1. **多步骤任务理解**（`metadata_first_intent_recognizer.py`）
   - 当前：LLM提示词没有明确说明如何识别多步骤任务
   - 应该：要求LLM返回详细的步骤列表和依赖关系

2. **任务分解**（`orchestration_engine.py`）
   - 当前：依赖DAG编排器，可能不够智能
   - 应该：使用LLM理解自然语言中的步骤和依赖关系

3. **数据分析**（`orchestration_engine.py`）
   - 当前：只在用户输入包含"分析"关键词时才使用LLM
   - 应该：根据任务上下文自动判断是否需要分析

4. **报告生成**（缺失）
   - 当前：完全没有报告生成功能
   - 应该：使用LLM生成结构化报告

5. **多步骤编排**（部分实现）
   - 当前：有DAG编排器，但可能不够智能
   - 应该：使用LLM理解步骤依赖，实现智能编排

### 改进优先级

1. **高优先级**：
   - 增强意图识别，支持多步骤任务
   - 实现多步骤执行器
   - 实现报告生成功能

2. **中优先级**：
   - 改进工具执行后的LLM处理
   - 增强任务分解的智能性

3. **低优先级**：
   - 优化LLM提示词
   - 改进错误处理



"""
MCP工具智能体（优化版）
专门管理和执行MCP工具，去除硬编码，添加缓存和性能优化
"""
import logging
import re
import time
import hashlib
from typing import Dict, Any, Optional, List
import json

from .base_agent import IntelligentAgent
from ..llm_integration import deepseek_llm

logger = logging.getLogger(__name__)


class MCPToolAgent(IntelligentAgent):
    """MCP工具智能体（优化版）- 带缓存和动态分类，不处理SAP工具"""
    
    def __init__(self, mcp_gateway=None):
        """
        初始化MCP工具智能体
        
        Args:
            mcp_gateway: MCP Gateway客户端（可选，默认使用service_clients）
        """
        super().__init__(
            agent_id="mcp_tool_agent",
            name="MCP工具智能体",
            description="专门管理和执行MCP工具，包括工具选择、参数优化、错误处理（不包含SAP工具）",
            capabilities={
                "tool_execution": "执行MCP工具",
                "tool_selection": "智能选择工具",
                "parameter_optimization": "优化工具参数",
                "error_handling": "工具错误处理"
            }
        )
        # 延迟导入避免循环依赖
        if mcp_gateway is None:
            from ..service_clients import service_clients
            self.mcp_gateway = service_clients.mcp_gateway
        else:
            self.mcp_gateway = mcp_gateway
        self.llm = deepseek_llm
        
        # 缓存机制
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
        self._tools_cache_time: Optional[float] = None
        self._tools_cache_ttl: float = 300.0  # 5分钟缓存
        
        self._analysis_cache: Dict[str, Dict[str, Any]] = {}
        self._analysis_cache_ttl: float = 600.0  # 10分钟缓存
    
    def _is_cache_valid(self, cache_time: Optional[float], ttl: float) -> bool:
        """检查缓存是否有效"""
        if cache_time is None:
            return False
        return (time.time() - cache_time) < ttl
    
    def _generate_cache_key(self, task: str, context: Dict[str, Any]) -> str:
        """生成缓存键"""
        # 提取关键信息
        key_data = {
            "task": task,
            "context_keys": sorted(context.keys())
        }
        # 添加关键上下文值
        for key in ["user_input", "query", "request"]:
            if key in context:
                key_data[key] = str(context[key])[:100]  # 限制长度
        
        key_str = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    async def get_tools(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """带缓存的工具获取（SAP工具已在MCP Gateway层面被过滤）"""
        if not force_refresh and self._is_cache_valid(self._tools_cache_time, self._tools_cache_ttl):
            logger.debug("Using cached tools list")
            return self._tools_cache or []
        
        try:
            tools = await self.mcp_gateway.list_tools()
            # 注意：SAP工具已经在MCP Gateway层面被过滤，这里不需要再次过滤
            self._tools_cache = tools
            self._tools_cache_time = time.time()
            logger.info(f"Refreshed tools cache: {len(tools)} tools")
            return tools
        except Exception as e:
            logger.warning(f"Failed to list tools: {e}, using cached tools if available")
            return self._tools_cache or []
    
    def _get_optimal_tool_limit(self, task_complexity: str) -> int:
        """基于任务复杂度动态确定工具数量限制"""
        limits = {
            "simple": 10,      # 简单查询
            "medium": 20,      # 中等复杂度
            "complex": 50,     # 复杂分析
            "exploratory": 100  # 探索性任务
        }
        return limits.get(task_complexity, 20)
    
    def _estimate_task_complexity(self, task: str, context: Dict[str, Any]) -> str:
        """估算任务复杂度"""
        task_lower = task.lower()
        context_str = str(context).lower()
        
        # 简单任务：单一操作、明确目标
        if any(keyword in task_lower for keyword in ["查询", "查", "获取", "get", "fetch", "计算", "calculate"]):
            if len(task) < 50 and len(context_str) < 200:
                return "simple"
        
        # 复杂任务：多步骤、需要分析
        if any(keyword in task_lower for keyword in ["分析", "analyze", "生成报告", "generate report", "综合", "comprehensive"]):
            return "complex"
        
        # 探索性任务：需要探索多个选项
        if any(keyword in task_lower for keyword in ["探索", "explore", "发现", "discover", "查找所有", "find all"]):
            return "exploratory"
        
        # 默认中等复杂度
        return "medium"
    
    async def _extract_context_dynamically(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """动态提取上下文关键信息（使用LLM，带降级）"""
        try:
            # 如果上下文很小，直接返回
            if len(str(context)) < 500:
                return context
            
            # 使用LLM提取关键信息
            from ..prompt_utils import get_system_prompt
            context_system_prompt = get_system_prompt(
                "mcp_tool_agent_context",
                fallback="你是一个上下文提取专家，擅长从复杂上下文中提取关键信息。"
            )
            
            prompt = f"""
从以下上下文中提取关键信息，用于工具选择和参数提取：

上下文: {json.dumps(context, ensure_ascii=False, indent=2)[:2000]}

请提取：
1. 用户输入或查询内容
2. 关键参数值（如收件人、主题、内容等）
3. 业务实体或对象
4. 操作类型或意图

返回JSON格式：
{{
    "user_input": "用户输入",
    "key_parameters": {{"参数名": "参数值"}},
    "entities": ["实体1", "实体2"],
    "operation_type": "操作类型"
}}
"""
            
            response = await self.llm.chat([
                {
                    "role": "system",
                    "content": context_system_prompt
                },
                {"role": "user", "content": prompt}
            ])
            
            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    return json.loads(response[json_start:json_end])
            
            # 降级：简单提取
            return self._simple_context_extraction(context)
            
        except Exception as e:
            logger.warning(f"Failed to extract context dynamically: {e}")
            return self._simple_context_extraction(context)
    
    def _simple_context_extraction(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """简单上下文提取（降级方案）"""
        context_summary = {}
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)):
                context_summary[key] = value
            elif isinstance(value, dict):
                # 动态检测关键字段（不硬编码字段名）
                value_str = str(value).lower()
                if any(k in value_str for k in ["content", "report", "result", "data", "message", "text", "body"]):
                    context_summary[key] = str(value)[:200]  # 动态长度限制
        return context_summary
    
    async def _get_prompt_template_from_db(self) -> Optional[str]:
        """从数据库获取提示词模板"""
        try:
            from ..database import get_db
            from database.src.models.prompt_template import PromptTemplate
            from sqlalchemy.orm import Session
            
            db_gen = get_db()
            db: Session = next(db_gen)
            
            try:
                # 查找mcp_tool_agent的提示词模板
                prompt = db.query(PromptTemplate).filter(
                    PromptTemplate.name == "mcp_tool_agent_analysis",
                    PromptTemplate.is_active == True
                ).first()
                
                if prompt and prompt.system_prompt:
                    return prompt.system_prompt
            finally:
                db.close()
        except Exception as e:
            logger.debug(f"Failed to load prompt from database: {e}")
        
        return None
    
    async def analyze_task(
        self,
        task_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析任务并选择最佳工具
        
        Args:
            task_description: 任务描述
            context: 上下文信息
            
        Returns:
            工具执行计划
        """
        try:
            # 检查缓存
            cache_key = self._generate_cache_key(task_description, context)
            if cache_key in self._analysis_cache:
                cached = self._analysis_cache[cache_key]
                if self._is_cache_valid(cached.get("timestamp"), self._analysis_cache_ttl):
                    logger.debug(f"Using cached analysis result for: {task_description[:50]}")
                    return cached["result"]
            
            # 获取可用工具列表（带缓存，SAP工具已在MCP Gateway层面被过滤）
            available_tools = await self.get_tools()
            
            if not available_tools:
                return {
                    "needs_tool": False,
                    "reason": "No tools available"
                }
            
            # 动态提取上下文
            context_summary = await self._extract_context_dynamically(context)
            
            # 动态确定工具数量限制（基于任务复杂度）
            task_complexity = self._estimate_task_complexity(task_description, context)
            tool_limit = self._get_optimal_tool_limit(task_complexity)
            
            # 构建增强的工具信息，充分利用工具的所有可用信息
            tools_info = []
            for tool in available_tools[:tool_limit]:
                tool_info = {
                    "name": tool.get("name"),
                    "description": tool.get("description", ""),
                    "tool_type": tool.get("tool_type", "function"),
                    "status": tool.get("status", "active")
                }
                
                # 提取参数信息（支持JSON Schema格式和直接字典格式）
                parameters = tool.get("parameters", {})
                if parameters:
                    # 如果是JSON Schema格式，提取properties
                    if isinstance(parameters, dict) and "properties" in parameters:
                        param_properties = parameters.get("properties", {})
                        required_params = parameters.get("required", [])
                        tool_info["parameters"] = {
                            "schema": "json_schema",
                            "properties": param_properties,
                            "required": required_params
                        }
                    else:
                        # 直接参数字典格式
                        tool_info["parameters"] = {
                            "schema": "direct",
                            "properties": parameters
                        }
                
                # 添加必需参数列表
                if tool.get("required_parameters"):
                    tool_info["required_parameters"] = tool.get("required_parameters")
                
                # 添加返回值定义
                if tool.get("returns"):
                    tool_info["returns"] = tool.get("returns")
                
                # 添加元数据（如果有）
                if tool.get("metadata"):
                    tool_info["metadata"] = tool.get("metadata")
                
                tools_info.append(tool_info)
            
            # 尝试从数据库加载提示词模板
            base_prompt_template = await self._get_prompt_template_from_db()
            
            # 构建Few-Shot示例（针对邮件发送工具）
            few_shot_examples = ""
            if any(tool.get("name") == "send_email" for tool in available_tools):
                few_shot_examples = """
**参数提取示例（send_email工具）**：

示例1：简单邮件
- 输入："发送测试邮件给yubin.liu@pcitc.com"
- 提取参数：
  - to_emails: "yubin.liu@pcitc.com" (从任务描述中查找包含"@"的字符串)
  - subject: "测试邮件" (从"测试邮件"推断，如果没有明确主题则使用默认值)
  - body: "这是一封测试邮件。" (如果没有明确正文，使用合理的默认值)

示例2：完整邮件
- 输入："给yubin.liu@pcitc.com发邮件，主题是会议通知，内容是明天下午3点开会"
- 提取参数：
  - to_emails: "yubin.liu@pcitc.com" (从"给XXX发"模式或直接查找邮箱)
  - subject: "会议通知" (从"主题是"后提取)
  - body: "明天下午3点开会" (从"内容是"后提取)

示例3：中文表达
- 输入："发送邮件给yubin.liu@pcitc.com，主题会议通知"
- 提取参数：
  - to_emails: "yubin.liu@pcitc.com" (查找包含"@"的字符串)
  - subject: "会议通知" (从"主题"后提取)
  - body: "这是一封邮件。" (使用默认值)

**参数提取规则**：
1. **邮箱地址提取**：
   - 必须查找任务描述中包含"@"的字符串（邮箱地址格式）
   - 支持模式："给XXX发"、"发送给XXX"、"发给XXX"（XXX是邮箱地址）
   - 如果找到多个邮箱，使用数组格式 ["email1@example.com", "email2@example.com"]
   - 如果只找到一个邮箱，可以使用字符串 "email@example.com" 或数组 ["email@example.com"]

2. **主题提取**：
   - 查找"主题："、"标题："、"关于："等关键词后的内容
   - 如果没有明确主题关键词，从任务描述推断（如"测试邮件" -> "测试邮件"）
   - 如果无法推断，使用合理的默认值（如"邮件"、"通知"等）

3. **正文提取**：
   - 查找"正文："、"内容："等关键词后的内容
   - 如果没有明确正文关键词，使用合理的默认值（如"这是一封邮件。"）

4. **参数验证（重要）**：
   - 在返回前，必须检查所有必需参数是否存在
   - 如果参数缺失，使用上述规则补充
   - 确保参数格式符合工具定义（to_emails可以是字符串或数组）

"""
            
            # 如果从数据库加载了模板，使用它；否则使用硬编码的模板
            if base_prompt_template:
                prompt = f"""{base_prompt_template}

**任务描述**：
{task_description}

**可用MCP工具列表**（包含完整信息）：
{json.dumps(tools_info, ensure_ascii=False, indent=2)}

**上下文信息**：
{json.dumps(context_summary, ensure_ascii=False, indent=2)}

{few_shot_examples}

**返回JSON格式**：
{{
    "needs_tool": true/false,
    "selected_tool": "工具名称（如果needs_tool为true，必须提供）",
    "optimized_parameters": {{
        "参数名": "参数值",
        // 重要：必须包含所有必需参数，不能遗漏
        // 对于send_email工具，必须包含：to_emails, subject, body
    }},
    "execution_strategy": "direct|preprocess|batch",
    "reasoning": "详细的分析过程，包括：任务需求分析、工具能力分析、匹配度评估、参数提取逻辑（必须说明每个参数是如何提取的）",
    "direct_result": "如果不需要工具且可以直接给出结果（如数学计算），在这里提供用户友好的结果格式"
}}

**重要提醒**：
- 在返回optimized_parameters之前，必须验证所有必需参数都存在
- 如果参数缺失，必须使用上述规则补充
- 不要遗漏任何必需参数，否则工具执行会失败
"""
            else:
                # 使用硬编码的模板（向后兼容）
                prompt = f"""
作为MCP工具智能体，深度分析以下任务并选择合适的工具。

**任务描述**：
{task_description}

**可用MCP工具列表**（包含完整信息）：
{json.dumps(tools_info, ensure_ascii=False, indent=2)}

**上下文信息**：
{json.dumps(context_summary, ensure_ascii=False, indent=2)}

{few_shot_examples}

**分析要求**：

1. **任务深度分析**：
   - 任务的核心需求是什么？
   - 需要执行什么类型的操作？（查询、发送、生成、转换等）
   - 需要访问什么数据源或系统？
   - 期望的输出形式是什么？

2. **工具能力匹配**：
   - 仔细检查每个工具的参数定义（parameters），理解工具的具体能力
   - 检查必需参数（required_parameters），确保任务能提供这些参数
   - 分析工具类型（tool_type）和元数据（metadata），理解工具的适用场景
   - 找到最能满足任务需求的工具

3. **参数提取（关键步骤）**：
   - **必须从任务描述中提取所有必需参数**
   - 对于邮箱地址：查找包含"@"的字符串
   - 对于主题：查找"主题"、"标题"等关键词后的内容，或从任务描述推断
   - 对于正文：查找"正文"、"内容"等关键词后的内容，或使用默认值
   - 从上下文信息中提取参数值（如果任务描述中没有）
   - **在返回前，验证所有必需参数都存在，如果缺失则使用规则补充**
   - 参数值必须符合工具的参数定义（类型、格式等）

4. **判断逻辑**：
   - 如果任务需要调用外部系统、执行操作、访问数据源，且工具列表中有匹配的工具，则必须使用工具
   - 如果任务只是询问信息或生成文本，且不需要外部系统，则可能不需要工具
   - 如果是简单的数学计算、文本处理等基础操作，不需要工具，直接返回结果
   - 必须基于工具的实际能力（参数定义、必需参数等）来判断，而不是仅凭工具名称

**返回JSON格式**：
{{
    "needs_tool": true/false,
    "selected_tool": "工具名称（如果needs_tool为true，必须提供）",
    "optimized_parameters": {{
        "参数名": "参数值",
        // 重要：必须包含所有必需参数，不能遗漏
        // 对于send_email工具，必须包含：to_emails, subject, body
    }},
    "execution_strategy": "direct|preprocess|batch",
    "reasoning": "详细的分析过程，包括：任务需求分析、工具能力分析、匹配度评估、参数提取逻辑（必须说明每个参数是如何提取的）",
    "direct_result": "如果不需要工具且可以直接给出结果（如数学计算），在这里提供用户友好的结果格式"
}}

**重要提醒**：
- 在返回optimized_parameters之前，必须验证所有必需参数都存在
- 如果参数缺失，必须使用上述规则补充
- 不要遗漏任何必需参数，否则工具执行会失败
"""
            
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            analysis_system_prompt = get_system_prompt(
                "mcp_tool_agent_analysis",
                fallback="你是一个MCP工具智能体，负责分析任务并选择合适的MCP工具执行。你需要仔细分析任务需求，检查可用工具列表，智能判断是否需要工具以及选择哪个工具。"
            )
            
            response = await self.llm.chat([
                {
                    "role": "system", 
                    "content": analysis_system_prompt
                },
                {"role": "user", "content": prompt}
            ])
            
            # 解析响应
            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    execution_plan = json.loads(response[json_start:json_end])
                else:
                    # 降级：简单匹配
                    execution_plan = await self._simple_tool_match(task_description, available_tools)
            else:
                execution_plan = response
            
            # 缓存结果
            self._analysis_cache[cache_key] = {
                "result": execution_plan,
                "timestamp": time.time()
            }
            
            return execution_plan
            
        except Exception as e:
            logger.error(f"Tool analysis failed: {e}", exc_info=True)
            return {
                "needs_tool": False,
                "error": str(e)
            }
    
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行工具调用
        
        Args:
            input_data: 输入数据（包含task或execution_plan）
            context: 上下文信息
            
        Returns:
            执行结果
        """
        try:
            # 获取执行计划
            task_description = input_data.get("task", "")
            execution_plan = input_data.get("execution_plan")
            
            if not execution_plan:
                # 如果没有执行计划，先分析任务
                execution_plan = await self.analyze_task(task_description, context)
            
            # 如果analyze_task返回needs_tool=False，直接返回
            # 信任LLM的判断，不再进行二次检查
            if not execution_plan.get("needs_tool"):
                reason = execution_plan.get("reasoning") or execution_plan.get("reason", "Task does not require tool execution")
                
                # 优先使用LLM直接提供的结果（如果存在）
                direct_result = execution_plan.get("direct_result")
                if direct_result:
                    formatted_output = direct_result
                else:
                    # 如果没有直接结果，使用LLM格式化响应
                    formatted_output = await self._format_no_tool_response(task_description, reason)
                
                return {
                    "agent_type": "mcp_tool",
                    "decision": "no_tool_needed",
                    "reason": reason,
                    "output": formatted_output,  # 添加友好的输出
                    "response": formatted_output  # 兼容字段
                }
            
            tool_name = execution_plan.get("selected_tool")
            tool_params = execution_plan.get("optimized_parameters", {})
            
            if not tool_name:
                return {
                    "agent_type": "mcp_tool",
                    "decision": "no_tool_selected",
                    "error": "No tool selected in execution plan"
                }
            
            # 执行MCP工具（使用缓存的工具列表）
            try:
                tools = await self.get_tools()
                tool_info = next((t for t in tools if t.get("name") == tool_name), None)
                
                if not tool_info:
                    raise ValueError(f"Tool {tool_name} not found")
                
                # 参数验证：检查必需参数是否存在
                # 如果LLM提取失败，记录警告（但不硬编码补充，让LLM自己学习）
                required_params = tool_info.get("required_parameters", [])
                missing_params = [p for p in required_params if p not in tool_params or not tool_params.get(p)]
                
                if missing_params:
                    logger.warning(
                        f"LLM提取的参数不完整，缺失必需参数: {missing_params}. "
                        f"工具: {tool_name}, 任务: {task_description}, "
                        f"已提取参数: {tool_params}. "
                        f"这可能是prompt设计问题，需要改进Few-Shot示例或参数提取规则。"
                    )
                    # 不硬编码补充，让错误暴露出来，以便改进prompt
                
                tool_id = tool_info.get("id") or tool_name
                tool_result = await self.mcp_gateway.execute_tool(
                    tool_id,
                    tool_params
                )
                
                # 理解工具输出
                understood_result = await self._understand_tool_output(
                    tool_result,
                    tool_name,
                    context
                )
                
                return {
                    "agent_type": "mcp_tool",
                    "tool_executed": tool_name,
                    "execution_success": True,
                    "raw_result": tool_result,
                    "understood_result": understood_result,
                    "execution_plan": execution_plan
                }
                
            except Exception as e:
                # 工具执行失败，提供智能降级
                return await self._handle_tool_failure(
                    tool_name,
                    tool_params,
                    e,
                    execution_plan,
                    context
                )
                
        except Exception as e:
            logger.error(f"MCP tool agent execution failed: {e}", exc_info=True)
            raise
    
    async def _enhance_tool_parameters(
        self,
        tool_name: str,
        tool_params: Dict[str, Any],
        task_description: str,
        tool_info: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        增强工具参数：补充缺失的必需参数
        
        Args:
            tool_name: 工具名称
            tool_params: 当前参数
            task_description: 任务描述
            tool_info: 工具信息
            context: 上下文
            
        Returns:
            增强后的参数字典
        """
        enhanced_params = tool_params.copy()
        required_params = tool_info.get("required_parameters", [])
        
        # 特殊处理：send_email工具
        if tool_name == "send_email":
            # 提取邮箱地址（如果缺失）
            if "to_emails" not in enhanced_params or not enhanced_params.get("to_emails"):
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, task_description)
                
                # 也尝试从"给XXX发"等模式提取
                send_patterns = [
                    r'给\s*([^\s]+@[^\s]+)\s*发',
                    r'发送给\s*([^\s]+@[^\s]+)',
                    r'发给\s*([^\s]+@[^\s]+)',
                    r'给\s*([^\s]+@[^\s]+)\s*发送',
                ]
                for pattern in send_patterns:
                    match = re.search(pattern, task_description)
                    if match:
                        email = match.group(1).strip()
                        if '@' in email:
                            emails.append(email)
                
                if emails:
                    # 去重并确保是列表格式
                    unique_emails = list(dict.fromkeys(emails))  # 保持顺序的去重
                    enhanced_params["to_emails"] = unique_emails if len(unique_emails) > 1 else unique_emails[0] if unique_emails else None
                    logger.info(f"Extracted to_emails from task description: {enhanced_params['to_emails']}")
            
            # 提取主题（如果缺失）
            if "subject" not in enhanced_params or not enhanced_params.get("subject"):
                # 尝试从任务描述中提取主题
                subject_patterns = [
                    r'主题[：:]\s*([^\n，,]+)',
                    r'标题[：:]\s*([^\n，,]+)',
                    r'关于[：:]\s*([^\n，,]+)',
                ]
                for pattern in subject_patterns:
                    match = re.search(pattern, task_description)
                    if match:
                        enhanced_params["subject"] = match.group(1).strip()
                        logger.info(f"Extracted subject from task description: {enhanced_params['subject']}")
                        break
                
                # 如果没有找到，使用默认值
                if "subject" not in enhanced_params or not enhanced_params.get("subject"):
                    # 从任务描述中提取关键词作为主题
                    if "测试" in task_description:
                        enhanced_params["subject"] = "测试邮件"
                    elif "通知" in task_description:
                        enhanced_params["subject"] = "通知"
                    else:
                        enhanced_params["subject"] = "邮件"
                    logger.info(f"Using default subject: {enhanced_params['subject']}")
            
            # 提取正文（如果缺失）
            if "body" not in enhanced_params or not enhanced_params.get("body"):
                # 尝试从任务描述中提取正文
                body_patterns = [
                    r'内容[：:]\s*([^\n]+)',
                    r'正文[：:]\s*([^\n]+)',
                    r'，\s*([^，,]+)$',  # 最后一个逗号后的内容
                ]
                for pattern in body_patterns:
                    match = re.search(pattern, task_description)
                    if match:
                        body = match.group(1).strip()
                        # 如果提取的内容不是邮箱地址，使用它
                        if '@' not in body:
                            enhanced_params["body"] = body
                            logger.info(f"Extracted body from task description: {enhanced_params['body']}")
                            break
                
                # 如果没有找到，使用默认值
                if "body" not in enhanced_params or not enhanced_params.get("body"):
                    enhanced_params["body"] = "这是一封测试邮件。"
                    logger.info(f"Using default body: {enhanced_params['body']}")
        
        # 通用检查：验证所有必需参数是否存在
        missing_params = []
        for req_param in required_params:
            if req_param not in enhanced_params or not enhanced_params.get(req_param):
                missing_params.append(req_param)
        
        if missing_params:
            logger.warning(f"Missing required parameters for {tool_name}: {missing_params}")
            logger.warning(f"Current parameters: {enhanced_params}")
            logger.warning(f"Task description: {task_description}")
        
        return enhanced_params
    
    async def _understand_tool_output(
        self,
        tool_result: Any,
        tool_name: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """理解工具输出（使用LLM）"""
        try:
            prompt = f"""
工具 "{tool_name}" 的执行结果：

{json.dumps(tool_result, ensure_ascii=False, indent=2)}

请分析：
1. **结果类型**：数据、错误、状态等
2. **关键信息**：提取重要信息
3. **业务含义**：在业务上下文中的含义
4. **后续建议**：下一步应该做什么？

返回JSON格式：
{{
    "result_type": "数据|错误|状态",
    "key_information": ["信息1", "信息2"],
    "business_meaning": "业务含义描述",
    "next_steps": ["建议1", "建议2"]
}}
"""
            
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            output_analysis_prompt = get_system_prompt(
                "mcp_tool_agent_output",
                fallback="你是一个工具输出分析专家，擅长理解工具执行结果。"
            )
            
            response = await self.llm.chat([
                {"role": "system", "content": output_analysis_prompt},
                {"role": "user", "content": prompt}
            ])
            
            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    return json.loads(response[json_start:json_end])
            
            return {
                "result_type": "unknown",
                "key_information": [],
                "business_meaning": "无法理解工具输出",
                "next_steps": []
            }
            
        except Exception as e:
            logger.warning(f"Failed to understand tool output: {e}")
            return {
                "result_type": "raw",
                "raw_result": tool_result
            }
    
    async def _handle_tool_failure(
        self,
        tool_name: str,
        tool_params: Dict[str, Any],
        error: Exception,
        execution_plan: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理工具执行失败"""
        error_handling = execution_plan.get("error_handling", {})
        retry_count = error_handling.get("retry_count", 0)
        fallback_tool = error_handling.get("fallback_tool")
        
        # 尝试重试
        if retry_count > 0:
            logger.info(f"Retrying tool {tool_name} (attempts left: {retry_count})")
            try:
                tool_result = await self.mcp_gateway.execute_tool(tool_name, tool_params)
                return {
                    "agent_type": "mcp_tool",
                    "tool_executed": tool_name,
                    "execution_success": True,
                    "raw_result": tool_result,
                    "retried": True
                }
            except Exception as retry_error:
                logger.warning(f"Tool retry failed: {retry_error}")
        
        # 尝试备选工具
        if fallback_tool:
            logger.info(f"Trying fallback tool: {fallback_tool}")
            try:
                tool_result = await self.mcp_gateway.execute_tool(fallback_tool, tool_params)
                return {
                    "agent_type": "mcp_tool",
                    "tool_executed": fallback_tool,
                    "execution_success": True,
                    "raw_result": tool_result,
                    "used_fallback": True,
                    "original_tool": tool_name
                }
            except Exception as fallback_error:
                logger.warning(f"Fallback tool failed: {fallback_error}")
        
        # 返回错误信息
        return {
            "agent_type": "mcp_tool",
            "tool_executed": tool_name,
            "execution_success": False,
            "error": str(error),
            "error_type": type(error).__name__,
            "suggestion": "工具执行失败，建议检查工具参数或使用其他工具"
        }
    
    async def _simple_tool_match(
        self,
        task_description: str,
        available_tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """简单工具匹配（降级方案）"""
        task_lower = task_description.lower()
        
        # 简单的关键词匹配
        for tool in available_tools:
            tool_name = tool.get("name", "").lower()
            tool_desc = tool.get("description", "").lower()
            
            # 检查工具名称或描述是否匹配任务
            if any(keyword in task_lower for keyword in [tool_name, *tool_desc.split()]):
                return {
                    "needs_tool": True,
                    "selected_tool": tool.get("name"),
                    "optimized_parameters": {},
                    "execution_strategy": "direct",
                    "reasoning": f"Simple keyword match: {tool_name}"
                }
        
        return {
            "needs_tool": False,
            "reason": "No matching tool found"
        }
    
    async def _format_no_tool_response(self, task_description: str, reason: str) -> str:
        """
        使用LLM格式化"不需要工具"的响应，提取关键信息并生成用户友好的格式
        
        Args:
            task_description: 任务描述
            reason: LLM 返回的原因
            
        Returns:
            格式化后的响应文本
        """
        try:
            # 使用LLM提取关键信息并格式化
            prompt = f"""
请将以下信息格式化为用户友好的响应格式。

任务：{task_description}

LLM分析结果：
{reason}

要求：
1. 如果是数学计算问题，直接显示计算结果，格式：**计算结果：XXX**
2. 如果是其他不需要工具的问题，提取关键信息，简洁明了地回复
3. 移除冗长的分析过程，只保留用户关心的结果
4. 使用Markdown格式，使输出更易读

请直接返回格式化后的响应，不要包含其他说明。
"""
            
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            format_system_prompt = get_system_prompt(
                "mcp_tool_agent_format",
                fallback="你是一个响应格式化专家，擅长将技术性的分析结果转换为用户友好的格式。"
            )
            
            formatted = await self.llm.chat([
                {
                    "role": "system",
                    "content": format_system_prompt
                },
                {"role": "user", "content": prompt}
            ])
            
            return formatted.strip()
            
        except Exception as e:
            logger.warning(f"Failed to format response with LLM: {e}")
            # 降级：简单提取关键信息
            return self._simple_format_fallback(reason)
    
    def _simple_format_fallback(self, reason: str) -> str:
        """
        简单的格式化降级方案（不使用LLM）
        
        Args:
            reason: LLM 返回的原因
            
        Returns:
            格式化后的响应文本
        """
        # 尝试提取结论或结果
        # 查找"结果"、"结论"、"答案"等关键词
        result_patterns = [
            r'结果[：:]\s*(\d+)',
            r'结论[：:](.+?)(?:\n|$)',
            r'答案[：:](.+?)(?:\n|$)',
            r'等于\s*(\d+)',
            r'=\s*(\d+)'
        ]
        
        for pattern in result_patterns:
            match = re.search(pattern, reason)
            if match:
                result = match.group(1).strip()
                # 如果是数字，可能是计算结果
                if result.isdigit():
                    return f"**计算结果：{result}**"
                return result
        
        # 如果太长，提取关键部分
        if len(reason) > 300:
            # 提取最后一段（通常是结论）
            paragraphs = [p.strip() for p in reason.split('\n') if p.strip()]
            if paragraphs:
                last_para = paragraphs[-1]
                if len(last_para) < 200:
                    return last_para
            return reason[:200] + "..."
        
        return reason


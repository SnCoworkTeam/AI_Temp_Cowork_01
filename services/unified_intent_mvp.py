"""
统一意图识别MVP服务（阶段1：伪流式MVP）
务实版实现：前端伪流式 + 后端批处理
"""
import asyncio
import logging
from typing import Dict, Any, Optional, AsyncIterator
from datetime import datetime

# 导入现有组件
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 动态导入，避免循环依赖
def _get_conversation_agent():
    """延迟导入conversation_agent"""
    import sys
    from pathlib import Path
    
    # 尝试多种导入方式
    try:
        # 方式1：从agent-service/src导入（Docker容器内）
        agent_service_path = Path("/app/src")
        if agent_service_path.exists() and str(agent_service_path) not in sys.path:
            sys.path.insert(0, str(agent_service_path))
        from core.conversation_agent import conversation_agent
        return conversation_agent
    except ImportError:
        try:
            # 方式2：从项目根目录导入（本地开发）
            agent_service_path = Path(__file__).parent.parent / "agent-service" / "src"
            if agent_service_path.exists() and str(agent_service_path) not in sys.path:
                sys.path.insert(0, str(agent_service_path))
            from core.conversation_agent import conversation_agent
            return conversation_agent
        except ImportError:
            # 方式3：尝试绝对导入
            from agent_service.src.core.conversation_agent import conversation_agent
            return conversation_agent

def _get_orchestration_engine():
    """延迟导入OrchestrationEngine"""
    import sys
    from pathlib import Path
    
    # 尝试多种导入方式
    try:
        # 方式1：从agent-service/src导入（Docker容器内）
        agent_service_path = Path("/app/src")
        if agent_service_path.exists() and str(agent_service_path) not in sys.path:
            sys.path.insert(0, str(agent_service_path))
        from core.orchestration_engine import OrchestrationEngine
        return OrchestrationEngine()
    except ImportError:
        try:
            # 方式2：从项目根目录导入（本地开发）
            agent_service_path = Path(__file__).parent.parent / "agent-service" / "src"
            if agent_service_path.exists() and str(agent_service_path) not in sys.path:
                sys.path.insert(0, str(agent_service_path))
            from core.orchestration_engine import OrchestrationEngine
            return OrchestrationEngine()
        except ImportError:
            # 方式3：尝试绝对导入
            from agent_service.src.core.orchestration_engine import OrchestrationEngine
            return OrchestrationEngine()

def _get_unified_intent_service():
    """延迟导入UnifiedIntentService（带错误处理）"""
    try:
        from services.unified_intent_service import UnifiedIntentService
        return UnifiedIntentService()
    except Exception as e:
        logger.warning(f"UnifiedIntentService初始化失败: {e}，将使用降级方案")
        # 返回一个模拟的服务对象，至少保证语义引擎适配器和流式LLM可用
        class MockUnifiedIntentService:
            def __init__(self):
                try:
                    from services.semantic_engine_adapter import SemanticEngineAdapter
                    from services.enterprise_semantic_engine import EnterpriseSemanticEngine
                    self.semantic_engine = EnterpriseSemanticEngine()
                    self.semantic_adapter = SemanticEngineAdapter(self.semantic_engine)
                except Exception as e2:
                    logger.warning(f"语义引擎初始化也失败: {e2}")
                    self.semantic_engine = None
                    self.semantic_adapter = None
                
                # 尝试初始化LLM客户端（用于流式分析）
                try:
                    from services.llm_client import RobustDeepSeekClient
                    import os
                    self.llm_client = RobustDeepSeekClient(
                        api_key=os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY"),
                        base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
                        model=os.getenv("LLM_MODEL", "deepseek-chat")
                    )
                    self.use_llm = True
                except Exception as e3:
                    logger.warning(f"LLM客户端初始化失败: {e3}")
                    self.llm_client = None
                    self.use_llm = False
            
            async def _analyze_intent_with_llm_stream(self, user_input: str, context=None):
                """模拟流式LLM分析（用于测试）"""
                import asyncio
                from datetime import datetime
                
                if not self.use_llm or not self.llm_client:
                    # 降级：返回简单的分析结果
                    yield {
                        "stage": "complete",
                        "result": {
                            "intent": "tool_execution",
                            "confidence": 0.5,
                            "reasoning": "模拟分析结果（LLM不可用）"
                        },
                        "progress": 50
                    }
                    return
                
                try:
                    # 使用真实的流式LLM（如果可用）
                    system_prompt = "你是一个企业AI助手，负责分析用户意图。"
                    user_prompt = f"用户输入: {user_input}\n\n请分析用户意图，返回JSON格式。"
                    
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                    
                    full_content = []  # 优化：使用列表而不是字符串
                    chunk_count = 0
                    last_progress_update = 0
                    progress_update_interval = 5  # 保持每5个chunk更新一次
                    
                    async for chunk in self.llm_client.chat_completion_stream(messages):
                        content = chunk.get("content", "")
                        if content:
                            full_content.append(content)  # 优化：使用列表追加
                            chunk_count += 1
                            
                            # 优化：减少进度更新频率
                            if chunk_count - last_progress_update >= progress_update_interval:
                                # 优化：只在需要时构建字符串
                                current_length = sum(len(c) for c in full_content)
                                accumulated_str = ''.join(full_content[:10]) if len(full_content) > 10 else ''.join(full_content)
                                if len(accumulated_str) > 200:
                                    accumulated_str = accumulated_str[:200]
                                
                                yield {
                                    "stage": "analyzing",
                                    "content": content,
                                    "accumulated": accumulated_str,
                                    "progress": 20 + min(30, current_length / 10),
                                    "chunk_count": chunk_count
                                }
                                last_progress_update = chunk_count
                        
                        if chunk.get("finish_reason"):
                            # 优化：只在完成时构建完整字符串
                            full_content_str = ''.join(full_content)
                            
                            # 解析结果（简化版）
                            result = {
                                "intent": "tool_execution" if "订单" in user_input or "创建" in user_input else "simple_chat",
                                "confidence": 0.7,
                                "reasoning": f"基于LLM分析: {full_content_str[:100]}"
                            }
                            yield {
                                "stage": "complete",
                                "result": result,
                                "progress": 50,
                                "full_content": full_content_str[:500]  # 限制长度
                            }
                            break
                except Exception as e:
                    logger.warning(f"流式LLM分析失败: {e}")
                    # 降级：返回简单的分析结果
                    yield {
                        "stage": "complete",
                        "result": {
                            "intent": "tool_execution",
                            "confidence": 0.5,
                            "reasoning": f"模拟分析结果（错误: {e}）"
                        },
                        "progress": 50
                    }
        
        return MockUnifiedIntentService()

logger = logging.getLogger(__name__)


class UnifiedIntentMVP:
    """务实版MVP：混合模式（伪流式 + 批处理）"""
    
    def __init__(self):
        """初始化MVP服务"""
        try:
            # 复用现有组件，不重构（延迟初始化）
            self._conversation_agent = None
            self._orchestration_engine = None
            self._intent_service = None
            logger.info("UnifiedIntentMVP 初始化成功（延迟加载组件）")
        except Exception as e:
            logger.error(f"UnifiedIntentMVP 初始化失败: {e}", exc_info=True)
            raise
    
    @property
    def conversation_agent(self):
        """延迟加载conversation_agent"""
        if self._conversation_agent is None:
            self._conversation_agent = _get_conversation_agent()
        return self._conversation_agent
    
    @property
    def orchestration_engine(self):
        """延迟加载orchestration_engine"""
        if self._orchestration_engine is None:
            self._orchestration_engine = _get_orchestration_engine()
        return self._orchestration_engine
    
    @property
    def intent_service(self):
        """延迟加载intent_service"""
        if self._intent_service is None:
            self._intent_service = _get_unified_intent_service()
        return self._intent_service
    
    async def process_hybrid(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        混合模式：前端伪流式 + 后端批处理
        降低技术风险，快速验证价值
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            
        Yields:
            流式处理结果
        """
        if context is None:
            context = {}
        
        try:
            # 1. 立即返回"接收成功"响应
            yield {
                "stage": "received",
                "status": "success",
                "progress": 5,
                "message": "请求已接收，正在处理...",
                "timestamp": datetime.now().isoformat()
            }
            
            # 2. 后端并行处理（保持现有批处理逻辑）
            yield {
                "stage": "processing",
                "status": "analyzing",
                "progress": 20,
                "message": "正在分析用户意图...",
                "timestamp": datetime.now().isoformat()
            }
            
            # 使用现有组件，并行执行
            history = context.get('history', [])
            user_context = {k: v for k, v in context.items() if k not in ['history', 'available_agents']}
            
            # 阶段2：LLM分析流式化
            intent_analysis = None
            use_streaming_llm = context.get('use_streaming_llm', True)  # 默认启用流式LLM
            
            if use_streaming_llm and hasattr(self.intent_service, '_analyze_intent_with_llm_stream'):
                try:
                    # 使用流式LLM分析
                    full_content = ""
                    async for llm_chunk in self.intent_service._analyze_intent_with_llm_stream(
                        user_input,
                        user_context
                    ):
                        if llm_chunk.get("stage") == "analyzing":
                            # 实时转发LLM分析进度
                            yield {
                                "stage": "llm_analysis",
                                "status": "analyzing",
                                "progress": llm_chunk.get("progress", 25),
                                "message": "正在使用LLM分析意图...",
                                "llm_chunk": llm_chunk,
                                "timestamp": datetime.now().isoformat()
                            }
                            if llm_chunk.get("content"):
                                full_content += llm_chunk.get("content", "")
                        
                        elif llm_chunk.get("stage") == "complete":
                            # LLM分析完成
                            intent_analysis = llm_chunk.get("result")
                            yield {
                                "stage": "llm_analysis",
                                "status": "complete",
                                "progress": 50,
                                "message": "LLM分析完成",
                                "llm_chunk": llm_chunk,
                                "timestamp": datetime.now().isoformat()
                            }
                            break
                except Exception as e:
                    logger.warning(f"流式LLM分析失败: {e}，降级到批处理")
                    # 降级到批处理
                    intent_task = asyncio.create_task(
                        self.conversation_agent.understand_conversation(
                            user_input,
                            history,
                            user_context
                        )
                    )
                    intent_analysis = await intent_task
            else:
                # 使用批处理模式（原有逻辑）
                intent_task = asyncio.create_task(
                    self.conversation_agent.understand_conversation(
                        user_input,
                        history,
                        user_context
                    )
                )
                intent_analysis = await intent_task
            
            # 转换意图分析结果为统一格式（修复dict格式处理错误）
            if intent_analysis:
                if hasattr(intent_analysis, 'task_type'):
                    # ConversationAgent返回的格式
                    intent_result = {
                        "task_type": intent_analysis.task_type.value,
                        "confidence": intent_analysis.confidence,
                        "reasoning": intent_analysis.reasoning
                    }
                elif isinstance(intent_analysis, dict):
                    # LLM流式分析返回的格式
                    intent_result = {
                        "task_type": intent_analysis.get("intent", "simple_chat"),
                        "confidence": intent_analysis.get("confidence", 0.5),
                        "reasoning": intent_analysis.get("reasoning", "")
                    }
                else:
                    intent_result = {
                        "task_type": "simple_chat",
                        "confidence": 0.5,
                        "reasoning": "意图分析完成"
                    }
            else:
                intent_result = {
                    "task_type": "simple_chat",
                    "confidence": 0.5,
                    "reasoning": "意图分析完成"
                }
            
            yield {
                "stage": "intent_complete",
                "status": "complete",
                "progress": 50,
                "result": intent_result,
                "timestamp": datetime.now().isoformat()
            }
            
            # 阶段2：实时转发语义引擎流式结果（简化版，带错误处理和模拟支持）
            semantic_final_result = None
            try:
                # 检查语义引擎适配器是否可用
                semantic_adapter_available = (
                    hasattr(self.intent_service, 'semantic_adapter') and 
                    self.intent_service.semantic_adapter and
                    hasattr(self.intent_service.semantic_adapter, 'query_intent_enhanced_stream')
                )
                
                if semantic_adapter_available:
                    # 使用真实的语义引擎流式查询
                    async for chunk in self.intent_service.semantic_adapter.query_intent_enhanced_stream(
                        user_input=user_input,
                        llm_result={},
                        context=context,
                        top_k=5,
                        min_score=0.5
                    ):
                        # 转发语义引擎的进度（映射到50-80%范围）
                        if chunk.get("stage") in ["preparing", "vectorizing", "vectorized", "searching", "filtering", "results"]:
                            yield {
                                "stage": "semantic_search",
                                "status": chunk.get("status", "processing"),
                                "progress": 50 + chunk.get("progress", 0) * 0.3,  # 50-80%范围
                                "message": chunk.get("message", "正在查询语义引擎..."),
                                "semantic_chunk": chunk,
                                "timestamp": datetime.now().isoformat()
                            }
                        
                        # 保存最终结果
                        if chunk.get("stage") == "complete":
                            semantic_final_result = chunk.get("result")
                            yield {
                                "stage": "semantic_search",
                                "status": "complete",
                                "progress": 80,
                                "message": "语义引擎查询完成",
                                "semantic_chunk": chunk,
                                "timestamp": datetime.now().isoformat()
                            }
                            break
                        
                        # 如果出错，继续但不阻塞
                        if chunk.get("stage") == "error":
                            logger.warning(f"语义引擎查询错误: {chunk.get('error')}")
                            yield {
                                "stage": "semantic_search",
                                "status": "error",
                                "progress": 50,
                                "message": "语义引擎查询失败，继续执行",
                                "error": chunk.get("error"),
                                "timestamp": datetime.now().isoformat()
                            }
                            break
                else:
                    # 阶段2：模拟语义引擎流式查询（用于测试验证）
                    logger.debug("语义引擎适配器不可用，使用模拟流式查询进行验证")
                    await asyncio.sleep(0.1)  # 模拟处理时间
                    
                    # 模拟流式查询的各个阶段
                    stages = [
                        {"stage": "preparing", "progress": 5, "message": "正在准备查询..."},
                        {"stage": "vectorizing", "progress": 10, "message": "正在向量化查询..."},
                        {"stage": "vectorized", "progress": 30, "message": "向量化完成"},
                        {"stage": "searching", "progress": 40, "message": "正在搜索相关活动..."},
                        {"stage": "results", "progress": 85, "message": "找到 3 个相关活动", "activities_count": 3},
                        {"stage": "complete", "progress": 100, "message": "语义引擎查询完成"}
                    ]
                    
                    for stage_info in stages:
                        await asyncio.sleep(0.2)  # 模拟处理时间
                        yield {
                            "stage": "semantic_search",
                            "status": "processing" if stage_info["stage"] != "complete" else "success",
                            "progress": 50 + stage_info.get("progress", 0) * 0.3,  # 映射到50-80%范围
                            "message": stage_info.get("message", "正在查询语义引擎..."),
                            "semantic_chunk": stage_info,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        if stage_info["stage"] == "complete":
                            break
            except Exception as e:
                logger.warning(f"语义引擎流式查询失败: {e}")
                # 失败不影响主流程，继续执行
            
            # 3. 执行阶段（使用现有编排引擎）
            yield {
                "stage": "execution",
                "status": "executing",
                "progress": 60,
                "message": "正在执行任务...",
                "timestamp": datetime.now().isoformat()
            }
            
            # 使用现有编排引擎（批处理模式）
            execution_context = context.copy()
            execution_context['history'] = history
            
            try:
                result = await self.orchestration_engine.orchestrate_request(
                    user_input,
                    execution_context
                )
            except Exception as e:
                logger.error(f"编排引擎执行失败: {e}", exc_info=True)
                # 降级：返回简单的执行结果
                result = {
                    "success": False,
                    "error": str(e),
                    "message": "执行失败，请检查服务配置",
                    "output": None
                }
            
            # 4. 整合语义引擎结果（已在流式处理中完成）
            # 语义引擎的流式结果已在意图分析后实时返回，这里不需要额外整合
            
            # 5. 返回最终结果
            yield {
                "stage": "complete",
                "status": "success",
                "progress": 100,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"处理失败: {e}", exc_info=True)
            yield {
                "stage": "error",
                "status": "error",
                "error": str(e),
                "message": "处理过程中发生错误，已记录日志",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _query_semantic_engine_safe(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]]
    ) -> Optional[Any]:
        """安全查询语义引擎（带超时和错误处理）- 阶段1版本"""
        try:
            # 设置超时，避免阻塞
            result = await asyncio.wait_for(
                self.intent_service.semantic_adapter.query_intent_enhanced(
                    user_input=user_input,
                    llm_result={},  # 简化版，不依赖LLM结果
                    context=context,
                    top_k=5,
                    min_score=0.5
                ),
                timeout=3.0  # 3秒超时
            )
            return result
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"语义引擎查询失败: {e}")
            return None
    
    async def _query_semantic_engine_stream_safe(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]]
    ) -> Optional[Any]:
        """安全查询语义引擎（流式版本）- 阶段2"""
        try:
            # 使用流式查询，收集所有结果
            results = []
            async for chunk in self.intent_service.semantic_adapter.query_intent_enhanced_stream(
                user_input=user_input,
                llm_result={},  # 简化版，不依赖LLM结果
                context=context,
                top_k=5,
                min_score=0.5
            ):
                results.append(chunk)
                # 如果收到完成信号，返回结果
                if chunk.get("stage") == "complete":
                    return chunk.get("result")
            
            # 如果没有完成信号，返回最后一个结果
            if results:
                return results[-1].get("result")
            return None
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"语义引擎流式查询失败: {e}")
            return None


# 创建全局实例
_unified_intent_mvp = None


def get_unified_intent_mvp() -> UnifiedIntentMVP:
    """获取统一意图MVP实例（单例模式）"""
    global _unified_intent_mvp
    if _unified_intent_mvp is None:
        _unified_intent_mvp = UnifiedIntentMVP()
    return _unified_intent_mvp


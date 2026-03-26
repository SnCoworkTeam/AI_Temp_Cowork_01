"""
LLM节点
调用大语言模型处理输入
"""
from typing import Dict, Any, Optional
import logging
import os
from datetime import datetime

from .base_node import BaseNode, NodeExecutionError
from ..config import settings

logger = logging.getLogger(__name__)

try:
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate
    from langchain.schema import HumanMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger.warning("LangChain not available, LLM Node will use mock implementation")


class LLMNode(BaseNode):
    """LLM节点 - 调用大语言模型"""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        config: Optional[Dict[str, Any]] = None,
        node_id: Optional[str] = None
    ):
        super().__init__(name, description, config, node_id)
        # 从配置中心读取配置（不硬编码默认值）
        # 优先使用节点配置，然后从配置中心读取，最后从环境变量读取
        self.model = self.config.get("model") or settings.LLM_MODEL
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 2000)
        self.prompt_template = self.config.get("prompt_template", "{input}")
        self.system_message = self.config.get("system_message", "")
        self.api_key = self.config.get("api_key") or settings.OPENAI_API_KEY
        # 支持自定义base_url（从配置中心读取）
        self.base_url = self.config.get("base_url") or settings.LLM_BASE_URL

        # 初始化LLM（延迟初始化）
        self._llm: Optional[Any] = None
    
    def _get_llm(self):
        """获取LLM实例（延迟初始化）"""
        if self._llm is not None:
            return self._llm
        
        if not LANGCHAIN_AVAILABLE:
            logger.warning("LangChain not available, using mock LLM")
            return None
        
        if not self.api_key:
            raise NodeExecutionError(
                self.name,
                "LLM API key not configured"
            )
        
        try:
            # 构建LLM配置参数
            # 尝试新版本参数（langchain-openai >= 0.1.0）
            llm_kwargs = {
                "model": self.model,  # 新版本使用 model
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "api_key": self.api_key,  # 新版本使用 api_key
            }
            
            # 如果设置了base_url（如DeepSeek），添加到配置中
            if self.base_url:
                # 确保base_url格式正确（去掉/v1后缀，ChatOpenAI会自动添加）
                base_url_clean = self.base_url.rstrip("/v1").rstrip("/")
                llm_kwargs["base_url"] = base_url_clean
                logger.info(f"Using custom LLM base URL: {base_url_clean} for model: {self.model}")
            
            try:
                self._llm = ChatOpenAI(**llm_kwargs)
            except TypeError:
                # 如果新版本参数失败，尝试旧版本参数
                logger.warning("Trying legacy ChatOpenAI parameters")
                llm_kwargs_legacy = {
                    "model_name": self.model,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "openai_api_key": self.api_key,
                }
                if self.base_url:
                    base_url_clean = self.base_url.rstrip("/v1").rstrip("/")
                    llm_kwargs_legacy["base_url"] = base_url_clean
                self._llm = ChatOpenAI(**llm_kwargs_legacy)
            
            logger.info(f"LLM initialized successfully: model={self.model}, base_url={self.base_url if self.base_url else 'default'}")
            return self._llm
        except Exception as e:
            raise NodeExecutionError(
                self.name,
                f"Failed to initialize LLM: {str(e)}",
                e
            )
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行LLM节点
        
        Args:
            state: 当前工作流状态
        
        Returns:
            更新后的状态
        """
        try:
            # 准备输入
            prompt = self.resolve_template(self.prompt_template, state)
            if not prompt:
                raise ValueError("Empty prompt generated")
            
            logger.info(
                f"LLM Node '{self.name}' executing with model: {self.model}, "
                f"base_url: {self.base_url}, "
                f"api_key: {self.api_key[:20] + '...' if self.api_key else 'NOT SET'}, "
                f"prompt length: {len(prompt)}"
            )
            
            # 总是尝试使用配置的LLM
            llm = self._get_configured_llm()
            if not llm:
                raise NodeExecutionError(
                    self.name,
                    "LLM not configured properly"
                )
            
            logger.info(
                f"LLM Node '{self.name}' calling LLM API with model={self.model}, "
                f"base_url={self.base_url}"
            )
            
            # 调用LLM
            messages = []
            
            if self.system_message:
                system_prompt = self.resolve_template(self.system_message, state)
                messages.append(SystemMessage(content=system_prompt))
            
            messages.append(HumanMessage(content=prompt))
            
            try:
                response = await llm.ainvoke(messages)
                llm_output = response.content if hasattr(response, 'content') else str(response)
                logger.info(f"LLM Node '{self.name}' received response, length: {len(llm_output)}")
            except Exception as api_error:
                logger.error(f"LLM Node '{self.name}' API call failed: {str(api_error)}", exc_info=True)
                raise NodeExecutionError(
                    self.name,
                    f"LLM API call failed: {str(api_error)}",
                    api_error
                )
            
            # 处理响应
            result = self._process_llm_response(llm_output)
            
            # 更新状态
            new_state = state.copy()
            output_key = f"{self.name}_output"
            new_state[output_key] = {
                "content": result,
                "model": self.model,
                "prompt": prompt[:200] + "..." if len(prompt) > 200 else prompt,
                "node_name": self.name,
            }
            
            # 也添加到根级别（方便访问）
            new_state[f"{self.name}_result"] = result
            new_state[f"{self.name}_raw_response"] = llm_output
            
            # 记录执行历史
            self._add_execution_history(new_state, {
                "node_id": self.name,
                "prompt": prompt[:500] + "..." if len(prompt) > 500 else prompt,  # 截断长文本
                "response": result,
                "timestamp": datetime.utcnow().isoformat() if hasattr(datetime, 'utcnow') else datetime.now().isoformat()
            })
            
            logger.info(f"LLM Node '{self.name}' completed successfully")
            
            return new_state
        
        except NodeExecutionError:
            raise
        except Exception as e:
            logger.error(f"LLM node {self.name} execution failed: {e}")
            # 返回错误信息而不是Mock数据
            return self._handle_execution_error(state, e)
    
    def _get_configured_llm(self):
        """获取配置的LLM实例"""
        if hasattr(self, '_llm') and self._llm:
            return self._llm
        
        if not LANGCHAIN_AVAILABLE:
            raise NodeExecutionError(
                self.name,
                "LangChain not available"
            )
        
        # 确保有API密钥
        api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise NodeExecutionError(
                self.name,
                "OpenAI API key not configured"
            )
        
        # 配置LLM
        base_url = self.base_url or settings.LLM_BASE_URL or os.getenv("LLM_BASE_URL")
        # 优先使用 self.model，然后是 settings.LLM_MODEL，最后才是环境变量
        # 如果都为空，根据 base_url 智能选择默认模型
        if self.model:
            model_name = self.model
        elif settings.LLM_MODEL:
            model_name = settings.LLM_MODEL
        else:
            env_model = os.getenv("LLM_MODEL")
            if env_model:
                model_name = env_model
            else:
                # 如果所有配置都为空，抛出错误（不允许硬编码默认值）
                raise NodeExecutionError(
                    self.name,
                    "LLM model not configured. Please set llm.model in config center or LLM_MODEL in environment variables."
                )
        
        try:
            # 构建LLM配置参数
            llm_kwargs = {
                "model": model_name,  # 新版本使用 model 而不是 model_name
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "api_key": api_key,  # 新版本使用 api_key 而不是 openai_api_key
                "timeout": self.config.get("timeout", 30),
                "max_retries": self.config.get("max_retries", 3)
            }
            
            # 如果设置了base_url（如DeepSeek），添加到配置中
            if base_url:
                # 确保base_url不以/v1结尾（ChatOpenAI会自动添加）
                base_url_clean = base_url.rstrip("/v1").rstrip("/")
                llm_kwargs["base_url"] = base_url_clean
                logger.info(f"Using custom LLM base URL: {base_url_clean} for model: {model_name}")
            
            # 尝试使用新版本的参数
            try:
                self._llm = ChatOpenAI(**llm_kwargs)
            except TypeError:
                # 如果新版本参数失败，尝试旧版本参数
                logger.warning("Trying legacy ChatOpenAI parameters")
                llm_kwargs_legacy = {
                    "model_name": model_name,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "openai_api_key": api_key,
                    "timeout": self.config.get("timeout", 30),
                    "max_retries": self.config.get("max_retries", 3)
                }
                if base_url:
                    base_url_clean = base_url.rstrip("/v1").rstrip("/")
                    llm_kwargs_legacy["base_url"] = base_url_clean
                self._llm = ChatOpenAI(**llm_kwargs_legacy)
            
            logger.info(f"LLM initialized successfully: model={model_name}, base_url={base_url if base_url else 'default'}")
            return self._llm
        except Exception as e:
            raise NodeExecutionError(
                self.name,
                f"Failed to initialize LLM: {str(e)}",
                e
            )
    
    def _process_llm_response(self, response: Any) -> str:
        """处理LLM响应"""
        if isinstance(response, str):
            return response
        elif hasattr(response, 'content'):
            return response.content
        else:
            return str(response)
    
    def _add_execution_history(self, state: Dict[str, Any], history_entry: Dict[str, Any]):
        """添加执行历史"""
        if "execution_history" not in state:
            state["execution_history"] = []
        state["execution_history"].append(history_entry)
    
    def _handle_execution_error(self, state: Dict, error: Exception) -> Dict:
        """处理执行错误"""
        new_state = state.copy()
        new_state[f"{self.name}_error"] = str(error)
        new_state[f"{self.name}_success"] = False
        
        # 记录错误历史
        self._add_execution_history(new_state, {
            "node_id": self.name,
            "error": str(error),
            "timestamp": datetime.utcnow().isoformat() if hasattr(datetime, 'utcnow') else datetime.now().isoformat(),
            "success": False
        })
        
        return new_state
    
    def validate_config(self) -> bool:
        """验证LLM节点配置"""
        required_configs = ['api_key']
        for config_key in required_configs:
            if not self.config.get(config_key) and not os.getenv("OPENAI_API_KEY"):
                raise NodeExecutionError(
                    self.name,
                    f"LLM {config_key} not configured"
                )
        
        # 验证模型名称
        model_name = self.model or os.getenv("LLM_MODEL")
        if not model_name:
            raise NodeExecutionError(
                self.name,
                "LLM model not configured"
            )
        
        return True
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        """验证输入状态"""
        if not super().validate_input(state):
            return False
        
        # 检查提示词模板是否有效
        if not self.prompt_template:
            logger.warning(f"LLM Node '{self.name}' has empty prompt template")
            return False
        
        return True
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """验证输出状态"""
        if not super().validate_output(output):
            return False
        
        # 检查是否有输出
        output_key = f"{self.name}_output"
        if output_key not in output:
            logger.warning(f"LLM Node '{self.name}' did not produce output")
            return False
        
        return True



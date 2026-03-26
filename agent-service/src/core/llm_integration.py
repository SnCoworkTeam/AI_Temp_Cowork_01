"""
LLM集成服务 - 从配置中心读取配置
"""
import logging
import os
from typing import Dict, Any, Optional, List
import json
import re
import sys
from pathlib import Path

# 初始化logger（在导入检查之前）
logger = logging.getLogger(__name__)

# 尝试导入httpx（用于直接HTTP调用配置中心）
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.warning("httpx not available, cannot read from config center via HTTP")

# 尝试导入httpx（用于直接HTTP调用配置中心）
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.warning("httpx not available, cannot read from config center via HTTP")

# 添加共享库路径（支持多种路径）
_current_file = Path(__file__).resolve()
_project_root = _current_file.parent.parent.parent.parent
_shared_libs_paths = [
    str(_project_root / "shared_libs"),
    "/shared_libs",  # Docker环境
    "/app/../shared_libs",  # Docker环境备用路径
]

for path in _shared_libs_paths:
    if Path(path).exists() and path not in sys.path:
        sys.path.insert(0, path)

try:
    from langchain_openai import ChatOpenAI
    # langchain 1.0+ 使用 langchain_core.messages
    try:
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    except ImportError:
        # 降级到旧版本路径
        try:
            from langchain.schema import HumanMessage, SystemMessage, AIMessage
        except ImportError:
            raise
    LANGCHAIN_AVAILABLE = True
    logger.info("LangChain packages imported successfully")
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    logger.error(f"Failed to import LangChain packages: {e}")

# 尝试导入config_client（直接导入模块，避免通过luminaos_common.__init__.py）
CONFIG_CLIENT_AVAILABLE = False
try:
    # 方法1: 尝试直接导入config_client模块（绕过__init__.py的依赖）
    import importlib.util
    from pathlib import Path

    # 查找config_client.py的路径
    _current_file = Path(__file__).resolve()
    _project_root = _current_file.parent.parent.parent.parent
    _config_client_paths = [
        _project_root / "shared_libs" / "luminaos_common" / "clients" / "config_client.py",
        Path("/shared_libs/luminaos_common/clients/config_client.py"),  # Docker环境
    ]

    _config_client_module = None
    for config_client_path in _config_client_paths:
        if config_client_path.exists():
            try:
                spec = importlib.util.spec_from_file_location(
                    "config_client",
                    str(config_client_path)
                )
                _config_client_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(_config_client_module)

                # 将模块注入到sys.modules，让后续导入可以找到
                sys.modules['luminaos_common.clients.config_client'] = _config_client_module
                get_config_client = _config_client_module.get_config_client
                CONFIG_CLIENT_AVAILABLE = True
                logger.info("Config client loaded directly from module file")
                break
            except Exception as e:
                logger.debug(f"Failed to load config_client from {config_client_path}: {e}")
                continue

    # 方法2: 如果直接导入失败，尝试通过luminaos_common导入（需要所有依赖）
    if not CONFIG_CLIENT_AVAILABLE:
        from luminaos_common.clients.config_client import get_config_client
        CONFIG_CLIENT_AVAILABLE = True
        logger.info("Config client loaded via luminaos_common")
except ImportError as e:
    CONFIG_CLIENT_AVAILABLE = False
    logger.warning(f"Config client not available: {e}")
    logger.warning("Will use environment variables or HTTP fallback")
except Exception as e:
    CONFIG_CLIENT_AVAILABLE = False
    logger.warning(f"Failed to initialize config client: {e}")
    logger.warning("Will use environment variables or HTTP fallback")


class DeepSeekLLM:
    """LLM集成类 - 从配置中心读取配置"""

    def __init__(self, model: Optional[str] = None):
        """
        初始化LLM集成

        Args:
            model: 指定模型名称（可选，如果提供则覆盖配置中心和环境变量的设置）
        """
        self.config_client = None
        self.api_key = None
        self.base_url = None
        self.model = model  # 如果指定了模型，优先使用
        self.temperature = 0.7
        self.max_tokens = 4096
        self.llm = None

        # 初始化配置客户端
        if CONFIG_CLIENT_AVAILABLE:
            try:
                # 确保CONFIG_CENTER_URL环境变量已设置（如果未设置，使用默认值）
                config_center_url = os.getenv("CONFIG_CENTER_URL")
                if not config_center_url:
                    # 本地开发环境默认使用localhost
                    if not os.getenv("DOCKER_CONTAINER") and not os.path.exists("/.dockerenv"):
                        os.environ["CONFIG_CENTER_URL"] = "http://localhost:8090"
                        logger.info("Set CONFIG_CENTER_URL to http://localhost:8090 (local development)")

                self.config_client = get_config_client()
                logger.info(f"Config client initialized: {self.config_client.config_center_url}")
            except Exception as e:
                logger.warning(f"Failed to initialize config client: {e}")
                logger.warning("Will try to read from config center via HTTP as fallback")
                self.config_client = None

        # 从配置中心加载配置
        self._load_config()

        if LANGCHAIN_AVAILABLE and self.api_key:
            self._init_llm()

    async def _load_config_async(self):
        """异步加载配置（从配置中心）"""
        if not self.config_client:
            # 如果没有配置客户端，尝试直接从配置中心HTTP API读取
            logger.warning("Config client not available, trying to read from config center via HTTP")

            if not HTTPX_AVAILABLE:
                logger.warning("httpx not available, falling back to environment variables")
                self._load_config_from_env()
                return

            config_center_url = os.getenv("CONFIG_CENTER_URL", "http://localhost:8090")
            logger.info(f"Attempting to read from config center via HTTP: {config_center_url}")
            logger.info(f"HTTPX_AVAILABLE: {HTTPX_AVAILABLE}")

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # 读取API key
                    api_key_url = f"{config_center_url}/api/config/llm.api_key"
                    logger.debug(f"Fetching API key from: {api_key_url}")
                    response = await client.get(
                        api_key_url,
                        params={"environment": "default"}
                    )
                    logger.debug(f"API key response status: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        api_key = data.get("value", "")
                        if api_key and api_key.strip():
                            self.api_key = api_key
                            logger.info(f"✅ API key loaded from config center via HTTP (length: {len(api_key)})")
                        else:
                            logger.warning(f"API key from config center is empty")
                    else:
                        logger.warning(f"Failed to fetch API key: HTTP {response.status_code} - {response.text[:200]}")

                    # 读取base_url
                    response = await client.get(
                        f"{config_center_url}/api/config/llm.base_url",
                        params={"environment": "default"}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        base_url = data.get("value", "")
                        if base_url and base_url.strip():
                            self.base_url = base_url

                    # 读取model
                    response = await client.get(
                        f"{config_center_url}/api/config/llm.model",
                        params={"environment": "default"}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        model = data.get("value", "")
                        if model and model.strip():
                            self.model = model

                    # 读取temperature
                    response = await client.get(
                        f"{config_center_url}/api/config/llm.temperature",
                        params={"environment": "default"}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("value") is not None:
                            self.temperature = float(data.get("value"))

                    # 读取max_tokens
                    response = await client.get(
                        f"{config_center_url}/api/config/llm.max_tokens",
                        params={"environment": "default"}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("value") is not None:
                            self.max_tokens = int(data.get("value"))

                    # 如果从配置中心读取到了API key，初始化LLM
                    if self.api_key and self.api_key.strip() and LANGCHAIN_AVAILABLE:
                        if not self.llm:
                            logger.info("Initializing LLM from config center (via HTTP)")
                            self._init_llm()
                        return
            except Exception as e:
                logger.error(f"Failed to read from config center via HTTP: {e}", exc_info=True)

            # 如果HTTP读取失败，使用环境变量
            logger.warning("Falling back to environment variables")
            self._load_config_from_env()
            # _load_config_from_env 内部会调用 _init_llm
            return

        try:
            llm_config = await self.config_client.get_llm_config()

            # 从配置中心加载配置（如果存在且非空）
            if llm_config.get("api_key") and llm_config["api_key"].strip():
                self.api_key = llm_config["api_key"]
            if llm_config.get("base_url") and llm_config["base_url"].strip():
                self.base_url = llm_config["base_url"]
            if llm_config.get("model") and llm_config["model"].strip():
                self.model = llm_config["model"]
            if llm_config.get("temperature") is not None:
                self.temperature = float(llm_config["temperature"])
            if llm_config.get("max_tokens") is not None:
                self.max_tokens = int(llm_config["max_tokens"])

            logger.info(f"LLM config loaded from config center: model={self.model or 'NOT SET'}, base_url={self.base_url or 'NOT SET'}, has_api_key={bool(self.api_key and self.api_key.strip())}")

            # 如果配置中心没有api_key或api_key为空，降级到环境变量
            if not self.api_key or not self.api_key.strip():
                logger.warning("API key not found or empty in config center, falling back to environment variables")
                env_api_key = os.getenv("OPENAI_API_KEY")
                if env_api_key and env_api_key.strip():
                    self.api_key = env_api_key
                    logger.info(f"API key loaded from environment variables (length: {len(self.api_key)})")
                else:
                    logger.error("OPENAI_API_KEY not found in environment variables either!")

            # 如果base_url或model缺失，也从环境变量补充
            if not self.base_url or not self.base_url.strip():
                self.base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
                logger.info(f"Base URL loaded from environment: {self.base_url}")
            if not self.model or not self.model.strip():
                # 如果初始化时没有指定模型，从环境变量或配置中心加载
                self.model = os.getenv("LLM_MODEL", "deepseek-chat")
                logger.info(f"Model loaded from environment: {self.model}")
            else:
                # 如果初始化时指定了模型，使用指定的模型
                logger.info(f"Using specified model: {self.model}")

            # 初始化LLM（如果api_key存在）
            if self.api_key and self.api_key.strip():
                if not self.llm:
                    if LANGCHAIN_AVAILABLE:
                        logger.info(f"Initializing LLM: api_key exists (length={len(self.api_key)}), model={self.model}, base_url={self.base_url}, LANGCHAIN_AVAILABLE={LANGCHAIN_AVAILABLE}")
                        self._init_llm()
                        if self.llm:
                            logger.info("LLM initialized successfully")
                        else:
                            logger.error("LLM initialization failed - check logs above for details")
                    else:
                        logger.error("Cannot initialize LLM: LANGCHAIN_AVAILABLE is False - langchain packages may not be installed correctly")
                else:
                    logger.info("LLM already initialized")
            else:
                logger.error("Cannot initialize LLM: API key is missing or empty")
        except Exception as e:
            logger.error(f"Failed to load config from config center: {e}")
            # 降级到环境变量
            self._load_config_from_env()
            if self.api_key and self.api_key.strip() and LANGCHAIN_AVAILABLE:
                self._init_llm()

    def _load_config(self):
        """同步加载配置（优先从配置中心，降级到环境变量）"""
        # 尝试从配置中心同步加载（如果可能）
        # 否则从环境变量加载（作为降级方案）
        if self.config_client:
            # 异步加载需要事件循环，这里先尝试同步方式
            # 实际使用时会通过异步方法加载
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果事件循环正在运行，创建任务
                    asyncio.create_task(self._load_config_async())
                else:
                    # 如果事件循环未运行，直接运行
                    loop.run_until_complete(self._load_config_async())
            except RuntimeError:
                # 没有事件循环，使用环境变量作为降级
                self._load_config_from_env()
        else:
            # 配置客户端不可用，使用环境变量
            self._load_config_from_env()

    def _load_config_from_env(self):
        """从环境变量加载配置（降级方案）"""
        logger.warning("Using environment variables for LLM config (config center not available or missing api_key)")
        self.api_key = os.getenv("SINOCHEM_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
        # 如果初始化时已经指定了模型，不要被环境变量覆盖
        if not self.model or not self.model.strip():
            self.model = os.getenv("LLM_MODEL", "deepseek-chat")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))

        if not self.api_key:
            logger.error("OPENAI_API_KEY not found in environment variables or config center")
        else:
            logger.info(f"API key loaded from environment variables (length: {len(self.api_key)})")
        if not self.base_url:
            logger.error("LLM_BASE_URL not found in environment variables or config center")
        if not self.model:
            logger.error("LLM_MODEL not found in environment variables or config center")

        # 如果从环境变量加载了配置，尝试初始化LLM
        if self.api_key and self.api_key.strip() and LANGCHAIN_AVAILABLE:
            if not self.llm:
                logger.info("Initializing LLM from environment variables")
                self._init_llm()

    def _init_llm(self):
        """初始化LLM客户端"""
        try:
            # 确保所有必需的配置都存在
            if not self.api_key or not self.api_key.strip():
                logger.error("Cannot initialize LLM: API key is missing or empty")
                self.llm = None
                return

            if not self.model or not self.model.strip():
                logger.warning("Model not set, using default: deepseek-chat")
                self.model = "deepseek-chat"

            if not self.base_url or not self.base_url.strip():
                logger.warning("Base URL not set, using default: https://api.deepseek.com")
                self.base_url = "https://api.deepseek.com"

            # 仅去除末尾斜杠，保留 /v1 等版本路径
            base_url_clean = self.base_url.rstrip("/")

            llm_kwargs = {
                "model": self.model,
                "temperature": self.temperature,
                "api_key": self.api_key,
                "base_url": base_url_clean,
                "max_tokens": self.max_tokens,
            }

            logger.info(f"Initializing LLM with: model={self.model}, base_url={base_url_clean}, api_key_length={len(self.api_key)}")

            self.llm = ChatOpenAI(**llm_kwargs)
            logger.info(f"DeepSeek LLM initialized successfully: model={self.model}, base_url={base_url_clean}")
        except Exception as e:
            logger.error(f"Failed to initialize DeepSeek LLM: {str(e)}", exc_info=True)
            self.llm = None

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        stream: bool = False
    ):
        """
        调用DeepSeek进行对话

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}, ...]
            system_prompt: 系统提示词
            temperature: 温度参数（覆盖默认值）

        Returns:
            LLM响应文本
        """
        if not self.llm:
            raise RuntimeError("DeepSeek LLM not initialized. Please set OPENAI_API_KEY and LLM_BASE_URL.")

        try:
            # 构建消息列表
            langchain_messages = []

            if system_prompt:
                langchain_messages.append(SystemMessage(content=system_prompt))

            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")

                if role == "system":
                    langchain_messages.append(SystemMessage(content=content))
                elif role == "user":
                    langchain_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    langchain_messages.append(AIMessage(content=content))

            # 临时设置温度（如果提供）
            original_temperature = self.llm.temperature
            if temperature is not None:
                self.llm.temperature = temperature

            try:
                if stream:
                    # 流式输出
                    async def stream_response():
                        async for chunk in self.llm.astream(langchain_messages):
                            content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                            if content:
                                yield content
                    return stream_response()
                else:
                    # 非流式输出
                    response = await self.llm.ainvoke(langchain_messages)
                    result = response.content if hasattr(response, 'content') else str(response)
                    logger.debug(f"DeepSeek chat completed, response length: {len(result)}")
                    return result
            finally:
                # 恢复原始温度
                if temperature is not None:
                    self.llm.temperature = original_temperature

        except Exception as e:
            err_text = str(e)
            logger.error(f"DeepSeek chat failed: {err_text}")

            # 兼容部分OpenAI兼容接口返回choices为空的情况，尝试直接HTTP回退
            if "null value for 'choices'" in err_text or "choices" in err_text:
                try:
                    import httpx

                    base_url = (self.base_url or "").rstrip("/")
                    if not base_url:
                        raise RuntimeError("LLM base_url is empty")

                    url = f"{base_url}/chat/completions"
                    payload = {
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature if temperature is not None else self.temperature,
                        "max_tokens": self.max_tokens,
                        "stream": stream,
                    }
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
                    }

                    async with httpx.AsyncClient(timeout=60.0) as client:
                        resp = await client.post(url, json=payload, headers=headers)
                    data = resp.json()

                    choices = data.get("choices") if isinstance(data, dict) else None
                    if choices:
                        first = choices[0]
                        msg = first.get("message") or {}
                        content = msg.get("content")
                        if content:
                            return content

                    # 如果choices为空，返回更明确的错误信息
                    msg = None
                    code = None
                    if isinstance(data, dict):
                        msg = data.get("msg") or data.get("message") or data.get("error")
                        code = data.get("code")
                    raise Exception(f"LLM response error: {msg or 'choices is empty'} (code={code})")
                except Exception as fallback_err:
                    logger.error(f"LLM HTTP fallback failed: {fallback_err}")
                    raise Exception(f"DeepSeek chat error: {fallback_err}") from fallback_err

            raise Exception(f"DeepSeek chat error: {err_text}")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        生成文本（简化接口）

        Args:
            prompt: 提示词
            system_prompt: 系统提示词
            temperature: 温度参数

        Returns:
            生成的文本
        """
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, system_prompt, temperature)

    def parse_json_response(self, text: str) -> Dict[str, Any]:
        """
        从LLM响应中解析JSON

        Args:
            text: LLM响应文本

        Returns:
            解析后的JSON字典
        """
        # 尝试提取JSON代码块
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试提取纯JSON对象
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = text

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {str(e)}")
            logger.error(f"Response text: {text[:500]}")
            raise ValueError(f"Invalid JSON response from LLM: {str(e)}")


# 全局LLM实例
deepseek_llm = DeepSeekLLM()

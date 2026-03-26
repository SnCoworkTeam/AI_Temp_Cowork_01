"""
配置管理中心
提供统一的配置管理、版本控制、动态更新功能
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
import redis.asyncio as redis
import httpx
import yaml
import json
import logging
import asyncio
import os
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic模型
class ConfigItem(BaseModel):
    """配置项"""
    key: str
    value: Any
    description: Optional[str] = None
    environment: str = "default"  # default, dev, test, prod
    version: int = 1


class ConfigUpdate(BaseModel):
    """配置更新"""
    value: Any
    description: Optional[str] = None


class ConfigService:
    """配置服务"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.config_prefix = "config:"
        self.version_prefix = "config:version:"
        self.subscribers = {}

    async def get_config(self, key: str, environment: str = "default") -> Optional[Dict[str, Any]]:
        """获取配置"""
        full_key = f"{self.config_prefix}{environment}:{key}"
        data = await self.redis.get(full_key)

        if data:
            return json.loads(data)
        return None

    async def set_config(self, config: ConfigItem) -> bool:
        """设置配置"""
        full_key = f"{self.config_prefix}{config.environment}:{config.key}"
        version_key = f"{self.version_prefix}{config.environment}:{config.key}"

        # 获取当前版本号
        current_version = await self.redis.get(version_key)
        if current_version:
            config.version = int(current_version) + 1

        # 保存配置
        config_data = {
            "key": config.key,
            "value": config.value,
            "description": config.description,
            "environment": config.environment,
            "version": config.version,
            "updated_at": datetime.now().isoformat()
        }

        await self.redis.set(full_key, json.dumps(config_data))
        await self.redis.set(version_key, str(config.version))

        # 发布配置更新事件
        await self.redis.publish(
            f"config:update:{config.environment}",
            json.dumps({"key": config.key, "version": config.version})
        )

        logger.info(f"Config updated: {config.environment}:{config.key} v{config.version}")
        return True

    async def delete_config(self, key: str, environment: str = "default") -> bool:
        """删除配置"""
        full_key = f"{self.config_prefix}{environment}:{key}"
        result = await self.redis.delete(full_key)
        return result > 0

    async def list_configs(self, environment: str = "default") -> List[Dict[str, Any]]:
        """列出所有配置"""
        pattern = f"{self.config_prefix}{environment}:*"
        keys = []

        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)

        configs = []
        for key in keys:
            data = await self.redis.get(key)
            if data:
                configs.append(json.loads(data))

        return configs

    async def get_all_configs(self, environment: str = "default") -> Dict[str, Any]:
        """获取所有配置（扁平化）"""
        configs = await self.list_configs(environment)
        result = {}
        for config in configs:
            result[config["key"]] = config["value"]
        return result


# 全局变量
redis_client: Optional[redis.Redis] = None
config_service: Optional[ConfigService] = None
service_id: Optional[str] = None
http_client: Optional[httpx.AsyncClient] = None
heartbeat_task: Optional[asyncio.Task] = None


async def register_to_registry():
    """注册到服务发现中心"""
    global service_id, http_client
    
    registry_url = os.getenv("REGISTRY_SERVICE_URL", "http://registry-service:8000")
    service_host = os.getenv("SERVICE_HOST", "config-center")
    service_port = int(os.getenv("PORT", "8090"))
    
    http_client = httpx.AsyncClient(timeout=10.0)
    
    registration_data = {
        "name": "config-center",
        "host": service_host,
        "port": service_port,
        "service_type": "http",
        "health_check_url": f"http://{service_host}:{service_port}/health",
        "metadata": {
            "description": "统一配置管理中心",
            "version": "1.0.0"
        },
        "tags": ["config", "management"]
    }
    
    try:
        response = await http_client.post(
            f"{registry_url}/api/register",
            json=registration_data
        )
        response.raise_for_status()
        result = response.json()
        service_id = result.get("service_id")
        logger.info(f"Config Center registered successfully: service_id={service_id}")
        return service_id
    except Exception as e:
        logger.warning(f"Failed to register to registry service: {e}")
        return None


async def send_heartbeat():
    """发送心跳"""
    global service_id, http_client
    
    if not service_id or not http_client:
        return
    
    registry_url = os.getenv("REGISTRY_SERVICE_URL", "http://registry-service:8000")
    
    try:
        response = await http_client.post(
            f"{registry_url}/api/heartbeat/{service_id}"
        )
        response.raise_for_status()
        logger.debug(f"Heartbeat sent successfully: service_id={service_id}")
    except Exception as e:
        logger.warning(f"Failed to send heartbeat: {e}")


async def heartbeat_loop():
    """心跳循环"""
    while True:
        try:
            await send_heartbeat()
            await asyncio.sleep(10)  # 每10秒发送一次心跳
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in heartbeat loop: {e}")
            await asyncio.sleep(10)


async def unregister_from_registry():
    """从服务发现中心注销"""
    global service_id, http_client
    
    if not service_id or not http_client:
        return
    
    registry_url = os.getenv("REGISTRY_SERVICE_URL", "http://registry-service:8000")
    
    try:
        response = await http_client.delete(
            f"{registry_url}/api/unregister/{service_id}"
        )
        response.raise_for_status()
        logger.info(f"Config Center unregistered successfully: service_id={service_id}")
    except Exception as e:
        logger.warning(f"Failed to unregister from registry service: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    global redis_client, config_service, heartbeat_task, http_client

    logger.info("Config Center starting up...")

    # 连接Redis
    redis_client = await redis.from_url(
        "redis://redis:6379/0",
        encoding="utf-8",
        decode_responses=True
    )

    # 初始化配置服务
    config_service = ConfigService(redis_client)

    # 加载默认配置
    await load_default_configs()

    # 注册到服务发现中心
    await register_to_registry()
    
    # 启动心跳任务
    if service_id:
        heartbeat_task = asyncio.create_task(heartbeat_loop())

    logger.info("Config Center started successfully")

    yield

    # 清理
    logger.info("Config Center shutting down...")
    
    # 停止心跳
    if heartbeat_task:
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
    
    # 注销服务
    await unregister_from_registry()
    
    # 关闭HTTP客户端
    if http_client:
        await http_client.aclose()
    
    # 关闭Redis连接
    if redis_client:
        await redis_client.close()
    logger.info("Config Center shut down")


async def load_default_configs():
    """加载默认配置"""
    llm_api_key = os.getenv("SINOCHEM_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    llm_base_url = os.getenv("LLM_BASE_URL", "")
    llm_model = os.getenv("LLM_MODEL", "Qwen2.5-72B-32K-B-DX0s")
    llm_provider = os.getenv("LLM_PROVIDER", "Sinochem")
    llm_available_models_env = os.getenv("LLM_AVAILABLE_MODELS", "").strip()
    if llm_available_models_env:
        try:
            llm_available_models = json.loads(llm_available_models_env)
        except Exception as exc:
            logger.warning(f"Failed to parse LLM_AVAILABLE_MODELS, falling back to single-model list: {exc}")
            llm_available_models = [
                {"value": llm_model, "label": llm_model, "provider": llm_provider},
            ]
    else:
        llm_available_models = [
            {"value": llm_model, "label": llm_model, "provider": llm_provider},
        ]

    default_configs = [
        ConfigItem(
            key="rate_limit.requests_per_minute",
            value=60,
            description="API限流：每分钟请求数",
            environment="default"
        ),
        ConfigItem(
            key="circuit_breaker.failure_threshold",
            value=5,
            description="熔断器：失败阈值",
            environment="default"
        ),
        ConfigItem(
            key="circuit_breaker.recovery_timeout",
            value=60,
            description="熔断器：恢复超时（秒）",
            environment="default"
        ),
        ConfigItem(
            key="service.request_timeout",
            value=30,
            description="服务请求超时（秒）",
            environment="default"
        ),
        ConfigItem(
            key="service.max_retries",
            value=3,
            description="服务请求最大重试次数",
            environment="default"
        ),
        # LLM配置（从环境变量读取，不硬编码）
        ConfigItem(
            key="llm.api_key",
            value=llm_api_key,
            description="LLM API密钥（内网模型/统一密钥）",
            environment="default"
        ),
        ConfigItem(
            key="llm.base_url",
            value=llm_base_url,
            description="LLM服务基础URL（OpenAI兼容）",
            environment="default"
        ),
        ConfigItem(
            key="llm.model",
            value=llm_model,
            description="LLM模型名称（内网模型）",
            environment="default"
        ),
        ConfigItem(
            key="llm.temperature",
            value=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            description="LLM温度参数",
            environment="default"
        ),
        ConfigItem(
            key="llm.max_tokens",
            value=int(os.getenv("LLM_MAX_TOKENS", "4096")),
            description="LLM最大token数",
            environment="default"
        ),
        ConfigItem(
            key="llm.default_model",
            value=llm_model,
            description="LLM默认模型（向后兼容）",
            environment="default"
        ),
        ConfigItem(
            key="llm.available_models",
            value=llm_available_models,
            description="可用LLM模型列表（内网/白名单）",
            environment="default"
        ),
        ConfigItem(
            key="llm.default_config",
            value={
                "temperature": 0.7,
                "max_tokens": 2000,
                "prompt_template": "{input}"
            },
            description="LLM节点默认配置",
            environment="default"
        ),
        # SAP ERP配置（从环境变量读取，不硬编码敏感信息）
        ConfigItem(
            key="sap.base_url",
            value=os.getenv("SAP_BASE_URL", ""),
            description="SAP系统基础URL（如：http://sap-server:8000）",
            environment="default"
        ),
        ConfigItem(
            key="sap.client",
            value=os.getenv("SAP_CLIENT", "100"),
            description="SAP客户端号",
            environment="default"
        ),
        ConfigItem(
            key="sap.username",
            value=os.getenv("SAP_USERNAME", ""),
            description="SAP用户名",
            environment="default"
        ),
        ConfigItem(
            key="sap.password",
            value=os.getenv("SAP_PASSWORD", ""),
            description="SAP密码",
            environment="default"
        ),
        ConfigItem(
            key="sap.language",
            value=os.getenv("SAP_LANGUAGE", "EN"),
            description="SAP语言代码（如：EN, ZH）",
            environment="default"
        ),
        ConfigItem(
            key="sap.timeout",
            value=int(os.getenv("SAP_TIMEOUT", "300000")),
            description="SAP请求超时时间（毫秒）",
            environment="default"
        ),
        ConfigItem(
            key="sap.max_retries",
            value=int(os.getenv("SAP_MAX_RETRIES", "3")),
            description="SAP请求最大重试次数",
            environment="default"
        ),
        ConfigItem(
            key="sap.page_size",
            value=int(os.getenv("SAP_PAGE_SIZE", "1000")),
            description="SAP分页大小",
            environment="default"
        ),
        ConfigItem(
            key="sap.max_records",
            value=int(os.getenv("SAP_MAX_RECORDS", "10000")),
            description="SAP最大记录数",
            environment="default"
        ),
        # SMTP邮件配置（从环境变量读取）
        ConfigItem(
            key="smtp.server",
            value=os.getenv("SMTP_SERVER", "smtp.163.com"),
            description="SMTP服务器地址",
            environment="default"
        ),
        ConfigItem(
            key="smtp.port",
            value=int(os.getenv("SMTP_PORT", "465")),
            description="SMTP端口（465用于SSL，587用于TLS）",
            environment="default"
        ),
        ConfigItem(
            key="smtp.username",
            value=os.getenv("SMTP_USERNAME", ""),
            description="SMTP用户名（邮箱地址）",
            environment="default"
        ),
        ConfigItem(
            key="smtp.password",
            value=os.getenv("SMTP_PASSWORD", ""),
            description="SMTP密码或授权码",
            environment="default"
        ),
        ConfigItem(
            key="smtp.from_email",
            value=os.getenv("SMTP_FROM_EMAIL", ""),
            description="默认发件人邮箱地址",
            environment="default"
        ),
        ConfigItem(
            key="smtp.use_tls",
            value=os.getenv("SMTP_USE_TLS", "false").lower() == "true",
            description="是否使用TLS（默认false）",
            environment="default"
        ),
        ConfigItem(
            key="smtp.use_ssl",
            value=os.getenv("SMTP_USE_SSL", "true").lower() == "true",
            description="是否使用SSL（默认true，163邮箱使用）",
            environment="default"
        ),
    ]

    for config in default_configs:
        existing = await config_service.get_config(config.key, config.environment)
        # 如果配置不存在，或者配置值为空字符串（需要更新），则设置/更新配置
        if not existing or (isinstance(config.value, str) and config.value.strip() and existing.get("value") != config.value):
            await config_service.set_config(config)
            logger.info(f"Config initialized/updated: {config.key} = {str(config.value)[:20]}...")


# 创建应用
app = FastAPI(
    title="Configuration Center",
    description="统一配置管理中心",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 路由
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "config-center"
    }


# LLM专用端点（必须在 /api/config/{key} 之前定义，避免路由冲突）
# 使用更具体的路径模式，确保不会被 /api/config/{key} 匹配
@app.get("/api/config/llm/models", tags=["LLM Config"])
async def get_llm_models(environment: str = "default"):
    """获取可用LLM模型列表（前端专用）"""
    models_config = await config_service.get_config("llm.available_models", environment)
    if models_config:
        return {"models": models_config.get("value", [])}
    # 返回默认值
    return {
        "models": [
            {"value": "deepseek-chat", "label": "DeepSeek Chat", "provider": "DeepSeek"},
            {"value": "gpt-4", "label": "GPT-4", "provider": "OpenAI"},
            {"value": "gpt-3.5-turbo", "label": "GPT-3.5 Turbo", "provider": "OpenAI"},
            {"value": "gpt-4-turbo", "label": "GPT-4 Turbo", "provider": "OpenAI"},
        ]
    }


@app.get("/api/config/llm/default", tags=["LLM Config"])
async def get_llm_default(environment: str = "default"):
    """获取LLM默认配置（前端专用）"""
    default_model_config = await config_service.get_config("llm.default_model", environment)
    default_config_config = await config_service.get_config("llm.default_config", environment)
    
    return {
        "default_model": default_model_config.get("value", "deepseek-chat") if default_model_config else "deepseek-chat",
        "default_config": default_config_config.get("value", {
            "temperature": 0.7,
            "max_tokens": 2000,
            "prompt_template": "{input}"
        }) if default_config_config else {
            "temperature": 0.7,
            "max_tokens": 2000,
            "prompt_template": "{input}"
        }
    }


@app.get("/api/config/{key}")
async def get_config(key: str, environment: str = "default"):
    """获取配置"""
    config = await config_service.get_config(key, environment)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return config


@app.post("/api/config")
async def create_config(config: ConfigItem):
    """创建/更新配置"""
    success = await config_service.set_config(config)
    if success:
        return {"message": "Config saved", "key": config.key, "version": config.version}
    raise HTTPException(status_code=500, detail="Failed to save config")


@app.put("/api/config/{key}")
async def update_config(key: str, update: ConfigUpdate, environment: str = "default"):
    """更新配置"""
    existing = await config_service.get_config(key, environment)
    if not existing:
        raise HTTPException(status_code=404, detail="Config not found")

    config = ConfigItem(
        key=key,
        value=update.value,
        description=update.description or existing.get("description"),
        environment=environment
    )

    success = await config_service.set_config(config)
    if success:
        return {"message": "Config updated", "key": key, "version": config.version}
    raise HTTPException(status_code=500, detail="Failed to update config")


@app.delete("/api/config/{key}")
async def delete_config(key: str, environment: str = "default"):
    """删除配置"""
    success = await config_service.delete_config(key, environment)
    if success:
        return {"message": "Config deleted", "key": key}
    raise HTTPException(status_code=404, detail="Config not found")


@app.get("/api/configs")
async def list_configs(environment: str = "default"):
    """列出所有配置"""
    configs = await config_service.list_configs(environment)
    return {"configs": configs, "count": len(configs)}


@app.get("/api/configs/all")
async def get_all_configs(environment: str = "default"):
    """获取所有配置（扁平化，适合服务使用）"""
    configs = await config_service.get_all_configs(environment)
    return configs


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Configuration Center",
        "version": "1.0.0",
        "status": "running"
    }

"""
SAP元数据智能体主应用
"""
import logging
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings

from .core.sap_metadata_orchestrator import SAPMetadataOrchestrator
from .services.sap_database_client import SAPDatabaseClient
from .services.sap_mcp_client import SAPMCPClient
from .services.metadata_client import MetadataClient
from .routes.sap_metadata_routes import router

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """应用配置"""
    # 配置中心URL
    config_center_url: str = os.getenv("CONFIG_CENTER_URL", "http://config-center:8090")
    
    # SAP数据库配置（可以从配置中心获取）
    sap_db_type: str = os.getenv("SAP_DB_TYPE", "hdb")
    sap_db_host: str = os.getenv("SAP_DB_HOST", "")
    sap_db_port: int = int(os.getenv("SAP_DB_PORT", "33015"))
    sap_db_name: str = os.getenv("SAP_DB_NAME", "")
    sap_db_user: str = os.getenv("SAP_DB_USER", "")
    sap_db_password: str = os.getenv("SAP_DB_PASSWORD", "")
    
    # SAP OData配置（可以从配置中心获取）
    sap_base_url: str = os.getenv("SAP_BASE_URL", "")
    sap_client: str = os.getenv("SAP_CLIENT", "100")
    sap_username: str = os.getenv("SAP_USERNAME", "")
    sap_password: str = os.getenv("SAP_PASSWORD", "")
    sap_language: str = os.getenv("SAP_LANGUAGE", "EN")
    
    # 服务集成配置
    mcp_gateway_url: str = os.getenv("MCP_GATEWAY_URL", "http://mcp-gateway:8001")
    metadata_service_url: str = os.getenv("METADATA_SERVICE_URL", "http://metadata-service:8005")
    knowledge_base_url: str = os.getenv("KNOWLEDGE_BASE_URL", "http://knowledge-base:8004")
    agent_service_url: str = os.getenv("AGENT_SERVICE_URL", "http://agent-service:8010")
    
    # 应用配置
    app_name: str = "SAP元数据智能体"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

# 全局编排器实例
orchestrator: SAPMetadataOrchestrator = None


async def load_config_from_center():
    """从配置中心加载SAP配置"""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            config_keys = [
                "sap.base_url", "sap.client", "sap.username", "sap.password",
                "sap.language", "sap.db_type", "sap.db_host", "sap.db_port",
                "sap.db_name", "sap.db_user", "sap.db_password"
            ]
            configs = {}
            for key in config_keys:
                try:
                    response = await client.get(f"{settings.config_center_url}/api/config/{key}")
                    if response.status_code == 200:
                        config_data = response.json()
                        if config_data and config_data.get("value"):
                            # 转换配置key格式
                            config_key = key.replace(".", "_").upper()
                            configs[config_key] = config_data["value"]
                            logger.info(f"Loaded config from center: {key}")
                except Exception as e:
                    logger.debug(f"Failed to load config {key}: {e}")
            return configs
    except Exception as e:
        logger.warning(f"Failed to load config from center: {e}, using environment variables")
        return {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global orchestrator
    
    logger.info("SAP Metadata Agent starting up...")
    
    # 从配置中心加载配置
    center_configs = await load_config_from_center()
    if center_configs:
        # 更新settings（如果配置中心有值）
        if "SAP_BASE_URL" in center_configs:
            settings.sap_base_url = center_configs["SAP_BASE_URL"]
        if "SAP_CLIENT" in center_configs:
            settings.sap_client = center_configs["SAP_CLIENT"]
        if "SAP_USERNAME" in center_configs:
            settings.sap_username = center_configs["SAP_USERNAME"]
        if "SAP_PASSWORD" in center_configs:
            settings.sap_password = center_configs["SAP_PASSWORD"]
        if "SAP_LANGUAGE" in center_configs:
            settings.sap_language = center_configs["SAP_LANGUAGE"]
        if "SAP_DB_TYPE" in center_configs:
            settings.sap_db_type = center_configs["SAP_DB_TYPE"]
        if "SAP_DB_HOST" in center_configs:
            settings.sap_db_host = center_configs["SAP_DB_HOST"]
        if "SAP_DB_PORT" in center_configs:
            settings.sap_db_port = int(center_configs["SAP_DB_PORT"])
        if "SAP_DB_NAME" in center_configs:
            settings.sap_db_name = center_configs["SAP_DB_NAME"]
        if "SAP_DB_USER" in center_configs:
            settings.sap_db_user = center_configs["SAP_DB_USER"]
        if "SAP_DB_PASSWORD" in center_configs:
            settings.sap_db_password = center_configs["SAP_DB_PASSWORD"]
        logger.info("Loaded SAP configuration from config center")
    
    # 初始化数据库客户端（如果配置了）
    db_client = None
    if settings.sap_db_host and settings.sap_db_user:
        try:
            db_client = SAPDatabaseClient(
                db_type=settings.sap_db_type,
                host=settings.sap_db_host,
                port=settings.sap_db_port,
                database=settings.sap_db_name,
                user=settings.sap_db_user,
                password=settings.sap_db_password
            )
            if db_client.connect():
                logger.info("SAP database client connected successfully")
            else:
                logger.warning("Failed to connect to SAP database, continuing without database discovery")
                db_client = None
        except Exception as e:
            logger.warning(f"Failed to initialize SAP database client: {e}, continuing without database discovery")
            db_client = None
    
    # 初始化MCP客户端
    mcp_client = None
    try:
        sap_mcp_server_url = os.getenv("SAP_MCP_SERVER_URL", "http://sap-mcp-server:3000")
        mcp_client = SAPMCPClient(
            mcp_gateway_url=settings.mcp_gateway_url,
            sap_mcp_server_url=sap_mcp_server_url
        )
        logger.info("SAP MCP client initialized (with direct server access)")
    except Exception as e:
        logger.warning(f"Failed to initialize SAP MCP client: {e}, continuing without OData discovery")
        mcp_client = None
    
    # 初始化元数据客户端
    metadata_client = None
    try:
        metadata_client = MetadataClient(settings.metadata_service_url)
        logger.info("Metadata client initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize metadata client: {e}")
        metadata_client = None
    
    # 创建编排器
    orchestrator = SAPMetadataOrchestrator(
        db_client=db_client,
        mcp_client=mcp_client,
        metadata_client=metadata_client,
        knowledge_base_url=settings.knowledge_base_url
    )
    
    # 将编排器注入到路由
    from .routes.sap_metadata_routes import set_orchestrator
    set_orchestrator(orchestrator)
    
    logger.info("SAP Metadata Agent started successfully")
    
    yield
    
    # 清理资源
    logger.info("SAP Metadata Agent shutting down...")
    if db_client:
        db_client.disconnect()
    if mcp_client:
        await mcp_client.close()
    if metadata_client:
        await metadata_client.close()
    if orchestrator:
        await orchestrator.semantic_builder.close()
    logger.info("SAP Metadata Agent shut down complete")


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    description="SAP ERP系统元数据管理和发现智能体",
    version=settings.app_version,
    lifespan=lifespan
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "endpoints": {
            "discover": "/api/sap-metadata/discover",
            "assets": "/api/sap-metadata/assets",
            "entities": "/api/sap-metadata/entities",
            "processes": "/api/sap-metadata/processes",
            "health": "/api/sap-metadata/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "sap-metadata-agent.src.main:app",
        host="0.0.0.0",
        port=8015,
        reload=settings.debug
    )


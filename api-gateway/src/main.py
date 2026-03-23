"""
API Gateway主应用
统一的API入口，提供路由、负载均衡、限流、熔断等功能
"""
from fastapi import FastAPI, Request, Response, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import logging

from .config import settings
from .core.service_discovery import service_discovery
from .core.proxy import gateway_proxy
from .core.intelligent_router import intelligent_router
from .core.stream_proxy import stream_proxy
from .core.websocket_proxy import websocket_proxy
from .middleware.rate_limiter import setup_rate_limiting, limiter
from .middleware.metrics import MetricsMiddleware
from .middleware.intelligent_routing import IntelligentRoutingMiddleware

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("API Gateway starting up...")

    # 启动服务发现客户端
    await service_discovery.start()

    # 启动网关代理
    await gateway_proxy.start()

    # 初始化智能路由器（如果需要LLM，会在这里初始化）
    logger.info("Intelligent Router initialized")

    logger.info(f"API Gateway started successfully on {settings.HOST}:{settings.PORT}")

    yield

    # 关闭时清理资源
    logger.info("API Gateway shutting down...")
    await service_discovery.stop()
    await gateway_proxy.stop()
    # 关闭流式代理客户端
    if stream_proxy.http_client:
        await stream_proxy.http_client.aclose()
    logger.info("API Gateway shutdown complete")


# 创建FastAPI应用
app = FastAPI(
    title="Enterprise AI Platform - API Gateway",
    description="统一的API网关，提供路由、负载均衡、限流、熔断等功能",
    version="1.0.0",
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加监控中间件
if settings.METRICS_ENABLED:
    app.add_middleware(MetricsMiddleware)

# 添加智能路由中间件（在其他中间件之后，路由之前）
app.add_middleware(IntelligentRoutingMiddleware)

# 配置限流
setup_rate_limiting(app)


# WebSocket路由 - 代理到agent-service
@app.websocket("/api/v1/ws/{session_id}")
async def websocket_proxy_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket代理端点

    将WebSocket连接代理到agent-service的WebSocket端点
    """
    from fastapi import WebSocketDisconnect
    try:
        # 直接代理到agent-service的WebSocket端点
        target_path = f"/api/v1/ws/{session_id}"
        await websocket_proxy.proxy_websocket(
            websocket=websocket,
            target_service="agent-service",
            target_path=target_path
        )
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket proxy error: {e}", exc_info=True)

# WebSocket路由 - 代理到workflow-engine
@app.websocket("/api/ws/workflows/{workflow_id}")
async def workflow_websocket_proxy_endpoint(websocket: WebSocket, workflow_id: str):
    """
    工作流WebSocket代理端点

    将WebSocket连接代理到workflow-engine的WebSocket端点
    """
    from fastapi import WebSocketDisconnect
    try:
        target_path = f"/api/ws/workflows/{workflow_id}"
        await websocket_proxy.proxy_websocket(
            websocket=websocket,
            target_service="workflow-engine",
            target_path=target_path
        )
    except WebSocketDisconnect:
        logger.info(f"Workflow WebSocket disconnected for workflow {workflow_id}")
    except Exception as e:
        logger.error(f"Workflow WebSocket proxy error: {e}", exc_info=True)


# 健康检查
@app.get("/health")
async def health_check():
    """网关健康检查"""
    registry_healthy = await service_discovery.healthcheck()

    return {
        "status": "healthy" if registry_healthy else "degraded",
        "service": "api-gateway",
        "registry_connection": "connected" if registry_healthy else "disconnected",
    }


# Prometheus指标端点
@app.get("/metrics")
async def metrics():
    """Prometheus指标"""
    if not settings.METRICS_ENABLED:
        raise HTTPException(status_code=404, detail="Metrics not enabled")

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# ========== 服务路由 ==========

# Workflow Engine - 处理不带路径参数的情况（必须在 /api/workflows/{path:path} 之前）
@app.api_route("/api/workflows", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def workflow_engine_proxy_root(request: Request):
    """工作流引擎代理（根路径）"""
    forward_path = "/api/v1/workflows"
    logger.info(f"Workflow proxy (root): {request.method} {request.url.path} -> workflow-engine:{forward_path}")
    return await gateway_proxy.forward_request(
        request=request,
        service_name="workflow-engine",
        path=forward_path
    )

# Workflow Engine Monitoring - 监控路由（必须在 /api/workflows 之前注册，避免路径冲突）
@app.api_route("/api/v1/monitoring", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@app.api_route("/api/v1/monitoring/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def workflow_monitoring_proxy(request: Request, path: str = ""):
    """工作流引擎监控代理"""
    # 构建转发路径 - 转发到工作流引擎的 /api/v1/monitoring/{path}
    forward_path = f"/api/v1/monitoring/{path}" if path else "/api/v1/monitoring"
    logger.info(f"Workflow monitoring proxy: {request.method} {request.url.path} -> workflow-engine:{forward_path}")
    return await gateway_proxy.forward_request(
        request=request,
        service_name="workflow-engine",
        path=forward_path
    )


# Workflow Engine - 处理带路径参数的情况
@app.api_route("/api/workflows/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def workflow_engine_proxy(request: Request, path: str):
    """工作流引擎代理"""
    # 移除路径中可能存在的重复前缀
    clean_path = path
    if clean_path.startswith("/api/v1/workflows/"):
        clean_path = clean_path[len("/api/v1/workflows/"):]
    elif clean_path.startswith("api/v1/workflows/"):
        clean_path = clean_path[len("api/v1/workflows/"):]
    elif clean_path.startswith("/api/workflows/"):
        clean_path = clean_path[len("/api/workflows/"):]
    elif clean_path.startswith("api/workflows/"):
        clean_path = clean_path[len("api/workflows/"):]
    elif clean_path.startswith("/api/v1/"):
        clean_path = clean_path[len("/api/v1/"):]
    elif clean_path.startswith("api/v1/"):
        clean_path = clean_path[len("api/v1/"):]
    elif clean_path.startswith("/api/"):
        clean_path = clean_path[len("/api/"):]
    elif clean_path.startswith("api/"):
        clean_path = clean_path[len("api/"):]

    # 构建转发路径 - 转发到工作流引擎的 /api/v1/workflows/{path}
    # 如果clean_path为空，说明请求的是 /api/workflows/，应该转发到 /api/v1/workflows
    if not clean_path or clean_path == "":
        forward_path = "/api/v1/workflows"
    else:
        forward_path = f"/api/v1/workflows/{clean_path}"

    logger.info(f"Workflow proxy: {request.method} {request.url.path} -> workflow-engine:{forward_path}")
    return await gateway_proxy.forward_request(
        request=request,
        service_name="workflow-engine",
        path=forward_path
    )


# MCP Gateway
@app.api_route("/api/mcp/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def mcp_gateway_proxy(request: Request, path: str):
    """MCP网关代理"""
    return await gateway_proxy.forward_request(
        request=request,
        service_name="mcp-gateway",
        path=f"/api/{path}"
    )


# Auth Service - 认证相关路由（/auth/*）
@app.api_route("/api/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE * 2}/minute")  # 认证服务允许更高频率
async def auth_service_proxy(request: Request, path: str):
    """认证服务代理"""
    # 移除路径中可能存在的 /api/auth 前缀（防止重复）
    clean_path = path
    if clean_path.startswith("/api/auth/"):
        clean_path = clean_path[len("/api/auth/"):]
    elif clean_path.startswith("api/auth/"):
        clean_path = clean_path[len("api/auth/"):]
    elif clean_path.startswith("/auth/"):
        clean_path = clean_path[len("/auth/"):]
    elif clean_path.startswith("auth/"):
        clean_path = clean_path[len("auth/"):]

    # 构建转发路径
    forward_path = f"/auth/{clean_path}" if clean_path else "/auth"
    return await gateway_proxy.forward_request(
        request=request,
        service_name="auth-service",
        path=forward_path
    )


# Auth Service - 用户相关路由（/users/*）
@app.api_route("/api/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def users_service_proxy(request: Request, path: str):
    """用户服务代理"""
    return await gateway_proxy.forward_request(
        request=request,
        service_name="auth-service",
        path=f"/users/{path}" if path else "/users"
    )


# Auth Service - 管理后台路由（/admin/*）
@app.api_route("/api/admin/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def admin_service_proxy(request: Request, path: str):
    """管理后台服务代理"""
    # 项目管理相关路由转发到project-management服务
    if path.startswith("projects"):
        clean_path = path[len("projects"):].lstrip("/")
        return await gateway_proxy.forward_request(
            request=request,
            service_name="project-management",
            path=f"/api/v1/projects/{clean_path}" if clean_path else "/api/v1/projects"
        )

    # 其他管理后台路由转发到auth-service
    return await gateway_proxy.forward_request(
        request=request,
        service_name="auth-service",
        path=f"/admin/{path}" if path else "/admin"
    )


# Project Management Service - 项目管理服务路由
@app.api_route("/api/v1/projects", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@app.api_route("/api/v1/projects/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def project_management_proxy(request: Request, path: str = ""):
    """项目管理服务代理"""
    forward_path = f"/api/v1/projects/{path}" if path else "/api/v1/projects"
    logger.info(f"Project management proxy: {request.method} {request.url.path} -> project-management:{forward_path}")
    return await gateway_proxy.forward_request(
        request=request,
        service_name="project-management",
        path=forward_path
    )

# 项目群管理路由
@app.api_route("/api/v1/programs", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@app.api_route("/api/v1/programs/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def programs_proxy(request: Request, path: str = ""):
    """项目群管理服务代理"""
    forward_path = f"/api/v1/programs/{path}" if path else "/api/v1/programs"
    logger.info(f"Programs proxy: {request.method} {request.url.path} -> project-management:{forward_path}")
    return await gateway_proxy.forward_request(
        request=request,
        service_name="project-management",
        path=forward_path
    )

# 任务管理路由
@app.api_route("/api/v1/tasks", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@app.api_route("/api/v1/tasks/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def tasks_proxy(request: Request, path: str = ""):
    """任务管理服务代理"""
    forward_path = f"/api/v1/tasks/{path}" if path else "/api/v1/tasks"
    return await gateway_proxy.forward_request(
        request=request,
        service_name="project-management",
        path=forward_path
    )

# 里程碑管理路由
@app.api_route("/api/v1/milestones", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@app.api_route("/api/v1/milestones/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def milestones_proxy(request: Request, path: str = ""):
    """里程碑管理服务代理"""
    forward_path = f"/api/v1/milestones/{path}" if path else "/api/v1/milestones"
    return await gateway_proxy.forward_request(
        request=request,
        service_name="project-management",
        path=forward_path
    )

# 周报管理路由
@app.api_route("/api/v1/weekly-reports", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@app.api_route("/api/v1/weekly-reports/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def weekly_reports_proxy(request: Request, path: str = ""):
    """周报管理服务代理"""
    forward_path = f"/api/v1/weekly-reports/{path}" if path else "/api/v1/weekly-reports"
    return await gateway_proxy.forward_request(
        request=request,
        service_name="project-management",
        path=forward_path
    )

# 月报管理路由
@app.api_route("/api/v1/monthly-reports", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@app.api_route("/api/v1/monthly-reports/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def monthly_reports_proxy(request: Request, path: str = ""):
    """月报管理服务代理"""
    forward_path = f"/api/v1/monthly-reports/{path}" if path else "/api/v1/monthly-reports"
    return await gateway_proxy.forward_request(
        request=request,
        service_name="project-management",
        path=forward_path
    )

# 风险管理路由
@app.api_route("/api/v1/risks", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@app.api_route("/api/v1/risks/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def risks_proxy(request: Request, path: str = ""):
    """风险管理服务代理"""
    forward_path = f"/api/v1/risks/{path}" if path else "/api/v1/risks"
    return await gateway_proxy.forward_request(
        request=request,
        service_name="project-management",
        path=forward_path
    )

# 项目阶段路由
@app.api_route("/api/v1/project-phases", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@app.api_route("/api/v1/project-phases/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def project_phases_proxy(request: Request, path: str = ""):
    """项目阶段服务代理"""
    forward_path = f"/api/v1/project-phases/{path}" if path else "/api/v1/project-phases"
    return await gateway_proxy.forward_request(
        request=request,
        service_name="project-management",
        path=forward_path
    )

# 基础数据管理路由
@app.api_route("/api/v1/basic-data", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@app.api_route("/api/v1/basic-data/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def basic_data_proxy(request: Request, path: str = ""):
    """基础数据管理服务代理"""
    forward_path = f"/api/v1/basic-data/{path}" if path else "/api/v1/basic-data"
    logger.info(f"Basic data proxy: {request.method} {request.url.path} -> project-management:{forward_path}")
    return await gateway_proxy.forward_request(
        request=request,
        service_name="project-management",
        path=forward_path
    )

# 待办事项管理路由
@app.api_route("/api/v1/todos", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@app.api_route("/api/v1/todos/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def todos_proxy(request: Request, path: str = ""):
    """待办事项管理服务代理"""
    forward_path = f"/api/v1/todos/{path}" if path else "/api/v1/todos"
    logger.info(f"Todos proxy: {request.method} {request.url.path} -> project-management:{forward_path}")
    return await gateway_proxy.forward_request(
        request=request,
        service_name="project-management",
        path=forward_path
    )

# 项目模板管理路由
@app.api_route("/api/v1/project-templates", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@app.api_route("/api/v1/project-templates/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def project_templates_proxy(request: Request, path: str = ""):
    """项目模板管理服务代理"""
    forward_path = f"/api/v1/project-templates/{path}" if path else "/api/v1/project-templates"
    logger.info(f"Project templates proxy: {request.method} {request.url.path} -> project-management:{forward_path}")
    return await gateway_proxy.forward_request(
        request=request,
        service_name="project-management",
        path=forward_path
    )


# Config Center - 配置中心路由
@app.api_route("/api/config/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def config_center_proxy(request: Request, path: str):
    """配置中心代理"""
    return await gateway_proxy.forward_request(
        request=request,
        service_name="config-center",
        path=f"/api/config/{path}" if path else "/api/config"
    )


# Knowledge Base
@app.api_route("/api/knowledge/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def knowledge_base_proxy(request: Request, path: str):
    """知识库服务代理"""
    # 移除路径中可能存在的重复前缀
    clean_path = path
    if clean_path.startswith("/api/knowledge/"):
        clean_path = clean_path[len("/api/knowledge/"):]
    elif clean_path.startswith("api/knowledge/"):
        clean_path = clean_path[len("api/knowledge/"):]
    elif clean_path.startswith("/api/"):
        clean_path = clean_path[len("/api/"):]
    elif clean_path.startswith("api/"):
        clean_path = clean_path[len("api/"):]

    # 构建转发路径
    forward_path = f"/api/{clean_path}" if clean_path else "/api"
    return await gateway_proxy.forward_request(
        request=request,
        service_name="knowledge-base",
        path=forward_path
    )


# AI Scenario Service - 场景库
@app.api_route("/api/ai-scenarios", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@app.api_route("/api/ai-scenarios/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def ai_scenario_proxy(request: Request, path: str = ""):
    """AI应用场景收集服务代理"""
    forward_path = f"/api/v1/ai-scenarios/{path}" if path else "/api/v1/ai-scenarios"
    return await gateway_proxy.forward_request(
        request=request,
        service_name="ai-scenario-service",
        path=forward_path,
    )


# Memory Service
@app.api_route("/api/memory/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def memory_service_proxy(request: Request, path: str):
    """记忆服务代理"""
    return await gateway_proxy.forward_request(
        request=request,
        service_name="memory-service",
        path=f"/api/{path}"
    )


# Metadata Service
@app.api_route("/api/metadata/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def metadata_service_proxy(request: Request, path: str):
    """元数据服务代理"""
    return await gateway_proxy.forward_request(
        request=request,
        service_name="metadata-service",
        path=f"/api/{path}"
    )


# DAG Orchestrator Service
@app.api_route("/api/dag/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def dag_orchestrator_proxy(request: Request, path: str):
    """DAG编排服务代理"""
    return await gateway_proxy.forward_request(
        request=request,
        service_name="dag-orchestrator",
        path=f"/api/v1/{path}" if path else "/api/v1"
    )


# Intelligent Routing - 智能路由端点（必须在 /api/chat/{path} 之前注册）
# 流式智能对话端点（必须在 /api/chat/intelligent 之前注册）
@app.api_route("/api/chat/intelligent/stream", methods=["POST"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def intelligent_chat_stream_proxy(request: Request):
    """
    流式智能对话端点 - 统一路由到agent-service
    所有智能路由决策由agent-service的OrchestrationEngine处理
    """
    try:
        # 统一路由到agent-service
        target_service = "agent-service"
        path = "/intelligent/stream"

        logger.info(f"Streaming routing: {request.method} {request.url.path} -> {target_service}:{path}")

        return await stream_proxy.proxy_stream(request, target_service, path)
    except Exception as e:
        logger.error(f"Error in streaming routing: {e}", exc_info=True)
        from fastapi.responses import StreamingResponse
        async def error_stream():
            import json
            error_msg = json.dumps({"type": "error", "error": str(e)})
            yield f"data: {error_msg}\n\n"

        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream",
            status_code=500
        )


@app.api_route("/api/chat/intelligent", methods=["POST"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def intelligent_chat_proxy(request: Request):
    """
    智能对话端点 - 统一路由到agent-service
    所有智能路由决策由agent-service的OrchestrationEngine处理
    """
    try:
        # 检查是否是流式请求
        accept_header = request.headers.get("accept", "")
        is_stream = "text/event-stream" in accept_header or request.query_params.get("stream") == "true"

        # 统一路由到agent-service
        target_service = "agent-service"

        if is_stream:
            # 流式请求，使用流式代理
            path = "/intelligent/stream"
            logger.info(f"Routing to {target_service}{path} (stream)")
            return await stream_proxy.proxy_stream(request, target_service, path)
        else:
            # 非流式请求，使用普通代理
            path = "/intelligent"
            logger.info(f"Routing to {target_service}{path}")

            # 转发请求到agent-service
            return await gateway_proxy.forward_request(
                request=request,
                service_name=target_service,
                path=path
            )
    except Exception as e:
        logger.error(f"Error routing to agent-service: {e}", exc_info=True)
        # 出错时返回错误响应
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Failed to route to agent-service",
                "error": str(e)
            }
        )




# Agent Service - 动态工作流路由（必须在 /api/agents/{path} 之前注册）
@app.api_route("/api/v1/dynamic-workflow/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def dynamic_workflow_proxy(request: Request, path: str):
    """动态工作流服务代理"""
    # 检查是否是流式请求
    accept_header = request.headers.get("accept", "")
    is_stream = "text/event-stream" in accept_header or "/stream" in path or "execute" in path

    logger.info(f"Dynamic workflow routing: {request.method} {request.url.path} -> agent-service:/api/v1/dynamic-workflow/{path}")

    if is_stream:
        # 流式请求，使用流式代理
        return await stream_proxy.proxy_stream(
            request=request,
            service_name="agent-service",
            path=f"/api/v1/dynamic-workflow/{path}" if path else "/api/v1/dynamic-workflow"
        )
    else:
        # 非流式请求，使用普通代理
        return await gateway_proxy.forward_request(
            request=request,
            service_name="agent-service",
            path=f"/api/v1/dynamic-workflow/{path}" if path else "/api/v1/dynamic-workflow"
        )


# Agent Service - /api/v1/prompts 路由（提示词管理，必须在 /api/v1/agents 之前注册）
@app.api_route("/api/v1/prompts", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@app.api_route("/api/v1/prompts/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def prompts_service_proxy(request: Request, path: str = ""):
    """提示词管理服务代理 - /api/v1/prompts 路由"""
    try:
        logger.info(f"Prompts routing: {request.method} {request.url.path} -> agent-service:/api/v1/prompts/{path if path else ''}")

        return await gateway_proxy.forward_request(
            request=request,
            service_name="agent-service",
            path=f"/api/v1/prompts/{path}" if path else "/api/v1/prompts"
        )
    except Exception as e:
        logger.error(f"Error routing prompts request to agent-service: {e}", exc_info=True)
        return JSONResponse(
            status_code=502,
            content={
                "detail": "Failed to connect to agent-service",
                "error": str(e),
                "message": "提示词服务暂时不可用，请检查agent-service是否正在运行"
            }
        )


# Agent Service - /api/v1/agents 路由（必须在 /api/agents/{path} 之前注册）
@app.api_route("/api/v1/agents", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@app.api_route("/api/v1/agents/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def agent_service_v1_proxy(request: Request, path: str = ""):
    """智能体服务代理 - /api/v1/agents 路由"""
    # 检查是否是流式请求
    accept_header = request.headers.get("accept", "")
    is_stream = "text/event-stream" in accept_header or "/stream" in path

    if is_stream:
        # 流式请求，使用流式代理
        return await stream_proxy.proxy_stream(
            request=request,
            service_name="agent-service",
            path=f"/api/v1/agents/{path}" if path else "/api/v1/agents"
        )
    else:
        # 非流式请求，使用普通代理
        return await gateway_proxy.forward_request(
            request=request,
            service_name="agent-service",
            path=f"/api/v1/agents/{path}" if path else "/api/v1/agents"
        )


# Agent Service - 其他路由
@app.api_route("/api/agents/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def agent_service_proxy(request: Request, path: str):
    """智能体服务代理"""
    # 检查是否是流式请求
    accept_header = request.headers.get("accept", "")
    is_stream = "text/event-stream" in accept_header or "/stream" in path

    if is_stream:
        # 流式请求，使用流式代理
        return await stream_proxy.proxy_stream(
            request=request,
            service_name="agent-service",
            path=f"/api/v1/{path}" if path else "/api/v1"
        )
    else:
        # 非流式请求，使用普通代理
        return await gateway_proxy.forward_request(
            request=request,
            service_name="agent-service",
            path=f"/api/v1/{path}" if path else "/api/v1"
        )


# Agent Orchestrator
@app.api_route("/api/orchestrate/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def agent_orchestrator_proxy(request: Request, path: str):
    """智能体编排服务代理"""
    return await gateway_proxy.forward_request(
        request=request,
        service_name="agent-orchestrator",
        path=f"/api/v1/orchestrate/{path}" if path else "/api/v1/orchestrate"
    )


# Agent Registry
@app.api_route("/api/agent-registry/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def agent_registry_proxy(request: Request, path: str):
    """智能体注册中心代理"""
    return await gateway_proxy.forward_request(
        request=request,
        service_name="agent-registry",
        path=f"/api/v1/registry/{path}" if path else "/api/v1/registry"
    )


# Registry Service (管理端点)
@app.api_route("/api/registry/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def registry_service_proxy(request: Request, path: str):
    """服务注册中心代理"""
    return await gateway_proxy.forward_request(
        request=request,
        service_name="registry-service",
        path=f"/api/{path}"
    )


# JoyAgent Adapter - JoyAgent适配器路由
@app.api_route("/api/joyagent/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def joyagent_adapter_proxy(request: Request, path: str):
    """JoyAgent适配器代理"""
    return await gateway_proxy.forward_request(
        request=request,
        service_name="joyagent-adapter",
        path=f"/api/joyagent/{path}" if path else "/api/joyagent"
    )


# 统一搜索路由
from .routes import unified_search, knowledge_graph_monitor, nl_query, assistant, intelligent_monitoring, knowledge_graph, analytics, enterprise_architecture, neo4j_graph
app.include_router(unified_search.router)
app.include_router(knowledge_graph_monitor.router)
app.include_router(knowledge_graph.router)
app.include_router(neo4j_graph.router)
app.include_router(nl_query.router)
app.include_router(assistant.router)
app.include_router(intelligent_monitoring.router)
app.include_router(analytics.router)
app.include_router(enterprise_architecture.router)

# 策略管理路由（里程碑3）
try:
    from .routes import policy_management
    app.include_router(policy_management.router)
    logger.info("策略管理API路由已注册")
except Exception as e:
    logger.warning(f"策略管理API路由注册失败: {e}")

# 反馈API路由
from .routes import feedback, value_metrics
app.include_router(feedback.router)
app.include_router(value_metrics.router)


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "API Gateway",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "Service Discovery",
            "Load Balancing",
            "Rate Limiting",
            "Circuit Breaker",
            "Request Retry",
            "Metrics Collection",
            "Unified Search"
        ]
    }


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器，确保所有错误响应都包含CORS头"""
    logger.error(f"Global exception: {exc}", exc_info=True)
    response = JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__
        }
    )
    # 确保CORS头存在
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

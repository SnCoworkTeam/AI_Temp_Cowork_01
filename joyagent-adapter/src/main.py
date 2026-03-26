"""
JoyAgent Adapter Service Main Application

FastAPI application that provides REST API for integrating JoyAgent-JDGenie
with the enterprise AI platform.
"""
import asyncio
import sys
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import structlog
import uvicorn

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.routes.joyagent import router as joyagent_router
from src.services.joyagent_service import joyagent_service
from src.integrations.platform_integration import platform_integrator


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting JoyAgent Adapter Service")

    try:
        # Initialize services
        await joyagent_service.initialize()
        await platform_integrator.initialize()

        logger.info(
            "JoyAgent Adapter Service started successfully",
            port=settings.service_port,
            debug=settings.debug
        )

        yield

    finally:
        # Shutdown
        logger.info("Shutting down JoyAgent Adapter Service")

        try:
            await joyagent_service.shutdown()
            await platform_integrator.shutdown()
            logger.info("JoyAgent Adapter Service shut down successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="JoyAgent Adapter Service",
    description="""
    JoyAgent Adapter Service provides REST API integration between JoyAgent-JDGenie
    and the Enterprise AI Platform.

    ## Features

    * **Multi-Agent Task Management** - Create and manage JoyAgent tasks
    * **Platform Integration** - Seamless integration with workflow engine, knowledge base, and MCP tools
    * **Real-time Status Tracking** - Monitor task progress and results
    * **Enterprise Features** - Authentication, logging, monitoring, and scalability

    ## Task Types

    * `query` - Natural language query processing
    * `report_generation` - Analytical report generation
    * `code_generation` - Code generation and analysis
    * `ppt_generation` - PowerPoint presentation creation
    * `data_analysis` - Data analysis and insights
    * `document_processing` - Document analysis and processing
    * `workflow_execution` - Workflow task execution

    ## Integration Endpoints

    * `/integrations/workflow` - Workflow engine integration
    * `/integrations/knowledge` - Knowledge base enhancement
    * `/integrations/mcp` - MCP tool coordination
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured logging"""
    logger.error(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_EXCEPTION",
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
            "timestamp": structlog.processors.TimeStamper()._make_stamper("iso")(None, None, None)["timestamp"]
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with structured logging"""
    logger.error(
        "Unexpected exception occurred",
        exception=str(exc),
        exception_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An internal server error occurred",
            "type": type(exc).__name__,
            "path": request.url.path,
            "timestamp": structlog.processors.TimeStamper()._make_stamper("iso")(None, None, None)["timestamp"]
        }
    )


# Include API routes
app.include_router(
    joyagent_router,
    prefix="/api/joyagent",
    tags=["JoyAgent"]
)


# Root endpoint
@app.get(
    "/",
    summary="Service Information",
    description="Get basic information about the JoyAgent Adapter Service"
)
async def root():
    """Root endpoint with service information"""
    return {
        "service": "JoyAgent Adapter Service",
        "version": "1.0.0",
        "description": "REST API for integrating JoyAgent-JDGenie with Enterprise AI Platform",
        "status": "healthy",
        "docs_url": "/docs",
        "health_url": "/api/joyagent/health",
        "capabilities": [
            "Multi-agent task management",
            "Platform service integration",
            "Real-time task monitoring",
            "Workflow integration",
            "Knowledge enhancement",
            "MCP tool coordination"
        ]
    }


# Additional health endpoint at root level
@app.get(
    "/health",
    summary="Health Check",
    description="Quick health check endpoint"
)
async def health():
    """Simple health check endpoint"""
    return {"status": "healthy", "service": "joyagent-adapter"}


def main():
    """Main entry point"""
    # Configure Python logging to work with structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper())
    )

    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.service_host,
        port=settings.service_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        workers=settings.worker_processes,
        access_log=True,
        use_colors=True
    )


if __name__ == "__main__":
    main()
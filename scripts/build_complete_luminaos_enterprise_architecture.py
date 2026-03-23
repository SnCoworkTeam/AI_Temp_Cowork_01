"""
完整的LuminaOS平台企业架构数据构建脚本
将LuminaOS平台作为企业架构的一部分，详细构建所有数据
包括：组织架构、业务架构、应用架构（所有微服务）、数据架构、技术架构
"""
import asyncio
import sys
from pathlib import Path
from uuid import uuid4
import logging
import os

# 设置Windows控制台编码
if sys.platform == "win32":
    os.system("chcp 65001")  # Change active code page to UTF-8

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.src.core.session import get_db, init_session_factory
from database.src.models.enterprise_architecture_models import (
    OrganizationUnit, BusinessRole, BusinessProcess, BusinessCapability,
    BusinessService, ApplicationSystem, ApplicationService, APIInterface,
    DataEntity, DataModel, DataFlow, TechnologyType, TechnologyInstance,
    TechnologyComponent, TechnologyStack, InfrastructureComponent
)
# 尝试多种路径
possible_paths = [
    project_root / "metadata-service" / "src",
    project_root / "metadata_service" / "src",
    Path("/app/src"),
    Path("/opt/enterprise-ai-platform/metadata-service/src"),
]
for path in possible_paths:
    if path.exists():
        sys.path.insert(0, str(path))
        break

try:
    from services.enterprise_architecture_sync_service import EnterpriseArchitectureSyncService
except ImportError:
    try:
        from metadata_service.src.services.enterprise_architecture_sync_service import EnterpriseArchitectureSyncService
    except ImportError:
        from src.services.enterprise_architecture_sync_service import EnterpriseArchitectureSyncService
from database.src.core.neo4j_client import get_neo4j_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ========== LuminaOS平台微服务定义 ==========
LUMINAOS_MICROSERVICES = [
    {
        "name": "API Gateway",
        "code": "API_GATEWAY",
        "description": "统一API网关，提供路由、限流、熔断等功能",
        "port": 8080,
        "endpoint": "http://api-gateway:8080",
        "health_check": "/health"
    },
    {
        "name": "Registry Service",
        "code": "REGISTRY_SERVICE",
        "description": "服务注册与发现中心",
        "port": 8000,
        "endpoint": "http://registry-service:8000",
        "health_check": "/health"
    },
    {
        "name": "Config Center",
        "code": "CONFIG_CENTER",
        "description": "配置管理中心",
        "port": 8090,
        "endpoint": "http://config-center:8090",
        "health_check": "/health"
    },
    {
        "name": "Auth Service",
        "code": "AUTH_SERVICE",
        "description": "认证授权服务",
        "port": 8003,
        "endpoint": "http://auth-service:8003",
        "health_check": "/health"
    },
    {
        "name": "Metadata Service",
        "code": "METADATA_SERVICE",
        "description": "元数据管理服务，提供企业架构管理功能",
        "port": 8005,
        "endpoint": "http://metadata-service:8005",
        "health_check": "/api/health"
    },
    {
        "name": "Knowledge Base",
        "code": "KNOWLEDGE_BASE",
        "description": "知识库服务，提供文档管理和向量检索",
        "port": 8004,
        "endpoint": "http://knowledge-base:8004",
        "health_check": "/api/health"
    },
    {
        "name": "Chat Service",
        "code": "CHAT_SERVICE",
        "description": "AI助手对话管理服务",
        "port": 8006,
        "endpoint": "http://chat-service:8006",
        "health_check": "/health"
    },
    {
        "name": "Workflow Engine",
        "code": "WORKFLOW_ENGINE",
        "description": "工作流编排和执行引擎",
        "port": 8002,
        "endpoint": "http://workflow-engine:8002",
        "health_check": "/health"
    },
    {
        "name": "Agent Service",
        "code": "AGENT_SERVICE",
        "description": "智能体核心服务",
        "port": 8010,
        "endpoint": "http://agent-service:8010",
        "health_check": "/api/v1/health"
    },
    {
        "name": "Agent Orchestrator",
        "code": "AGENT_ORCHESTRATOR",
        "description": "智能体编排服务",
        "port": 8011,
        "endpoint": "http://agent-orchestrator:8011",
        "health_check": "/api/v1/health"
    },
    {
        "name": "Agent Registry",
        "code": "AGENT_REGISTRY",
        "description": "智能体注册中心",
        "port": 8012,
        "endpoint": "http://agent-registry:8012",
        "health_check": "/api/v1/health"
    },
    {
        "name": "DAG Orchestrator",
        "code": "DAG_ORCHESTRATOR",
        "description": "DAG编排服务",
        "port": 8009,
        "endpoint": "http://dag-orchestrator:8009",
        "health_check": "/health"
    },
    {
        "name": "MCP Gateway",
        "code": "MCP_GATEWAY",
        "description": "MCP协议网关服务",
        "port": 8001,
        "endpoint": "http://mcp-gateway:8001",
        "health_check": "/health"
    },
    {
        "name": "SAP MCP Server",
        "code": "SAP_MCP_SERVER",
        "description": "SAP OData转MCP协议服务",
        "port": 3001,
        "endpoint": "http://sap-mcp-server:3000",
        "health_check": "/health"
    },
    {
        "name": "Memory Service",
        "code": "MEMORY_SERVICE",
        "description": "智能体记忆管理服务",
        "port": 8013,
        "endpoint": "http://memory-service:8013",
        "health_check": "/health"
    },
    {
        "name": "JoyAgent Adapter",
        "code": "JOYAGENT_ADAPTER",
        "description": "JoyAgent适配器服务",
        "port": 8007,
        "endpoint": "http://joyagent-adapter:8007",
        "health_check": "/health"
    },
    {
        "name": "Web UI",
        "code": "WEB_UI",
        "description": "前端Web界面",
        "port": 3000,
        "endpoint": "http://web-ui:3000",
        "health_check": "/api/health"
    }
]


async def init_organization_architecture(db, sync_service):
    """初始化组织架构数据"""
    print("=" * 60)
    print("初始化组织架构数据...")
    print("=" * 60)
    
    # 1. 创建组织单元
    orgs = [
        {
            "name": "LuminaOS集团",
            "code": "LUMINA_GROUP",
            "description": "LuminaOS企业AI平台总部",
            "organization_type": "集团",
            "level": 1
        },
        {
            "name": "技术中心",
            "code": "TECH_CENTER",
            "description": "技术研发中心",
            "organization_type": "部门",
            "level": 2,
            "parent_code": "LUMINA_GROUP"
        },
        {
            "name": "产品部",
            "code": "PRODUCT_DEPT",
            "description": "产品管理部门",
            "organization_type": "部门",
            "level": 2,
            "parent_code": "LUMINA_GROUP"
        },
        {
            "name": "AI平台团队",
            "code": "AI_PLATFORM_TEAM",
            "description": "AI平台开发与维护团队",
            "organization_type": "团队",
            "level": 3,
            "parent_code": "TECH_CENTER"
        },
        {
            "name": "企业架构团队",
            "code": "EA_TEAM",
            "description": "企业架构管理团队",
            "organization_type": "团队",
            "level": 3,
            "parent_code": "TECH_CENTER"
        },
        {
            "name": "基础设施团队",
            "code": "INFRA_TEAM",
            "description": "基础设施运维团队",
            "organization_type": "团队",
            "level": 3,
            "parent_code": "TECH_CENTER"
        }
    ]
    
    org_map = {}
    for org_data in orgs:
        # 检查是否已存在
        existing = db.query(OrganizationUnit).filter_by(code=org_data["code"]).first()
        if existing:
            org_map[org_data["code"]] = existing
            print(f"  [SKIP] 组织单元已存在: {existing.name}")
            continue
            
        parent_id = None
        if "parent_code" in org_data:
            parent = org_map.get(org_data["parent_code"])
            if parent:
                parent_id = parent.id
        
        org = OrganizationUnit(
            id=uuid4(),
            name=org_data["name"],
            code=org_data["code"],
            description=org_data["description"],
            organization_type=org_data["organization_type"],
            level=org_data["level"],
            parent_id=parent_id,
            status="active"
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        org_map[org.code] = org
        print(f"  ✅ 创建组织单元: {org.name}")
        
        # 同步到Neo4j
        await sync_service.sync_organization_unit(org)
            
    return org_map


async def init_business_architecture(db, sync_service, org_map):
    """初始化业务架构数据"""
    print("\n" + "=" * 60)
    print("初始化业务架构数据...")
    print("=" * 60)
    
    # 1. 创建业务能力
    capabilities = [
        {
            "name": "智能决策支持",
            "code": "INTELLIGENT_DECISION_SUPPORT",
            "description": "利用AI提供决策支持能力",
            "level": 1,
            "maturity_level": "mature",
            "business_value": "high",
            "investment_priority": "high",
            "owner_org_code": "AI_PLATFORM_TEAM"
        },
        {
            "name": "数据治理",
            "code": "DATA_GOVERNANCE",
            "description": "管理企业数据资产",
            "level": 1,
            "maturity_level": "mature",
            "business_value": "high",
            "investment_priority": "high",
            "owner_org_code": "TECH_CENTER"
        },
        {
            "name": "企业架构管理",
            "code": "ENTERPRISE_ARCHITECTURE_MANAGEMENT",
            "description": "企业架构规划、设计和管理",
            "level": 1,
            "maturity_level": "developing",
            "business_value": "high",
            "investment_priority": "high",
            "owner_org_code": "EA_TEAM"
        },
        {
            "name": "智能体服务",
            "code": "AGENT_SERVICES",
            "description": "提供智能体创建、管理和执行能力",
            "level": 1,
            "maturity_level": "mature",
            "business_value": "high",
            "investment_priority": "high",
            "owner_org_code": "AI_PLATFORM_TEAM"
        },
        {
            "name": "工作流编排",
            "code": "WORKFLOW_ORCHESTRATION",
            "description": "提供工作流编排和执行能力",
            "level": 1,
            "maturity_level": "mature",
            "business_value": "high",
            "investment_priority": "high",
            "owner_org_code": "AI_PLATFORM_TEAM"
        },
        {
            "name": "知识管理",
            "code": "KNOWLEDGE_MANAGEMENT",
            "description": "企业知识库管理和检索",
            "level": 1,
            "maturity_level": "mature",
            "business_value": "high",
            "investment_priority": "high",
            "owner_org_code": "AI_PLATFORM_TEAM"
        }
    ]
    
    cap_map = {}
    for cap_data in capabilities:
        existing = db.query(BusinessCapability).filter_by(name=cap_data["name"]).first()
        if existing:
            cap_map[cap_data["name"]] = existing
            print(f"  [SKIP] 业务能力已存在: {existing.name}")
            continue
            
        org = org_map.get(cap_data["owner_org_code"])
        # 检查code字段是否存在
        cap_kwargs = {
            "id": uuid4(),
            "name": cap_data["name"],
            "description": cap_data["description"],
            "level": cap_data["level"],
            "owner_organization_id": org.id if org else None
        }
        # code字段可能不存在，暂时不添加
        # if "code" in cap_data:
        #     try:
        #         cap_kwargs["code"] = cap_data["code"]
        #     except:
        #         pass
        # 新字段可能不存在，暂时注释掉
        # if "maturity_level" in cap_data and cap_data.get("maturity_level"):
        #     try:
        #         cap_kwargs["maturity_level"] = cap_data["maturity_level"]
        #     except:
        #         pass
        # if "business_value" in cap_data and cap_data.get("business_value"):
        #     try:
        #         cap_kwargs["business_value"] = cap_data["business_value"]
        #     except:
        #         pass
        # if "investment_priority" in cap_data and cap_data.get("investment_priority"):
        #     try:
        #         cap_kwargs["investment_priority"] = cap_data["investment_priority"]
        #     except:
        #         pass
        
        capability = BusinessCapability(**cap_kwargs)
        db.add(capability)
        db.commit()
        db.refresh(capability)
        cap_map[capability.name] = capability
        print(f"  ✅ 创建业务能力: {capability.name}")
        
        # 同步到Neo4j
        await sync_service.sync_business_capability(capability)
            
    # 2. 创建业务流程
    processes = [
        {
            "name": "AI模型开发流程",
            "code": "AI_MODEL_DEVELOPMENT",
            "description": "AI模型的开发、训练、部署流程",
            "classification": "支持流程",
            "level": 1,
            "owner": "AI平台团队",
            "priority": "high",
            "org_code": "AI_PLATFORM_TEAM"
        },
        {
            "name": "企业架构管理流程",
            "code": "EA_MANAGEMENT",
            "description": "企业架构的规划、设计、实施和治理流程",
            "classification": "支持流程",
            "level": 1,
            "owner": "企业架构团队",
            "priority": "high",
            "org_code": "EA_TEAM"
        },
        {
            "name": "智能体生命周期管理",
            "code": "AGENT_LIFECYCLE",
            "description": "智能体的创建、注册、执行、监控和退役流程",
            "classification": "核心流程",
            "level": 1,
            "owner": "AI平台团队",
            "priority": "high",
            "org_code": "AI_PLATFORM_TEAM"
        },
        {
            "name": "工作流编排流程",
            "code": "WORKFLOW_ORCHESTRATION_PROCESS",
            "description": "工作流的创建、编排、执行和监控流程",
            "classification": "核心流程",
            "level": 1,
            "owner": "AI平台团队",
            "priority": "high",
            "org_code": "AI_PLATFORM_TEAM"
        },
        {
            "name": "知识库管理流程",
            "code": "KB_MANAGEMENT",
            "description": "知识库的创建、文档上传、向量化、检索流程",
            "classification": "支持流程",
            "level": 1,
            "owner": "AI平台团队",
            "priority": "medium",
            "org_code": "AI_PLATFORM_TEAM"
        }
    ]
    
    proc_map = {}
    for proc_data in processes:
        existing = db.query(BusinessProcess).filter_by(name=proc_data["name"]).first()
        if existing:
            proc_map[proc_data["name"]] = existing
            print(f"  [SKIP] 业务流程已存在: {existing.name}")
            continue
            
        org = org_map.get(proc_data["org_code"])
        process = BusinessProcess(
            id=uuid4(),
            name=proc_data["name"],
            description=proc_data["description"],
            classification=proc_data["classification"],
            level=proc_data["level"],
            owner=proc_data["owner"],
            organization_id=org.id if org else None,
            status="active"
        )
        db.add(process)
        db.commit()
        db.refresh(process)
        proc_map[process.name] = process
        print(f"  ✅ 创建业务流程: {process.name}")
        
        # 同步到Neo4j
        await sync_service.sync_business_process(process)
            
    return cap_map


async def init_application_architecture(db, sync_service, org_map):
    """初始化应用架构数据 - LuminaOS平台及其所有微服务"""
    print("\n" + "=" * 60)
    print("初始化应用架构数据 - LuminaOS平台...")
    print("=" * 60)
    
    # 1. 创建LuminaOS AI平台应用系统
    org_ai_platform = org_map.get("AI_PLATFORM_TEAM")
    
    # 检查是否已存在
    existing_platform = db.query(ApplicationSystem).filter_by(name="LuminaOS AI平台").first()
    if existing_platform:
        luminaos_platform = existing_platform
        print(f"  [SKIP] 应用系统已存在: {luminaos_platform.name}")
    else:
        luminaos_platform = ApplicationSystem(
        id=uuid4(),
        name="LuminaOS AI平台",
        code="LUMINAOS_AI_PLATFORM",
        description="企业级AI能力中台，提供智能体、工作流、知识图谱、企业架构等核心能力",
        system_type="自建系统",
        vendor="LuminaOS",
        version="1.0.0",
        system_category="核心系统",
        deployment_model="cloud",
        criticality="critical",
        availability_requirement="99.9%",
        support_team="AI平台团队",
        cost_center="TECH-001",
        business_owner_org_id=org_ai_platform.id if org_ai_platform else None,
        status="active",
        license_info={"type": "proprietary", "expiry": None},
        integration_points=[
            {"type": "REST API", "endpoint": "http://api-gateway:8080"},
            {"type": "MCP Protocol", "endpoint": "http://mcp-gateway:8001"}
        ]
        )
        db.add(luminaos_platform)
        db.commit()
        db.refresh(luminaos_platform)
        print(f"  ✅ 创建应用系统: {luminaos_platform.name}")
        await sync_service.sync_application_system(luminaos_platform)
    
    # 2. 为每个微服务创建ApplicationService
    service_map = {}
    for microservice in LUMINAOS_MICROSERVICES:
        # 检查是否已存在
        existing_service = db.query(ApplicationService).filter_by(name=microservice["name"]).first()
        if existing_service:
            service_map[microservice["code"]] = existing_service
            print(f"  [SKIP] 应用服务已存在: {existing_service.name}")
            continue
            
        service = ApplicationService(
            id=uuid4(),
            application_id=luminaos_platform.id,
            name=microservice["name"],
            code=microservice["code"],
            description=microservice["description"],
            service_type="Microservice",
            protocol="HTTP",
            endpoint=microservice["endpoint"],
            version="1.0.0",
            status="active",
            health_check_endpoint=f"{microservice['endpoint']}{microservice['health_check']}",
            service_dependencies=[]  # 可以根据实际情况填充
        )
        db.add(service)
        db.commit()
        db.refresh(service)
        service_map[microservice["code"]] = service
        print(f"  ✅ 创建应用服务: {service.name} ({service.code})")
        
        # 同步到Neo4j（如果方法存在）
        if hasattr(sync_service, 'sync_application_service'):
            await sync_service.sync_application_service(service)
    
    # 3. 创建主要API接口
    api_interfaces = [
        {
            "name": "企业架构组织列表",
            "code": "GET_ORGANIZATIONS",
            "path": "/api/enterprise-architecture/organizations",
            "method": "GET",
            "service_code": "METADATA_SERVICE",
            "description": "获取组织架构列表"
        },
        {
            "name": "企业架构业务架构",
            "code": "GET_BUSINESS_ARCHITECTURE",
            "path": "/api/enterprise-architecture/business",
            "method": "GET",
            "service_code": "METADATA_SERVICE",
            "description": "获取业务架构数据"
        },
        {
            "name": "技术实例列表",
            "code": "GET_TECHNOLOGY_INSTANCES",
            "path": "/api/enterprise-architecture/technology/instances",
            "method": "GET",
            "service_code": "METADATA_SERVICE",
            "description": "获取技术实例列表"
        },
        {
            "name": "智能体创建",
            "code": "CREATE_AGENT",
            "path": "/api/v1/agents",
            "method": "POST",
            "service_code": "AGENT_SERVICE",
            "description": "创建智能体"
        },
        {
            "name": "工作流执行",
            "code": "EXECUTE_WORKFLOW",
            "path": "/api/workflows/execute",
            "method": "POST",
            "service_code": "WORKFLOW_ENGINE",
            "description": "执行工作流"
        },
        {
            "name": "知识库查询",
            "code": "QUERY_KNOWLEDGE_BASE",
            "path": "/api/knowledge-bases/query",
            "method": "POST",
            "service_code": "KNOWLEDGE_BASE",
            "description": "查询知识库"
        }
    ]
    
    for api_data in api_interfaces:
        service = service_map.get(api_data["service_code"])
        if service:
            # APIInterface的name字段可能不存在，先创建基本字段
            api = APIInterface(
                id=uuid4(),
                code=api_data["code"],
                service_id=service.id,
                application_system_id=luminaos_platform.id,
                path=api_data["path"],
                method=api_data["method"],
                interface_type="REST",
                description=api_data["description"]
            )
            # 尝试设置可选字段（如果模型支持）
            try:
                api.name = api_data["name"]
            except:
                pass
            try:
                api.endpoint = f"{service.endpoint}{api_data['path']}"
            except:
                pass
            try:
                api.protocol = "HTTP"
            except:
                pass
            try:
                api.version = "v1"
            except:
                pass
            try:
                api.status = "active"
            except:
                pass
            db.add(api)
            db.commit()
            db.refresh(api)
            print(f"  ✅ 创建API接口: {api.method} {api.path}")
            
            # 同步到Neo4j（如果方法存在）
            if hasattr(sync_service, 'sync_api_interface'):
                await sync_service.sync_api_interface(api)
    
    return luminaos_platform, service_map


async def init_data_architecture(db, sync_service, luminaos_platform):
    """初始化数据架构数据"""
    print("\n" + "=" * 60)
    print("初始化数据架构数据...")
    print("=" * 60)
    
    # 1. 创建数据模型
    data_model = DataModel(
        id=uuid4(),
        name="LuminaOS平台数据模型",
        description="LuminaOS平台核心数据模型，包括企业架构、智能体、工作流、知识库等",
        model_type="logical",
        version="1.0",
        application_system_id=luminaos_platform.id,
        status="active",
        definition={
            "entities": [
                "OrganizationUnit",
                "BusinessProcess",
                "BusinessCapability",
                "ApplicationSystem",
                "TechnologyInstance",
                "Agent",
                "Workflow",
                "KnowledgeBase"
            ]
        }
    )
    db.add(data_model)
    db.commit()
    db.refresh(data_model)
    print(f"  ✅ 创建数据模型: {data_model.name}")
    # 同步到Neo4j（暂时跳过，后续通过sync_all_ea_data统一同步）
    # await sync_service.sync_data_model(data_model)
    
    # 2. 创建数据实体
    entities = [
        {
            "name": "组织单元",
            "code": "ORG_UNIT",
            "description": "组织架构中的组织单元实体",
            "entity_type": "主数据",
            "table_name": "organization_units",
            "schema_name": "public"
        },
        {
            "name": "业务流程",
            "code": "BUSINESS_PROCESS",
            "description": "业务流程实体",
            "entity_type": "业务数据",
            "table_name": "business_processes",
            "schema_name": "public"
        },
        {
            "name": "业务能力",
            "code": "BUSINESS_CAPABILITY",
            "description": "业务能力实体",
            "entity_type": "业务数据",
            "table_name": "business_capabilities",
            "schema_name": "public"
        },
        {
            "name": "应用系统",
            "code": "APPLICATION_SYSTEM",
            "description": "应用系统实体",
            "entity_type": "业务数据",
            "table_name": "application_systems",
            "schema_name": "public"
        },
        {
            "name": "技术实例",
            "code": "TECHNOLOGY_INSTANCE",
            "description": "技术实例实体",
            "entity_type": "技术数据",
            "table_name": "technology_instances",
            "schema_name": "public"
        },
        {
            "name": "智能体",
            "code": "AGENT",
            "description": "智能体实体",
            "entity_type": "业务数据",
            "table_name": "agents",
            "schema_name": "public"
        },
        {
            "name": "工作流",
            "code": "WORKFLOW",
            "description": "工作流实体",
            "entity_type": "业务数据",
            "table_name": "workflows",
            "schema_name": "public"
        },
        {
            "name": "知识库",
            "code": "KNOWLEDGE_BASE",
            "description": "知识库实体",
            "entity_type": "业务数据",
            "table_name": "knowledge_bases",
            "schema_name": "public"
        }
    ]
    
    entity_map = {}
    for ent_data in entities:
        existing = db.query(DataEntity).filter_by(name=ent_data["name"]).first()
        if existing:
            entity_map[ent_data["code"]] = existing
            print(f"  [SKIP] 数据实体已存在: {existing.name}")
            continue
            
        entity = DataEntity(
            id=uuid4(),
            name=ent_data["name"],
            code=ent_data["code"],
            description=ent_data["description"],
            entity_type=ent_data["entity_type"],
            application_system_id=luminaos_platform.id,
            data_model_id=data_model.id,
            table_name=ent_data.get("table_name"),
            schema_name=ent_data.get("schema_name"),
            status="active",
            sensitivity_level="internal",
            retention_policy="长期保留",
            backup_frequency="每日",
            data_volume="待统计"
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        entity_map[entity.code] = entity
        print(f"  ✅ 创建数据实体: {entity.name} ({entity.code})")
        
        # 同步到Neo4j（暂时跳过，后续通过sync_all_ea_data统一同步）
        # if hasattr(sync_service, 'sync_data_entity'):
        #     await sync_service.sync_data_entity(entity)
    
    return entity_map


async def init_technology_architecture(db, sync_service, luminaos_platform):
    """初始化技术架构数据 - 按系统划分"""
    print("\n" + "=" * 60)
    print("初始化技术架构数据 - LuminaOS平台技术实例...")
    print("=" * 60)
    
    # 1. 创建技术类型
    tech_types_data = [
        {"name": "PostgreSQL", "category": "Database", "description": "关系型数据库", "lifecycle_status": "strategic"},
        {"name": "Neo4j", "category": "Database", "description": "图数据库", "lifecycle_status": "strategic"},
        {"name": "Qdrant", "category": "Vector Database", "description": "向量数据库", "lifecycle_status": "strategic"},
        {"name": "Redis", "category": "Cache", "description": "内存数据库/缓存", "lifecycle_status": "strategic"},
        {"name": "FastAPI", "category": "Framework", "description": "Python Web框架", "lifecycle_status": "strategic"},
        {"name": "Python", "category": "Language", "description": "编程语言", "lifecycle_status": "strategic"},
        {"name": "Docker", "category": "Containerization", "description": "容器化技术", "lifecycle_status": "strategic"},
        {"name": "Nginx", "category": "Web Server", "description": "高性能Web服务器/反向代理", "lifecycle_status": "strategic"},
        {"name": "Node.js", "category": "Runtime", "description": "JavaScript运行时", "lifecycle_status": "strategic"},
        {"name": "Next.js", "category": "Framework", "description": "React前端框架", "lifecycle_status": "strategic"},
    ]
    
    tech_type_map = {}
    for tt_data in tech_types_data:
        existing = db.query(TechnologyType).filter_by(name=tt_data["name"]).first()
        if existing:
            tech_type_map[tt_data["name"]] = existing
            print(f"  [SKIP] 技术类型已存在: {existing.name}")
            continue
            
        tech_type = TechnologyType(id=uuid4(), **tt_data)
        db.add(tech_type)
        db.commit()
        db.refresh(tech_type)
        tech_type_map[tech_type.name] = tech_type
        print(f"  ✅ 创建技术类型: {tech_type.name} ({tech_type.category})")
        
            # 同步到Neo4j（暂时跳过，后续通过sync_all_ea_data统一同步）
            # await sync_service.sync_technology_type(tech_type)
    
    # 2. 创建技术实例（按系统划分，所有实例都属于LuminaOS平台）
    tech_instances_data = [
        {
            "name": "LuminaOS PostgreSQL主库",
            "instance_id": "LUMINAOS_PG_001",
            "technology_name": "PostgreSQL",
            "version": "15.0",
            "vendor": "PostgreSQL",
            "deployment_type": "dedicated",
            "host": "postgres",
            "port": 5432,
            "description": "LuminaOS平台关系型数据存储",
            "capacity": "500GB",
            "location": "应用服务器"
        },
        {
            "name": "LuminaOS Neo4j图库",
            "instance_id": "LUMINAOS_NEO4J_001",
            "technology_name": "Neo4j",
            "version": "5.14",
            "vendor": "Neo4j",
            "deployment_type": "dedicated",
            "host": "43.143.90.179",
            "port": 7687,
            "description": "LuminaOS平台知识图谱数据存储",
            "capacity": "200GB",
            "location": "图数据库服务器"
        },
        {
            "name": "LuminaOS Redis缓存",
            "instance_id": "LUMINAOS_REDIS_001",
            "technology_name": "Redis",
            "version": "7.0",
            "vendor": "Redis",
            "deployment_type": "dedicated",
            "host": "redis",
            "port": 6379,
            "description": "LuminaOS平台缓存服务",
            "capacity": "16GB",
            "location": "应用服务器"
        },
        {
            "name": "LuminaOS FastAPI服务实例",
            "instance_id": "LUMINAOS_FASTAPI_001",
            "technology_name": "FastAPI",
            "version": "0.104.1",
            "vendor": "FastAPI",
            "deployment_type": "dedicated",
            "host": "应用服务器",
            "port": 8005,
            "description": "LuminaOS平台核心API服务",
            "capacity": "N/A",
            "location": "应用服务器"
        },
        {
            "name": "LuminaOS Next.js前端服务",
            "instance_id": "LUMINAOS_NEXTJS_001",
            "technology_name": "Next.js",
            "version": "14.0",
            "vendor": "Vercel",
            "deployment_type": "dedicated",
            "host": "web-ui",
            "port": 3000,
            "description": "LuminaOS平台前端Web界面",
            "capacity": "N/A",
            "location": "应用服务器"
        }
    ]
    
    for inst_data in tech_instances_data:
        existing = db.query(TechnologyInstance).filter_by(instance_id=inst_data["instance_id"]).first()
        if existing:
            print(f"  [SKIP] 技术实例已存在: {existing.name}")
            continue
            
        tech_type = tech_type_map.get(inst_data["technology_name"])
        if tech_type:
            instance = TechnologyInstance(
                id=uuid4(),
                name=inst_data["name"],
                instance_id=inst_data["instance_id"],
                application_system_id=luminaos_platform.id,
                technology_type=tech_type.category,
                technology_name=inst_data["technology_name"],
                technology_type_id=tech_type.id,
                version=inst_data["version"],
                vendor=inst_data["vendor"],
                deployment_type=inst_data["deployment_type"],
                host=inst_data["host"],
                port=inst_data["port"],
                description=inst_data["description"],
                capacity=inst_data.get("capacity"),
                location=inst_data.get("location"),
                status="active",
                lifecycle_status="strategic"
            )
            db.add(instance)
            db.commit()
            db.refresh(instance)
            print(f"  ✅ 创建技术实例: {instance.name} ({instance.technology_name})")
            
            # 同步到Neo4j（如果方法存在）
            if hasattr(sync_service, 'sync_technology_instance'):
                await sync_service.sync_technology_instance(instance)
        else:
            print(f"  ❌ 警告: 未找到技术类型 {inst_data['technology_name']}，跳过创建实例 {inst_data['name']}")
    
    # 3. 创建技术组件
    tech_components_data = [
        {
            "name": "LuminaOS API Gateway",
            "description": "LuminaOS平台的统一API网关",
            "component_type": "API Gateway",
            "version": "1.0.0",
            "vendor": "LuminaOS"
        },
        {
            "name": "LuminaOS Workflow Engine",
            "description": "LuminaOS平台的工作流编排与执行引擎",
            "component_type": "Workflow Engine",
            "version": "1.0.0",
            "vendor": "LuminaOS"
        },
        {
            "name": "LuminaOS Knowledge Base",
            "description": "LuminaOS平台的知识库管理模块",
            "component_type": "Knowledge Base",
            "version": "1.0.0",
            "vendor": "LuminaOS"
        },
        {
            "name": "LuminaOS Agent Service",
            "description": "LuminaOS平台的智能体核心服务",
            "component_type": "Agent Service",
            "version": "1.0.0",
            "vendor": "LuminaOS"
        }
    ]
    
    for tc_data in tech_components_data:
        existing = db.query(TechnologyComponent).filter_by(name=tc_data["name"]).first()
        if existing:
            print(f"  [SKIP] 技术组件已存在: {existing.name}")
            continue
        
        # 移除vendor字段（如果存在），因为TechnologyComponent不支持
        component_data = {k: v for k, v in tc_data.items() if k != "vendor"}
        component = TechnologyComponent(id=uuid4(), **component_data)
        db.add(component)
        db.commit()
        db.refresh(component)
        print(f"  ✅ 创建技术组件: {component.name}")
        
        # 同步到Neo4j（如果方法存在）
        if hasattr(sync_service, 'sync_technology_component'):
            await sync_service.sync_technology_component(component)
    
    # 4. 创建技术栈
    tech_stacks_data = [
        {
            "name": "LuminaOS核心技术栈",
            "description": "LuminaOS平台后端核心技术栈",
            "stack_type": "Backend",
            "technologies": ["Python", "FastAPI", "PostgreSQL", "Neo4j", "Qdrant", "Redis", "Docker"]
        },
        {
            "name": "LuminaOS前端技术栈",
            "description": "LuminaOS平台前端技术栈",
            "stack_type": "Frontend",
            "technologies": ["React", "Next.js", "Ant Design", "TypeScript"]
        }
    ]
    
    for ts_data in tech_stacks_data:
        existing = db.query(TechnologyStack).filter_by(name=ts_data["name"]).first()
        if existing:
            print(f"  [SKIP] 技术栈已存在: {existing.name}")
            continue
        
        # 移除stack_type和technologies字段（如果存在），因为TechnologyStack可能不支持
        stack_data = {k: v for k, v in ts_data.items() if k not in ["stack_type", "technologies"]}
        stack = TechnologyStack(id=uuid4(), **stack_data)
        db.add(stack)
        db.commit()
        db.refresh(stack)
        print(f"  ✅ 创建技术栈: {stack.name}")
        
        # 同步到Neo4j（如果方法存在）
        if hasattr(sync_service, 'sync_technology_stack'):
            await sync_service.sync_technology_stack(stack)
    
    # 5. 创建基础设施组件
    infra_components_data = [
        {
            "name": "LuminaOS应用服务器",
            "description": "承载LuminaOS平台服务的应用服务器",
            "component_type": "Virtual Machine",
            "location": "阿里云华东1区",
            "ip_address": "43.143.139.197",
            "os": "Ubuntu 22.04",
            "status": "active"
        },
        {
            "name": "LuminaOS图数据库服务器",
            "description": "承载Neo4j图数据库的独立服务器",
            "component_type": "Virtual Machine",
            "location": "阿里云华东1区",
            "ip_address": "43.143.90.179",
            "os": "Ubuntu 22.04",
            "status": "active"
        }
    ]
    
    for ic_data in infra_components_data:
        existing = db.query(InfrastructureComponent).filter_by(name=ic_data["name"]).first()
        if existing:
            print(f"  [SKIP] 基础设施组件已存在: {existing.name}")
            continue
        
        # 移除可能不支持的字段
        infra_data = {k: v for k, v in ic_data.items() if k not in ["location", "ip_address", "os", "status"]}
        infra = InfrastructureComponent(id=uuid4(), **infra_data)
        db.add(infra)
        db.commit()
        db.refresh(infra)
        print(f"  ✅ 创建基础设施组件: {infra.name}")
        
        # 同步到Neo4j（如果方法存在）
        if hasattr(sync_service, 'sync_infrastructure_component'):
            await sync_service.sync_infrastructure_component(infra)


async def main():
    """主函数"""
    print("=" * 60)
    print("LuminaOS平台企业架构完整数据构建")
    print("=" * 60)
    
    # 初始化数据库连接
    init_session_factory()
    db = next(get_db())
    
    # 初始化Neo4j客户端
    neo4j_client = get_neo4j_client()
    neo4j_connected = await neo4j_client.connect()
    if neo4j_connected:
        print("✅ Neo4j连接成功")
    else:
        print(f"[WARN] Neo4j连接失败，将继续初始化PostgreSQL数据: {neo4j_client.settings.NEO4J_URI}")
    
    # 创建同步服务
    sync_service = EnterpriseArchitectureSyncService(db, neo4j_client)
    
    try:
        # 1. 初始化组织架构
        org_map = await init_organization_architecture(db, sync_service)
        
        # 2. 初始化业务架构
        cap_map = await init_business_architecture(db, sync_service, org_map)
        
        # 3. 初始化应用架构
        luminaos_platform, service_map = await init_application_architecture(db, sync_service, org_map)
        
        # 4. 初始化数据架构
        entity_map = await init_data_architecture(db, sync_service, luminaos_platform)
        
        # 5. 初始化技术架构
        await init_technology_architecture(db, sync_service, luminaos_platform)
        
        print("\n" + "=" * 60)
        print("✅ LuminaOS平台企业架构数据构建完成！")
        print("=" * 60)
        print(f"  - 组织单元: {len(org_map)} 个")
        print(f"  - 业务能力: {len(cap_map)} 个")
        print(f"  - 应用系统: 1 个 (LuminaOS AI平台)")
        print(f"  - 应用服务: {len(service_map)} 个微服务")
        print(f"  - 数据实体: {len(entity_map)} 个")
        print(f"  - 技术实例: 按系统划分，属于LuminaOS平台")
        
    except Exception as e:
        logger.error(f"Error building LuminaOS enterprise architecture: {str(e)}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()
        if neo4j_connected:
            await neo4j_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())


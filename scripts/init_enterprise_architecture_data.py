"""
企业架构数据初始化脚本
创建完整的LuminaOS平台企业架构示例数据
"""
import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

import logging

from database.src.core.database import get_database_manager
from database.src.core.session import get_db, init_session_factory
from database.src.models.enterprise_architecture_models import (
    OrganizationUnit, BusinessRole, BusinessProcess, BusinessCapability,
    BusinessService, ApplicationSystem, ApplicationService, APIInterface,
    DataEntity, DataModel, DataFlow, TechnologyType, TechnologyInstance,
    TechnologyComponent, TechnologyStack, InfrastructureComponent
)
import sys
sys.path.insert(0, str(project_root / "metadata-service" / "src"))

from services.enterprise_architecture_sync_service import (
    EnterpriseArchitectureSyncService
)
from database.src.core.neo4j_client import get_neo4j_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
            "description": "AI平台开发团队",
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
        }
    ]
    
    org_map = {}
    for org_data in orgs:
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
        org_map[org_data["code"]] = org
        
        # 同步到Neo4j
        await sync_service.sync_organization_unit(org)
        print(f"  ✅ 创建组织单元: {org.name} ({org.code})")
    
    # 2. 创建业务角色
    roles = [
        {
            "name": "企业架构师",
            "description": "负责企业架构设计和规划",
            "role_type": "技术角色",
            "organization_code": "EA_TEAM"
        },
        {
            "name": "AI平台架构师",
            "description": "负责AI平台技术架构",
            "role_type": "技术角色",
            "organization_code": "AI_PLATFORM_TEAM"
        },
        {
            "name": "产品经理",
            "description": "负责产品规划和管理",
            "role_type": "业务角色",
            "organization_code": "PRODUCT_DEPT"
        }
    ]
    
    for role_data in roles:
        org = org_map.get(role_data["organization_code"])
        if org:
            role = BusinessRole(
                id=uuid4(),
                name=role_data["name"],
                description=role_data["description"],
                role_type=role_data["role_type"],
                organization_id=org.id,
                status="active"
            )
            db.add(role)
            db.commit()
            db.refresh(role)
            
            await sync_service.sync_business_role(role)
            print(f"  ✅ 创建业务角色: {role.name}")
    
    return org_map


async def init_business_architecture(db, sync_service, org_map):
    """初始化业务架构数据"""
    print("\n" + "=" * 60)
    print("初始化业务架构数据...")
    print("=" * 60)
    
    # 1. 创建业务能力
    capabilities = [
        {
            "name": "AI能力",
            "description": "提供AI相关的业务能力",
            "level": 1,
            "org_code": "LUMINA_GROUP"
        },
        {
            "name": "企业架构管理能力",
            "description": "提供企业架构管理和分析能力",
            "level": 1,
            "org_code": "LUMINA_GROUP"
        },
        {
            "name": "智能工作流能力",
            "description": "提供智能工作流编排和执行能力",
            "level": 2,
            "org_code": "AI_PLATFORM_TEAM"
        }
    ]
    
    cap_map = {}
    for cap_data in capabilities:
        org = org_map.get(cap_data["org_code"])
        capability = BusinessCapability(
            id=uuid4(),
            name=cap_data["name"],
            description=cap_data["description"],
            level=cap_data["level"],
            owner_organization_id=org.id if org else None,
            status="active"
        )
        db.add(capability)
        db.commit()
        db.refresh(capability)
        cap_map[cap_data["name"]] = capability
        
        # 同步到Neo4j
        await sync_service.sync_business_capability(capability)
        print(f"  ✅ 创建业务能力: {capability.name}")
    
    # 2. 创建业务流程
    processes = [
        {
            "name": "企业架构建模",
            "description": "建立和维护企业架构模型",
            "owner": "企业架构师",
            "classification": "管理流程",
            "level": 1,
            "org_code": "EA_TEAM",
            "capability": "企业架构管理能力"
        },
        {
            "name": "AI服务开发",
            "description": "开发和部署AI服务",
            "owner": "AI平台架构师",
            "classification": "开发流程",
            "level": 1,
            "org_code": "AI_PLATFORM_TEAM",
            "capability": "AI能力"
        },
        {
            "name": "工作流编排",
            "description": "设计和执行智能工作流",
            "owner": "产品经理",
            "classification": "运营流程",
            "level": 2,
            "org_code": "AI_PLATFORM_TEAM",
            "capability": "智能工作流能力"
        }
    ]
    
    for proc_data in processes:
        org = org_map.get(proc_data["org_code"])
        process = BusinessProcess(
            id=uuid4(),
            name=proc_data["name"],
            description=proc_data["description"],
            owner=proc_data["owner"],
            classification=proc_data["classification"],
            level=proc_data["level"],
            organization_id=org.id if org else None,
            status="active"
        )
        db.add(process)
        db.commit()
        db.refresh(process)
        
        # 同步到Neo4j
        await sync_service.sync_business_process(process)
        print(f"  ✅ 创建业务流程: {process.name}")
    
    return cap_map


async def init_application_architecture(db, sync_service, org_map):
    """初始化应用架构数据"""
    print("\n" + "=" * 60)
    print("初始化应用架构数据...")
    print("=" * 60)
    
    # 1. 创建应用系统
    systems = [
        {
            "name": "LuminaOS AI平台",
            "description": "企业AI平台核心系统",
            "system_type": "自建系统",
            "vendor": "LuminaOS",
            "version": "1.0.0",
            "system_category": "核心系统",
            "org_code": "AI_PLATFORM_TEAM"
        },
        {
            "name": "SAP ERP",
            "description": "SAP企业资源规划系统",
            "system_type": "商业系统",
            "vendor": "SAP",
            "version": "S4 HANA",
            "system_category": "核心系统",
            "org_code": "LUMINA_GROUP"
        },
        {
            "name": "WMS仓库管理系统",
            "description": "仓库管理系统",
            "system_type": "商业系统",
            "vendor": "第三方",
            "version": "v2.0",
            "system_category": "外围系统",
            "org_code": "LUMINA_GROUP"
        },
        {
            "name": "CRM客户关系管理",
            "description": "客户关系管理系统",
            "system_type": "商业系统",
            "vendor": "第三方",
            "version": "v3.0",
            "system_category": "外围系统",
            "org_code": "LUMINA_GROUP"
        }
    ]
    
    system_map = {}
    for sys_data in systems:
        org = org_map.get(sys_data["org_code"])
        system = ApplicationSystem(
            id=uuid4(),
            name=sys_data["name"],
            description=sys_data["description"],
            system_type=sys_data["system_type"],
            vendor=sys_data["vendor"],
            version=sys_data["version"],
            system_category=sys_data["system_category"],
            business_owner_org_id=org.id if org else None,
            status="active"
        )
        db.add(system)
        db.commit()
        db.refresh(system)
        system_map[sys_data["name"]] = system
        
        # 同步到Neo4j
        await sync_service.sync_application_system(system)
        print(f"  ✅ 创建应用系统: {system.name} ({system.system_category})")
    
    # 2. 创建应用服务
    services = [
        {
            "name": "企业架构服务",
            "description": "提供企业架构管理服务",
            "service_type": "REST API",
            "endpoint": "/api/enterprise-architecture",
            "system_name": "LuminaOS AI平台"
        },
        {
            "name": "工作流引擎服务",
            "description": "提供工作流编排和执行服务",
            "service_type": "REST API",
            "endpoint": "/api/workflows",
            "system_name": "LuminaOS AI平台"
        }
    ]
    
    for svc_data in services:
        system = system_map.get(svc_data["system_name"])
        if system:
            service = ApplicationService(
                id=uuid4(),
                name=svc_data["name"],
                description=svc_data["description"],
                service_type=svc_data["service_type"],
                endpoint=svc_data["endpoint"],
                application_system_id=system.id,
                status="active"
            )
            db.add(service)
            db.commit()
            print(f"  ✅ 创建应用服务: {service.name}")
    
    # 3. 创建API接口
    apis = [
        {
            "path": "/api/enterprise-architecture/organizations",
            "method": "GET",
            "description": "获取组织架构列表",
            "system_name": "LuminaOS AI平台"
        },
        {
            "path": "/api/enterprise-architecture/business",
            "method": "GET",
            "description": "获取业务架构",
            "system_name": "LuminaOS AI平台"
        }
    ]
    
    for api_data in apis:
        system = system_map.get(api_data["system_name"])
        if system:
            api = APIInterface(
                id=uuid4(),
                path=api_data["path"],
                method=api_data["method"],
                description=api_data["description"],
                application_system_id=system.id,
                code=f"{api_data['method']}_{api_data['path'].replace('/', '_')}"
            )
            db.add(api)
            db.commit()
            print(f"  ✅ 创建API接口: {api.method} {api.path}")
    
    return system_map


async def init_data_architecture(db, sync_service, system_map):
    """初始化数据架构数据"""
    print("\n" + "=" * 60)
    print("初始化数据架构数据...")
    print("=" * 60)
    
    lumina_system = system_map.get("LuminaOS AI平台")
    sap_system = system_map.get("SAP ERP")
    
    # 1. 创建数据实体
    entities = [
        {
            "name": "组织单元",
            "description": "组织架构中的组织单元实体",
            "entity_type": "主数据",
            "system_name": "LuminaOS AI平台",
            "code": "ORG_UNIT"
        },
        {
            "name": "业务流程",
            "description": "业务流程实体",
            "entity_type": "业务数据",
            "system_name": "LuminaOS AI平台",
            "code": "BUSINESS_PROCESS"
        },
        {
            "name": "采购订单",
            "description": "SAP采购订单",
            "entity_type": "事务数据",
            "system_name": "SAP ERP",
            "code": "PURCHASE_ORDER"
        }
    ]
    
    for ent_data in entities:
        system = system_map.get(ent_data["system_name"])
        if system:
            entity = DataEntity(
                id=uuid4(),
                name=ent_data["name"],
                description=ent_data["description"],
                entity_type=ent_data["entity_type"],
                application_system_id=system.id,
                code=ent_data["code"],
                status="active"
            )
            db.add(entity)
            db.commit()
            print(f"  ✅ 创建数据实体: {entity.name} ({entity.code})")
    
    # 2. 创建数据模型
    models = [
        {
            "name": "企业架构数据模型",
            "description": "企业架构核心数据模型",
            "model_type": "概念模型",
            "version": "1.0",
            "system_name": "LuminaOS AI平台"
        }
    ]
    
    for model_data in models:
        system = system_map.get(model_data["system_name"])
        if system:
            model = DataModel(
                id=uuid4(),
                name=model_data["name"],
                description=model_data["description"],
                model_type=model_data["model_type"],
                version=model_data["version"],
                application_system_id=system.id,
                status="active"
            )
            db.add(model)
            db.commit()
            print(f"  ✅ 创建数据模型: {model.name}")
    
    # 3. 创建数据流
    flows = [
        {
            "name": "组织数据流",
            "description": "组织架构数据流向",
            "flow_type": "数据同步",
            "source_system": "LuminaOS AI平台",
            "target_system": "SAP ERP"
        }
    ]
    
    for flow_data in flows:
        source = system_map.get(flow_data["source_system"])
        target = system_map.get(flow_data["target_system"])
        if source and target:
            flow = DataFlow(
                id=uuid4(),
                name=flow_data["name"],
                description=flow_data["description"],
                flow_type=flow_data["flow_type"],
                source_system_id=source.id,
                target_system_id=target.id,
                status="active"
            )
            db.add(flow)
            db.commit()
            print(f"  ✅ 创建数据流: {flow.name}")


async def init_technology_architecture(db, sync_service, system_map):
    """初始化技术架构数据"""
    print("\n" + "=" * 60)
    print("初始化技术架构数据...")
    print("=" * 60)
    
    # 1. 创建技术类型
    tech_types = [
        {
            "name": "PostgreSQL",
            "category": "Database",
            "description": "PostgreSQL关系数据库",
            "lifecycle_status": "strategic"
        },
        {
            "name": "Neo4j",
            "category": "Database",
            "description": "Neo4j图数据库",
            "lifecycle_status": "strategic"
        },
        {
            "name": "FastAPI",
            "category": "Framework",
            "description": "FastAPI Web框架",
            "lifecycle_status": "strategic"
        },
        {
            "name": "Oracle Database",
            "category": "Database",
            "description": "Oracle数据库",
            "lifecycle_status": "tactical"
        }
    ]
    
    tech_type_map = {}
    for type_data in tech_types:
        tech_type = TechnologyType(
            id=uuid4(),
            name=type_data["name"],
            category=type_data["category"],
            description=type_data["description"],
            lifecycle_status=type_data["lifecycle_status"]
        )
        db.add(tech_type)
        db.commit()
        db.refresh(tech_type)
        tech_type_map[type_data["name"]] = tech_type
        print(f"  ✅ 创建技术类型: {tech_type.name} ({tech_type.category})")
    
    # 2. 创建技术实例
    instances = [
        {
            "name": "LuminaOS PostgreSQL主库",
            "instance_id": "PG_MAIN_001",
            "technology_name": "PostgreSQL",
            "version": "15.0",
            "vendor": "PostgreSQL",
            "deployment_type": "dedicated",
            "host": "postgres.enterprise-ai-platform",
            "port": 5432,
            "system_name": "LuminaOS AI平台"
        },
        {
            "name": "LuminaOS Neo4j图库",
            "instance_id": "NEO4J_MAIN_001",
            "technology_name": "Neo4j",
            "version": "5.14",
            "vendor": "Neo4j",
            "deployment_type": "dedicated",
            "host": "neo4j.enterprise-ai-platform",
            "port": 7687,
            "system_name": "LuminaOS AI平台"
        },
        {
            "name": "SAP ERP Oracle数据库",
            "instance_id": "ORACLE_SAP_001",
            "technology_name": "Oracle Database",
            "version": "19c",
            "vendor": "Oracle",
            "deployment_type": "dedicated",
            "host": "oracle-sap.enterprise-ai-platform",
            "port": 1521,
            "system_name": "SAP ERP"
        }
    ]
    
    for inst_data in instances:
        system = system_map.get(inst_data["system_name"])
        tech_type = tech_type_map.get(inst_data["technology_name"])
        
        if system and tech_type:
            instance = TechnologyInstance(
                id=uuid4(),
                name=inst_data["name"],
                instance_id=inst_data["instance_id"],
                application_system_id=system.id,
                technology_type=tech_type.category,
                technology_name=inst_data["technology_name"],
                technology_type_id=tech_type.id,
                version=inst_data["version"],
                vendor=inst_data["vendor"],
                deployment_type=inst_data["deployment_type"],
                host=inst_data["host"],
                port=inst_data["port"],
                status="active"
            )
            db.add(instance)
            db.commit()
            db.refresh(instance)
            
            # 同步到Neo4j
            await sync_service.sync_technology_instance(instance)
            print(f"  ✅ 创建技术实例: {instance.name} ({instance.technology_name})")
    
    # 3. 创建技术组件
    components = [
        {
            "name": "API Gateway",
            "description": "统一API网关",
            "component_type": "中间件",
            "version": "1.0.0",
            "vendor": "LuminaOS"
        },
        {
            "name": "Workflow Engine",
            "description": "工作流引擎",
            "component_type": "应用组件",
            "version": "1.0.0",
            "vendor": "LuminaOS"
        }
    ]
    
    for comp_data in components:
        component = TechnologyComponent(
            id=uuid4(),
            name=comp_data["name"],
            description=comp_data["description"],
            component_type=comp_data["component_type"],
            version=comp_data["version"],
            vendor=comp_data["vendor"],
            status="active"
        )
        db.add(component)
        db.commit()
        print(f"  ✅ 创建技术组件: {component.name}")
    
    # 4. 创建技术栈
    stacks = [
        {
            "name": "LuminaOS技术栈",
            "description": "LuminaOS平台核心技术栈",
            "stack_type": "应用技术栈",
            "technologies": ["PostgreSQL", "Neo4j", "FastAPI"]
        }
    ]
    
    for stack_data in stacks:
        stack = TechnologyStack(
            id=uuid4(),
            name=stack_data["name"],
            description=stack_data["description"],
            stack_type=stack_data["stack_type"],
            status="active"
        )
        db.add(stack)
        db.commit()
        print(f"  ✅ 创建技术栈: {stack.name}")


async def main():
    """主函数"""
    print("=" * 60)
    print("LuminaOS平台企业架构数据初始化")
    print("=" * 60)
    
    # 初始化数据库会话工厂
    init_session_factory()
    
    # 初始化数据库连接
    db = next(get_db())
    
    # 初始化Neo4j客户端（可选，如果连接失败会继续执行但不同步到Neo4j）
    neo4j_client = None
    try:
        neo4j_client = get_neo4j_client()
        await neo4j_client.connect()
        print("[OK] Neo4j连接成功")
    except Exception as e:
        print(f"[WARN] Neo4j连接失败，将继续初始化PostgreSQL数据: {str(e)}")
        print("   数据将仅保存到PostgreSQL，稍后可通过API同步到Neo4j")
    
    # 创建同步服务
    sync_service = EnterpriseArchitectureSyncService(db, neo4j_client) if neo4j_client else None
    
    try:
        # 1. 初始化组织架构
        org_map = await init_organization_architecture(db, sync_service)
        
        # 2. 初始化业务架构
        cap_map = await init_business_architecture(db, sync_service, org_map)
        
        # 3. 初始化应用架构
        system_map = await init_application_architecture(db, sync_service, org_map)
        
        # 4. 初始化数据架构
        await init_data_architecture(db, sync_service, system_map)
        
        # 5. 初始化技术架构
        await init_technology_architecture(db, sync_service, system_map)
        
        # 如果Neo4j未连接，提示用户稍后同步
        if not neo4j_client:
            print("\n" + "=" * 60)
            print("[WARN] 注意：数据已保存到PostgreSQL，但未同步到Neo4j")
            print("   请稍后通过以下方式同步到Neo4j：")
            print("   1. 等待Neo4j服务完全启动")
            print("   2. 调用API: POST /api/enterprise-architecture/sync/all")
            print("=" * 60)
        
        print("\n" + "=" * 60)
        print("✅ 企业架构数据初始化完成！")
        print("=" * 60)
        
        # 统计信息
        from sqlalchemy import func
        stats = {
            "组织单元": db.query(func.count(OrganizationUnit.id)).scalar(),
            "业务角色": db.query(func.count(BusinessRole.id)).scalar(),
            "业务流程": db.query(func.count(BusinessProcess.id)).scalar(),
            "业务能力": db.query(func.count(BusinessCapability.id)).scalar(),
            "应用系统": db.query(func.count(ApplicationSystem.id)).scalar(),
            "技术实例": db.query(func.count(TechnologyInstance.id)).scalar()
        }
        
        print("\n数据统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
    except Exception as e:
        logger.error(f"Error initializing enterprise architecture data: {str(e)}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()
        if neo4j_client:
            await neo4j_client.disconnect()


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())


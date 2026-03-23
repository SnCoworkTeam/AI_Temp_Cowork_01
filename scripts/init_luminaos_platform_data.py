"""
LuminaOS平台数据初始化脚本
创建完整的LuminaOS平台数据，包括：
1. LuminaOS AI平台应用系统
2. 按系统划分的技术架构（每个系统有自己的技术实例）
3. 平台的微服务、数据库、中间件等
"""
import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from database.src.core.session import get_db, init_session_factory
from database.src.models.enterprise_architecture_models import (
    OrganizationUnit, ApplicationSystem, TechnologyType, TechnologyInstance,
    ApplicationService, APIInterface, DataEntity
)
import sys
sys.path.insert(0, str(project_root / "metadata-service" / "src"))

from services.enterprise_architecture_sync_service import (
    EnterpriseArchitectureSyncService
)
from database.src.core.neo4j_client import get_neo4j_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_luminaos_platform():
    """初始化LuminaOS平台数据"""
    print("=" * 60)
    print("LuminaOS平台数据初始化")
    print("=" * 60)
    
    # 初始化数据库连接
    init_session_factory()
    db = next(get_db())
    
    # 初始化Neo4j客户端（可选）
    neo4j_client = None
    try:
        neo4j_client = get_neo4j_client()
        await neo4j_client.connect()
        print("[OK] Neo4j连接成功")
    except Exception as e:
        print(f"[WARN] Neo4j连接失败，将继续初始化PostgreSQL数据: {str(e)}")
    
    sync_service = EnterpriseArchitectureSyncService(db, neo4j_client) if neo4j_client else None
    
    try:
        # 1. 查找或创建组织单元
        org = db.query(OrganizationUnit).filter(
            OrganizationUnit.code == "AI_PLATFORM_TEAM"
        ).first()
        
        if not org:
            # 创建组织单元
            org = OrganizationUnit(
                id=uuid4(),
                name="AI平台团队",
                code="AI_PLATFORM_TEAM",
                description="AI平台开发团队",
                organization_type="团队",
                level=3,
                status="active"
            )
            db.add(org)
            db.commit()
            db.refresh(org)
            print(f"[OK] 创建组织单元: {org.name}")
        
        # 2. 创建LuminaOS AI平台应用系统
        luminaos_system = db.query(ApplicationSystem).filter(
            ApplicationSystem.name == "LuminaOS AI平台"
        ).first()
        
        if not luminaos_system:
            luminaos_system = ApplicationSystem(
                id=uuid4(),
                name="LuminaOS AI平台",
                description="企业AI平台核心系统，提供智能体、工作流、知识图谱等能力",
                system_type="自建系统",
                vendor="LuminaOS",
                version="1.0.0",
                system_category="核心系统",
                business_owner_org_id=org.id,
                status="active"
            )
            db.add(luminaos_system)
            db.commit()
            db.refresh(luminaos_system)
            print(f"[OK] 创建应用系统: {luminaos_system.name}")
            
            if sync_service:
                await sync_service.sync_application_system(luminaos_system)
        else:
            print(f"[INFO] 应用系统已存在: {luminaos_system.name}")
        
        # 3. 创建技术类型
        tech_types_data = [
            {"name": "PostgreSQL", "category": "Database", "description": "PostgreSQL关系数据库"},
            {"name": "Neo4j", "category": "Database", "description": "Neo4j图数据库"},
            {"name": "Qdrant", "category": "Database", "description": "Qdrant向量数据库"},
            {"name": "Redis", "category": "Database", "description": "Redis缓存数据库"},
            {"name": "FastAPI", "category": "Framework", "description": "FastAPI Web框架"},
            {"name": "Python", "category": "Language", "description": "Python编程语言"},
            {"name": "Docker", "category": "Infrastructure", "description": "Docker容器化"},
            {"name": "Nginx", "category": "Middleware", "description": "Nginx反向代理"},
        ]
        
        tech_type_map = {}
        for type_data in tech_types_data:
            tech_type = db.query(TechnologyType).filter(
                TechnologyType.name == type_data["name"]
            ).first()
            
            if not tech_type:
                tech_type = TechnologyType(
                    id=uuid4(),
                    name=type_data["name"],
                    category=type_data["category"],
                    description=type_data["description"],
                    lifecycle_status="strategic"
                )
                db.add(tech_type)
                db.commit()
                db.refresh(tech_type)
                print(f"[OK] 创建技术类型: {tech_type.name}")
            
            tech_type_map[type_data["name"]] = tech_type
        
        # 4. 创建LuminaOS平台的技术实例（按系统划分）
        tech_instances_data = [
            # 数据库实例
            {
                "name": "LuminaOS PostgreSQL主库",
                "instance_id": "PG_LUMINAOS_001",
                "technology_name": "PostgreSQL",
                "version": "15.0",
                "vendor": "PostgreSQL",
                "deployment_type": "dedicated",
                "host": "postgres.enterprise-ai-platform",
                "port": 5432,
                "location": "应用服务器",
                "description": "LuminaOS平台主数据库，存储业务数据"
            },
            {
                "name": "LuminaOS Neo4j图库",
                "instance_id": "NEO4J_LUMINAOS_001",
                "technology_name": "Neo4j",
                "version": "5.14",
                "vendor": "Neo4j",
                "deployment_type": "dedicated",
                "host": "43.143.90.179",
                "port": 7687,
                "location": "图数据库服务器",
                "description": "LuminaOS平台图数据库，存储关系数据"
            },
            {
                "name": "LuminaOS Qdrant向量库",
                "instance_id": "QDRANT_LUMINAOS_001",
                "technology_name": "Qdrant",
                "version": "1.7.0",
                "vendor": "Qdrant",
                "deployment_type": "dedicated",
                "host": "qdrant.enterprise-ai-platform",
                "port": 6333,
                "location": "应用服务器",
                "description": "LuminaOS平台向量数据库，存储嵌入向量"
            },
            {
                "name": "LuminaOS Redis缓存",
                "instance_id": "REDIS_LUMINAOS_001",
                "technology_name": "Redis",
                "version": "7.0",
                "vendor": "Redis",
                "deployment_type": "dedicated",
                "host": "redis.enterprise-ai-platform",
                "port": 6379,
                "location": "应用服务器",
                "description": "LuminaOS平台缓存数据库"
            },
            # 中间件实例
            {
                "name": "LuminaOS Nginx网关",
                "instance_id": "NGINX_LUMINAOS_001",
                "technology_name": "Nginx",
                "version": "1.25.0",
                "vendor": "Nginx",
                "deployment_type": "dedicated",
                "host": "nginx.enterprise-ai-platform",
                "port": 80,
                "location": "应用服务器",
                "description": "LuminaOS平台反向代理网关"
            },
        ]
        
        for inst_data in tech_instances_data:
            tech_type = tech_type_map.get(inst_data["technology_name"])
            if not tech_type:
                continue
            
            # 检查是否已存在
            existing = db.query(TechnologyInstance).filter(
                TechnologyInstance.instance_id == inst_data["instance_id"]
            ).first()
            
            if existing:
                print(f"[INFO] 技术实例已存在: {inst_data['name']}")
                continue
            
            instance = TechnologyInstance(
                id=uuid4(),
                name=inst_data["name"],
                instance_id=inst_data["instance_id"],
                application_system_id=luminaos_system.id,
                technology_type=tech_type.category,
                technology_name=inst_data["technology_name"],
                technology_type_id=tech_type.id,
                version=inst_data["version"],
                vendor=inst_data["vendor"],
                deployment_type=inst_data["deployment_type"],
                host=inst_data["host"],
                port=inst_data["port"],
                location=inst_data.get("location"),
                description=inst_data.get("description"),
                status="active"
            )
            db.add(instance)
            db.commit()
            db.refresh(instance)
            
            if sync_service:
                await sync_service.sync_technology_instance(instance)
            
            print(f"[OK] 创建技术实例: {instance.name} (系统: {luminaos_system.name})")
        
        # 5. 创建LuminaOS平台的应用服务
        services_data = [
            {"name": "企业架构服务", "endpoint": "/api/enterprise-architecture", "description": "提供企业架构管理服务"},
            {"name": "工作流引擎服务", "endpoint": "/api/workflows", "description": "提供工作流编排和执行服务"},
            {"name": "智能体服务", "endpoint": "/api/agents", "description": "提供智能体管理服务"},
            {"name": "知识图谱服务", "endpoint": "/api/knowledge-graph", "description": "提供知识图谱服务"},
            {"name": "元数据服务", "endpoint": "/api/metadata", "description": "提供元数据管理服务"},
        ]
        
        for svc_data in services_data:
            existing = db.query(ApplicationService).filter(
                ApplicationService.name == svc_data["name"],
                ApplicationService.application_system_id == luminaos_system.id
            ).first()
            
            if existing:
                continue
            
            service = ApplicationService(
                id=uuid4(),
                name=svc_data["name"],
                description=svc_data["description"],
                service_type="REST API",
                endpoint=svc_data["endpoint"],
                application_system_id=luminaos_system.id,
                status="active"
            )
            db.add(service)
            db.commit()
            print(f"[OK] 创建应用服务: {service.name}")
        
        # 6. 创建数据实体
        entities_data = [
            {"name": "组织单元", "code": "ORG_UNIT", "entity_type": "主数据", "description": "组织架构中的组织单元实体"},
            {"name": "业务流程", "code": "BUSINESS_PROCESS", "entity_type": "业务数据", "description": "业务流程实体"},
            {"name": "应用系统", "code": "APPLICATION_SYSTEM", "entity_type": "主数据", "description": "应用系统实体"},
            {"name": "技术实例", "code": "TECHNOLOGY_INSTANCE", "entity_type": "主数据", "description": "技术实例实体"},
        ]
        
        for ent_data in entities_data:
            existing = db.query(DataEntity).filter(
                DataEntity.code == ent_data["code"],
                DataEntity.application_system_id == luminaos_system.id
            ).first()
            
            if existing:
                continue
            
            entity = DataEntity(
                id=uuid4(),
                name=ent_data["name"],
                code=ent_data["code"],
                description=ent_data["description"],
                entity_type=ent_data["entity_type"],
                application_system_id=luminaos_system.id,
                status="active"
            )
            db.add(entity)
            db.commit()
            print(f"[OK] 创建数据实体: {entity.name} ({entity.code})")
        
        print("\n" + "=" * 60)
        print("[OK] LuminaOS平台数据初始化完成！")
        print("=" * 60)
        
        # 统计信息
        from sqlalchemy import func
        stats = {
            "应用系统": db.query(func.count(ApplicationSystem.id)).filter(
                ApplicationSystem.name == "LuminaOS AI平台"
            ).scalar(),
            "技术实例": db.query(func.count(TechnologyInstance.id)).filter(
                TechnologyInstance.application_system_id == luminaos_system.id
            ).scalar(),
            "应用服务": db.query(func.count(ApplicationService.id)).filter(
                ApplicationService.application_system_id == luminaos_system.id
            ).scalar(),
            "数据实体": db.query(func.count(DataEntity.id)).filter(
                DataEntity.application_system_id == luminaos_system.id
            ).scalar()
        }
        
        print("\n数据统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
    except Exception as e:
        logger.error(f"Error initializing LuminaOS platform data: {str(e)}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()
        if neo4j_client:
            await neo4j_client.disconnect()


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    asyncio.run(init_luminaos_platform())


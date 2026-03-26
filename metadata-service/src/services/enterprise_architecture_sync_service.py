"""
企业架构数据同步服务
负责PostgreSQL和Neo4j之间的数据同步
"""
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from uuid import UUID
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.models.enterprise_architecture_models import (
    OrganizationUnit, BusinessRole, BusinessProcess, BusinessCapability,
    BusinessService, ApplicationSystem, ApplicationService, APIInterface,
    DataEntity, DataModel, DataFlow, TechnologyType, TechnologyInstance,
    TechnologyComponent, TechnologyStack, InfrastructureComponent
)
from database.src.core.neo4j_client import Neo4jClient, get_neo4j_client

logger = logging.getLogger(__name__)


class EnterpriseArchitectureSyncService:
    """企业架构数据同步服务"""
    
    def __init__(self, db: Session, neo4j_client: Optional[Neo4jClient] = None):
        self.db = db
        self.neo4j = neo4j_client or get_neo4j_client()
    
    # ========== 组织架构同步 ==========
    
    async def sync_organization_unit(self, org_unit: OrganizationUnit) -> Optional[str]:
        """同步组织单元到Neo4j"""
        if not self.neo4j:
            logger.warning("Neo4j client not available, skipping sync")
            return None
        
        try:
            # 准备节点属性
            properties = {
                "uuid": str(org_unit.id),
                "name": org_unit.name,
                "code": org_unit.code,
                "description": org_unit.description,
                "organization_type": org_unit.organization_type,
                "level": org_unit.level,
                "location": org_unit.location,
                "status": org_unit.status,
                "created_at": org_unit.created_at.isoformat() if org_unit.created_at else None,
                "updated_at": org_unit.updated_at.isoformat() if org_unit.updated_at else None
            }
            
            # 先尝试根据UUID查找节点
            existing_node_id = await self.neo4j.find_node_by_uuid(
                str(org_unit.id),
                labels=["OrganizationUnit"]
            )
            
            if existing_node_id:
                # 更新现有节点
                node_id = await self.neo4j.update_node(
                    node_id=existing_node_id,
                    labels=["OrganizationUnit"],
                    properties=properties
                )
                if not org_unit.neo4j_node_id:
                    org_unit.neo4j_node_id = node_id
                    self.db.commit()
            else:
                # 创建新节点
                node_id = await self.neo4j.create_node(
                    labels=["OrganizationUnit"],
                    properties=properties
                )
                # 更新PostgreSQL中的neo4j_node_id
                org_unit.neo4j_node_id = node_id
                self.db.commit()
            
            # 同步父子关系
            if org_unit.parent_id:
                parent = self.db.query(OrganizationUnit).filter(
                    OrganizationUnit.id == org_unit.parent_id
                ).first()
                if parent and parent.neo4j_node_id:
                    await self.neo4j.create_relationship(
                        source_id=parent.neo4j_node_id,
                        target_id=node_id,
                        rel_type="PARENT_OF",
                        properties={}
                    )
            
            return node_id
        except Exception as e:
            logger.error(f"Error syncing organization unit to Neo4j: {str(e)}", exc_info=True)
            return None
    
    async def sync_business_role(self, role: BusinessRole) -> Optional[str]:
        """同步业务角色到Neo4j"""
        if not self.neo4j:
            return None
        
        try:
            properties = {
                "uuid": str(role.id),
                "name": role.name,
                "description": role.description,
                "role_type": role.role_type,
                "status": role.status
            }
            
            existing_node_id = await self.neo4j.find_node_by_uuid(
                str(role.id),
                labels=["BusinessRole"]
            )
            
            if existing_node_id:
                node_id = await self.neo4j.update_node(
                    node_id=existing_node_id,
                    labels=["BusinessRole"],
                    properties=properties
                )
                if not role.neo4j_node_id:
                    role.neo4j_node_id = node_id
                    self.db.commit()
            else:
                node_id = await self.neo4j.create_node(
                    labels=["BusinessRole"],
                    properties=properties
                )
                role.neo4j_node_id = node_id
                self.db.commit()
            
            # 同步组织关系
            if role.organization_id:
                org = self.db.query(OrganizationUnit).filter(
                    OrganizationUnit.id == role.organization_id
                ).first()
                if org and org.neo4j_node_id:
                    await self.neo4j.create_relationship(
                        source_id=org.neo4j_node_id,
                        target_id=node_id,
                        rel_type="HAS_ROLE",
                        properties={}
                    )
            
            return node_id
        except Exception as e:
            logger.error(f"Error syncing business role to Neo4j: {str(e)}", exc_info=True)
            return None
    
    # ========== 业务架构同步 ==========
    
    async def sync_business_process(self, process: BusinessProcess) -> Optional[str]:
        """同步业务流程到Neo4j"""
        if not self.neo4j:
            return None
        
        try:
            properties = {
                "uuid": str(process.id),
                "name": process.name,
                "description": process.description,
                "owner": process.owner,
                "status": process.status,
                "classification": process.classification,
                "level": process.level
            }
            
            existing_node_id = await self.neo4j.find_node_by_uuid(
                str(process.id),
                labels=["BusinessProcess"]
            )
            
            if existing_node_id:
                node_id = await self.neo4j.update_node(
                    node_id=existing_node_id,
                    labels=["BusinessProcess"],
                    properties=properties
                )
                if not process.neo4j_node_id:
                    process.neo4j_node_id = node_id
                    self.db.commit()
            else:
                node_id = await self.neo4j.create_node(
                    labels=["BusinessProcess"],
                    properties=properties
                )
                process.neo4j_node_id = node_id
                self.db.commit()
            
            # 同步组织关系
            if process.organization_id:
                org = self.db.query(OrganizationUnit).filter(
                    OrganizationUnit.id == process.organization_id
                ).first()
                if org and org.neo4j_node_id:
                    await self.neo4j.create_relationship(
                        source_id=org.neo4j_node_id,
                        target_id=node_id,
                        rel_type="OWNS",
                        properties={}
                    )
            
            # 同步父子关系
            if process.parent_id:
                parent = self.db.query(BusinessProcess).filter(
                    BusinessProcess.id == process.parent_id
                ).first()
                if parent and parent.neo4j_node_id:
                    await self.neo4j.create_relationship(
                        source_id=parent.neo4j_node_id,
                        target_id=node_id,
                        rel_type="PARENT_OF",
                        properties={}
                    )
            
            return node_id
        except Exception as e:
            logger.error(f"Error syncing business process to Neo4j: {str(e)}", exc_info=True)
            return None
    
    async def sync_business_capability(self, capability: BusinessCapability) -> Optional[str]:
        """同步业务能力到Neo4j"""
        if not self.neo4j:
            return None
        
        try:
            properties = {
                "uuid": str(capability.id),
                "name": capability.name,
                "description": capability.description,
                "level": capability.level
            }
            
            existing_node_id = await self.neo4j.find_node_by_uuid(
                str(capability.id),
                labels=["BusinessCapability"]
            )
            
            if existing_node_id:
                node_id = await self.neo4j.update_node(
                    node_id=existing_node_id,
                    labels=["BusinessCapability"],
                    properties=properties
                )
                if not capability.neo4j_node_id:
                    capability.neo4j_node_id = node_id
                    self.db.commit()
            else:
                node_id = await self.neo4j.create_node(
                    labels=["BusinessCapability"],
                    properties=properties
                )
                capability.neo4j_node_id = node_id
                self.db.commit()
            
            # 同步组织关系
            if capability.owner_organization_id:
                org = self.db.query(OrganizationUnit).filter(
                    OrganizationUnit.id == capability.owner_organization_id
                ).first()
                if org and org.neo4j_node_id:
                    await self.neo4j.create_relationship(
                        source_id=org.neo4j_node_id,
                        target_id=node_id,
                        rel_type="OWNS",
                        properties={}
                    )
            
            return node_id
        except Exception as e:
            logger.error(f"Error syncing business capability to Neo4j: {str(e)}", exc_info=True)
            return None
    
    # ========== 应用架构同步 ==========
    
    async def sync_application_system(self, system: ApplicationSystem) -> Optional[str]:
        """同步应用系统到Neo4j"""
        if not self.neo4j:
            return None
        
        try:
            properties = {
                "uuid": str(system.id),
                "name": system.name,
                "description": system.description,
                "system_type": system.system_type,
                "vendor": system.vendor,
                "version": system.version,
                "status": system.status,
                "system_category": system.system_category
            }
            
            existing_node_id = await self.neo4j.find_node_by_uuid(
                str(system.id),
                labels=["ApplicationSystem"]
            )
            
            if existing_node_id:
                node_id = await self.neo4j.update_node(
                    node_id=existing_node_id,
                    labels=["ApplicationSystem", system.system_category or "Custom"],
                    properties=properties
                )
                if not system.neo4j_node_id:
                    system.neo4j_node_id = node_id
                    self.db.commit()
            else:
                node_id = await self.neo4j.create_node(
                    labels=["ApplicationSystem", system.system_category or "Custom"],
                    properties=properties
                )
                system.neo4j_node_id = node_id
                self.db.commit()
            
            # 同步组织关系
            if system.business_owner_org_id:
                org = self.db.query(OrganizationUnit).filter(
                    OrganizationUnit.id == system.business_owner_org_id
                ).first()
                if org and org.neo4j_node_id:
                    await self.neo4j.create_relationship(
                        source_id=org.neo4j_node_id,
                        target_id=node_id,
                        rel_type="OWNS",
                        properties={}
                    )
            
            return node_id
        except Exception as e:
            logger.error(f"Error syncing application system to Neo4j: {str(e)}", exc_info=True)
            return None
    
    # ========== 技术架构同步 ==========
    
    async def sync_technology_instance(self, instance: TechnologyInstance) -> Optional[str]:
        """同步技术实例到Neo4j"""
        if not self.neo4j:
            return None
        
        try:
            properties = {
                "uuid": str(instance.id),
                "name": instance.name,
                "instance_id": instance.instance_id,
                "technology_type": instance.technology_type,
                "technology_name": instance.technology_name,
                "version": instance.version,
                "vendor": instance.vendor,
                "deployment_type": instance.deployment_type,
                "host": instance.host,
                "port": instance.port,
                "location": instance.location,
                "status": instance.status
            }
            
            existing_node_id = await self.neo4j.find_node_by_uuid(
                str(instance.id),
                labels=["TechnologyInstance"]
            )
            
            if existing_node_id:
                node_id = await self.neo4j.update_node(
                    node_id=existing_node_id,
                    labels=["TechnologyInstance", instance.technology_type],
                    properties=properties
                )
                if not instance.neo4j_node_id:
                    instance.neo4j_node_id = node_id
                    self.db.commit()
            else:
                node_id = await self.neo4j.create_node(
                    labels=["TechnologyInstance", instance.technology_type],
                    properties=properties
                )
                instance.neo4j_node_id = node_id
                self.db.commit()
            
            # 同步应用系统关系
            if instance.application_system_id:
                system = self.db.query(ApplicationSystem).filter(
                    ApplicationSystem.id == instance.application_system_id
                ).first()
                if system and system.neo4j_node_id:
                    await self.neo4j.create_relationship(
                        source_id=system.neo4j_node_id,
                        target_id=node_id,
                        rel_type="USES_TECHNOLOGY",
                        properties={
                            "usage_type": "primary" if instance.technology_type == "Database" else "supporting"
                        }
                    )
            
            # 同步技术类型关系
            if instance.technology_type_id:
                tech_type = self.db.query(TechnologyType).filter(
                    TechnologyType.id == instance.technology_type_id
                ).first()
                if tech_type and tech_type.neo4j_node_id:
                    await self.neo4j.create_relationship(
                        source_id=node_id,
                        target_id=tech_type.neo4j_node_id,
                        rel_type="INSTANCE_OF",
                        properties={}
                    )
            
            return node_id
        except Exception as e:
            logger.error(f"Error syncing technology instance to Neo4j: {str(e)}", exc_info=True)
            return None
    
    # ========== 批量同步 ==========
    
    async def sync_all_organizations(self) -> Dict[str, int]:
        """同步所有组织单元到Neo4j"""
        results = {"success": 0, "failed": 0}
        
        orgs = self.db.query(OrganizationUnit).all()
        for org in orgs:
            try:
                node_id = await self.sync_organization_unit(org)
                if node_id:
                    results["success"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                logger.error(f"Error syncing organization {org.id}: {str(e)}")
                results["failed"] += 1
        
        return results
    
    async def sync_all_business_processes(self) -> Dict[str, int]:
        """同步所有业务流程到Neo4j"""
        results = {"success": 0, "failed": 0}
        
        processes = self.db.query(BusinessProcess).all()
        for process in processes:
            try:
                node_id = await self.sync_business_process(process)
                if node_id:
                    results["success"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                logger.error(f"Error syncing business process {process.id}: {str(e)}")
                results["failed"] += 1
        
        return results
    
    async def sync_all_application_systems(self) -> Dict[str, int]:
        """同步所有应用系统到Neo4j"""
        results = {"success": 0, "failed": 0}
        
        systems = self.db.query(ApplicationSystem).all()
        for system in systems:
            try:
                node_id = await self.sync_application_system(system)
                if node_id:
                    results["success"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                logger.error(f"Error syncing application system {system.id}: {str(e)}")
                results["failed"] += 1
        
        return results
    
    async def sync_all_technology_instances(self) -> Dict[str, int]:
        """同步所有技术实例到Neo4j"""
        results = {"success": 0, "failed": 0}
        
        instances = self.db.query(TechnologyInstance).all()
        for instance in instances:
            try:
                node_id = await self.sync_technology_instance(instance)
                if node_id:
                    results["success"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                logger.error(f"Error syncing technology instance {instance.id}: {str(e)}")
                results["failed"] += 1
        
        return results
    
    async def sync_all_enterprise_architecture(self) -> Dict[str, Any]:
        """同步所有企业架构数据到Neo4j"""
        results = {
            "organizations": await self.sync_all_organizations(),
            "business_processes": await self.sync_all_business_processes(),
            "application_systems": await self.sync_all_application_systems(),
            "technology_instances": await self.sync_all_technology_instances()
        }
        
        total_success = sum(r["success"] for r in results.values())
        total_failed = sum(r["failed"] for r in results.values())
        
        results["summary"] = {
            "total_success": total_success,
            "total_failed": total_failed
        }
        
        return results


#!/usr/bin/env python3
"""
演示数据生成脚本
生成完整的演示数据以满足演示需求
"""

import os
import sys
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DemoDataGenerator:
    """演示数据生成器"""
    
    def __init__(self):
        """初始化"""
        self.pg_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USER', 'ai_user'),
            'password': os.getenv('DB_PASSWORD', 'ai_password'),
            'database': os.getenv('DB_NAME', 'ai_platform')
        }
        
        self.neo4j_config = {
            'uri': os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
            'user': os.getenv('NEO4j_USER', 'neo4j'),
            'password': os.getenv('NEO4J_PASSWORD', 'neo4j_password')
        }
        
        self.qdrant_config = {
            'url': os.getenv('QDRANT_URL', 'http://localhost:6333'),
            'api_key': os.getenv('QDRANT_API_KEY', None)
        }
    
    def generate_users(self, count: int = 5) -> List[str]:
        """生成演示用户"""
        logger.info(f"生成 {count} 个演示用户...")
        user_ids = []
        
        try:
            conn = psycopg2.connect(**self.pg_config)
            cursor = conn.cursor()
            
            users_data = [
                ('admin', 'admin@example.com', '管理员', 'active'),
                ('demo_user', 'demo_user@example.com', '演示用户', 'active'),
                ('developer', 'developer@example.com', '开发者', 'active'),
                ('analyst', 'analyst@example.com', '分析师', 'active'),
                ('manager', 'manager@example.com', '经理', 'active'),
            ]
            
            for username, email, display_name, status in users_data[:count]:
                user_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO users (id, username, email, password_hash, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT (username) DO UPDATE
                    SET email = EXCLUDED.email, status = EXCLUDED.status, updated_at = NOW()
                    RETURNING id
                """, (user_id, username, email, 'demo_hash', status))
                
                result = cursor.fetchone()
                if result:
                    user_ids.append(str(result[0]))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"成功生成 {len(user_ids)} 个用户")
            return user_ids
            
        except Exception as e:
            logger.error(f"生成用户失败: {e}", exc_info=True)
            return []
    
    def generate_roles_and_permissions(self) -> Dict[str, List[str]]:
        """生成角色和权限"""
        logger.info("生成角色和权限...")
        
        try:
            conn = psycopg2.connect(**self.pg_config)
            cursor = conn.cursor()
            
            # 创建角色
            roles = [
                ('admin', '管理员', '系统管理员角色'),
                ('user', '普通用户', '普通用户角色'),
                ('developer', '开发者', '开发者角色'),
                ('viewer', '查看者', '只读用户角色'),
            ]
            
            role_ids = {}
            for name, display_name, description in roles:
                role_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO roles (id, name, display_name, description, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT (name) DO UPDATE
                    SET display_name = EXCLUDED.display_name, description = EXCLUDED.description
                    RETURNING id
                """, (role_id, name, display_name, description))
                
                result = cursor.fetchone()
                if result:
                    role_ids[name] = str(result[0])
            
            # 创建权限
            permissions = [
                ('read', '读取', '读取权限'),
                ('write', '写入', '写入权限'),
                ('delete', '删除', '删除权限'),
                ('admin', '管理', '管理权限'),
            ]
            
            permission_ids = {}
            for name, display_name, description in permissions:
                perm_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO permissions (id, name, display_name, description, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT (name) DO UPDATE
                    SET display_name = EXCLUDED.display_name, description = EXCLUDED.description
                    RETURNING id
                """, (perm_id, name, display_name, description))
                
                result = cursor.fetchone()
                if result:
                    permission_ids[name] = str(result[0])
            
            # 关联角色和权限
            role_permissions = {
                'admin': ['read', 'write', 'delete', 'admin'],
                'user': ['read', 'write'],
                'developer': ['read', 'write'],
                'viewer': ['read'],
            }
            
            for role_name, perm_names in role_permissions.items():
                if role_name in role_ids:
                    role_id = role_ids[role_name]
                    for perm_name in perm_names:
                        if perm_name in permission_ids:
                            perm_id = permission_ids[perm_name]
                            cursor.execute("""
                                INSERT INTO role_permissions (role_id, permission_id, created_at)
                                VALUES (%s, %s, NOW())
                                ON CONFLICT DO NOTHING
                            """, (role_id, perm_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("成功生成角色和权限")
            return {'roles': role_ids, 'permissions': permission_ids}
            
        except Exception as e:
            logger.error(f"生成角色和权限失败: {e}", exc_info=True)
            return {}
    
    def generate_workflows(self, count: int = 3) -> List[str]:
        """生成演示工作流"""
        logger.info(f"生成 {count} 个演示工作流...")
        workflow_ids = []
        
        try:
            conn = psycopg2.connect(**self.pg_config)
            cursor = conn.cursor()
            
            workflows = [
                ('数据提取工作流', '从多个数据源提取数据并处理', 'active'),
                ('文档分析工作流', '分析文档内容并生成摘要', 'active'),
                ('知识图谱构建工作流', '构建企业知识图谱', 'active'),
            ]
            
            for name, description, status in workflows[:count]:
                workflow_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO workflow_definitions (id, name, description, version, status, config, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT (name) DO UPDATE
                    SET description = EXCLUDED.description, status = EXCLUDED.status, updated_at = NOW()
                    RETURNING id
                """, (workflow_id, name, description, '1.0.0', status, '{}'))
                
                result = cursor.fetchone()
                if result:
                    workflow_ids.append(str(result[0]))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"成功生成 {len(workflow_ids)} 个工作流")
            return workflow_ids
            
        except Exception as e:
            logger.error(f"生成工作流失败: {e}", exc_info=True)
            return []
    
    def generate_knowledge_bases(self, count: int = 3) -> List[str]:
        """生成演示知识库"""
        logger.info(f"生成 {count} 个演示知识库...")
        kb_ids = []
        
        try:
            conn = psycopg2.connect(**self.pg_config)
            cursor = conn.cursor()
            
            knowledge_bases = [
                ('企业架构知识库', '存储企业架构相关文档', 'active'),
                ('技术文档知识库', '存储技术文档和API文档', 'active'),
                ('业务知识库', '存储业务规则和流程文档', 'active'),
            ]
            
            for name, description, status in knowledge_bases[:count]:
                kb_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO knowledge_bases (id, name, description, status, embedding_model, chunk_strategy, chunk_size, chunk_overlap, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT DO NOTHING
                    RETURNING id
                """, (kb_id, name, description, status, 'text-embedding-ada-002', 'sentence', 1000, 200))
                
                result = cursor.fetchone()
                if result:
                    kb_ids.append(str(result[0]))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"成功生成 {len(kb_ids)} 个知识库")
            return kb_ids
            
        except Exception as e:
            logger.error(f"生成知识库失败: {e}", exc_info=True)
            return []
    
    def generate_documents(self, kb_ids: List[str], count_per_kb: int = 3) -> List[str]:
        """生成演示文档"""
        logger.info(f"为每个知识库生成 {count_per_kb} 个文档...")
        doc_ids = []
        
        try:
            conn = psycopg2.connect(**self.pg_config)
            cursor = conn.cursor()
            
            doc_templates = [
                ('企业架构设计文档', 'pdf', '企业架构设计相关文档'),
                ('技术规范文档', 'pdf', '技术规范和标准文档'),
                ('业务流程文档', 'word', '业务流程和规则文档'),
            ]
            
            for kb_id in kb_ids:
                for i, (name, file_type, description) in enumerate(doc_templates[:count_per_kb]):
                    doc_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO documents (id, knowledge_base_id, filename, file_type, status, description, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                        RETURNING id
                    """, (doc_id, kb_id, f"{name}_{i+1}.{file_type}", file_type, 'processed', description))
                    
                    result = cursor.fetchone()
                    if result:
                        doc_ids.append(str(result[0]))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"成功生成 {len(doc_ids)} 个文档")
            return doc_ids
            
        except Exception as e:
            logger.error(f"生成文档失败: {e}", exc_info=True)
            return []
    
    def generate_neo4j_data(self, node_count: int = 20, relationship_count: int = 30):
        """生成Neo4j演示数据"""
        logger.info(f"生成Neo4j数据: {node_count} 个节点, {relationship_count} 个关系...")
        
        try:
            driver = GraphDatabase.driver(
                self.neo4j_config['uri'],
                auth=(self.neo4j_config['user'], self.neo4j_config['password'])
            )
            
            with driver.session() as session:
                # 创建组织架构节点
                org_nodes = [
                    ('公司', 'Organization', {'name': '示例公司', 'type': 'company'}),
                    ('部门A', 'Department', {'name': '技术部', 'type': 'department'}),
                    ('部门B', 'Department', {'name': '业务部', 'type': 'department'}),
                    ('团队1', 'Team', {'name': '开发团队', 'type': 'team'}),
                    ('团队2', 'Team', {'name': '测试团队', 'type': 'team'}),
                ]
                
                node_ids = []
                for name, label, props in org_nodes:
                    result = session.run(f"""
                        CREATE (n:{label} $props)
                        RETURN id(n) as id
                    """, props={**props, 'created_at': datetime.now().isoformat()})
                    
                    record = result.single()
                    if record:
                        node_ids.append(record['id'])
                
                # 创建业务架构节点
                business_nodes = [
                    ('业务流程1', 'BusinessProcess', {'name': '订单处理流程', 'type': 'process'}),
                    ('业务流程2', 'BusinessProcess', {'name': '客户服务流程', 'type': 'process'}),
                    ('业务能力1', 'BusinessCapability', {'name': '订单管理', 'type': 'capability'}),
                    ('业务能力2', 'BusinessCapability', {'name': '客户管理', 'type': 'capability'}),
                ]
                
                for name, label, props in business_nodes:
                    result = session.run(f"""
                        CREATE (n:{label} $props)
                        RETURN id(n) as id
                    """, props={**props, 'created_at': datetime.now().isoformat()})
                    
                    record = result.single()
                    if record:
                        node_ids.append(record['id'])
                
                # 创建应用架构节点
                app_nodes = [
                    ('应用系统1', 'ApplicationSystem', {'name': '订单管理系统', 'type': 'application'}),
                    ('应用系统2', 'ApplicationSystem', {'name': '客户关系管理系统', 'type': 'application'}),
                    ('数据实体1', 'DataEntity', {'name': '订单', 'type': 'entity'}),
                    ('数据实体2', 'DataEntity', {'name': '客户', 'type': 'entity'}),
                ]
                
                for name, label, props in app_nodes:
                    result = session.run(f"""
                        CREATE (n:{label} $props)
                        RETURN id(n) as id
                    """, props={**props, 'created_at': datetime.now().isoformat()})
                    
                    record = result.single()
                    if record:
                        node_ids.append(record['id'])
                
                # 创建关系
                relationships = [
                    ('BELONGS_TO', '部门A', '公司'),
                    ('BELONGS_TO', '部门B', '公司'),
                    ('HAS_TEAM', '部门A', '团队1'),
                    ('HAS_TEAM', '部门A', '团队2'),
                    ('SUPPORTS', '应用系统1', '业务流程1'),
                    ('USES', '业务流程1', '业务能力1'),
                    ('STORES', '应用系统1', '数据实体1'),
                ]
                
                for rel_type, from_name, to_name in relationships[:relationship_count]:
                    session.run(f"""
                        MATCH (a), (b)
                        WHERE a.name = $from_name AND b.name = $to_name
                        CREATE (a)-[r:{rel_type} {{created_at: $created_at}}]->(b)
                    """, from_name=from_name, to_name=to_name, created_at=datetime.now().isoformat())
                
            driver.close()
            
            logger.info(f"成功生成Neo4j数据")
            
        except Exception as e:
            logger.error(f"生成Neo4j数据失败: {e}", exc_info=True)
    
    def generate_qdrant_data(self):
        """生成Qdrant演示数据"""
        logger.info("生成Qdrant演示数据...")
        
        try:
            client = QdrantClient(
                url=self.qdrant_config['url'],
                api_key=self.qdrant_config['api_key']
            )
            
            # 创建演示集合（如果不存在）
            collection_name = 'demo_vectors'
            vector_size = 1536  # OpenAI embedding size
            
            try:
                client.get_collection(collection_name)
                logger.info(f"集合 {collection_name} 已存在")
            except:
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"创建集合 {collection_name}")
            
            # 生成一些演示向量
            points = []
            for i in range(10):
                vector = np.random.rand(vector_size).tolist()
                points.append(
                    PointStruct(
                        id=i,
                        vector=vector,
                        payload={
                            'text': f'演示文档 {i+1}',
                            'type': 'demo',
                            'created_at': datetime.now().isoformat()
                        }
                    )
                )
            
            client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            logger.info(f"成功生成 {len(points)} 个向量到Qdrant")
            
        except Exception as e:
            logger.error(f"生成Qdrant数据失败: {e}", exc_info=True)
    
    def run(self):
        """运行完整的数据生成流程"""
        logger.info("=" * 60)
        logger.info("开始生成演示数据")
        logger.info("=" * 60)
        
        # 生成用户
        user_ids = self.generate_users(5)
        
        # 生成角色和权限
        roles_perms = self.generate_roles_and_permissions()
        
        # 生成工作流
        workflow_ids = self.generate_workflows(3)
        
        # 生成知识库
        kb_ids = self.generate_knowledge_bases(3)
        
        # 生成文档
        doc_ids = self.generate_documents(kb_ids, 3)
        
        # 生成Neo4j数据
        self.generate_neo4j_data(20, 30)
        
        # 生成Qdrant数据
        self.generate_qdrant_data()
        
        logger.info("=" * 60)
        logger.info("演示数据生成完成")
        logger.info("=" * 60)
        
        return {
            'users': len(user_ids),
            'workflows': len(workflow_ids),
            'knowledge_bases': len(kb_ids),
            'documents': len(doc_ids),
        }


if __name__ == '__main__':
    generator = DemoDataGenerator()
    results = generator.run()
    print(f"\n演示数据生成完成！\n生成结果: {results}")


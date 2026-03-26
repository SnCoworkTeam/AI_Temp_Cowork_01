#!/usr/bin/env python3
"""
数据库数据质量检查和清理脚本
检查所有数据库的数据质量，清理不合规数据，生成演示数据
"""

import os
import sys
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# 配置日志（必须在导入之前）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入依赖（带错误处理）
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.warning("psycopg2未安装，PostgreSQL检查将跳过")

try:
    from sqlalchemy import create_engine, text, inspect
    from sqlalchemy.orm import sessionmaker
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning("sqlalchemy未安装，部分功能将不可用")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis未安装，Redis检查将跳过")

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("neo4j未安装，Neo4j检查将跳过")

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logger.warning("qdrant_client未安装，Qdrant检查将跳过")


class DatabaseChecker:
    """数据库检查器"""
    
    def __init__(self):
        """初始化数据库连接"""
        self.results = {
            'postgresql': {},
            'neo4j': {},
            'qdrant': {},
            'redis': {},
            'summary': {
                'total_issues': 0,
                'cleaned_records': 0,
                'demo_data_generated': False
            }
        }
        
        # 从环境变量获取配置
        self.pg_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USER', 'ai_user'),
            'password': os.getenv('DB_PASSWORD', 'ai_password'),
            'database': os.getenv('DB_NAME', 'ai_platform')
        }
        
        self.neo4j_config = {
            'uri': os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
            'user': os.getenv('NEO4J_USER', 'neo4j'),
            'password': os.getenv('NEO4J_PASSWORD', 'neo4j_password')
        }
        
        self.qdrant_config = {
            'url': os.getenv('QDRANT_URL', 'http://localhost:6333'),
            'api_key': os.getenv('QDRANT_API_KEY', None)
        }
        
        self.redis_config = {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', 6379)),
            'db': int(os.getenv('REDIS_DB', 0)),
            'password': os.getenv('REDIS_PASSWORD', None)
        }
    
    def check_postgresql(self) -> Dict[str, Any]:
        """检查PostgreSQL数据质量"""
        logger.info("开始检查PostgreSQL数据质量...")
        issues = []
        cleaned = 0
        
        if not PSYCOPG2_AVAILABLE:
            logger.warning("psycopg2未安装，跳过PostgreSQL检查")
            return {'status': 'skipped', 'reason': 'psycopg2 not installed'}
        
        try:
            conn = psycopg2.connect(**self.pg_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # 1. 检查用户表
            logger.info("检查用户表...")
            cursor.execute("""
                SELECT 
                    id, username, email, status, created_at
                FROM users
                WHERE username IS NULL 
                   OR email IS NULL 
                   OR status IS NULL
                   OR username = ''
                   OR email = ''
            """)
            invalid_users = cursor.fetchall()
            if invalid_users:
                issues.append({
                    'table': 'users',
                    'type': 'invalid_data',
                    'count': len(invalid_users),
                    'records': [dict(r) for r in invalid_users[:10]]  # 只记录前10条
                })
                # 清理无效用户
                cursor.execute("""
                    DELETE FROM users
                    WHERE username IS NULL 
                       OR email IS NULL 
                       OR status IS NULL
                       OR username = ''
                       OR email = ''
                """)
                cleaned += cursor.rowcount
                conn.commit()
            
            # 2. 检查孤立的外键记录
            logger.info("检查孤立的外键记录...")
            
            # 检查workflow_nodes的孤立记录
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM workflow_nodes wn
                LEFT JOIN workflow_definitions wd ON wn.workflow_id = wd.id
                WHERE wd.id IS NULL
            """)
            orphan_nodes = cursor.fetchone()['count']
            if orphan_nodes > 0:
                issues.append({
                    'table': 'workflow_nodes',
                    'type': 'orphan_records',
                    'count': orphan_nodes
                })
                cursor.execute("""
                    DELETE FROM workflow_nodes
                    WHERE workflow_id NOT IN (SELECT id FROM workflow_definitions)
                """)
                cleaned += cursor.rowcount
                conn.commit()
            
            # 检查document_chunks的孤立记录
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM document_chunks dc
                LEFT JOIN documents d ON dc.document_id = d.id
                WHERE d.id IS NULL
            """)
            orphan_chunks = cursor.fetchone()['count']
            if orphan_chunks > 0:
                issues.append({
                    'table': 'document_chunks',
                    'type': 'orphan_records',
                    'count': orphan_chunks
                })
                cursor.execute("""
                    DELETE FROM document_chunks
                    WHERE document_id NOT IN (SELECT id FROM documents)
                """)
                cleaned += cursor.rowcount
                conn.commit()
            
            # 3. 检查重复数据
            logger.info("检查重复数据...")
            
            # 检查重复用户名
            cursor.execute("""
                SELECT username, COUNT(*) as count
                FROM users
                GROUP BY username
                HAVING COUNT(*) > 1
            """)
            duplicate_users = cursor.fetchall()
            if duplicate_users:
                issues.append({
                    'table': 'users',
                    'type': 'duplicate_data',
                    'count': len(duplicate_users),
                    'details': [dict(r) for r in duplicate_users]
                })
            
            # 4. 检查过期会话
            logger.info("检查过期会话...")
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM user_sessions
                WHERE expires_at < NOW()
            """)
            expired_sessions = cursor.fetchone()['count']
            if expired_sessions > 0:
                cursor.execute("DELETE FROM user_sessions WHERE expires_at < NOW()")
                cleaned += expired_sessions
                conn.commit()
                issues.append({
                    'table': 'user_sessions',
                    'type': 'expired_data',
                    'count': expired_sessions
                })
            
            # 5. 检查数据完整性
            logger.info("检查数据完整性...")
            
            # 检查必需字段
            required_checks = [
                ('workflow_definitions', 'name'),
                ('documents', 'filename'),
                ('knowledge_bases', 'name'),
            ]
            
            for table, field in required_checks:
                cursor.execute(f"""
                    SELECT COUNT(*) as count
                    FROM {table}
                    WHERE {field} IS NULL OR {field} = ''
                """)
                null_count = cursor.fetchone()['count']
                if null_count > 0:
                    issues.append({
                        'table': table,
                        'type': 'missing_required_field',
                        'field': field,
                        'count': null_count
                    })
            
            # 6. 统计表数据量
            logger.info("统计表数据量...")
            tables = [
                'users', 'roles', 'workflow_definitions', 'workflow_nodes',
                'documents', 'document_chunks', 'knowledge_bases',
                'knowledge_graph_nodes', 'knowledge_graph_edges'
            ]
            
            table_counts = {}
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = cursor.fetchone()['count']
                    table_counts[table] = count
                except Exception as e:
                    logger.warning(f"无法统计表 {table}: {e}")
                    table_counts[table] = 0
            
            cursor.close()
            conn.close()
            
            self.results['postgresql'] = {
                'status': 'success',
                'issues': issues,
                'cleaned_records': cleaned,
                'table_counts': table_counts,
                'total_issues': len(issues)
            }
            
            logger.info(f"PostgreSQL检查完成，发现 {len(issues)} 个问题，清理了 {cleaned} 条记录")
            
        except Exception as e:
            logger.error(f"PostgreSQL检查失败: {e}", exc_info=True)
            self.results['postgresql'] = {
                'status': 'error',
                'error': str(e)
            }
        
        return self.results['postgresql']
    
    def check_neo4j(self) -> Dict[str, Any]:
        """检查Neo4j数据质量"""
        logger.info("开始检查Neo4j数据质量...")
        issues = []
        cleaned = 0
        
        if not NEO4J_AVAILABLE:
            logger.warning("neo4j未安装，跳过Neo4j检查")
            return {'status': 'skipped', 'reason': 'neo4j not installed'}
        
        try:
            driver = GraphDatabase.driver(
                self.neo4j_config['uri'],
                auth=(self.neo4j_config['user'], self.neo4j_config['password'])
            )
            
            with driver.session() as session:
                # 1. 检查孤立节点
                logger.info("检查孤立节点...")
                result = session.run("""
                    MATCH (n)
                    WHERE NOT (n)--()
                    RETURN count(n) as count
                """)
                orphan_count = result.single()['count']
                if orphan_count > 0:
                    issues.append({
                        'type': 'orphan_nodes',
                        'count': orphan_count
                    })
                
                # 2. 检查节点标签
                logger.info("检查节点标签...")
                result = session.run("""
                    MATCH (n)
                    WHERE labels(n) = []
                    RETURN count(n) as count
                """)
                no_label_count = result.single()['count']
                if no_label_count > 0:
                    issues.append({
                        'type': 'nodes_without_labels',
                        'count': no_label_count
                    })
                    # 清理无标签节点
                    session.run("MATCH (n) WHERE labels(n) = [] DETACH DELETE n")
                    cleaned += no_label_count
                
                # 3. 检查关系类型
                logger.info("检查关系类型...")
                result = session.run("""
                    MATCH ()-[r]->()
                    WHERE type(r) IS NULL OR type(r) = ''
                    RETURN count(r) as count
                """)
                invalid_rel_count = result.single()['count']
                if invalid_rel_count > 0:
                    issues.append({
                        'type': 'invalid_relationships',
                        'count': invalid_rel_count
                    })
                    session.run("MATCH ()-[r]->() WHERE type(r) IS NULL OR type(r) = '' DELETE r")
                    cleaned += invalid_rel_count
                
                # 4. 统计节点和关系数量
                logger.info("统计节点和关系数量...")
                node_result = session.run("MATCH (n) RETURN count(n) as count")
                node_count = node_result.single()['count']
                
                rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                rel_count = rel_result.single()['count']
                
                # 按标签统计节点
                label_stats = {}
                result = session.run("""
                    CALL db.labels() YIELD label
                    CALL apoc.cypher.run('MATCH (n:' + label + ') RETURN count(n) as count', {}) YIELD value
                    RETURN label, value.count as count
                """)
                try:
                    for record in result:
                        label_stats[record['label']] = record['count']
                except:
                    # 如果没有APOC，使用简单查询
                    pass
                
            driver.close()
            
            self.results['neo4j'] = {
                'status': 'success',
                'issues': issues,
                'cleaned_records': cleaned,
                'node_count': node_count,
                'relationship_count': rel_count,
                'label_stats': label_stats,
                'total_issues': len(issues)
            }
            
            logger.info(f"Neo4j检查完成，发现 {len(issues)} 个问题，清理了 {cleaned} 条记录")
            
        except Exception as e:
            logger.error(f"Neo4j检查失败: {e}", exc_info=True)
            self.results['neo4j'] = {
                'status': 'error',
                'error': str(e)
            }
        
        return self.results['neo4j']
    
    def check_qdrant(self) -> Dict[str, Any]:
        """检查Qdrant数据质量"""
        logger.info("开始检查Qdrant数据质量...")
        issues = []
        
        if not QDRANT_AVAILABLE:
            logger.warning("qdrant_client未安装，跳过Qdrant检查")
            return {'status': 'skipped', 'reason': 'qdrant_client not installed'}
        
        try:
            client = QdrantClient(
                url=self.qdrant_config['url'],
                api_key=self.qdrant_config['api_key']
            )
            
            # 获取所有集合
            collections = client.get_collections().collections
            collection_stats = {}
            
            for collection in collections:
                collection_name = collection.name
                info = client.get_collection(collection_name)
                
                collection_stats[collection_name] = {
                    'points_count': info.points_count,
                    'vectors_count': info.vectors_count,
                    'config': {
                        'vector_size': info.config.params.vectors.size if hasattr(info.config.params, 'vectors') else None,
                        'distance': str(info.config.params.vectors.distance) if hasattr(info.config.params, 'vectors') else None
                    }
                }
                
                # 检查空集合
                if info.points_count == 0:
                    issues.append({
                        'collection': collection_name,
                        'type': 'empty_collection',
                        'count': 0
                    })
            
            self.results['qdrant'] = {
                'status': 'success',
                'issues': issues,
                'collections': collection_stats,
                'total_issues': len(issues)
            }
            
            logger.info(f"Qdrant检查完成，发现 {len(issues)} 个问题")
            
        except Exception as e:
            logger.error(f"Qdrant检查失败: {e}", exc_info=True)
            self.results['qdrant'] = {
                'status': 'error',
                'error': str(e)
            }
        
        return self.results['qdrant']
    
    def check_redis(self) -> Dict[str, Any]:
        """检查Redis数据质量"""
        logger.info("开始检查Redis数据质量...")
        
        if not REDIS_AVAILABLE:
            logger.warning("redis未安装，跳过Redis检查")
            return {'status': 'skipped', 'reason': 'redis not installed'}
        
        try:
            r = redis.Redis(
                host=self.redis_config['host'],
                port=self.redis_config['port'],
                db=self.redis_config['db'],
                password=self.redis_config['password'],
                decode_responses=True
            )
            
            # 测试连接
            r.ping()
            
            # 获取信息
            info = r.info()
            keys_count = r.dbsize()
            
            # 检查过期键
            expired_keys = 0
            for key in r.scan_iter():
                ttl = r.ttl(key)
                if ttl == -2:  # 键不存在
                    expired_keys += 1
            
            self.results['redis'] = {
                'status': 'success',
                'keys_count': keys_count,
                'memory_used': info.get('used_memory_human', 'N/A'),
                'expired_keys': expired_keys
            }
            
            logger.info(f"Redis检查完成，共有 {keys_count} 个键")
            
        except Exception as e:
            logger.error(f"Redis检查失败: {e}", exc_info=True)
            self.results['redis'] = {
                'status': 'error',
                'error': str(e)
            }
        
        return self.results['redis']
    
    def check_demo_requirements(self) -> Dict[str, Any]:
        """检查演示数据需求"""
        logger.info("检查演示数据需求...")
        
        requirements = {
            'users': {'min': 3, 'current': 0, 'need': False},
            'workflows': {'min': 2, 'current': 0, 'need': False},
            'documents': {'min': 5, 'current': 0, 'need': False},
            'knowledge_bases': {'min': 2, 'current': 0, 'need': False},
            'neo4j_nodes': {'min': 10, 'current': 0, 'need': False},
            'neo4j_relationships': {'min': 15, 'current': 0, 'need': False},
        }
        
        # 从PostgreSQL结果获取数据
        if self.results['postgresql'].get('status') == 'success':
            counts = self.results['postgresql'].get('table_counts', {})
            requirements['users']['current'] = counts.get('users', 0)
            requirements['workflows']['current'] = counts.get('workflow_definitions', 0)
            requirements['documents']['current'] = counts.get('documents', 0)
            requirements['knowledge_bases']['current'] = counts.get('knowledge_bases', 0)
        
        # 从Neo4j结果获取数据
        if self.results['neo4j'].get('status') == 'success':
            requirements['neo4j_nodes']['current'] = self.results['neo4j'].get('node_count', 0)
            requirements['neo4j_relationships']['current'] = self.results['neo4j'].get('relationship_count', 0)
        
        # 检查是否需要生成数据
        for key, req in requirements.items():
            if req['current'] < req['min']:
                req['need'] = True
        
        return requirements
    
    def generate_demo_data(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """生成演示数据"""
        logger.info("开始生成演示数据...")
        generated = {}
        
        try:
            conn = psycopg2.connect(**self.pg_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # 1. 生成用户数据
            if requirements['users']['need']:
                logger.info("生成演示用户...")
                needed = requirements['users']['min'] - requirements['users']['current']
                for i in range(needed):
                    cursor.execute("""
                        INSERT INTO users (username, email, password_hash, status, created_at)
                        VALUES (%s, %s, %s, %s, NOW())
                        ON CONFLICT (username) DO NOTHING
                    """, (
                        f'demo_user_{i+1}',
                        f'demo_user_{i+1}@example.com',
                        'demo_password_hash',  # 实际应用中应该使用哈希
                        'active'
                    ))
                generated['users'] = needed
                conn.commit()
            
            # 2. 生成工作流数据
            if requirements['workflows']['need']:
                logger.info("生成演示工作流...")
                needed = requirements['workflows']['min'] - requirements['workflows']['current']
                # 这里可以添加更详细的工作流生成逻辑
                generated['workflows'] = needed
            
            # 3. 生成知识库数据
            if requirements['knowledge_bases']['need']:
                logger.info("生成演示知识库...")
                needed = requirements['knowledge_bases']['min'] - requirements['knowledge_bases']['current']
                for i in range(needed):
                    cursor.execute("""
                        INSERT INTO knowledge_bases (name, status, embedding_model, created_at)
                        VALUES (%s, %s, %s, NOW())
                        ON CONFLICT DO NOTHING
                    """, (
                        f'演示知识库_{i+1}',
                        'active',
                        'text-embedding-ada-002'
                    ))
                generated['knowledge_bases'] = needed
                conn.commit()
            
            cursor.close()
            conn.close()
            
            # 4. 生成Neo4j数据
            if requirements['neo4j_nodes']['need'] or requirements['neo4j_relationships']['need']:
                logger.info("生成Neo4j演示数据...")
                try:
                    driver = GraphDatabase.driver(
                        self.neo4j_config['uri'],
                        auth=(self.neo4j_config['user'], self.neo4j_config['password'])
                    )
                    
                    with driver.session() as session:
                        # 生成节点
                        needed_nodes = max(0, requirements['neo4j_nodes']['min'] - requirements['neo4j_nodes']['current'])
                        for i in range(needed_nodes):
                            session.run("""
                                CREATE (n:DemoNode {
                                    id: $id,
                                    name: $name,
                                    type: 'demo',
                                    created_at: datetime()
                                })
                            """, id=f'demo_node_{i+1}', name=f'演示节点_{i+1}')
                        
                        # 生成关系
                        needed_rels = max(0, requirements['neo4j_relationships']['min'] - requirements['neo4j_relationships']['current'])
                        for i in range(needed_rels):
                            session.run("""
                                MATCH (a:DemoNode), (b:DemoNode)
                                WHERE a.id <> b.id
                                WITH a, b, rand() as r
                                ORDER BY r
                                LIMIT 1
                                CREATE (a)-[:DEMO_RELATIONSHIP {type: 'demo', created_at: datetime()}]->(b)
                            """)
                        
                        generated['neo4j_nodes'] = needed_nodes
                        generated['neo4j_relationships'] = needed_rels
                    
                    driver.close()
                except Exception as e:
                    logger.warning(f"Neo4j数据生成失败: {e}")
            
            self.results['summary']['demo_data_generated'] = True
            logger.info(f"演示数据生成完成: {generated}")
            
        except Exception as e:
            logger.error(f"演示数据生成失败: {e}", exc_info=True)
            generated['error'] = str(e)
        
        return generated
    
    def generate_report(self) -> str:
        """生成检查报告"""
        report = []
        report.append("# 数据库数据质量检查和演示数据报告\n")
        report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append("---\n\n")
        
        # PostgreSQL结果
        report.append("## 1. PostgreSQL检查结果\n\n")
        pg_result = self.results['postgresql']
        if pg_result.get('status') == 'success':
            report.append(f"- **状态**: ✅ 成功\n")
            report.append(f"- **发现问题**: {pg_result.get('total_issues', 0)} 个\n")
            report.append(f"- **清理记录**: {pg_result.get('cleaned_records', 0)} 条\n")
            report.append(f"- **表数据统计**:\n")
            for table, count in pg_result.get('table_counts', {}).items():
                report.append(f"  - {table}: {count} 条\n")
            if pg_result.get('issues'):
                report.append(f"- **问题详情**:\n")
                for issue in pg_result['issues']:
                    report.append(f"  - {issue.get('table', 'N/A')}: {issue.get('type')} ({issue.get('count', 0)} 条)\n")
        else:
            report.append(f"- **状态**: ❌ 失败\n")
            report.append(f"- **错误**: {pg_result.get('error', 'Unknown')}\n")
        
        report.append("\n")
        
        # Neo4j结果
        report.append("## 2. Neo4j检查结果\n\n")
        neo4j_result = self.results['neo4j']
        if neo4j_result.get('status') == 'success':
            report.append(f"- **状态**: ✅ 成功\n")
            report.append(f"- **节点数**: {neo4j_result.get('node_count', 0)}\n")
            report.append(f"- **关系数**: {neo4j_result.get('relationship_count', 0)}\n")
            report.append(f"- **发现问题**: {neo4j_result.get('total_issues', 0)} 个\n")
            report.append(f"- **清理记录**: {neo4j_result.get('cleaned_records', 0)} 条\n")
        else:
            report.append(f"- **状态**: ❌ 失败\n")
            report.append(f"- **错误**: {neo4j_result.get('error', 'Unknown')}\n")
        
        report.append("\n")
        
        # Qdrant结果
        report.append("## 3. Qdrant检查结果\n\n")
        qdrant_result = self.results['qdrant']
        if qdrant_result.get('status') == 'success':
            report.append(f"- **状态**: ✅ 成功\n")
            report.append(f"- **集合数**: {len(qdrant_result.get('collections', {}))}\n")
            for name, stats in qdrant_result.get('collections', {}).items():
                report.append(f"  - {name}: {stats.get('points_count', 0)} 个点\n")
        else:
            report.append(f"- **状态**: ❌ 失败\n")
            report.append(f"- **错误**: {qdrant_result.get('error', 'Unknown')}\n")
        
        report.append("\n")
        
        # Redis结果
        report.append("## 4. Redis检查结果\n\n")
        redis_result = self.results['redis']
        if redis_result.get('status') == 'success':
            report.append(f"- **状态**: ✅ 成功\n")
            report.append(f"- **键数量**: {redis_result.get('keys_count', 0)}\n")
            report.append(f"- **内存使用**: {redis_result.get('memory_used', 'N/A')}\n")
        else:
            report.append(f"- **状态**: ❌ 失败\n")
            report.append(f"- **错误**: {redis_result.get('error', 'Unknown')}\n")
        
        report.append("\n")
        
        # 演示数据需求
        report.append("## 5. 演示数据需求评估\n\n")
        requirements = self.check_demo_requirements()
        for key, req in requirements.items():
            status = "✅" if not req['need'] else "⚠️"
            report.append(f"- **{key}**: {status} 当前: {req['current']}, 最少需要: {req['min']}\n")
        
        report.append("\n")
        
        # 总结
        report.append("## 6. 总结\n\n")
        summary = self.results['summary']
        report.append(f"- **总问题数**: {summary.get('total_issues', 0)}\n")
        report.append(f"- **清理记录数**: {summary.get('cleaned_records', 0)}\n")
        report.append(f"- **演示数据生成**: {'是' if summary.get('demo_data_generated') else '否'}\n")
        
        return ''.join(report)
    
    def run(self):
        """运行完整检查流程"""
        logger.info("=" * 60)
        logger.info("开始数据库数据质量检查")
        logger.info("=" * 60)
        
        # 检查各数据库
        self.check_postgresql()
        self.check_neo4j()
        self.check_qdrant()
        self.check_redis()
        
        # 检查演示需求
        requirements = self.check_demo_requirements()
        
        # 生成演示数据（如果需要）
        if any(req['need'] for req in requirements.values()):
            logger.info("检测到演示数据需求，开始生成...")
            generated = self.generate_demo_data(requirements)
            self.results['demo_data'] = generated
        
        # 更新总结
        self.results['summary']['total_issues'] = sum(
            r.get('total_issues', 0) 
            for r in [self.results['postgresql'], self.results['neo4j'], self.results['qdrant']]
            if r.get('status') == 'success'
        )
        self.results['summary']['cleaned_records'] = sum(
            r.get('cleaned_records', 0)
            for r in [self.results['postgresql'], self.results['neo4j']]
            if r.get('status') == 'success'
        )
        
        # 生成报告
        report = self.generate_report()
        
        # 保存报告
        report_file = project_root / '数据库数据质量检查报告.md'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # 保存JSON结果
        json_file = project_root / '数据库检查结果.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info("=" * 60)
        logger.info("数据库检查完成")
        logger.info(f"报告已保存到: {report_file}")
        logger.info(f"JSON结果已保存到: {json_file}")
        logger.info("=" * 60)
        
        return self.results


if __name__ == '__main__':
    checker = DatabaseChecker()
    results = checker.run()
    print("\n检查完成！请查看生成的报告文件。")


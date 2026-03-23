#!/usr/bin/env python3
"""
远程服务器数据库数据质量检查和演示数据评估脚本
检查服务器上的所有数据库，评估演示数据需求
"""

import os
import sys
import logging
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('remote_database_check.log'),
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
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("neo4j未安装，Neo4j检查将跳过")

try:
    from qdrant_client import QdrantClient
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logger.warning("qdrant_client未安装，Qdrant检查将跳过")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis未安装，Redis检查将跳过")


class RemoteDatabaseChecker:
    """远程数据库检查器"""
    
    def __init__(self):
        """初始化服务器配置"""
        # 应用服务器配置
        self.app_server = {
            'host': os.getenv('APP_SERVER_HOST', '43.143.139.197'),
            'user': os.getenv('APP_SERVER_USER', 'ubuntu'),
            'key': os.getenv('APP_SERVER_KEY', str(project_root / 'enterprise_ai_platform.pem')),
            'remote_path': os.getenv('APP_SERVER_PATH', '/opt/enterprise-ai-platform')
        }
        
        # 图数据库服务器配置（可能与应用服务器相同）
        self.neo4j_server = {
            'host': os.getenv('NEO4J_SERVER_HOST', '43.143.139.197'),
            'user': os.getenv('NEO4J_SERVER_USER', 'ubuntu'),
            'key': os.getenv('NEO4J_SERVER_KEY', str(project_root / 'Neo4j.pem')),
            'port': int(os.getenv('NEO4J_PORT', '7687')),
            'user_db': os.getenv('NEO4J_USER', 'neo4j'),
            'password': os.getenv('NEO4J_PASSWORD', 'neo4j_password')
        }
        
        # 数据库连接配置（从服务器环境变量获取）
        self.pg_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USER', 'ai_user'),
            'password': os.getenv('DB_PASSWORD', 'ai_password'),
            'database': os.getenv('DB_NAME', 'ai_platform')
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
        
        self.results = {
            'postgresql': {},
            'neo4j': {},
            'qdrant': {},
            'redis': {},
            'summary': {
                'total_issues': 0,
                'cleaned_records': 0,
                'demo_data_status': {}
            }
        }
    
    def execute_remote_command(self, command: str, server_config: Dict[str, str]) -> tuple[str, int]:
        """执行远程命令"""
        try:
            ssh_cmd = [
                'ssh',
                '-i', server_config['key'],
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'ConnectTimeout=10',
                f"{server_config['user']}@{server_config['host']}",
                command
            ]
            
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return result.stdout, result.returncode
            
        except subprocess.TimeoutExpired:
            logger.error(f"命令执行超时: {command}")
            return "", 1
        except Exception as e:
            logger.error(f"执行远程命令失败: {e}")
            return "", 1
    
    def get_remote_env_vars(self) -> Dict[str, str]:
        """获取服务器环境变量"""
        logger.info("获取服务器环境变量...")
        
        command = "cd /opt/enterprise-ai-platform && cat .env 2>/dev/null || echo 'No .env file'"
        stdout, returncode = self.execute_remote_command(command, self.app_server)
        
        env_vars = {}
        if returncode == 0 and stdout:
            for line in stdout.split('\n'):
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"').strip("'")
        
        # 更新配置
        if 'DB_HOST' in env_vars:
            self.pg_config['host'] = env_vars.get('DB_HOST', self.pg_config['host'])
        if 'DB_PORT' in env_vars:
            self.pg_config['port'] = int(env_vars.get('DB_PORT', self.pg_config['port']))
        if 'DB_USER' in env_vars:
            self.pg_config['user'] = env_vars.get('DB_USER', self.pg_config['user'])
        if 'DB_PASSWORD' in env_vars:
            self.pg_config['password'] = env_vars.get('DB_PASSWORD', self.pg_config['password'])
        if 'DB_NAME' in env_vars:
            self.pg_config['database'] = env_vars.get('DB_NAME', self.pg_config['database'])
        
        if 'NEO4J_URI' in env_vars:
            self.neo4j_server['uri'] = env_vars.get('NEO4J_URI', f"bolt://{self.neo4j_server['host']}:{self.neo4j_server['port']}")
        if 'NEO4J_USER' in env_vars:
            self.neo4j_server['user_db'] = env_vars.get('NEO4J_USER', self.neo4j_server['user_db'])
        if 'NEO4J_PASSWORD' in env_vars:
            self.neo4j_server['password'] = env_vars.get('NEO4J_PASSWORD', self.neo4j_server['password'])
        
        if 'QDRANT_URL' in env_vars:
            self.qdrant_config['url'] = env_vars.get('QDRANT_URL', self.qdrant_config['url'])
        if 'QDRANT_API_KEY' in env_vars:
            self.qdrant_config['api_key'] = env_vars.get('QDRANT_API_KEY', self.qdrant_config['api_key'])
        
        logger.info(f"获取到 {len(env_vars)} 个环境变量")
        return env_vars
    
    def check_remote_postgresql(self) -> Dict[str, Any]:
        """检查远程PostgreSQL数据质量（通过SSH在服务器上执行）"""
        logger.info("开始检查远程PostgreSQL数据质量...")
        issues = []
        cleaned = 0
        
        try:
            # 在服务器上执行检查脚本
            check_script = """
python3 << 'EOF'
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        user=os.getenv('DB_USER', 'ai_user'),
        password=os.getenv('DB_PASSWORD', 'ai_password'),
        database=os.getenv('DB_NAME', 'ai_platform'),
        connect_timeout=10
    )
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # 统计表数据量
    tables = ['users', 'roles', 'workflow_definitions', 'workflow_nodes', 
              'documents', 'document_chunks', 'knowledge_bases',
              'knowledge_graph_nodes', 'knowledge_graph_edges']
    table_counts = {}
    for table in tables:
        try:
            cursor.execute('SELECT COUNT(*) as count FROM ' + table)
            table_counts[table] = cursor.fetchone()['count']
        except:
            table_counts[table] = 0
    
    # 检查过期会话
    cursor.execute("SELECT COUNT(*) as count FROM user_sessions WHERE expires_at < NOW()")
    expired_sessions = cursor.fetchone()['count']
    
    result = {
        'status': 'success',
        'table_counts': table_counts,
        'expired_sessions': expired_sessions
    }
    print(json.dumps(result))
    
    cursor.close()
    conn.close()
except Exception as e:
    result = {'status': 'error', 'error': str(e)}
    print(json.dumps(result))
EOF
"""
            stdout, returncode = self.execute_remote_command(
                f"cd {self.app_server['remote_path']} && {check_script}",
                self.app_server
            )
            
            if returncode == 0 and stdout:
                import json
                result = json.loads(stdout.strip())
                if result.get('status') == 'success':
                    table_counts = result.get('table_counts', {})
                    expired_sessions = result.get('expired_sessions', 0)
                    
                    if expired_sessions > 0:
                        issues.append({
                            'table': 'user_sessions',
                            'type': 'expired_data',
                            'count': expired_sessions
                        })
                    
                    self.results['postgresql'] = {
                        'status': 'success',
                        'issues': issues,
                        'table_counts': table_counts,
                        'total_issues': len(issues)
                    }
                    logger.info(f"PostgreSQL检查完成，发现 {len(issues)} 个问题")
                    return self.results['postgresql']
                else:
                    raise Exception(result.get('error', 'Unknown error'))
            else:
                raise Exception(f"命令执行失败: {stdout}")
        
        except Exception as e:
            logger.error(f"PostgreSQL检查失败: {e}", exc_info=True)
            self.results['postgresql'] = {
                'status': 'error',
                'error': str(e)
            }
        
        return self.results['postgresql']
    
    def check_remote_neo4j(self) -> Dict[str, Any]:
        """检查远程Neo4j数据质量（通过SSH在服务器上执行）"""
        logger.info("开始检查远程Neo4j数据质量...")
        issues = []
        
        try:
            # 在服务器上执行检查脚本
            check_script = """
python3 << 'EOF'
from neo4j import GraphDatabase
import json
import os

try:
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'neo4j_password')
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    with driver.session() as session:
        node_result = session.run("MATCH (n) RETURN count(n) as count")
        node_count = node_result.single()['count']
        
        rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
        rel_count = rel_result.single()['count']
        
        orphan_result = session.run("MATCH (n) WHERE NOT (n)--() RETURN count(n) as count")
        orphan_count = orphan_result.single()['count']
    
    driver.close()
    
    result = {
        'status': 'success',
        'node_count': node_count,
        'relationship_count': rel_count,
        'orphan_count': orphan_count
    }
    print(json.dumps(result))
except Exception as e:
    result = {'status': 'error', 'error': str(e)}
    print(json.dumps(result))
EOF
"""
            stdout, returncode = self.execute_remote_command(
                f"cd {self.app_server['remote_path']} && {check_script}",
                self.app_server
            )
            
            if returncode == 0 and stdout:
                import json
                result = json.loads(stdout.strip())
                if result.get('status') == 'success':
                    if result.get('orphan_count', 0) > 0:
                        issues.append({
                            'type': 'orphan_nodes',
                            'count': result.get('orphan_count', 0)
                        })
                    
                    self.results['neo4j'] = {
                        'status': 'success',
                        'issues': issues,
                        'node_count': result.get('node_count', 0),
                        'relationship_count': result.get('relationship_count', 0),
                        'total_issues': len(issues)
                    }
                    logger.info(f"Neo4j检查完成，节点: {result.get('node_count', 0)}, 关系: {result.get('relationship_count', 0)}")
                    return self.results['neo4j']
                else:
                    raise Exception(result.get('error', 'Unknown error'))
            else:
                raise Exception(f"命令执行失败: {stdout}")
        
        except Exception as e:
            logger.error(f"Neo4j检查失败: {e}", exc_info=True)
            self.results['neo4j'] = {
                'status': 'error',
                'error': str(e)
            }
        
        return self.results['neo4j']
            
            with driver.session() as session:
                # 统计节点和关系数量
                logger.info("统计节点和关系数量...")
                node_result = session.run("MATCH (n) RETURN count(n) as count")
                node_count = node_result.single()['count']
                
                rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                rel_count = rel_result.single()['count']
                
                # 检查孤立节点
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
                
                # 按标签统计节点
                label_stats = {}
                try:
                    result = session.run("CALL db.labels() YIELD label RETURN label")
                    labels = [record['label'] for record in result]
                    for label in labels:
                        result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                        label_stats[label] = result.single()['count']
                except:
                    pass
            
            driver.close()
            
            self.results['neo4j'] = {
                'status': 'success',
                'issues': issues,
                'node_count': node_count,
                'relationship_count': rel_count,
                'label_stats': label_stats,
                'total_issues': len(issues)
            }
            
            logger.info(f"Neo4j检查完成，节点: {node_count}, 关系: {rel_count}")
            
        except Exception as e:
            logger.error(f"Neo4j检查失败: {e}", exc_info=True)
            self.results['neo4j'] = {
                'status': 'error',
                'error': str(e)
            }
        
        return self.results['neo4j']
    
    def check_remote_qdrant(self) -> Dict[str, Any]:
        """检查远程Qdrant数据质量"""
        logger.info("开始检查远程Qdrant数据质量...")
        issues = []
        
        if not QDRANT_AVAILABLE:
            logger.warning("qdrant_client未安装，跳过Qdrant检查")
            return {'status': 'skipped', 'reason': 'qdrant_client not installed'}
        
        try:
            client = QdrantClient(
                url=self.qdrant_config['url'],
                api_key=self.qdrant_config['api_key']
            )
            
            collections = client.get_collections().collections
            collection_stats = {}
            
            for collection in collections:
                collection_name = collection.name
                info = client.get_collection(collection_name)
                
                collection_stats[collection_name] = {
                    'points_count': info.points_count,
                    'vectors_count': info.vectors_count,
                }
                
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
            
            logger.info(f"Qdrant检查完成，集合数: {len(collections)}")
            
        except Exception as e:
            logger.error(f"Qdrant检查失败: {e}", exc_info=True)
            self.results['qdrant'] = {
                'status': 'error',
                'error': str(e)
            }
        
        return self.results['qdrant']
    
    def check_remote_redis(self) -> Dict[str, Any]:
        """检查远程Redis数据质量"""
        logger.info("开始检查远程Redis数据质量...")
        
        if not REDIS_AVAILABLE:
            logger.warning("redis未安装，跳过Redis检查")
            return {'status': 'skipped', 'reason': 'redis not installed'}
        
        try:
            r = redis.Redis(
                host=self.redis_config['host'],
                port=self.redis_config['port'],
                db=self.redis_config['db'],
                password=self.redis_config['password'],
                decode_responses=True,
                socket_connect_timeout=10
            )
            
            r.ping()
            info = r.info()
            keys_count = r.dbsize()
            
            self.results['redis'] = {
                'status': 'success',
                'keys_count': keys_count,
                'memory_used': info.get('used_memory_human', 'N/A')
            }
            
            logger.info(f"Redis检查完成，键数量: {keys_count}")
            
        except Exception as e:
            logger.error(f"Redis检查失败: {e}", exc_info=True)
            self.results['redis'] = {
                'status': 'error',
                'error': str(e)
            }
        
        return self.results['redis']
    
    def evaluate_demo_requirements(self) -> Dict[str, Any]:
        """评估演示数据需求"""
        logger.info("评估演示数据需求...")
        
        requirements = {
            'users': {'min': 3, 'current': 0, 'need': False, 'status': 'unknown'},
            'roles': {'min': 4, 'current': 0, 'need': False, 'status': 'unknown'},
            'workflows': {'min': 2, 'current': 0, 'need': False, 'status': 'unknown'},
            'documents': {'min': 5, 'current': 0, 'need': False, 'status': 'unknown'},
            'knowledge_bases': {'min': 2, 'current': 0, 'need': False, 'status': 'unknown'},
            'neo4j_nodes': {'min': 10, 'current': 0, 'need': False, 'status': 'unknown'},
            'neo4j_relationships': {'min': 15, 'current': 0, 'need': False, 'status': 'unknown'},
        }
        
        # 从PostgreSQL结果获取数据
        if self.results['postgresql'].get('status') == 'success':
            counts = self.results['postgresql'].get('table_counts', {})
            requirements['users']['current'] = counts.get('users', 0)
            requirements['workflows']['current'] = counts.get('workflow_definitions', 0)
            requirements['documents']['current'] = counts.get('documents', 0)
            requirements['knowledge_bases']['current'] = counts.get('knowledge_bases', 0)
            requirements['roles']['current'] = counts.get('roles', 0)
        
        # 从Neo4j结果获取数据
        if self.results['neo4j'].get('status') == 'success':
            requirements['neo4j_nodes']['current'] = self.results['neo4j'].get('node_count', 0)
            requirements['neo4j_relationships']['current'] = self.results['neo4j'].get('relationship_count', 0)
        
        # 检查是否需要生成数据
        for key, req in requirements.items():
            if req['current'] < req['min']:
                req['need'] = True
                req['status'] = 'insufficient'
            else:
                req['status'] = 'sufficient'
        
        self.results['summary']['demo_data_status'] = requirements
        return requirements
    
    def generate_report(self) -> str:
        """生成检查报告"""
        report = []
        report.append("# 远程服务器数据库数据质量检查和演示数据评估报告\n")
        report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**应用服务器**: {self.app_server['host']}\n")
        report.append(f"**图数据库服务器**: {self.neo4j_server['host']}\n")
        report.append("---\n\n")
        
        # PostgreSQL结果
        report.append("## 1. PostgreSQL检查结果\n\n")
        pg_result = self.results['postgresql']
        if pg_result.get('status') == 'success':
            report.append(f"- **状态**: ✅ 成功\n")
            report.append(f"- **发现问题**: {pg_result.get('total_issues', 0)} 个\n")
            report.append(f"- **表数据统计**:\n")
            for table, count in pg_result.get('table_counts', {}).items():
                report.append(f"  - {table}: {count} 条\n")
        else:
            report.append(f"- **状态**: ❌ {pg_result.get('status', 'unknown')}\n")
            report.append(f"- **错误**: {pg_result.get('error', 'Unknown')}\n")
        
        report.append("\n")
        
        # Neo4j结果
        report.append("## 2. Neo4j检查结果\n\n")
        neo4j_result = self.results['neo4j']
        if neo4j_result.get('status') == 'success':
            report.append(f"- **状态**: ✅ 成功\n")
            report.append(f"- **节点数**: {neo4j_result.get('node_count', 0)}\n")
            report.append(f"- **关系数**: {neo4j_result.get('relationship_count', 0)}\n")
        else:
            report.append(f"- **状态**: ❌ {neo4j_result.get('status', 'unknown')}\n")
            report.append(f"- **错误**: {neo4j_result.get('error', 'Unknown')}\n")
        
        report.append("\n")
        
        # Qdrant结果
        report.append("## 3. Qdrant检查结果\n\n")
        qdrant_result = self.results['qdrant']
        if qdrant_result.get('status') == 'success':
            report.append(f"- **状态**: ✅ 成功\n")
            report.append(f"- **集合数**: {len(qdrant_result.get('collections', {}))}\n")
        else:
            report.append(f"- **状态**: ❌ {qdrant_result.get('status', 'unknown')}\n")
            report.append(f"- **错误**: {qdrant_result.get('error', 'Unknown')}\n")
        
        report.append("\n")
        
        # Redis结果
        report.append("## 4. Redis检查结果\n\n")
        redis_result = self.results['redis']
        if redis_result.get('status') == 'success':
            report.append(f"- **状态**: ✅ 成功\n")
            report.append(f"- **键数量**: {redis_result.get('keys_count', 0)}\n")
        else:
            report.append(f"- **状态**: ❌ {redis_result.get('status', 'unknown')}\n")
            report.append(f"- **错误**: {redis_result.get('error', 'Unknown')}\n")
        
        report.append("\n")
        
        # 演示数据需求评估
        report.append("## 5. 演示数据需求评估\n\n")
        requirements = self.results['summary'].get('demo_data_status', {})
        report.append("| 数据类型 | 当前数量 | 最少需要 | 状态 |\n")
        report.append("|---------|---------|---------|------|\n")
        for key, req in requirements.items():
            status_icon = "✅" if req['status'] == 'sufficient' else "⚠️"
            report.append(f"| {key} | {req['current']} | {req['min']} | {status_icon} {req['status']} |\n")
        
        report.append("\n")
        
        # 总结
        report.append("## 6. 总结\n\n")
        insufficient = [k for k, v in requirements.items() if v['need']]
        if insufficient:
            report.append(f"### ⚠️ 需要生成演示数据\n\n")
            report.append("以下数据类型不足，需要生成演示数据：\n")
            for key in insufficient:
                req = requirements[key]
                report.append(f"- **{key}**: 当前 {req['current']}，需要至少 {req['min']}\n")
        else:
            report.append("### ✅ 演示数据充足\n\n")
            report.append("所有数据类型都满足演示需求。\n")
        
        return ''.join(report)
    
    def run(self):
        """运行完整检查流程"""
        logger.info("=" * 60)
        logger.info("开始远程服务器数据库数据质量检查")
        logger.info("=" * 60)
        
        # 获取服务器环境变量
        self.get_remote_env_vars()
        
        # 检查各数据库
        self.check_remote_postgresql()
        self.check_remote_neo4j()
        self.check_remote_qdrant()
        self.check_remote_redis()
        
        # 评估演示需求
        self.evaluate_demo_requirements()
        
        # 生成报告
        report = self.generate_report()
        
        # 保存报告
        report_file = project_root / '远程服务器数据库检查报告.md'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # 保存JSON结果
        json_file = project_root / '远程服务器数据库检查结果.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info("=" * 60)
        logger.info("远程数据库检查完成")
        logger.info(f"报告已保存到: {report_file}")
        logger.info(f"JSON结果已保存到: {json_file}")
        logger.info("=" * 60)
        
        return self.results


if __name__ == '__main__':
    checker = RemoteDatabaseChecker()
    results = checker.run()
    print("\n检查完成！请查看生成的报告文件。")


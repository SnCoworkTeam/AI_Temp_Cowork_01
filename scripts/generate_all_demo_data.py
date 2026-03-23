#!/usr/bin/env python3
"""
完整演示数据生成脚本
生成PostgreSQL和Neo4j的演示数据
"""

import os
import sys
import logging
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.warning("psycopg2未安装，PostgreSQL数据生成将跳过")


class CompleteDemoDataGenerator:
    """完整演示数据生成器"""
    
    def __init__(self):
        """初始化服务器配置"""
        # 应用服务器配置
        self.app_server = {
            'host': os.getenv('APP_SERVER_HOST', '43.143.139.197'),
            'user': os.getenv('APP_SERVER_USER', 'ubuntu'),
            'key': os.getenv('APP_SERVER_KEY', str(project_root / 'enterprise_ai_platform.pem')),
            'remote_path': os.getenv('APP_SERVER_PATH', '/opt/enterprise-ai-platform')
        }
        
        # 图数据库服务器配置
        self.neo4j_server = {
            'host': os.getenv('NEO4J_SERVER_HOST', '43.143.139.197'),
            'user': os.getenv('NEO4J_SERVER_USER', 'ubuntu'),
            'key': os.getenv('NEO4J_SERVER_KEY', str(project_root / 'Neo4j.pem')),
            'remote_path': os.getenv('NEO4J_SERVER_PATH', '/opt/enterprise-ai-platform')
        }
        
        # 数据库配置
        self.pg_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USER', 'ai_user'),
            'password': os.getenv('DB_PASSWORD', 'ai_password'),
            'database': os.getenv('DB_NAME', 'ai_platform')
        }
        
        self.results = {
            'postgresql': {},
            'neo4j': {},
            'summary': {}
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
                timeout=120,
                encoding='utf-8',
                errors='ignore'
            )
            
            return result.stdout, result.returncode
            
        except subprocess.TimeoutExpired:
            logger.error(f"命令执行超时: {command}")
            return "", 1
        except Exception as e:
            logger.error(f"执行远程命令失败: {e}")
            return "", 1
    
    def generate_postgresql_roles(self) -> Dict[str, Any]:
        """在应用服务器上生成PostgreSQL角色数据"""
        logger.info("生成PostgreSQL角色数据...")
        
        if not PSYCOPG2_AVAILABLE:
            logger.warning("psycopg2未安装，跳过PostgreSQL数据生成")
            return {'status': 'skipped'}
        
        # 在服务器上执行生成脚本
        generate_script = """
python3 << 'EOF'
import psycopg2
import json
import os
import uuid

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        user=os.getenv('DB_USER', 'ai_user'),
        password=os.getenv('DB_PASSWORD', 'ai_password'),
        database=os.getenv('DB_NAME', 'ai_platform'),
        connect_timeout=10
    )
    cursor = conn.cursor()
    
    result_data = {
        'status': 'success',
        'generated': {
            'roles': 0,
            'permissions': 0,
            'role_permissions': 0
        }
    }
    
    # 创建角色
    roles = [
        ('admin', '管理员', '系统管理员角色', True),
        ('user', '普通用户', '普通用户角色', False),
        ('developer', '开发者', '开发者角色', False),
        ('viewer', '查看者', '只读用户角色', False)
    ]
    
    role_ids = {}
    for code, name, description, is_system in roles:
        role_id = str(uuid.uuid4())
        cursor.execute('INSERT INTO roles (id, code, name, description, is_system, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, NOW(), NOW()) ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, updated_at = NOW() RETURNING id', (role_id, code, name, description, is_system))
        result = cursor.fetchone()
        if result:
            role_ids[code] = str(result[0])
            result_data['generated']['roles'] += 1
    
    # 创建权限
    permissions = [
        ('read', '读取', '读取权限'),
        ('write', '写入', '写入权限'),
        ('delete', '删除', '删除权限'),
        ('admin', '管理', '管理权限')
    ]
    
    permission_ids = {}
    for code, name, description in permissions:
        perm_id = str(uuid.uuid4())
        cursor.execute('INSERT INTO permissions (id, code, name, description, created_at, updated_at) VALUES (%s, %s, %s, %s, NOW(), NOW()) ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, updated_at = NOW() RETURNING id', (perm_id, code, name, description))
        result = cursor.fetchone()
        if result:
            permission_ids[code] = str(result[0])
            result_data['generated']['permissions'] += 1
    
    # 关联角色和权限
    role_permissions = {
        'admin': ['read', 'write', 'delete', 'admin'],
        'user': ['read', 'write'],
        'developer': ['read', 'write'],
        'viewer': ['read']
    }
    
    for role_code, perm_codes in role_permissions.items():
        if role_code in role_ids:
            role_id = role_ids[role_code]
            for perm_code in perm_codes:
                if perm_code in permission_ids:
                    perm_id = permission_ids[perm_code]
                    cursor.execute('INSERT INTO role_permissions (role_id, permission_id, created_at) VALUES (%s, %s, NOW()) ON CONFLICT DO NOTHING', (role_id, perm_id))
                    result_data['generated']['role_permissions'] += 1
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(json.dumps(result_data, ensure_ascii=False))
    
except Exception as e:
    result_data = {'status': 'error', 'error': str(e)}
    print(json.dumps(result_data, ensure_ascii=False))
    sys.exit(1)
EOF
"""
        
        command = f"cd {self.app_server['remote_path']} && source .env 2>/dev/null; {generate_script}"
        stdout, returncode = self.execute_remote_command(command, self.app_server)
        
        if returncode == 0 and stdout:
            try:
                import json
                result = json.loads(stdout.strip())
                return result
            except:
                raise Exception(f"JSON解析失败: {stdout[:200]}")
        else:
            raise Exception(f"命令执行失败: {stdout}")
    
    def generate_neo4j_demo_data(self) -> Dict[str, Any]:
        """在Neo4j服务器上生成演示数据"""
        logger.info("生成Neo4j演示数据...")
        
        # 读取生成脚本内容
        script_path = project_root / 'scripts' / 'generate_neo4j_demo_data_on_server.py'
        if not script_path.exists():
            raise Exception(f"生成脚本不存在: {script_path}")
        
        # 上传脚本到服务器
        logger.info("上传Neo4j数据生成脚本到服务器...")
        upload_cmd = [
            'scp',
            '-i', self.neo4j_server['key'],
            '-o', 'StrictHostKeyChecking=no',
            str(script_path),
            f"{self.neo4j_server['user']}@{self.neo4j_server['host']}:{self.neo4j_server['remote_path']}/scripts/"
        ]
        
        result = subprocess.run(upload_cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise Exception(f"脚本上传失败: {result.stderr}")
        
        # 在服务器上执行生成脚本
        logger.info("在服务器上执行Neo4j数据生成...")
        command = f"cd {self.neo4j_server['remote_path']} && source .env 2>/dev/null && python3 scripts/generate_neo4j_demo_data_on_server.py"
        stdout, returncode = self.execute_remote_command(command, self.neo4j_server)
        
        if returncode == 0 and stdout:
            try:
                import json
                result = json.loads(stdout.strip())
                return result
            except:
                raise Exception(f"JSON解析失败: {stdout[:200]}")
        else:
            raise Exception(f"命令执行失败: {stdout}")
    
    def run(self):
        """运行完整数据生成流程"""
        logger.info("=" * 60)
        logger.info("开始生成完整演示数据")
        logger.info("=" * 60)
        
        # 1. 生成PostgreSQL角色数据
        try:
            pg_result = self.generate_postgresql_roles()
            self.results['postgresql'] = pg_result
            logger.info("PostgreSQL角色数据生成完成")
        except Exception as e:
            logger.error(f"PostgreSQL数据生成失败: {e}", exc_info=True)
            self.results['postgresql'] = {'status': 'error', 'error': str(e)}
        
        # 2. 生成Neo4j演示数据
        try:
            neo4j_result = self.generate_neo4j_demo_data()
            self.results['neo4j'] = neo4j_result
            logger.info("Neo4j演示数据生成完成")
        except Exception as e:
            logger.error(f"Neo4j数据生成失败: {e}", exc_info=True)
            self.results['neo4j'] = {'status': 'error', 'error': str(e)}
        
        # 3. 生成总结
        self.results['summary'] = {
            'postgresql_success': self.results['postgresql'].get('status') == 'success',
            'neo4j_success': self.results['neo4j'].get('status') == 'success',
            'all_success': (
                self.results['postgresql'].get('status') == 'success' and
                self.results['neo4j'].get('status') == 'success'
            )
        }
        
        logger.info("=" * 60)
        logger.info("演示数据生成完成")
        logger.info("=" * 60)
        
        return self.results


if __name__ == '__main__':
    generator = CompleteDemoDataGenerator()
    results = generator.run()
    print(f"\n生成完成！PostgreSQL: {results['postgresql'].get('status')}, Neo4j: {results['neo4j'].get('status')}")


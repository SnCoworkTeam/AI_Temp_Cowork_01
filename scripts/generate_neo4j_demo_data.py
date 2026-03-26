#!/usr/bin/env python3
"""
Neo4j演示数据生成脚本
根据演示方案生成完整的企业架构演示数据
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


class Neo4jDemoDataGenerator:
    """Neo4j演示数据生成器"""
    
    def __init__(self):
        """初始化服务器配置"""
        # 图数据库服务器配置
        self.neo4j_server = {
            'host': os.getenv('NEO4J_SERVER_HOST', '43.143.139.197'),
            'user': os.getenv('NEO4J_SERVER_USER', 'ubuntu'),
            'key': os.getenv('NEO4J_SERVER_KEY', str(project_root / 'Neo4j.pem')),
            'remote_path': os.getenv('NEO4J_SERVER_PATH', '/opt/enterprise-ai-platform')
        }
        
        self.generated_data = {
            'nodes': 0,
            'relationships': 0,
            'details': {}
        }
    
    def execute_remote_command(self, command: str) -> tuple[str, int]:
        """执行远程命令"""
        try:
            ssh_cmd = [
                'ssh',
                '-i', self.neo4j_server['key'],
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'ConnectTimeout=10',
                f"{self.neo4j_server['user']}@{self.neo4j_server['host']}",
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
    
    def generate_demo_data(self) -> Dict[str, Any]:
        """在服务器上生成演示数据"""
        logger.info("开始在服务器上生成Neo4j演示数据...")
        
        # 在服务器上执行生成脚本
        generate_script = """
python3 << 'EOF'
from neo4j import GraphDatabase
import json
import os
import uuid
from datetime import datetime

try:
    # 从环境变量获取配置
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'neo4j_password')
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    result_data = {
        'status': 'success',
        'generated': {
            'nodes': 0,
            'relationships': 0,
            'details': {}
        }
    }
    
    with driver.session() as session:
        # 1. 生成组织架构数据
        print("生成组织架构数据...")
        
        # 创建组织
        org_id = str(uuid.uuid4())
        org_result = session.run("""
            MERGE (org:Organization {name: '示例公司', code: 'COMPANY_001'})
            ON CREATE SET org.id = $id, org.type = 'Company', org.created_at = $created_at
            RETURN org.name as name
        """, id=org_id, created_at=datetime.now().isoformat())
        org_name = org_result.single()['name']
        result_data['generated']['nodes'] += 1
        result_data['generated']['details']['Organization'] = 1
        
        # 创建部门
        departments = [
            {'name': '技术部', 'code': 'DEPT_TECH'},
            {'name': '业务部', 'code': 'DEPT_BUSINESS'}
        ]
        dept_count = 0
        for dept in departments:
            dept_id = str(uuid.uuid4())
            session.run("""
                MERGE (dept:Department {name: $name, code: $code})
                ON CREATE SET dept.id = $id, dept.type = 'Department', dept.created_at = $created_at
                WITH dept
                MATCH (org:Organization {name: '示例公司'})
                MERGE (dept)-[:BELONGS_TO]->(org)
            """, name=dept['name'], code=dept['code'], id=dept_id, created_at=datetime.now().isoformat())
            dept_count += 1
            result_data['generated']['nodes'] += 1
            result_data['generated']['relationships'] += 1
        result_data['generated']['details']['Department'] = dept_count
        
        # 创建团队
        teams = [
            {'name': '开发团队', 'code': 'TEAM_DEV', 'dept': '技术部'},
            {'name': '测试团队', 'code': 'TEAM_TEST', 'dept': '技术部'},
            {'name': '业务分析团队', 'code': 'TEAM_BA', 'dept': '业务部'}
        ]
        team_count = 0
        for team in teams:
            team_id = str(uuid.uuid4())
            session.run("""
                MERGE (team:Team {name: $name, code: $code})
                ON CREATE SET team.id = $id, team.type = 'Team', team.created_at = $created_at
                WITH team
                MATCH (dept:Department {name: $dept_name})
                MERGE (dept)-[:HAS_TEAM]->(team)
            """, name=team['name'], code=team['code'], dept_name=team['dept'], id=team_id, created_at=datetime.now().isoformat())
            team_count += 1
            result_data['generated']['nodes'] += 1
            result_data['generated']['relationships'] += 1
        result_data['generated']['details']['Team'] = team_count
        
        # 2. 生成业务架构数据
        print("生成业务架构数据...")
        
        # 创建业务流程
        processes = [
            {'name': '订单处理流程', 'code': 'PROC_ORDER'},
            {'name': '客户服务流程', 'code': 'PROC_CUSTOMER'},
            {'name': '采购流程', 'code': 'PROC_PURCHASE'}
        ]
        process_count = 0
        for proc in processes:
            proc_id = str(uuid.uuid4())
            session.run("""
                MERGE (bp:BusinessProcess {name: $name, code: $code})
                ON CREATE SET bp.id = $id, bp.type = 'BusinessProcess', bp.created_at = $created_at
            """, name=proc['name'], code=proc['code'], id=proc_id, created_at=datetime.now().isoformat())
            process_count += 1
            result_data['generated']['nodes'] += 1
        result_data['generated']['details']['BusinessProcess'] = process_count
        
        # 创建业务能力
        capabilities = [
            {'name': '订单管理', 'code': 'CAP_ORDER'},
            {'name': '客户管理', 'code': 'CAP_CUSTOMER'},
            {'name': '库存管理', 'code': 'CAP_INVENTORY'},
            {'name': '采购管理', 'code': 'CAP_PURCHASE'}
        ]
        cap_count = 0
        for cap in capabilities:
            cap_id = str(uuid.uuid4())
            session.run("""
                MERGE (bc:BusinessCapability {name: $name, code: $code})
                ON CREATE SET bc.id = $id, bc.type = 'BusinessCapability', bc.created_at = $created_at
            """, name=cap['name'], code=cap['code'], id=cap_id, created_at=datetime.now().isoformat())
            cap_count += 1
            result_data['generated']['nodes'] += 1
        result_data['generated']['details']['BusinessCapability'] = cap_count
        
        # 创建业务流程-业务能力关系
        process_cap_mappings = [
            ('订单处理流程', '订单管理'),
            ('订单处理流程', '库存管理'),
            ('客户服务流程', '客户管理'),
            ('采购流程', '采购管理'),
            ('采购流程', '库存管理')
        ]
        for proc_name, cap_name in process_cap_mappings:
            session.run("""
                MATCH (bp:BusinessProcess {name: $proc_name})
                MATCH (bc:BusinessCapability {name: $cap_name})
                MERGE (bp)-[:USES]->(bc)
            """, proc_name=proc_name, cap_name=cap_name)
            result_data['generated']['relationships'] += 1
        
        # 3. 生成应用架构数据
        print("生成应用架构数据...")
        
        # 创建应用系统
        systems = [
            {'name': '订单管理系统', 'code': 'APP_OMS', 'type': 'Core'},
            {'name': '客户关系管理系统', 'code': 'APP_CRM', 'type': 'Core'},
            {'name': '库存管理系统', 'code': 'APP_WMS', 'type': 'Core'},
            {'name': '采购管理系统', 'code': 'APP_PMS', 'type': 'Core'}
        ]
        system_count = 0
        for sys in systems:
            sys_id = str(uuid.uuid4())
            session.run("""
                MERGE (asys:ApplicationSystem {name: $name, code: $code})
                ON CREATE SET asys.id = $id, asys.type = $type, asys.created_at = $created_at
            """, name=sys['name'], code=sys['code'], type=sys['type'], id=sys_id, created_at=datetime.now().isoformat())
            system_count += 1
            result_data['generated']['nodes'] += 1
        result_data['generated']['details']['ApplicationSystem'] = system_count
        
        # 创建业务能力-应用系统关系
        cap_system_mappings = [
            ('订单管理', '订单管理系统'),
            ('客户管理', '客户关系管理系统'),
            ('库存管理', '库存管理系统'),
            ('采购管理', '采购管理系统')
        ]
        for cap_name, sys_name in cap_system_mappings:
            session.run("""
                MATCH (bc:BusinessCapability {name: $cap_name})
                MATCH (asys:ApplicationSystem {name: $sys_name})
                MERGE (bc)-[:SUPPORTS]->(asys)
            """, cap_name=cap_name, sys_name=sys_name)
            result_data['generated']['relationships'] += 1
        
        # 4. 生成数据架构数据
        print("生成数据架构数据...")
        
        # 创建数据实体
        entities = [
            {'name': '订单', 'code': 'DATA_ORDER', 'system': '订单管理系统'},
            {'name': '客户', 'code': 'DATA_CUSTOMER', 'system': '客户关系管理系统'},
            {'name': '库存', 'code': 'DATA_INVENTORY', 'system': '库存管理系统'},
            {'name': '采购单', 'code': 'DATA_PO', 'system': '采购管理系统'}
        ]
        entity_count = 0
        for entity in entities:
            entity_id = str(uuid.uuid4())
            session.run("""
                MERGE (de:DataEntity {name: $name, code: $code})
                ON CREATE SET de.id = $id, de.type = 'DataEntity', de.created_at = $created_at
                WITH de
                MATCH (asys:ApplicationSystem {name: $system_name})
                MERGE (asys)-[:STORES]->(de)
            """, name=entity['name'], code=entity['code'], system_name=entity['system'], id=entity_id, created_at=datetime.now().isoformat())
            entity_count += 1
            result_data['generated']['nodes'] += 1
            result_data['generated']['relationships'] += 1
        result_data['generated']['details']['DataEntity'] = entity_count
        
        # 5. 生成技术架构数据
        print("生成技术架构数据...")
        
        # 创建技术组件
        components = [
            {'name': 'PostgreSQL数据库', 'code': 'TECH_PG', 'type': 'Database'},
            {'name': 'Redis缓存', 'code': 'TECH_REDIS', 'type': 'Cache'},
            {'name': 'Nginx服务器', 'code': 'TECH_NGINX', 'type': 'WebServer'},
            {'name': 'Docker容器', 'code': 'TECH_DOCKER', 'type': 'Container'},
            {'name': 'Kubernetes集群', 'code': 'TECH_K8S', 'type': 'Orchestration'}
        ]
        component_count = 0
        for comp in components:
            comp_id = str(uuid.uuid4())
            session.run("""
                MERGE (tc:TechnologyComponent {name: $name, code: $code})
                ON CREATE SET tc.id = $id, tc.type = $type, tc.created_at = $created_at
            """, name=comp['name'], code=comp['code'], type=comp['type'], id=comp_id, created_at=datetime.now().isoformat())
            component_count += 1
            result_data['generated']['nodes'] += 1
        result_data['generated']['details']['TechnologyComponent'] = component_count
        
        # 创建数据实体-技术组件关系
        entity_tech_mappings = [
            ('订单', 'PostgreSQL数据库'),
            ('客户', 'PostgreSQL数据库'),
            ('库存', 'PostgreSQL数据库'),
            ('采购单', 'PostgreSQL数据库')
        ]
        for entity_name, tech_name in entity_tech_mappings:
            session.run("""
                MATCH (de:DataEntity {name: $entity_name})
                MATCH (tc:TechnologyComponent {name: $tech_name})
                MERGE (de)-[:USES_TECH]->(tc)
            """, entity_name=entity_name, tech_name=tech_name)
            result_data['generated']['relationships'] += 1
        
        # 创建技术栈
        stacks = [
            {'name': 'Java技术栈', 'code': 'STACK_JAVA'},
            {'name': 'Python技术栈', 'code': 'STACK_PYTHON'}
        ]
        stack_count = 0
        for stack in stacks:
            stack_id = str(uuid.uuid4())
            session.run("""
                MERGE (ts:TechnologyStack {name: $name, code: $code})
                ON CREATE SET ts.id = $id, ts.type = 'TechnologyStack', ts.created_at = $created_at
            """, name=stack['name'], code=stack['code'], id=stack_id, created_at=datetime.now().isoformat())
            stack_count += 1
            result_data['generated']['nodes'] += 1
        result_data['generated']['details']['TechnologyStack'] = stack_count
        
        # 创建技术栈-组件关系
        stack_component_mappings = [
            ('Java技术栈', 'PostgreSQL数据库'),
            ('Java技术栈', 'Redis缓存'),
            ('Python技术栈', 'PostgreSQL数据库'),
            ('Python技术栈', 'Docker容器')
        ]
        for stack_name, comp_name in stack_component_mappings:
            session.run("""
                MATCH (ts:TechnologyStack {name: $stack_name})
                MATCH (tc:TechnologyComponent {name: $comp_name})
                MERGE (ts)-[:CONTAINS]->(tc)
            """, stack_name=stack_name, comp_name=comp_name)
            result_data['generated']['relationships'] += 1
        
        # 6. 验证完整追踪链（场景2）
        print("验证完整追踪链...")
        chain_result = session.run("""
            MATCH path = (bp:BusinessProcess {name: '订单处理流程'})-[:USES]->(bc:BusinessCapability {name: '订单管理'})-[:SUPPORTS]->(asys:ApplicationSystem {name: '订单管理系统'})-[:STORES]->(de:DataEntity {name: '订单'})-[:USES_TECH]->(tc:TechnologyComponent {name: 'PostgreSQL数据库'})
            RETURN count(path) as chain_count
        """)
        chain_count = chain_result.single()['chain_count']
        result_data['generated']['details']['full_tracking_chains'] = chain_count
        
        # 7. 验证影响分析链（场景3）
        print("验证影响分析链...")
        impact_result = session.run("""
            MATCH path = (tc:TechnologyComponent {name: 'PostgreSQL数据库'})<-[:USES_TECH]-(de:DataEntity)<-[:STORES]-(asys:ApplicationSystem)-[:SUPPORTS]-(bc:BusinessCapability)<-[:USES]-(bp:BusinessProcess)
            RETURN count(path) as impact_count
        """)
        impact_count = impact_result.single()['impact_count']
        result_data['generated']['details']['impact_chains'] = impact_count
    
    driver.close()
    print(json.dumps(result_data, ensure_ascii=False))
    
except Exception as e:
    result_data = {'status': 'error', 'error': str(e)}
    print(json.dumps(result_data, ensure_ascii=False))
    sys.exit(1)
EOF
"""
        
        command = f"cd {self.neo4j_server['remote_path']} && source .env 2>/dev/null; {generate_script}"
        stdout, returncode = self.execute_remote_command(command)
        
        if returncode == 0 and stdout:
            try:
                import json
                result = json.loads(stdout.strip())
                if result.get('status') == 'success':
                    self.generated_data = result.get('generated', {})
                    logger.info(f"演示数据生成完成: {self.generated_data['nodes']} 个节点, {self.generated_data['relationships']} 条关系")
                    return result
                else:
                    raise Exception(result.get('error', 'Unknown error'))
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}, 输出: {stdout[:200]}")
                raise Exception(f"JSON解析失败: {e}")
        else:
            raise Exception(f"命令执行失败: {stdout}")
    
    def run(self):
        """运行数据生成流程"""
        logger.info("=" * 60)
        logger.info("开始生成Neo4j演示数据")
        logger.info("=" * 60)
        
        try:
            result = self.generate_demo_data()
            logger.info("=" * 60)
            logger.info("演示数据生成完成")
            logger.info(f"生成节点: {self.generated_data.get('nodes', 0)}")
            logger.info(f"生成关系: {self.generated_data.get('relationships', 0)}")
            logger.info("=" * 60)
            return result
        except Exception as e:
            logger.error(f"数据生成失败: {e}", exc_info=True)
            return {'status': 'error', 'error': str(e)}


if __name__ == '__main__':
    generator = Neo4jDemoDataGenerator()
    result = generator.run()
    print(f"\n生成完成！结果: {result.get('status', 'unknown')}")


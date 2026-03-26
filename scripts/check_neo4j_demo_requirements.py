#!/usr/bin/env python3
"""
Neo4j图数据库演示数据需求检查脚本
根据演示方案检查Neo4j数据是否满足演示需求
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
        logging.FileHandler('neo4j_demo_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class Neo4jDemoChecker:
    """Neo4j演示数据需求检查器"""
    
    def __init__(self):
        """初始化服务器配置"""
        # 图数据库服务器配置
        self.neo4j_server = {
            'host': os.getenv('NEO4J_SERVER_HOST', '43.143.139.197'),
            'user': os.getenv('NEO4J_SERVER_USER', 'ubuntu'),
            'key': os.getenv('NEO4J_SERVER_KEY', str(project_root / 'Neo4j.pem')),
            'remote_path': os.getenv('NEO4J_SERVER_PATH', '/opt/enterprise-ai-platform')
        }
        
        # Neo4j连接配置
        self.neo4j_config = {
            'uri': os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
            'user': os.getenv('NEO4J_USER', 'neo4j'),
            'password': os.getenv('NEO4J_PASSWORD', 'neo4j_password')
        }
        
        self.results = {
            'node_counts': {},
            'relationship_counts': {},
            'scenario_checks': {},
            'data_quality': {},
            'summary': {}
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
                timeout=60,
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
    
    def check_neo4j_data(self) -> Dict[str, Any]:
        """在服务器上检查Neo4j数据"""
        logger.info("开始在服务器上检查Neo4j数据...")
        
        # 在服务器上执行检查脚本
        check_script = """
python3 << 'EOF'
from neo4j import GraphDatabase
import json
import os

try:
    # 从环境变量获取配置
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'neo4j_password')
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    result_data = {
        'status': 'success',
        'node_counts': {},
        'relationship_counts': {},
        'scenario_data': {}
    }
    
    with driver.session() as session:
        # 1. 统计各类型节点数量
        node_types = [
            'Organization', 'Department', 'Team',
            'BusinessProcess', 'BusinessCapability', 'BusinessService',
            'ApplicationSystem', 'ApplicationService',
            'DataEntity', 'DataModel', 'DataFlow',
            'TechnologyComponent', 'TechnologyStack', 'Infrastructure'
        ]
        
        for node_type in node_types:
            query = f"MATCH (n:{node_type}) RETURN count(n) as count"
            result = session.run(query)
            count = result.single()['count']
            result_data['node_counts'][node_type] = count
        
        # 2. 统计各类型关系数量
        relationship_types = [
            'BELONGS_TO', 'HAS_TEAM',
            'SUPPORTS', 'USES', 'CONTAINS',
            'PROVIDES', 'CONSUMES', 'EXPOSES',
            'STORES', 'TRANSFORMS', 'BELONGS_TO',
            'USES_TECH', 'DEPLOYS_ON'
        ]
        
        for rel_type in relationship_types:
            query = f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count"
            result = session.run(query)
            count = result.single()['count']
            result_data['relationship_counts'][rel_type] = count
        
        # 3. 检查场景1: 组织架构层级
        org_query = "MATCH path = (org:Organization)-[:BELONGS_TO*]->(dept:Department)-[:HAS_TEAM]->(team:Team) RETURN count(path) as path_count"
        result = session.run(org_query)
        result_data['scenario_data']['org_hierarchy_paths'] = result.single()['path_count']
        
        # 4. 检查场景2: 完整追踪链（业务流程到技术组件）
        tracking_query = "MATCH path = (bp:BusinessProcess)-[:USES]->(bc:BusinessCapability)-[:SUPPORTS]->(asys:ApplicationSystem)-[:STORES]->(de:DataEntity)-[:USES_TECH]->(tc:TechnologyComponent) RETURN count(path) as path_count"
        result = session.run(tracking_query)
        result_data['scenario_data']['full_tracking_paths'] = result.single()['path_count']
        
        # 5. 检查场景3: 影响分析链（技术组件到业务流程）
        impact_query = "MATCH path = (tc:TechnologyComponent)<-[:USES_TECH]-(asys:ApplicationSystem)-[:SUPPORTS]->(bp:BusinessProcess) RETURN count(path) as path_count"
        result = session.run(impact_query)
        result_data['scenario_data']['impact_paths'] = result.single()['path_count']
        
        # 6. 检查孤立节点
        orphan_query = "MATCH (n) WHERE NOT (n)--() RETURN count(n) as count"
        result = session.run(orphan_query)
        result_data['orphan_nodes'] = result.single()['count']
        
        # 7. 检查节点属性完整性
        node_props_check = {}
        for node_type in ['Organization', 'BusinessProcess', 'ApplicationSystem']:
            query = "MATCH (n:" + node_type + ") WHERE n.name IS NULL OR n.name = '' RETURN count(n) as count"
            result = session.run(query)
            node_props_check[node_type] = result.single()['count']
        result_data['missing_properties'] = node_props_check
        
    driver.close()
    print(json.dumps(result_data))
    
except Exception as e:
    result_data = {'status': 'error', 'error': str(e)}
    print(json.dumps(result_data))
EOF
"""
        
        command = f"cd {self.neo4j_server['remote_path']} && source .env 2>/dev/null; {check_script}"
        stdout, returncode = self.execute_remote_command(command)
        
        if returncode == 0 and stdout:
            try:
                import json
                result = json.loads(stdout.strip())
                if result.get('status') == 'success':
                    self.results['node_counts'] = result.get('node_counts', {})
                    self.results['relationship_counts'] = result.get('relationship_counts', {})
                    self.results['scenario_data'] = result.get('scenario_data', {})
                    self.results['data_quality'] = {
                        'orphan_nodes': result.get('orphan_nodes', 0),
                        'missing_properties': result.get('missing_properties', {})
                    }
                    logger.info("Neo4j数据检查完成")
                    return result
                else:
                    raise Exception(result.get('error', 'Unknown error'))
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}, 输出: {stdout[:200]}")
                raise Exception(f"JSON解析失败: {e}")
        else:
            raise Exception(f"命令执行失败: {stdout}")
    
    def evaluate_demo_requirements(self) -> Dict[str, Any]:
        """评估演示需求"""
        logger.info("评估演示需求...")
        
        # 定义演示需求
        requirements = {
            'scenario1': {
                'name': '企业架构全景展示',
                'node_requirements': {
                    'Organization': 1,
                    'Department': 2,
                    'Team': 3,
                    'BusinessProcess': 3,
                    'BusinessCapability': 4,
                    'BusinessService': 2,
                    'ApplicationSystem': 4,
                    'ApplicationService': 3,
                    'DataEntity': 4,
                    'DataModel': 2,
                    'DataFlow': 2,
                    'TechnologyComponent': 5,
                    'TechnologyStack': 2,
                    'Infrastructure': 2
                },
                'relationship_requirements': {
                    'BELONGS_TO': 5,
                    'HAS_TEAM': 3,
                    'SUPPORTS': 4,
                    'USES': 5,
                    'PROVIDES': 3,
                    'STORES': 4,
                    'USES_TECH': 4,
                    'DEPLOYS_ON': 3,
                    'TRANSFORMS': 2,
                    'CONTAINS': 4
                },
                'total_nodes_min': 33,
                'total_relationships_min': 37
            },
            'scenario2': {
                'name': '业务流程到技术实现追踪',
                'full_tracking_paths_min': 1,
                'description': '需要至少1条完整的5层追踪链'
            },
            'scenario3': {
                'name': '变更影响分析',
                'impact_paths_min': 1,
                'description': '需要至少1条完整的影响分析链'
            },
            'scenario4': {
                'name': '架构标准化展示',
                'technology_stacks_min': 2,
                'technology_components_min': 5,
                'description': '需要至少2个技术栈和5个技术组件'
            }
        }
        
        # 评估每个场景
        scenario_checks = {}
        
        # 场景1评估
        scenario1_check = {
            'name': requirements['scenario1']['name'],
            'node_checks': {},
            'relationship_checks': {},
            'passed': True,
            'missing_nodes': [],
            'missing_relationships': []
        }
        
        node_counts = self.results.get('node_counts', {})
        for node_type, min_count in requirements['scenario1']['node_requirements'].items():
            current_count = node_counts.get(node_type, 0)
            scenario1_check['node_checks'][node_type] = {
                'current': current_count,
                'required': min_count,
                'sufficient': current_count >= min_count
            }
            if current_count < min_count:
                scenario1_check['passed'] = False
                scenario1_check['missing_nodes'].append({
                    'type': node_type,
                    'current': current_count,
                    'required': min_count,
                    'needed': min_count - current_count
                })
        
        rel_counts = self.results.get('relationship_counts', {})
        for rel_type, min_count in requirements['scenario1']['relationship_requirements'].items():
            current_count = rel_counts.get(rel_type, 0)
            scenario1_check['relationship_checks'][rel_type] = {
                'current': current_count,
                'required': min_count,
                'sufficient': current_count >= min_count
            }
            if current_count < min_count:
                scenario1_check['passed'] = False
                scenario1_check['missing_relationships'].append({
                    'type': rel_type,
                    'current': current_count,
                    'required': min_count,
                    'needed': min_count - current_count
                })
        
        total_nodes = sum(node_counts.values())
        total_rels = sum(rel_counts.values())
        scenario1_check['total_nodes'] = {
            'current': total_nodes,
            'required': requirements['scenario1']['total_nodes_min'],
            'sufficient': total_nodes >= requirements['scenario1']['total_nodes_min']
        }
        scenario1_check['total_relationships'] = {
            'current': total_rels,
            'required': requirements['scenario1']['total_relationships_min'],
            'sufficient': total_rels >= requirements['scenario1']['total_relationships_min']
        }
        
        scenario_checks['scenario1'] = scenario1_check
        
        # 场景2评估
        scenario2_check = {
            'name': requirements['scenario2']['name'],
            'full_tracking_paths': self.results.get('scenario_data', {}).get('full_tracking_paths', 0),
            'required': requirements['scenario2']['full_tracking_paths_min'],
            'passed': self.results.get('scenario_data', {}).get('full_tracking_paths', 0) >= requirements['scenario2']['full_tracking_paths_min']
        }
        scenario_checks['scenario2'] = scenario2_check
        
        # 场景3评估
        scenario3_check = {
            'name': requirements['scenario3']['name'],
            'impact_paths': self.results.get('scenario_data', {}).get('impact_paths', 0),
            'required': requirements['scenario3']['impact_paths_min'],
            'passed': self.results.get('scenario_data', {}).get('impact_paths', 0) >= requirements['scenario3']['impact_paths_min']
        }
        scenario_checks['scenario3'] = scenario3_check
        
        # 场景4评估
        tech_stacks = node_counts.get('TechnologyStack', 0)
        tech_components = node_counts.get('TechnologyComponent', 0)
        scenario4_check = {
            'name': requirements['scenario4']['name'],
            'technology_stacks': {
                'current': tech_stacks,
                'required': requirements['scenario4']['technology_stacks_min'],
                'sufficient': tech_stacks >= requirements['scenario4']['technology_stacks_min']
            },
            'technology_components': {
                'current': tech_components,
                'required': requirements['scenario4']['technology_components_min'],
                'sufficient': tech_components >= requirements['scenario4']['technology_components_min']
            },
            'passed': (tech_stacks >= requirements['scenario4']['technology_stacks_min'] and
                      tech_components >= requirements['scenario4']['technology_components_min'])
        }
        scenario_checks['scenario4'] = scenario4_check
        
        self.results['scenario_checks'] = scenario_checks
        
        # 计算总体通过率
        passed_scenarios = sum(1 for check in scenario_checks.values() if check.get('passed', False))
        total_scenarios = len(scenario_checks)
        
        self.results['summary'] = {
            'total_scenarios': total_scenarios,
            'passed_scenarios': passed_scenarios,
            'pass_rate': f"{passed_scenarios}/{total_scenarios}",
            'all_passed': passed_scenarios == total_scenarios
        }
        
        return scenario_checks
    
    def generate_report(self) -> str:
        """生成检查报告"""
        report = []
        report.append("# Neo4j图数据库演示数据需求检查报告\n")
        report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**图数据库服务器**: {self.neo4j_server['host']}\n")
        report.append("---\n\n")
        
        # 节点统计
        report.append("## 1. 节点统计\n\n")
        node_counts = self.results.get('node_counts', {})
        report.append("| 节点类型 | 当前数量 | 最少需要 | 状态 |\n")
        report.append("|---------|---------|---------|------|\n")
        
        requirements = {
            'Organization': 1, 'Department': 2, 'Team': 3,
            'BusinessProcess': 3, 'BusinessCapability': 4, 'BusinessService': 2,
            'ApplicationSystem': 4, 'ApplicationService': 3,
            'DataEntity': 4, 'DataModel': 2, 'DataFlow': 2,
            'TechnologyComponent': 5, 'TechnologyStack': 2, 'Infrastructure': 2
        }
        
        for node_type, min_count in requirements.items():
            current = node_counts.get(node_type, 0)
            status = "✅" if current >= min_count else "⚠️"
            report.append(f"| {node_type} | {current} | {min_count} | {status} |\n")
        
        total_nodes = sum(node_counts.values())
        report.append(f"\n**总节点数**: {total_nodes} (最少需要: 33)\n\n")
        
        # 关系统计
        report.append("## 2. 关系统计\n\n")
        rel_counts = self.results.get('relationship_counts', {})
        report.append("| 关系类型 | 当前数量 | 最少需要 | 状态 |\n")
        report.append("|---------|---------|---------|------|\n")
        
        rel_requirements = {
            'BELONGS_TO': 5, 'HAS_TEAM': 3,
            'SUPPORTS': 4, 'USES': 5,
            'PROVIDES': 3, 'STORES': 4,
            'USES_TECH': 4, 'DEPLOYS_ON': 3,
            'TRANSFORMS': 2, 'CONTAINS': 4
        }
        
        for rel_type, min_count in rel_requirements.items():
            current = rel_counts.get(rel_type, 0)
            status = "✅" if current >= min_count else "⚠️"
            report.append(f"| {rel_type} | {current} | {min_count} | {status} |\n")
        
        total_rels = sum(rel_counts.values())
        report.append(f"\n**总关系数**: {total_rels} (最少需要: 37)\n\n")
        
        # 场景检查
        report.append("## 3. 演示场景检查\n\n")
        scenario_checks = self.results.get('scenario_checks', {})
        
        for scenario_id, check in scenario_checks.items():
            status = "✅ 通过" if check.get('passed', False) else "⚠️ 不满足"
            report.append(f"### {check.get('name', scenario_id)}\n\n")
            report.append(f"- **状态**: {status}\n")
            
            if scenario_id == 'scenario1':
                if check.get('missing_nodes'):
                    report.append("- **缺失节点**:\n")
                    for missing in check['missing_nodes']:
                        report.append(f"  - {missing['type']}: 当前 {missing['current']}, 需要 {missing['required']}, 缺少 {missing['needed']}\n")
                
                if check.get('missing_relationships'):
                    report.append("- **缺失关系**:\n")
                    for missing in check['missing_relationships']:
                        report.append(f"  - {missing['type']}: 当前 {missing['current']}, 需要 {missing['required']}, 缺少 {missing['needed']}\n")
            
            elif scenario_id == 'scenario2':
                report.append(f"- **完整追踪链**: {check.get('full_tracking_paths', 0)} 条 (需要: {check.get('required', 1)})\n")
            
            elif scenario_id == 'scenario3':
                report.append(f"- **影响分析链**: {check.get('impact_paths', 0)} 条 (需要: {check.get('required', 1)})\n")
            
            elif scenario_id == 'scenario4':
                report.append(f"- **技术栈**: {check.get('technology_stacks', {}).get('current', 0)} 个 (需要: {check.get('technology_stacks', {}).get('required', 2)})\n")
                report.append(f"- **技术组件**: {check.get('technology_components', {}).get('current', 0)} 个 (需要: {check.get('technology_components', {}).get('required', 5)})\n")
            
            report.append("\n")
        
        # 数据质量
        report.append("## 4. 数据质量检查\n\n")
        data_quality = self.results.get('data_quality', {})
        orphan_nodes = data_quality.get('orphan_nodes', 0)
        missing_props = data_quality.get('missing_properties', {})
        
        report.append(f"- **孤立节点**: {orphan_nodes} 个\n")
        if missing_props:
            report.append("- **缺失属性节点**:\n")
            for node_type, count in missing_props.items():
                if count > 0:
                    report.append(f"  - {node_type}: {count} 个节点缺少name属性\n")
        
        report.append("\n")
        
        # 总结
        report.append("## 5. 总结\n\n")
        summary = self.results.get('summary', {})
        report.append(f"- **总场景数**: {summary.get('total_scenarios', 0)}\n")
        report.append(f"- **通过场景数**: {summary.get('passed_scenarios', 0)}\n")
        report.append(f"- **通过率**: {summary.get('pass_rate', '0/0')}\n")
        
        if summary.get('all_passed', False):
            report.append("\n### ✅ 所有演示场景数据充足\n\n")
            report.append("Neo4j数据满足所有演示需求，可以进行完整演示。\n")
        else:
            report.append("\n### ⚠️ 部分演示场景数据不足\n\n")
            report.append("需要生成缺失的数据以满足演示需求。\n")
        
        return ''.join(report)
    
    def run(self):
        """运行完整检查流程"""
        logger.info("=" * 60)
        logger.info("开始Neo4j演示数据需求检查")
        logger.info("=" * 60)
        
        # 检查Neo4j数据
        self.check_neo4j_data()
        
        # 评估演示需求
        self.evaluate_demo_requirements()
        
        # 生成报告
        report = self.generate_report()
        
        # 保存报告
        report_file = project_root / 'Neo4j演示数据需求检查报告.md'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # 保存JSON结果
        json_file = project_root / 'Neo4j演示数据检查结果.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info("=" * 60)
        logger.info("Neo4j演示数据检查完成")
        logger.info(f"报告已保存到: {report_file}")
        logger.info(f"JSON结果已保存到: {json_file}")
        logger.info("=" * 60)
        
        return self.results


if __name__ == '__main__':
    checker = Neo4jDemoChecker()
    results = checker.run()
    print("\n检查完成！请查看生成的报告文件。")


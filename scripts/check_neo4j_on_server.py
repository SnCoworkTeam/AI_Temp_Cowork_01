#!/usr/bin/env python3
"""
在服务器上执行的Neo4j演示数据需求检查脚本
"""

from neo4j import GraphDatabase
import json
import os
import sys

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
            try:
                query = f"MATCH (n:{node_type}) RETURN count(n) as count"
                result = session.run(query)
                count = result.single()['count']
                result_data['node_counts'][node_type] = count
            except Exception as e:
                result_data['node_counts'][node_type] = 0
        
        # 2. 统计各类型关系数量
        relationship_types = [
            'BELONGS_TO', 'HAS_TEAM',
            'SUPPORTS', 'USES', 'CONTAINS',
            'PROVIDES', 'CONSUMES', 'EXPOSES',
            'STORES', 'TRANSFORMS',
            'USES_TECH', 'DEPLOYS_ON'
        ]
        
        for rel_type in relationship_types:
            try:
                query = f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count"
                result = session.run(query)
                count = result.single()['count']
                result_data['relationship_counts'][rel_type] = count
            except Exception as e:
                result_data['relationship_counts'][rel_type] = 0
        
        # 3. 检查场景1: 组织架构层级
        try:
            org_query = "MATCH path = (org:Organization)-[:BELONGS_TO*]->(dept:Department)-[:HAS_TEAM]->(team:Team) RETURN count(path) as path_count"
            result = session.run(org_query)
            result_data['scenario_data']['org_hierarchy_paths'] = result.single()['path_count']
        except:
            result_data['scenario_data']['org_hierarchy_paths'] = 0
        
        # 4. 检查场景2: 完整追踪链（业务流程到技术组件）
        try:
            tracking_query = "MATCH path = (bp:BusinessProcess)-[:USES]->(bc:BusinessCapability)-[:SUPPORTS]->(asys:ApplicationSystem)-[:STORES]->(de:DataEntity)-[:USES_TECH]->(tc:TechnologyComponent) RETURN count(path) as path_count"
            result = session.run(tracking_query)
            result_data['scenario_data']['full_tracking_paths'] = result.single()['path_count']
        except:
            result_data['scenario_data']['full_tracking_paths'] = 0
        
        # 5. 检查场景3: 影响分析链（技术组件到业务流程）
        try:
            impact_query = "MATCH path = (tc:TechnologyComponent)<-[:USES_TECH]-(asys:ApplicationSystem)-[:SUPPORTS]->(bp:BusinessProcess) RETURN count(path) as path_count"
            result = session.run(impact_query)
            result_data['scenario_data']['impact_paths'] = result.single()['path_count']
        except:
            result_data['scenario_data']['impact_paths'] = 0
        
        # 6. 检查孤立节点
        try:
            orphan_query = "MATCH (n) WHERE NOT (n)--() RETURN count(n) as count"
            result = session.run(orphan_query)
            result_data['orphan_nodes'] = result.single()['count']
        except:
            result_data['orphan_nodes'] = 0
        
        # 7. 检查节点属性完整性
        node_props_check = {}
        for node_type in ['Organization', 'BusinessProcess', 'ApplicationSystem']:
            try:
                query = f"MATCH (n:{node_type}) WHERE n.name IS NULL OR n.name = '' RETURN count(n) as count"
                result = session.run(query)
                node_props_check[node_type] = result.single()['count']
            except:
                node_props_check[node_type] = 0
        result_data['missing_properties'] = node_props_check
        
        # 8. 检查所有节点和关系的总数
        try:
            total_nodes_query = "MATCH (n) RETURN count(n) as count"
            result = session.run(total_nodes_query)
            result_data['total_nodes'] = result.single()['count']
        except:
            result_data['total_nodes'] = 0
        
        try:
            total_rels_query = "MATCH ()-[r]->() RETURN count(r) as count"
            result = session.run(total_rels_query)
            result_data['total_relationships'] = result.single()['count']
        except:
            result_data['total_relationships'] = 0
    
    driver.close()
    print(json.dumps(result_data, ensure_ascii=False))
    
except Exception as e:
    result_data = {'status': 'error', 'error': str(e)}
    print(json.dumps(result_data, ensure_ascii=False))
    sys.exit(1)


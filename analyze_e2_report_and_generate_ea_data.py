"""
分析E2现状调研报告，生成企业架构数据
"""
import sys
import os
import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
import re

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "database"))
sys.path.insert(0, str(Path(__file__).parent / "shared_libs"))

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("警告: python-docx未安装，尝试使用其他方法")
    try:
        import zipfile
        import xml.etree.ElementTree as ET
        DOCX_AVAILABLE = True
        USE_ZIP_METHOD = True
    except:
        USE_ZIP_METHOD = False

import psycopg2
from psycopg2.extras import execute_values

# 数据库配置 - 支持环境变量覆盖
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'ai_platform'),
    'user': os.getenv('DB_USER', 'ai_user'),
    'password': os.getenv('DB_PASSWORD', 'ai_password')
}

class E2ReportAnalyzer:
    """E2报告分析器"""
    
    def __init__(self, doc_path: str):
        self.doc_path = doc_path
        self.content = ""
        self.sections = {}
        
    def extract_text(self) -> str:
        """提取文档文本"""
        if not DOCX_AVAILABLE:
            raise ImportError("无法读取Word文档，请安装python-docx: pip install python-docx")
        
        try:
            doc = Document(self.doc_path)
            paragraphs = []
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    paragraphs.append(text)
            self.content = "\n".join(paragraphs)
            return self.content
        except Exception as e:
            print(f"读取文档失败: {e}")
            raise
    
    def parse_sections(self):
        """解析文档章节"""
        lines = self.content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            # 检测章节标题（通常是大写、加粗或特定格式）
            if self._is_section_header(line):
                if current_section:
                    self.sections[current_section] = '\n'.join(current_content)
                current_section = line.strip()
                current_content = []
            else:
                if current_section:
                    current_content.append(line)
        
        if current_section:
            self.sections[current_section] = '\n'.join(current_content)
    
    def _is_section_header(self, line: str) -> bool:
        """判断是否是章节标题"""
        line = line.strip()
        if not line:
            return False
        
        # 检查是否是标题格式
        patterns = [
            r'^第[一二三四五六七八九十\d]+[章节部分]',  # 第X章
            r'^\d+[\.\s]+[A-Z\u4e00-\u9fa5]',  # 数字编号
            r'^[一二三四五六七八九十]+[、\.]',  # 中文编号
            r'^[A-Z][A-Z\s]+$',  # 全大写
        ]
        
        for pattern in patterns:
            if re.match(pattern, line):
                return True
        
        # 检查长度和格式
        if len(line) < 50 and (line.isupper() or '系统' in line or '流程' in line or '架构' in line):
            return True
        
        return False
    
    def extract_business_processes(self) -> List[Dict[str, Any]]:
        """提取业务流程"""
        processes = []
        
        # 搜索业务流程相关关键词
        keywords = ['采购', '销售', '库存', '生产', '财务', '订单', '发货', '收货', '付款', '收款']
        
        for keyword in keywords:
            # 在文档中查找包含关键词的段落
            pattern = rf'{keyword}[流程|过程|业务|管理]'
            matches = re.finditer(pattern, self.content, re.IGNORECASE)
            
            for match in matches:
                # 提取上下文
                start = max(0, match.start() - 100)
                end = min(len(self.content), match.end() + 200)
                context = self.content[start:end]
                
                # 提取流程名称
                process_name = self._extract_name(context, keyword)
                if process_name:
                    processes.append({
                        'name': process_name,
                        'description': context[:500],
                        'classification': '核心流程',
                        'status': 'active'
                    })
        
        # 去重
        seen = set()
        unique_processes = []
        for p in processes:
            if p['name'] not in seen:
                seen.add(p['name'])
                unique_processes.append(p)
        
        return unique_processes[:20]  # 限制数量
    
    def extract_application_systems(self) -> List[Dict[str, Any]]:
        """提取应用系统"""
        systems = []
        
        # 搜索系统相关关键词
        system_keywords = ['SAP', 'ERP', 'CRM', '系统', '平台', '模块', '功能']
        
        for keyword in system_keywords:
            pattern = rf'{keyword}[A-Za-z0-9\s]*系统|系统[A-Za-z0-9\s]*{keyword}'
            matches = re.finditer(pattern, self.content, re.IGNORECASE)
            
            for match in matches:
                context_start = max(0, match.start() - 50)
                context_end = min(len(self.content), match.end() + 200)
                context = self.content[context_start:context_end]
                
                system_name = self._extract_system_name(context, match.group())
                if system_name and len(system_name) < 100:
                    systems.append({
                        'name': system_name,
                        'description': context[:500],
                        'system_type': self._classify_system_type(system_name),
                        'status': 'active'
                    })
        
        # 去重
        seen = set()
        unique_systems = []
        for s in systems:
            if s['name'] not in seen:
                seen.add(s['name'])
                unique_systems.append(s)
        
        return unique_systems[:15]
    
    def extract_data_entities(self) -> List[Dict[str, Any]]:
        """提取数据实体"""
        entities = []
        
        # 搜索数据实体关键词
        entity_keywords = ['订单', '物料', '供应商', '客户', '库存', '发票', '合同', '主数据']
        
        for keyword in entity_keywords:
            pattern = rf'{keyword}[数据|信息|实体|主数据]|主数据.*{keyword}'
            matches = re.finditer(pattern, self.content, re.IGNORECASE)
            
            for match in matches:
                context_start = max(0, match.start() - 50)
                context_end = min(len(self.content), match.end() + 200)
                context = self.content[context_start:context_end]
                
                entity_name = self._extract_name(context, keyword)
                if entity_name:
                    entities.append({
                        'name': entity_name,
                        'description': context[:500],
                        'entity_type': '业务实体'
                    })
        
        # 去重
        seen = set()
        unique_entities = []
        for e in entities:
            if e['name'] not in seen:
                seen.add(e['name'])
                unique_entities.append(e)
        
        return unique_entities[:20]
    
    def extract_technology_components(self) -> List[Dict[str, Any]]:
        """提取技术组件"""
        components = []
        
        # 技术组件关键词
        tech_keywords = ['数据库', '服务器', '中间件', '接口', 'API', '网络', '存储', '备份']
        
        for keyword in tech_keywords:
            pattern = rf'{keyword}[A-Za-z0-9\s]*|技术[A-Za-z0-9\s]*{keyword}'
            matches = re.finditer(pattern, self.content, re.IGNORECASE)
            
            for match in matches:
                context_start = max(0, match.start() - 50)
                context_end = min(len(self.content), match.end() + 200)
                context = self.content[context_start:context_end]
                
                component_name = self._extract_name(context, keyword)
                if component_name:
                    components.append({
                        'name': component_name,
                        'description': context[:500],
                        'component_type': self._classify_component_type(keyword)
                    })
        
        # 去重
        seen = set()
        unique_components = []
        for c in components:
            if c['name'] not in seen:
                seen.add(c['name'])
                unique_components.append(c)
        
        return unique_components[:15]
    
    def _extract_name(self, context: str, keyword: str) -> Optional[str]:
        """从上下文中提取名称"""
        # 尝试提取包含关键词的短语
        pattern = rf'[^。，；\n]*{keyword}[^。，；\n]*'
        matches = re.findall(pattern, context)
        if matches:
            name = matches[0].strip()
            # 清理名称
            name = re.sub(r'\s+', '', name)
            if 5 <= len(name) <= 50:
                return name
        return None
    
    def _extract_system_name(self, context: str, match: str) -> Optional[str]:
        """提取系统名称"""
        # 尝试提取系统名称
        patterns = [
            rf'{match}',
            rf'[A-Z]+系统',
            rf'[A-Z]+平台',
        ]
        
        for pattern in patterns:
            found = re.search(pattern, context, re.IGNORECASE)
            if found:
                name = found.group().strip()
                if 3 <= len(name) <= 50:
                    return name
        
        return match.strip() if match else None
    
    def _classify_system_type(self, name: str) -> str:
        """分类系统类型"""
        name_lower = name.lower()
        if 'erp' in name_lower or 'sap' in name_lower:
            return 'ERP'
        elif 'crm' in name_lower:
            return 'CRM'
        elif 'scm' in name_lower or '供应链' in name:
            return 'SCM'
        elif 'wms' in name_lower or '仓储' in name:
            return 'WMS'
        else:
            return '业务系统'
    
    def _classify_component_type(self, keyword: str) -> str:
        """分类组件类型"""
        type_mapping = {
            '数据库': '数据库',
            '服务器': '服务器',
            '中间件': '中间件',
            '接口': '接口',
            'API': '接口',
            '网络': '网络',
            '存储': '存储',
            '备份': '存储'
        }
        return type_mapping.get(keyword, '基础设施')
    
    def analyze(self) -> Dict[str, Any]:
        """分析文档并提取企业架构信息"""
        print("=" * 60)
        print("分析E2现状调研报告")
        print("=" * 60)
        
        # 提取文本
        print("\n1. 提取文档文本...")
        self.extract_text()
        print(f"   文档长度: {len(self.content)} 字符")
        
        # 解析章节
        print("\n2. 解析文档章节...")
        self.parse_sections()
        print(f"   发现 {len(self.sections)} 个章节")
        
        # 提取企业架构信息
        print("\n3. 提取业务流程...")
        processes = self.extract_business_processes()
        print(f"   提取到 {len(processes)} 个业务流程")
        
        print("\n4. 提取应用系统...")
        systems = self.extract_application_systems()
        print(f"   提取到 {len(systems)} 个应用系统")
        
        print("\n5. 提取数据实体...")
        entities = self.extract_data_entities()
        print(f"   提取到 {len(entities)} 个数据实体")
        
        print("\n6. 提取技术组件...")
        components = self.extract_technology_components()
        print(f"   提取到 {len(components)} 个技术组件")
        
        return {
            'processes': processes,
            'systems': systems,
            'entities': entities,
            'components': components
        }


class EADataGenerator:
    """企业架构数据生成器"""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.conn = None
    
    def connect(self):
        """连接数据库"""
        self.conn = psycopg2.connect(**self.db_config)
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
    
    def insert_business_processes(self, processes: List[Dict[str, Any]]):
        """插入业务流程"""
        if not processes:
            return
        
        cur = self.conn.cursor()
        try:
            for process in processes:
                cur.execute("""
                    INSERT INTO business_processes 
                    (id, name, description, classification, status, meta_data)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    str(uuid.uuid4()),
                    process['name'],
                    process.get('description', ''),
                    process.get('classification', '核心流程'),
                    process.get('status', 'active'),
                    json.dumps(process.get('meta_data', {}), ensure_ascii=False)
                ))
            
            self.conn.commit()
            print(f"   [OK] 插入 {len(processes)} 个业务流程")
        except Exception as e:
            self.conn.rollback()
            print(f"   [ERROR] 插入业务流程失败: {e}")
        finally:
            cur.close()
    
    def insert_application_systems(self, systems: List[Dict[str, Any]]):
        """插入应用系统"""
        if not systems:
            return
        
        cur = self.conn.cursor()
        try:
            for system in systems:
                cur.execute("""
                    INSERT INTO application_systems 
                    (id, name, description, system_type, status, meta_data)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    str(uuid.uuid4()),
                    system['name'],
                    system.get('description', ''),
                    system.get('system_type', '业务系统'),
                    system.get('status', 'active'),
                    json.dumps(system.get('meta_data', {}), ensure_ascii=False)
                ))
            
            self.conn.commit()
            print(f"   [OK] 插入 {len(systems)} 个应用系统")
        except Exception as e:
            self.conn.rollback()
            print(f"   [ERROR] 插入应用系统失败: {e}")
        finally:
            cur.close()
    
    def insert_data_entities(self, entities: List[Dict[str, Any]]):
        """插入数据实体"""
        if not entities:
            return
        
        cur = self.conn.cursor()
        try:
            for entity in entities:
                cur.execute("""
                    INSERT INTO data_entities 
                    (id, name, description, entity_type, meta_data)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    str(uuid.uuid4()),
                    entity['name'],
                    entity.get('description', ''),
                    entity.get('entity_type', '业务实体'),
                    json.dumps(entity.get('meta_data', {}), ensure_ascii=False)
                ))
            
            self.conn.commit()
            print(f"   [OK] 插入 {len(entities)} 个数据实体")
        except Exception as e:
            self.conn.rollback()
            print(f"   [ERROR] 插入数据实体失败: {e}")
        finally:
            cur.close()
    
    def insert_technology_components(self, components: List[Dict[str, Any]]):
        """插入技术组件"""
        if not components:
            return
        
        cur = self.conn.cursor()
        try:
            for component in components:
                cur.execute("""
                    INSERT INTO technology_components 
                    (id, name, description, component_type, meta_data)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    str(uuid.uuid4()),
                    component['name'],
                    component.get('description', ''),
                    component.get('component_type', '基础设施'),
                    json.dumps(component.get('meta_data', {}), ensure_ascii=False)
                ))
            
            self.conn.commit()
            print(f"   [OK] 插入 {len(components)} 个技术组件")
        except Exception as e:
            self.conn.rollback()
            print(f"   [ERROR] 插入技术组件失败: {e}")
        finally:
            cur.close()
    
    def generate_relationships(self):
        """生成架构关系"""
        cur = self.conn.cursor()
        try:
            # 获取所有业务流程和应用系统
            cur.execute("SELECT id, name FROM business_processes LIMIT 10")
            processes = cur.fetchall()
            
            cur.execute("SELECT id, name FROM application_systems LIMIT 10")
            systems = cur.fetchall()
            
            # 创建关系：业务流程 -> 应用系统
            relationships = []
            for i, (process_id, process_name) in enumerate(processes):
                if i < len(systems):
                    system_id, system_name = systems[i]
                    relationships.append((
                        str(uuid.uuid4()),
                        str(process_id),
                        'business_process',
                        str(system_id),
                        'application_system',
                        'implements',
                        f'{process_name}由{system_name}实现'
                    ))
            
            if relationships:
                execute_values(
                    cur,
                    """
                    INSERT INTO architecture_relationships 
                    (id, source_id, source_type, target_id, target_type, relationship_type, description)
                    VALUES %s
                    ON CONFLICT DO NOTHING
                    """,
                    relationships
                )
                self.conn.commit()
                print(f"   [OK] 生成 {len(relationships)} 个架构关系")
        except Exception as e:
            self.conn.rollback()
            print(f"   [ERROR] 生成架构关系失败: {e}")
        finally:
            cur.close()


def main():
    """主函数"""
    doc_path = "E2现状调研报告文档_ZHTJJ_MM_v1.5.docx"
    
    if not os.path.exists(doc_path):
        print(f"错误: 文件不存在: {doc_path}")
        return
    
    try:
        # 分析文档
        analyzer = E2ReportAnalyzer(doc_path)
        ea_data = analyzer.analyze()
        
        # 生成数据
        print("\n" + "=" * 60)
        print("生成企业架构数据")
        print("=" * 60)
        
        generator = EADataGenerator(DB_CONFIG)
        generator.connect()
        
        try:
            print("\n插入数据到数据库...")
            generator.insert_business_processes(ea_data['processes'])
            generator.insert_application_systems(ea_data['systems'])
            generator.insert_data_entities(ea_data['entities'])
            generator.insert_technology_components(ea_data['components'])
            
            print("\n生成架构关系...")
            generator.generate_relationships()
            
            print("\n" + "=" * 60)
            print("完成！")
            print("=" * 60)
            print(f"\n生成的数据:")
            print(f"  - 业务流程: {len(ea_data['processes'])} 个")
            print(f"  - 应用系统: {len(ea_data['systems'])} 个")
            print(f"  - 数据实体: {len(ea_data['entities'])} 个")
            print(f"  - 技术组件: {len(ea_data['components'])} 个")
            
        finally:
            generator.close()
    
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()


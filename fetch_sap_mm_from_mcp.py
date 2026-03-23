#!/usr/bin/env python3
"""
从SAP OData MCP服务获取SAP MM数据并构建元数据
"""
import requests
import json
import sys
import time
from typing import List, Dict, Any, Optional

# 配置
METADATA_SERVICE_URL = "http://localhost:8005/api/business-entities"
KNOWLEDGE_SERVICE_URL = "http://localhost:8003/api/knowledge/documents"
MCP_SERVER_URL = "http://localhost:3001"  # SAP OData MCP服务URL
MCP_ENDPOINT = f"{MCP_SERVER_URL}/mcp"

# SAP MM核心表定义（基于SAP标准）
SAP_MM_TABLES = {
    "MARA": {
        "name": "material",
        "display_name": "物料主数据",
        "description": "SAP MM模块的物料主数据表，存储物料的基本信息",
        "key_fields": ["MATNR", "MAKTX", "MEINS", "MTART", "MATKL"],
        "category": "master_data",
        "odata_service": "MMIM_MATERIAL_DATA_SRV"
    },
    "LFA1": {
        "name": "vendor",
        "display_name": "供应商主数据",
        "description": "SAP MM模块的供应商主数据表，存储供应商的基本信息",
        "key_fields": ["LIFNR", "NAME1", "ORT01", "LAND1"],
        "category": "master_data",
        "odata_service": None  # 需要查找对应的OData服务
    },
    "EKKO": {
        "name": "purchase_order_header",
        "display_name": "采购订单抬头",
        "description": "SAP MM模块的采购订单抬头表",
        "key_fields": ["EBELN", "LIFNR", "BEDAT", "ZTERM"],
        "category": "transaction_data",
        "odata_service": "C_PURCHASEORDER_FS_SRV"
    },
    "EKPO": {
        "name": "purchase_order_item",
        "display_name": "采购订单行项目",
        "description": "SAP MM模块的采购订单行项目表",
        "key_fields": ["EBELN", "EBELP", "MATNR", "MENGE", "NETPR"],
        "category": "transaction_data",
        "odata_service": "C_PURCHASEORDER_FS_SRV"
    },
    "EBAN": {
        "name": "purchase_requisition",
        "display_name": "采购申请",
        "description": "SAP MM模块的采购申请表",
        "key_fields": ["BANFN", "BNFPO", "MATNR", "MENGE"],
        "category": "transaction_data",
        "odata_service": None
    },
    "MARD": {
        "name": "material_storage_location",
        "display_name": "物料库存地点视图",
        "description": "SAP MM模块的物料库存地点视图表",
        "key_fields": ["MATNR", "WERKS", "LGORT", "LABST"],
        "category": "master_data",
        "odata_service": "MMIM_STOCKINDATERANGE_SRV"
    },
    "MKPF": {
        "name": "material_document_header",
        "display_name": "物料凭证抬头",
        "description": "SAP MM模块的物料凭证抬头表",
        "key_fields": ["MBLNR", "MJAHR", "BUDAT", "BLART"],
        "category": "transaction_data",
        "odata_service": None
    },
    "MSEG": {
        "name": "material_document_item",
        "display_name": "物料凭证行项目",
        "description": "SAP MM模块的物料凭证行项目表",
        "key_fields": ["MBLNR", "MJAHR", "ZEILE", "BWART", "MENGE"],
        "category": "transaction_data",
        "odata_service": None
    }
}

class SAPMCPClient:
    """SAP OData MCP客户端"""
    
    def __init__(self, base_url: str = MCP_SERVER_URL):
        self.base_url = base_url
        self.mcp_endpoint = f"{base_url}/mcp"
        self.session_id: Optional[str] = None
        self.http_client = requests.Session()
        self.http_client.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream'
        })
    
    def initialize(self) -> bool:
        """初始化MCP会话"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "sap-mm-metadata-builder",
                        "version": "1.0.0"
                    }
                }
            }
            
            response = self.http_client.post(self.mcp_endpoint, json=payload, timeout=30)
            response.raise_for_status()
            
            # 从响应头或响应体中获取session_id
            if 'mcp-session-id' in response.headers:
                self.session_id = response.headers['mcp-session-id']
            else:
                result = response.json()
                if 'result' in result and 'sessionId' in result['result']:
                    self.session_id = result['result']['sessionId']
            
            if self.session_id:
                self.http_client.headers['mcp-session-id'] = self.session_id
                print(f"✅ MCP会话初始化成功: {self.session_id[:20]}...")
                return True
            else:
                print("⚠️  未获取到session_id，尝试继续...")
                return True  # 某些实现可能不需要session_id
                
        except Exception as e:
            print(f"❌ MCP会话初始化失败: {e}")
            return False
    
    def search_services_rest(self, query: str = "material") -> List[Dict[str, Any]]:
        """使用REST API搜索SAP OData服务（备用方案）"""
        try:
            # 使用REST API获取所有服务
            response = self.http_client.get(f"{self.base_url}/api/services", timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if result.get('success') and 'services' in result:
                all_services = result['services']
                # 简单过滤包含query的服务
                if query:
                    filtered = [s for s in all_services if query.lower() in s.get('name', '').lower() or 
                               query.lower() in s.get('description', '').lower()]
                    return filtered[:20]
                return all_services[:20]
            
            return []
        except Exception as e:
            print(f"⚠️  REST API搜索服务失败: {e}")
            return []
    
    def search_services(self, query: str = "material", limit: int = 20) -> List[Dict[str, Any]]:
        """搜索SAP OData服务（优先使用MCP，失败则使用REST API）"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "search-sap-services",
                    "arguments": {
                        "query": query,
                        "limit": limit
                    }
                }
            }
            
            response = self.http_client.post(self.mcp_endpoint, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            if 'result' in result and 'content' in result['result']:
                content = result['result']['content']
                if isinstance(content, list):
                    return content
                elif isinstance(content, str):
                    # 尝试解析JSON字符串
                    return json.loads(content)
            
            return []
        except Exception as e:
            print(f"⚠️  MCP搜索服务失败，尝试REST API: {e}")
            # 失败时使用REST API
            return self.search_services_rest(query)
    
    def discover_service_entities_rest(self, service_id: str) -> List[Dict[str, Any]]:
        """使用REST API发现服务的实体（备用方案）"""
        try:
            response = self.http_client.get(
                f"{self.base_url}/api/services/{service_id}/entities",
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('success') and 'entities' in result:
                return result['entities']
            
            return []
        except Exception as e:
            print(f"⚠️  REST API发现实体失败: {e}")
            return []
    
    def discover_service_entities(self, service_id: str) -> List[Dict[str, Any]]:
        """发现服务的实体（优先使用MCP，失败则使用REST API）"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "discover-service-entities",
                    "arguments": {
                        "serviceId": service_id
                    }
                }
            }
            
            response = self.http_client.post(self.mcp_endpoint, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            if 'result' in result and 'content' in result['result']:
                content = result['result']['content']
                if isinstance(content, list):
                    return content
                elif isinstance(content, str):
                    return json.loads(content)
            
            return []
        except Exception as e:
            print(f"⚠️  MCP发现实体失败，尝试REST API: {e}")
            # 失败时使用REST API
            return self.discover_service_entities_rest(service_id)
    
    def get_entity_data(self, service_id: str, entity_name: str, filters: Optional[Dict] = None, top: int = 10) -> List[Dict[str, Any]]:
        """获取实体数据"""
        try:
            arguments = {
                "serviceId": service_id,
                "entityName": entity_name,
                "operation": "read"
            }
            
            if filters:
                arguments["filters"] = filters
            
            payload = {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "execute-entity-operation",
                    "arguments": arguments
                }
            }
            
            response = self.http_client.post(self.mcp_endpoint, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            
            if 'result' in result and 'content' in result['result']:
                content = result['result']['content']
                if isinstance(content, list):
                    return content
                elif isinstance(content, str):
                    data = json.loads(content)
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict) and 'value' in data:
                        return data['value']
            
            return []
        except Exception as e:
            print(f"⚠️  获取实体数据失败: {e}")
            return []

def create_entity_from_table(table_name: str, table_info: Dict[str, Any], mcp_data: Optional[Dict] = None) -> Dict[str, Any]:
    """从SAP表信息创建业务实体"""
    # 根据category映射到正确的entity_type
    # entity_type枚举值: domain, concept, term, glossary, policy, rule
    # 对于SAP MM表，统一使用"concept"
    entity_type = "concept"
    
    entity = {
        "name": table_info["name"],
        "display_name": table_info["display_name"],
        "entity_type": entity_type,
        "description": table_info["description"],
        "business_definition": f"{table_info['display_name']}是{table_info['description']}，用于SAP MM模块的{table_info['category']}管理",
        "metadata": {
            "sap_table": table_name,
            "sap_module": "MM",
            "category": table_info["category"],
            "key_fields": table_info.get("key_fields", []),
            "odata_service": table_info.get("odata_service")
        }
    }
    
    # 如果从MCP获取到数据，补充更多信息
    if mcp_data:
        entity["metadata"]["mcp_data"] = mcp_data
    
    return entity

def create_entities_from_tables(mcp_client: SAPMCPClient) -> List[Dict[str, Any]]:
    """从SAP表定义创建实体列表，并尝试从MCP获取实际数据"""
    entities = []
    
    print("\n=== 从MCP服务获取SAP MM数据 ===\n")
    
    for table_name, table_info in SAP_MM_TABLES.items():
        print(f"处理表: {table_name} ({table_info['display_name']})...")
        
        mcp_data = None
        odata_service = table_info.get("odata_service")
        
        # 如果指定了OData服务，尝试获取数据
        if odata_service:
            try:
                # 发现实体
                entities_list = mcp_client.discover_service_entities(odata_service)
                print(f"  发现 {len(entities_list)} 个实体")
                
                # 尝试获取示例数据
                if entities_list:
                    # 使用第一个实体获取示例数据
                    first_entity = entities_list[0] if isinstance(entities_list[0], dict) else {"name": entities_list[0]}
                    entity_name = first_entity.get("name", str(first_entity))
                    
                    sample_data = mcp_client.get_entity_data(odata_service, entity_name, top=5)
                    if sample_data:
                        mcp_data = {
                            "service": odata_service,
                            "entities": entities_list[:3],  # 只保存前3个实体信息
                            "sample_count": len(sample_data)
                        }
                        print(f"  获取到 {len(sample_data)} 条示例数据")
            except Exception as e:
                print(f"  ⚠️  获取MCP数据失败: {e}")
        
        entity = create_entity_from_table(table_name, table_info, mcp_data)
        entities.append(entity)
        time.sleep(0.5)  # 避免请求过快
    
    return entities

def import_entities(entities: List[Dict[str, Any]]) -> int:
    """批量导入实体"""
    created = 0
    failed = 0
    
    print(f"\n=== 导入 {len(entities)} 个SAP MM实体 ===\n")
    
    for i, entity in enumerate(entities, 1):
        print(f"[{i}/{len(entities)}] 创建: {entity['display_name']}...")
        try:
            response = requests.post(
                METADATA_SERVICE_URL,
                json=entity,
                timeout=10
            )
            if response.status_code in [200, 201]:
                result = response.json()
                entity_id = result.get('id', 'N/A')
                print(f"   ✅ 成功 (ID: {entity_id})")
                created += 1
            elif response.status_code == 409:
                print(f"   ⚠️  已存在")
            else:
                print(f"   ❌ 失败: HTTP {response.status_code} - {response.text[:100]}")
                failed += 1
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            failed += 1
        
        time.sleep(0.3)
    
    print(f"\n=== 导入完成 ===")
    print(f"✅ 成功: {created}")
    print(f"❌ 失败: {failed}")
    
    return created

def main():
    """主函数"""
    print("=" * 60)
    print("SAP MM元数据构建（基于MCP服务和网络数据）")
    print("=" * 60)
    print()
    
    # 初始化MCP客户端
    print("🔌 连接SAP OData MCP服务...")
    mcp_client = SAPMCPClient()
    
    if not mcp_client.initialize():
        print("⚠️  MCP服务连接失败，将使用基础表定义创建实体")
        mcp_client = None
    
    # 从表定义创建实体（可能包含MCP数据）
    print("\n📋 准备SAP MM实体定义...")
    if mcp_client:
        entities = create_entities_from_tables(mcp_client)
    else:
        # 如果没有MCP客户端，使用基础定义
        entities = [create_entity_from_table(tn, ti) for tn, ti in SAP_MM_TABLES.items()]
    
    print(f"   准备了 {len(entities)} 个实体定义\n")
    
    # 导入实体
    created = import_entities(entities)
    
    if created > 0:
        print(f"\n🎉 成功创建了 {created} 个SAP MM实体！")
        print("\n下一步:")
        print("1. 执行本体构建: POST /api/ontology/sap/build")
        print("2. 导入知识库文档: python generate_sap_mm_documents_from_web.py")
    else:
        print("\n⚠️  未创建任何实体，请检查服务状态")

if __name__ == "__main__":
    main()

"""
SAP OData元数据解析器（Python版本）
用于解析OData XML元数据，提取EntitySet、EntityType、Property和NavigationProperty
"""
import xml.etree.ElementTree as ET
import logging
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# SAP和EDM命名空间
SAP_NS = "http://www.sap.com/Protocols/SAPData"
EDM_NS = "http://schemas.microsoft.com/ado/2007/06/edm"


class SAPODataMetadataParser:
    """SAP OData元数据解析器"""
    
    def __init__(self):
        """初始化解析器"""
        # 注册命名空间（用于查找）
        ET.register_namespace('sap', SAP_NS)
        ET.register_namespace('edm', EDM_NS)
    
    def parse_metadata(self, xml_data: str) -> Dict[str, Any]:
        """
        解析OData XML元数据
        
        Args:
            xml_data: OData $metadata XML字符串
            
        Returns:
            解析结果，包含entities、entity_sets_count、entity_types_count
        """
        try:
            root = ET.fromstring(xml_data)
            
            # 提取EntitySet
            entity_sets = self._extract_entity_sets(root, xml_data)
            
            # 提取EntityType
            entity_types = self._extract_entity_types(root, xml_data)
            
            # 匹配EntitySet和EntityType
            entities = self._match_entity_sets_to_types(entity_sets, entity_types)
            
            return {
                "entities": entities,
                "entity_sets_count": len(entity_sets),
                "entity_types_count": len(entity_types),
                "matched_entities_count": len(entities)
            }
        except ET.ParseError as e:
            logger.warning(f"XML parsing error: {e}")
            # 返回空结果而不是抛出异常
            return {
                "entities": [],
                "entity_sets_count": 0,
                "entity_types_count": 0,
                "matched_entities_count": 0,
                "error": f"Invalid XML format: {e}"
            }
        except Exception as e:
            logger.error(f"Failed to parse OData metadata: {e}", exc_info=True)
            return {
                "entities": [],
                "entity_sets_count": 0,
                "entity_types_count": 0,
                "matched_entities_count": 0,
                "error": str(e)
            }
    
    def _extract_entity_sets(self, root: ET.Element, xml_data: str) -> List[Dict]:
        """提取EntitySet定义"""
        entity_sets = []
        
        # 查找EntityContainer
        # 尝试多种命名空间格式
        container = None
        for ns in [EDM_NS, "", "{http://schemas.microsoft.com/ado/2007/06/edm}"]:
            try:
                if ns:
                    container = root.find(f".//{{{ns}}}EntityContainer")
                else:
                    container = root.find(".//EntityContainer")
                if container is not None:
                    break
            except:
                continue
        
        if container is None:
            logger.warning("EntityContainer not found in XML")
            return entity_sets
        
        # 提取EntitySet
        for ns in [EDM_NS, "", "{http://schemas.microsoft.com/ado/2007/06/edm}"]:
            try:
                if ns:
                    entity_set_elements = container.findall(f"{{{ns}}}EntitySet")
                else:
                    entity_set_elements = container.findall("EntitySet")
                
                for entity_set in entity_set_elements:
                    name = entity_set.get("Name")
                    entity_type = entity_set.get("EntityType")
                    
                    if not name or not entity_type:
                        continue
                    
                    # 提取SAP注解（使用正则表达式，因为可能不在属性中）
                    entity_set_data = {
                        "name": name,
                        "entity_type": entity_type,
                        "is_creatable": self._extract_sap_annotation_from_xml(xml_data, "EntitySet", name, "creatable", default="true") == "true",
                        "is_updatable": self._extract_sap_annotation_from_xml(xml_data, "EntitySet", name, "updatable", default="true") == "true",
                        "is_deletable": self._extract_sap_annotation_from_xml(xml_data, "EntitySet", name, "deletable", default="true") == "true",
                        "sap_label": self._extract_sap_annotation_from_xml(xml_data, "EntitySet", name, "label"),
                        "sap_content_version": self._extract_sap_annotation_from_xml(xml_data, "EntitySet", name, "content-version")
                    }
                    entity_sets.append(entity_set_data)
                
                if entity_sets:
                    break
            except Exception as e:
                logger.debug(f"Failed to extract EntitySets with namespace {ns}: {e}")
                continue
        
        return entity_sets
    
    def _extract_entity_types(self, root: ET.Element, xml_data: str) -> List[Dict]:
        """提取EntityType定义"""
        entity_types = []
        
        # 尝试多种命名空间格式
        for ns in [EDM_NS, "", "{http://schemas.microsoft.com/ado/2007/06/edm}"]:
            try:
                if ns:
                    entity_type_elements = root.findall(f".//{{{ns}}}EntityType")
                else:
                    entity_type_elements = root.findall(".//EntityType")
                
                for entity_type in entity_type_elements:
                    name = entity_type.get("Name")
                    if not name:
                        continue
                    
                    # 提取内容（用于解析子元素）
                    content = ET.tostring(entity_type, encoding='unicode')
                    
                    entity_type_data = {
                        "name": name,
                        "full_name": name,  # 简化处理
                        "sap_label": self._extract_sap_annotation_from_xml(xml_data, "EntityType", name, "label"),
                        "properties": self._extract_properties_from_content(content),
                        "keys": self._extract_keys_from_content(content),
                        "navigation_properties": self._extract_navigation_properties_from_content(content)
                    }
                    entity_types.append(entity_type_data)
                
                if entity_types:
                    break
            except Exception as e:
                logger.debug(f"Failed to extract EntityTypes with namespace {ns}: {e}")
                continue
        
        return entity_types
    
    def _extract_properties_from_content(self, content: str) -> List[Dict]:
        """从EntityType内容中提取属性（Property）"""
        properties = []
        
        # 支持多种格式（包括命名空间前缀）：
        # 1. 自闭合标签: <Property .../> 或 <edm:Property .../> 或 <ns0:Property .../>
        # 2. 闭合标签: <Property>...</Property> 或 <edm:Property>...</edm:Property>
        # ET.tostring()会将命名空间转换为edm:, sap:等前缀（如果已注册）或ns0:, ns1:等
        property_patterns = [
            re.compile(r'<(?:edm|ns\d+):Property\s+([^>]*?)/>', re.IGNORECASE),  # 自闭合标签（支持edm:或ns0:等前缀）
            re.compile(r'<(?:edm|ns\d+):Property\s+Name="([^"]+)"[^>]*>([\s\S]*?)</(?:edm|ns\d+):Property>', re.IGNORECASE)  # 闭合标签（支持edm:或ns0:等前缀）
        ]
        
        processed_names = set()  # 避免重复处理
        
        for pattern in property_patterns:
            for match in pattern.finditer(content):
                property_content = match.group(0)
                
                # 提取Name属性
                name_match = re.search(r'Name="([^"]+)"', property_content, re.IGNORECASE)
                if not name_match:
                    continue
                
                name = name_match.group(1)
                if name in processed_names:
                    continue
                processed_names.add(name)
                
                # 提取Type
                type_match = re.search(r'Type="([^"]*)"', property_content, re.IGNORECASE)
                prop_type = type_match.group(1) if type_match else 'Edm.String'
                
                # 提取Nullable
                nullable_match = re.search(r'Nullable="([^"]*)"', property_content, re.IGNORECASE)
                nullable = nullable_match.group(1) == 'true' if nullable_match else True
                
                # 提取MaxLength
                max_length_match = re.search(r'MaxLength="(\d+)"', property_content, re.IGNORECASE)
                max_length = int(max_length_match.group(1)) if max_length_match else None
                
                # 提取Precision
                precision_match = re.search(r'Precision="(\d+)"', property_content, re.IGNORECASE)
                precision = int(precision_match.group(1)) if precision_match else None
                
                # 提取Scale
                scale_match = re.search(r'Scale="(\d+)"', property_content, re.IGNORECASE)
                scale = int(scale_match.group(1)) if scale_match else None
                
                # 提取SAP特定属性（支持多种格式）
                # 格式1: 直接在Property标签属性中（支持sap:label，ET.tostring()后通常保持sap:前缀）
                sap_label_match = re.search(r'sap:label="([^"]*)"', property_content, re.IGNORECASE)
                if not sap_label_match:
                    # 格式2: 在Annotation元素中
                    sap_label_match = re.search(r'<Annotation[^>]*Term="[^"]*sap:label"[^>]*>[\s\S]*?<String[^>]*>([^<]*)</String>', property_content, re.IGNORECASE)
                sap_label = sap_label_match.group(1) if sap_label_match else None
                
                # 提取sapSemantics（支持sap:semantics）
                sap_semantics_match = re.search(r'sap:semantics="([^"]*)"', property_content, re.IGNORECASE)
                if not sap_semantics_match:
                    # 格式2: 在Annotation元素中
                    sap_semantics_match = re.search(r'<Annotation[^>]*Term="[^"]*sap:semantics"[^>]*>[\s\S]*?<String[^>]*>([^<]*)</String>', property_content, re.IGNORECASE)
                sap_semantics = sap_semantics_match.group(1) if sap_semantics_match else None
                
                # 提取sapQuickinfo（支持sap:quickinfo）
                sap_quickinfo_match = re.search(r'sap:quickinfo="([^"]*)"', property_content, re.IGNORECASE)
                if not sap_quickinfo_match:
                    # 格式2: 在Annotation元素中
                    sap_quickinfo_match = re.search(r'<Annotation[^>]*Term="[^"]*sap:quickinfo"[^>]*>[\s\S]*?<String[^>]*>([^<]*)</String>', property_content, re.IGNORECASE)
                sap_quickinfo = sap_quickinfo_match.group(1) if sap_quickinfo_match else None
                
                properties.append({
                    "name": name,
                    "type": prop_type,
                    "nullable": nullable,
                    "max_length": max_length,
                    "precision": precision,
                    "scale": scale,
                    "sap_label": sap_label,
                    "sap_semantics": sap_semantics,
                    "sap_quickinfo": sap_quickinfo
                })
        
        return properties
    
    def _extract_keys_from_content(self, content: str) -> List[str]:
        """从EntityType内容中提取键（Key）"""
        keys = []
        
        # 支持多种PropertyRef格式
        key_patterns = [
            re.compile(r'<PropertyRef\s+Name="([^"]+)"[^>]*/>', re.IGNORECASE),
            re.compile(r'<PropertyRef\s+Name="([^"]+)"[^>]*>', re.IGNORECASE)
        ]
        
        for pattern in key_patterns:
            for match in pattern.finditer(content):
                key_name = match.group(1)
                if key_name not in keys:
                    keys.append(key_name)
        
        return keys
    
    def _extract_navigation_properties_from_content(self, content: str) -> List[Dict]:
        """从EntityType内容中提取导航属性（NavigationProperty）"""
        navigation_properties = []
        
        # 支持自闭合标签和闭合标签，支持edm:或ns0:等命名空间前缀
        nav_prop_patterns = [
            re.compile(r'<(?:edm|ns\d+):NavigationProperty\s+([^>]*?)/>', re.IGNORECASE),  # 自闭合标签
            re.compile(r'<(?:edm|ns\d+):NavigationProperty\s+([^>]*?)>', re.IGNORECASE)  # 闭合标签
        ]
        
        for pattern in nav_prop_patterns:
            for match in pattern.finditer(content):
                nav_prop_content = match.group(0)
                
                # 提取Name
                name_match = re.search(r'Name="([^"]+)"', nav_prop_content, re.IGNORECASE)
                if not name_match:
                    continue
                
                # 提取Type
                type_match = re.search(r'Type="([^"]+)"', nav_prop_content, re.IGNORECASE)
                if not type_match:
                    continue
                
                nav_prop_data = {
                    "name": name_match.group(1),
                    "type": type_match.group(1)
                }
                
                # 提取Relationship（如果存在）
                relationship_match = re.search(r'Relationship="([^"]*)"', nav_prop_content, re.IGNORECASE)
                if relationship_match:
                    nav_prop_data["relationship"] = relationship_match.group(1)
                
                # 提取Partner（如果存在）
                partner_match = re.search(r'Partner="([^"]*)"', nav_prop_content, re.IGNORECASE)
                if partner_match:
                    nav_prop_data["partner"] = partner_match.group(1)
                
                # 提取SAP注解（如果存在）
                sap_label_match = re.search(r'sap:label="([^"]*)"', nav_prop_content, re.IGNORECASE)
                if sap_label_match:
                    nav_prop_data["sap_label"] = sap_label_match.group(1)
                
                navigation_properties.append(nav_prop_data)
        
        return navigation_properties
    
    def _extract_sap_annotation_from_xml(
        self,
        xml_data: str,
        element_type: str,
        element_name: str,
        annotation_name: str,
        default: Optional[str] = None
    ) -> Optional[str]:
        """
        从XML中提取SAP注解
        
        Args:
            xml_data: 完整的XML字符串
            element_type: 元素类型（EntitySet, EntityType等）
            element_name: 元素名称
            annotation_name: 注解名称（如label, semantics）
            default: 默认值
            
        Returns:
            注解值或默认值
        """
        try:
            # 方法1: 从属性中提取（如果存在）
            attr_pattern = rf'<{element_type}[^>]*Name="{re.escape(element_name)}"[^>]*sap:{re.escape(annotation_name)}="([^"]*)"[^>]*>'
            match = re.search(attr_pattern, xml_data, re.IGNORECASE)
            if match:
                return match.group(1)
            
            # 方法2: 从Annotation元素中提取
            # 查找包含该元素的Annotation
            annotation_pattern = rf'<{element_type}[^>]*Name="{re.escape(element_name)}"[^>]*>([\s\S]*?)</{element_type}>'
            element_match = re.search(annotation_pattern, xml_data, re.IGNORECASE)
            if element_match:
                element_content = element_match.group(1)
                # 查找Annotation元素
                annotation_regex = rf'<Annotation[^>]*Term="[^"]*sap:{re.escape(annotation_name)}"[^>]*>'
                if re.search(annotation_regex, element_content, re.IGNORECASE):
                    # 提取String或Bool值
                    string_match = re.search(r'<String[^>]*>([^<]*)</String>', element_content, re.IGNORECASE)
                    if string_match:
                        return string_match.group(1)
                    bool_match = re.search(r'<Bool[^>]*>([^<]*)</Bool>', element_content, re.IGNORECASE)
                    if bool_match:
                        return bool_match.group(1)
            
            return default
        except Exception as e:
            logger.debug(f"Failed to extract SAP annotation {annotation_name} for {element_name}: {e}")
            return default
    
    def _match_entity_sets_to_types(
        self,
        entity_sets: List[Dict],
        entity_types: List[Dict]
    ) -> List[Dict]:
        """匹配EntitySet和EntityType"""
        entities = []
        entity_type_map = {et["name"]: et for et in entity_types}
        
        for entity_set in entity_sets:
            entity_type_name = entity_set["entity_type"]
            
            # 尝试精确匹配
            entity_type = entity_type_map.get(entity_type_name)
            
            # 尝试去掉命名空间匹配
            if not entity_type:
                simple_name = entity_type_name.split(".")[-1]
                entity_type = entity_type_map.get(simple_name)
            
            # 尝试去掉Type后缀匹配
            if not entity_type:
                base_name = simple_name.replace("Type", "")
                entity_type = entity_type_map.get(base_name)
            
            if entity_type:
                entity = {
                    "name": entity_set["name"],
                    "type": entity_type["name"],
                    "full_type": entity_type["full_name"],
                    "is_creatable": entity_set["is_creatable"],
                    "is_updatable": entity_set["is_updatable"],
                    "is_deletable": entity_set["is_deletable"],
                    "sap_label": entity_set["sap_label"] or entity_type["sap_label"],
                    "properties": entity_type["properties"],
                    "keys": entity_type["keys"],
                    "navigation_properties": entity_type["navigation_properties"]
                }
                entities.append(entity)
            else:
                logger.warning(f"EntityType not found for EntitySet: {entity_set['name']} (type: {entity_type_name})")
        
        return entities


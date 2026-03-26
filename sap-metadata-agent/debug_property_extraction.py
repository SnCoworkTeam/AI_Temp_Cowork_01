"""调试属性提取问题"""
import sys
import xml.etree.ElementTree as ET
import re
from pathlib import Path

agent_path = Path(__file__).parent
sys.path.insert(0, str(agent_path))

xml_data = '''<?xml version="1.0" encoding="utf-8"?>
<edmx:Edmx xmlns:edmx="http://schemas.microsoft.com/ado/2007/06/edmx" Version="4.0">
  <edmx:DataServices>
    <Schema xmlns="http://schemas.microsoft.com/ado/2007/06/edm" 
            xmlns:sap="http://www.sap.com/Protocols/SAPData"
            Namespace="com.sap.gateway.srvd.a2x.api_glaccount.v0001">
      <EntityContainer Name="API_GLACCOUNT_SRV_Entities">
        <EntitySet Name="A_GLAccount" 
                   EntityType="com.sap.gateway.srvd.a2x.api_glaccount.v0001.A_GLAccountType" 
                   sap:creatable="true" sap:updatable="true" sap:deletable="true" 
                   sap:content-version="1" sap:label="总账科目"/>
      </EntityContainer>
      <EntityType Name="A_GLAccountType" sap:label="总账科目" sap:content-version="1">
        <Key>
          <PropertyRef Name="GLAccount"/>
        </Key>
        <Property Name="GLAccount" Type="Edm.String" Nullable="false" MaxLength="10" 
                  sap:label="总账科目编号" sap:semantics="text"/>
        <Property Name="GLAccountName" Type="Edm.String" MaxLength="50" 
                  sap:label="总账科目名称" sap:semantics="text"/>
      </EntityType>
    </Schema>
  </edmx:DataServices>
</edmx:Edmx>'''

# 解析XML
root = ET.fromstring(xml_data)
EDM_NS = "http://schemas.microsoft.com/ado/2007/06/edm"

# 查找EntityType
entity_types = root.findall(f".//{{{EDM_NS}}}EntityType")
if not entity_types:
    entity_types = root.findall(".//EntityType")

print(f"找到 {len(entity_types)} 个EntityType")

for entity_type in entity_types:
    name = entity_type.get("Name")
    print(f"\nEntityType: {name}")
    
    # 使用tostring获取内容
    content = ET.tostring(entity_type, encoding='unicode')
    print(f"Content长度: {len(content)}")
    print(f"\n完整Content:\n{content}")
    
    # 测试正则表达式（支持命名空间前缀）
    property_patterns = [
        re.compile(r'<(?:ns\d+:)?Property\s+([^>]*?)/>', re.IGNORECASE),  # 自闭合标签
        re.compile(r'<(?:ns\d+:)?Property\s+Name="([^"]+)"[^>]*>([\s\S]*?)</(?:ns\d+:)?Property>', re.IGNORECASE)  # 闭合标签
    ]
    
    for i, pattern in enumerate(property_patterns):
        matches = list(pattern.finditer(content))
        print(f"\n模式 {i+1} 匹配数: {len(matches)}")
        for match in matches:
            print(f"  匹配: {match.group(0)[:150]}")
    
    # 也尝试直接查找Property字符串
    if 'Property' in content:
        print(f"\n找到'Property'字符串，位置: {content.find('Property')}")
        # 提取包含Property的行
        lines = content.split('\n')
        for line in lines:
            if 'Property' in line:
                print(f"  包含Property的行: {line.strip()[:150]}")

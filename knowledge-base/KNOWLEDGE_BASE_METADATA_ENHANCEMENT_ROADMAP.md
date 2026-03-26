# 知识库元数据体系完善路线图

## 📅 实施时间表

### 第一阶段：基础元数据扩展（1-2个月）

#### Week 1-2: 数据库模型扩展
- [ ] 设计元数据扩展方案
- [ ] 创建数据库迁移脚本
- [ ] 扩展Document模型字段
- [ ] 扩展KnowledgeBase模型字段
- [ ] 创建KnowledgeAssociation关联表

#### Week 3-4: 元数据服务层
- [ ] 实现元数据提取服务
- [ ] 实现元数据验证服务
- [ ] 实现元数据迁移服务
- [ ] 更新文档处理流程集成元数据提取

#### Week 5-6: API接口扩展
- [ ] 扩展文档上传API支持新元数据
- [ ] 扩展文档查询API支持元数据过滤
- [ ] 创建知识关联管理API
- [ ] 创建元数据管理API

#### Week 7-8: 前端界面
- [ ] 设计元数据编辑界面
- [ ] 实现元数据展示组件
- [ ] 实现关联关系可视化
- [ ] 实现元数据搜索和过滤

---

### 第二阶段：关系网络构建（2-3个月）

#### Week 9-10: 关联关系管理
- [ ] 实现知识关联服务
- [ ] 实现关联关系验证
- [ ] 实现关联关系查询
- [ ] 实现关联关系推荐

#### Week 11-12: 知识图谱增强
- [ ] 扩展知识图谱节点类型
- [ ] 扩展知识图谱边关系类型
- [ ] 实现知识图谱自动构建
- [ ] 实现知识图谱查询优化

#### Week 13-14: 多维分类体系
- [ ] 实现业务分类管理
- [ ] 实现技术分类管理
- [ ] 实现项目分类管理
- [ ] 实现安全分类管理

#### Week 15-16: 分类体系集成
- [ ] 实现分类体系配置
- [ ] 实现分类自动推荐
- [ ] 实现分类统计和报表
- [ ] 实现分类权限控制

---

### 第三阶段：智能语义增强（3-4个月）

#### Week 17-18: 业务语义提取
- [ ] 实现业务上下文提取器
- [ ] 实现业务术语映射器
- [ ] 实现SAP对象映射器
- [ ] 集成到文档处理流程

#### Week 19-20: 智能标签生成
- [ ] 实现AI关键词生成器
- [ ] 实现自动分类器
- [ ] 实现相似文档匹配
- [ ] 实现标签推荐系统

#### Week 21-22: 实体识别增强
- [ ] 实现增强实体识别器
- [ ] 实现实体关系提取
- [ ] 实现实体知识图谱链接
- [ ] 实现实体查询和统计

#### Week 23-24: 语义向量增强
- [ ] 实现主题向量生成
- [ ] 实现语义向量生成
- [ ] 实现多向量融合
- [ ] 实现语义搜索优化

---

### 第四阶段：质量与治理体系（4-5个月）

#### Week 25-26: 质量评估扩展
- [ ] 实现准确性评估
- [ ] 实现时效性评估
- [ ] 实现实用性评估
- [ ] 实现质量证据收集

#### Week 27-28: 知识治理服务
- [ ] 实现自动归档服务
- [ ] 实现过时检测服务
- [ ] 实现更新提醒服务
- [ ] 实现质量监控服务

#### Week 29-30: 访问控制体系
- [ ] 实现权限管理服务
- [ ] 实现角色管理服务
- [ ] 实现访问范围控制
- [ ] 实现访问日志记录

#### Week 31-32: 使用统计分析
- [ ] 实现访问统计服务
- [ ] 实现下载统计服务
- [ ] 实现引用统计服务
- [ ] 实现使用分析报表

---

## 🔧 技术实现细节

### 1. 数据库迁移脚本示例

```python
# database/src/migrations/versions/019_extend_document_metadata.py

"""扩展文档元数据字段

Revision ID: 019_extend_document_metadata
Revises: 018_add_knowledge_bases_table
Create Date: 2024-02-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # 添加知识标识字段
    op.add_column('documents', sa.Column('knowledge_id', sa.String(50), nullable=True, comment='知识ID（业务标识符）'))
    op.add_column('documents', sa.Column('knowledge_type', sa.String(50), nullable=True, comment='知识类型'))
    
    # 添加主题分类字段
    op.add_column('documents', sa.Column('business_domain', sa.String(100), nullable=True, comment='业务域'))
    op.add_column('documents', sa.Column('function_module', sa.String(100), nullable=True, comment='功能模块'))
    op.add_column('documents', sa.Column('business_process', sa.String(200), nullable=True, comment='业务流程'))
    op.add_column('documents', sa.Column('technical_topic', sa.String(200), nullable=True, comment='技术主题'))
    
    # 添加关键词字段（JSONB）
    op.add_column('documents', sa.Column('core_keywords', postgresql.JSONB, nullable=True, comment='核心关键词'))
    op.add_column('documents', sa.Column('extended_keywords', postgresql.JSONB, nullable=True, comment='扩展关键词'))
    op.add_column('documents', sa.Column('synonyms', postgresql.JSONB, nullable=True, comment='同义词映射'))
    
    # 添加价值标签字段
    op.add_column('documents', sa.Column('usage_frequency', sa.String(20), nullable=True, comment='使用频率'))
    op.add_column('documents', sa.Column('impact_scope', sa.String(20), nullable=True, comment='影响范围'))
    op.add_column('documents', sa.Column('criticality', sa.String(20), nullable=True, comment='关键程度'))
    op.add_column('documents', sa.Column('update_frequency', sa.String(20), nullable=True, comment='更新频率'))
    
    # 添加生命周期字段
    op.add_column('documents', sa.Column('created_department', sa.String(100), nullable=True, comment='创建部门'))
    op.add_column('documents', sa.Column('creation_purpose', sa.Text, nullable=True, comment='创建目的'))
    op.add_column('documents', sa.Column('creation_source', sa.String(50), nullable=True, comment='创建来源'))
    op.add_column('documents', sa.Column('effective_date', sa.Date, nullable=True, comment='生效日期'))
    op.add_column('documents', sa.Column('version_history', postgresql.JSONB, nullable=True, comment='版本历史'))
    op.add_column('documents', sa.Column('revision_notes', sa.Text, nullable=True, comment='修订说明'))
    op.add_column('documents', sa.Column('lifecycle_status', sa.String(20), nullable=True, comment='生命周期状态'))
    op.add_column('documents', sa.Column('review_status', sa.String(20), nullable=True, comment='审核状态'))
    op.add_column('documents', sa.Column('usage_status', sa.String(20), nullable=True, comment='使用状态'))
    
    # 添加质量评估字段
    op.add_column('documents', sa.Column('accuracy_rating', sa.String(5), nullable=True, comment='准确性评级'))
    op.add_column('documents', sa.Column('timeliness_assessment', sa.String(20), nullable=True, comment='时效性评估'))
    op.add_column('documents', sa.Column('practicality_feedback', sa.String(10), nullable=True, comment='实用性反馈'))
    
    # 添加访问控制字段
    op.add_column('documents', sa.Column('access_permission', sa.String(20), nullable=True, comment='访问权限'))
    op.add_column('documents', sa.Column('access_roles', postgresql.JSONB, nullable=True, comment='访问角色'))
    op.add_column('documents', sa.Column('access_scope', sa.String(100), nullable=True, comment='访问范围'))
    
    # 添加分类体系字段（JSONB）
    op.add_column('documents', sa.Column('organization_metadata', postgresql.JSONB, nullable=True, comment='组织结构元数据'))
    
    # 添加关联关系字段（JSONB）
    op.add_column('documents', sa.Column('associations_metadata', postgresql.JSONB, nullable=True, comment='关联关系元数据'))
    
    # 添加业务语义字段（JSONB）
    op.add_column('documents', sa.Column('business_semantics_metadata', postgresql.JSONB, nullable=True, comment='业务语义元数据'))
    
    # 添加智能理解字段（JSONB）
    op.add_column('documents', sa.Column('intelligent_understanding_metadata', postgresql.JSONB, nullable=True, comment='智能理解元数据'))
    
    # 创建索引
    op.create_index('idx_documents_knowledge_id', 'documents', ['knowledge_id'])
    op.create_index('idx_documents_knowledge_type', 'documents', ['knowledge_type'])
    op.create_index('idx_documents_business_domain', 'documents', ['business_domain'])
    op.create_index('idx_documents_function_module', 'documents', ['function_module'])
    op.create_index('idx_documents_lifecycle_status', 'documents', ['lifecycle_status'])
    op.create_index('idx_documents_review_status', 'documents', ['review_status'])
    
    # 创建GIN索引用于JSONB字段查询
    op.execute('CREATE INDEX idx_documents_core_keywords ON documents USING GIN (core_keywords)')
    op.execute('CREATE INDEX idx_documents_organization_metadata ON documents USING GIN (organization_metadata)')
    op.execute('CREATE INDEX idx_documents_associations_metadata ON documents USING GIN (associations_metadata)')

def downgrade():
    # 删除索引
    op.drop_index('idx_documents_knowledge_id', 'documents')
    op.drop_index('idx_documents_knowledge_type', 'documents')
    op.drop_index('idx_documents_business_domain', 'documents')
    op.drop_index('idx_documents_function_module', 'documents')
    op.drop_index('idx_documents_lifecycle_status', 'documents')
    op.drop_index('idx_documents_review_status', 'documents')
    op.execute('DROP INDEX IF EXISTS idx_documents_core_keywords')
    op.execute('DROP INDEX IF EXISTS idx_documents_organization_metadata')
    op.execute('DROP INDEX IF EXISTS idx_documents_associations_metadata')
    
    # 删除字段
    op.drop_column('documents', 'knowledge_id')
    op.drop_column('documents', 'knowledge_type')
    op.drop_column('documents', 'business_domain')
    op.drop_column('documents', 'function_module')
    op.drop_column('documents', 'business_process')
    op.drop_column('documents', 'technical_topic')
    op.drop_column('documents', 'core_keywords')
    op.drop_column('documents', 'extended_keywords')
    op.drop_column('documents', 'synonyms')
    op.drop_column('documents', 'usage_frequency')
    op.drop_column('documents', 'impact_scope')
    op.drop_column('documents', 'criticality')
    op.drop_column('documents', 'update_frequency')
    op.drop_column('documents', 'created_department')
    op.drop_column('documents', 'creation_purpose')
    op.drop_column('documents', 'creation_source')
    op.drop_column('documents', 'effective_date')
    op.drop_column('documents', 'version_history')
    op.drop_column('documents', 'revision_notes')
    op.drop_column('documents', 'lifecycle_status')
    op.drop_column('documents', 'review_status')
    op.drop_column('documents', 'usage_status')
    op.drop_column('documents', 'accuracy_rating')
    op.drop_column('documents', 'timeliness_assessment')
    op.drop_column('documents', 'practicality_feedback')
    op.drop_column('documents', 'access_permission')
    op.drop_column('documents', 'access_roles')
    op.drop_column('documents', 'access_scope')
    op.drop_column('documents', 'organization_metadata')
    op.drop_column('documents', 'associations_metadata')
    op.drop_column('documents', 'business_semantics_metadata')
    op.drop_column('documents', 'intelligent_understanding_metadata')
```

### 2. 知识关联表创建

```python
# database/src/migrations/versions/020_create_knowledge_associations.py

"""创建知识关联表

Revision ID: 020_create_knowledge_associations
Revises: 019_extend_document_metadata
Create Date: 2024-02-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID

def upgrade():
    op.create_table(
        'knowledge_associations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('source_knowledge_id', UUID(as_uuid=True), sa.ForeignKey('documents.id'), nullable=False, comment='源知识ID'),
        sa.Column('target_knowledge_id', UUID(as_uuid=True), sa.ForeignKey('documents.id'), nullable=False, comment='目标知识ID'),
        sa.Column('association_type', sa.String(50), nullable=False, comment='关联类型：父子/依赖/参考/版本/相似/互补'),
        sa.Column('strength', sa.String(20), nullable=False, comment='关联强度：强/中/弱'),
        sa.Column('description', sa.Text, nullable=True, comment='关联描述'),
        sa.Column('properties', postgresql.JSONB, nullable=True, comment='关联属性'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), comment='更新时间'),
        
        # 唯一约束：同一对知识不能有重复的关联类型
        sa.UniqueConstraint('source_knowledge_id', 'target_knowledge_id', 'association_type', name='uq_knowledge_association'),
        
        # 索引
        sa.Index('idx_assoc_source', 'source_knowledge_id'),
        sa.Index('idx_assoc_target', 'target_knowledge_id'),
        sa.Index('idx_assoc_type', 'association_type'),
        sa.Index('idx_assoc_strength', 'strength'),
    )

def downgrade():
    op.drop_table('knowledge_associations')
```

### 3. 元数据提取服务

```python
# knowledge-base/src/services/metadata_extraction_service.py

"""
元数据提取服务
负责从文档内容中提取各种元数据
"""
import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from ..core.metadata_enhancer import MetadataEnhancer
from ..core.document_quality import DocumentQualityAssessor

logger = logging.getLogger(__name__)


class MetadataExtractionService:
    """元数据提取服务"""
    
    def __init__(self):
        self.metadata_enhancer = MetadataEnhancer()
        self.quality_assessor = DocumentQualityAssessor()
    
    def extract_content_metadata(
        self,
        text: str,
        filename: str,
        existing_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """提取内容层元数据"""
        metadata = existing_metadata or {}
        
        # 提取知识类型（基于文件名和内容）
        knowledge_type = self._extract_knowledge_type(filename, text)
        metadata['knowledge_identity'] = {
            'knowledge_id': self._generate_knowledge_id(knowledge_type),
            'knowledge_type': knowledge_type,
            'knowledge_category': self._categorize_knowledge_type(knowledge_type)
        }
        
        # 提取主题分类
        metadata['content_theme'] = {
            'business_domain': self._extract_business_domain(text),
            'function_module': self._extract_function_module(text),
            'business_process': self._extract_business_process(text),
            'technical_topic': self._extract_technical_topic(text)
        }
        
        # 提取关键词体系
        enhanced_metadata = self.metadata_enhancer.enhance(text)
        metadata['keyword_system'] = {
            'core_keywords': enhanced_metadata.keywords[:10],  # Top 10
            'extended_keywords': enhanced_metadata.keywords[10:20],  # Next 10
            'synonyms': self._extract_synonyms(text, enhanced_metadata.keywords)
        }
        
        # 提取价值标签（基于内容特征）
        metadata['value_tags'] = {
            'usage_frequency': self._estimate_usage_frequency(text),
            'impact_scope': self._estimate_impact_scope(text),
            'criticality': self._estimate_criticality(text),
            'update_frequency': self._estimate_update_frequency(text)
        }
        
        return metadata
    
    def extract_structural_metadata(
        self,
        text: str,
        knowledge_base_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """提取结构层元数据"""
        metadata = {}
        
        # 提取组织分类
        metadata['organization'] = {
            'business_classification': self._extract_business_classification(text),
            'technical_classification': self._extract_technical_classification(text),
            'project_classification': self._extract_project_classification(text),
            'security_classification': self._extract_security_classification(text)
        }
        
        return metadata
    
    def extract_administrative_metadata(
        self,
        document_id: str,
        uploaded_by: Optional[str] = None,
        department: Optional[str] = None
    ) -> Dict[str, Any]:
        """提取管理层元数据"""
        metadata = {}
        
        # 生命周期信息
        metadata['lifecycle'] = {
            'creation_info': {
                'department': department or '未指定',
                'purpose': '文档上传',
                'source': '用户上传'
            },
            'version_management': {
                'current_version': 'v1.0',
                'version_history': [],
                'revision_notes': '',
                'effective_date': datetime.now().date().isoformat()
            },
            'status_management': {
                'lifecycle_status': '活跃',
                'review_status': '草稿',
                'usage_status': '正常'
            }
        }
        
        # 访问控制
        metadata['access_control'] = {
            'permission': '部门级',
            'roles': [],
            'scope': department or '未指定'
        }
        
        return metadata
    
    def extract_semantic_metadata(
        self,
        text: str,
        embedding: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """提取语义层元数据"""
        metadata = {}
        
        # 业务语义
        metadata['business_semantics'] = {
            'business_context': self._extract_business_context(text),
            'business_term_mapping': self._extract_business_term_mapping(text)
        }
        
        # 智能理解
        metadata['intelligent_understanding'] = {
            'vector_features': {
                'content_vector': embedding or [],
                'topic_vector': [],  # 待实现
                'semantic_vector': []  # 待实现
            },
            'intelligent_tags': {
                'ai_keywords': self._extract_ai_keywords(text),
                'auto_classification': self._auto_classify(text),
                'similar_documents': []  # 待实现
            },
            'entity_recognition': self._recognize_entities(text)
        }
        
        return metadata
    
    # 辅助方法
    def _extract_knowledge_type(self, filename: str, text: str) -> str:
        """提取知识类型"""
        # 基于文件名和内容关键词判断
        filename_lower = filename.lower()
        text_lower = text.lower()
        
        if any(word in filename_lower for word in ['规范', '标准', 'specification']):
            return '规范'
        elif any(word in filename_lower for word in ['手册', 'manual', 'guide']):
            return '手册'
        elif any(word in filename_lower for word in ['指南', 'guide', 'tutorial']):
            return '指南'
        elif any(word in filename_lower for word in ['报告', 'report']):
            return '报告'
        elif any(word in filename_lower for word in ['方案', 'solution', 'plan']):
            return '方案'
        elif any(word in filename_lower for word in ['脚本', 'script', '.py', '.sh']):
            return '脚本'
        elif any(word in filename_lower for word in ['配置', 'config', '.conf', '.ini']):
            return '配置'
        else:
            return '文档'
    
    def _generate_knowledge_id(self, knowledge_type: str) -> str:
        """生成知识ID"""
        # 格式：K + 年份 + 月份 + 序号
        now = datetime.now()
        prefix = knowledge_type[0] if knowledge_type else 'K'
        return f"{prefix}{now.year}{now.month:02d}{now.day:02d}001"  # 简化版，实际应从数据库获取序号
    
    def _categorize_knowledge_type(self, knowledge_type: str) -> str:
        """分类知识类型"""
        doc_types = ['规范', '手册', '指南', '报告', '方案']
        code_types = ['脚本', '配置', '程序', '补丁']
        data_types = ['数据集', '模型', '指标']
        exp_types = ['案例', '经验', '教训', '最佳实践']
        
        if knowledge_type in doc_types:
            return '文档类'
        elif knowledge_type in code_types:
            return '代码类'
        elif knowledge_type in data_types:
            return '数据类'
        elif knowledge_type in exp_types:
            return '经验类'
        else:
            return '文档类'
    
    def _extract_business_domain(self, text: str) -> str:
        """提取业务域"""
        # 基于关键词匹配
        domains = {
            '销售与分销': ['销售', '订单', '客户', 'SD', 'sales'],
            '采购': ['采购', '供应商', 'MM', 'procurement'],
            '财务': ['财务', '会计', 'FI', 'CO', 'finance'],
            '生产': ['生产', '制造', 'PP', 'production'],
            '人力': ['人力', 'HR', '人事', 'human']
        }
        
        text_lower = text.lower()
        for domain, keywords in domains.items():
            if any(keyword in text_lower for keyword in keywords):
                return domain
        
        return '未分类'
    
    def _extract_function_module(self, text: str) -> str:
        """提取功能模块"""
        # 识别SAP模块
        sap_modules = {
            'SAP SD': ['SD', '销售', '分销'],
            'SAP MM': ['MM', '采购', '物料'],
            'SAP FI': ['FI', '财务', '会计'],
            'SAP CO': ['CO', '成本', '控制'],
            'SAP PP': ['PP', '生产', '计划']
        }
        
        text_upper = text.upper()
        for module, keywords in sap_modules.items():
            if any(keyword in text_upper for keyword in keywords):
                return module
        
        return '未指定'
    
    def _extract_business_process(self, text: str) -> str:
        """提取业务流程"""
        # 基于关键词识别流程
        processes = {
            '销售订单处理': ['订单', '销售订单', 'VA01'],
            '采购流程': ['采购', '采购订单', 'ME21N'],
            '财务结算': ['结算', '财务', 'F-02']
        }
        
        text_lower = text.lower()
        for process, keywords in processes.items():
            if any(keyword in text_lower for keyword in keywords):
                return process
        
        return '未指定'
    
    def _extract_technical_topic(self, text: str) -> str:
        """提取技术主题"""
        # 提取技术相关关键词
        topics = []
        if '定价' in text or '定价过程' in text:
            topics.append('定价配置')
        if '信用' in text or '信用检查' in text:
            topics.append('信用管理')
        if '物料' in text or '物料主数据' in text:
            topics.append('物料管理')
        
        return '/'.join(topics) if topics else '未指定'
    
    def _extract_synonyms(self, text: str, keywords: List[str]) -> Dict[str, List[str]]:
        """提取同义词"""
        # 简化版：基于常见同义词映射
        synonym_map = {
            '销售订单': ['销售凭证', '销售单据', '订单'],
            '客户': ['客户主数据', '客户信息'],
            '物料': ['物料主数据', '产品']
        }
        
        synonyms = {}
        for keyword in keywords:
            if keyword in synonym_map:
                synonyms[keyword] = synonym_map[keyword]
        
        return synonyms
    
    def _estimate_usage_frequency(self, text: str) -> str:
        """估算使用频率"""
        # 基于内容特征估算
        if len(text) > 10000:
            return '高频'
        elif len(text) > 5000:
            return '中频'
        else:
            return '低频'
    
    def _estimate_impact_scope(self, text: str) -> str:
        """估算影响范围"""
        # 基于关键词判断
        if any(word in text.lower() for word in ['企业', '全公司', 'global']):
            return '企业级'
        elif any(word in text.lower() for word in ['部门', '部门级']):
            return '部门级'
        else:
            return '个人级'
    
    def _estimate_criticality(self, text: str) -> str:
        """估算关键程度"""
        # 基于关键词判断
        if any(word in text.lower() for word in ['关键', '重要', 'critical', 'important']):
            return '关键'
        elif any(word in text.lower() for word in ['一般', 'normal']):
            return '一般'
        else:
            return '重要'
    
    def _estimate_update_frequency(self, text: str) -> str:
        """估算更新频率"""
        # 基于内容类型判断
        if any(word in text.lower() for word in ['实时', 'realtime']):
            return '实时'
        elif any(word in text.lower() for word in ['每日', 'daily']):
            return '每日'
        elif any(word in text.lower() for word in ['每周', 'weekly']):
            return '每周'
        else:
            return '每月'
    
    def _extract_business_classification(self, text: str) -> Dict[str, str]:
        """提取业务分类"""
        return {
            'department': self._extract_department(text),
            'function': self._extract_function(text),
            'process': self._extract_business_process(text)
        }
    
    def _extract_technical_classification(self, text: str) -> Dict[str, str]:
        """提取技术分类"""
        return {
            'system': self._extract_system(text),
            'module': self._extract_function_module(text),
            'tech_stack': self._extract_tech_stack(text)
        }
    
    def _extract_project_classification(self, text: str) -> Dict[str, str]:
        """提取项目分类"""
        return {
            'project': '未指定',
            'product': '未指定',
            'version': 'v1.0'
        }
    
    def _extract_security_classification(self, text: str) -> Dict[str, str]:
        """提取安全分类"""
        return {
            'security_level': '内部',
            'permission': '部门级',
            'scope': '未指定'
        }
    
    def _extract_department(self, text: str) -> str:
        """提取部门"""
        departments = {
            '销售运营部': ['销售', '订单'],
            'IT部': ['系统', '技术', 'IT'],
            '财务部': ['财务', '会计']
        }
        
        text_lower = text.lower()
        for dept, keywords in departments.items():
            if any(keyword in text_lower for keyword in keywords):
                return dept
        
        return '未指定'
    
    def _extract_function(self, text: str) -> str:
        """提取职能"""
        return '未指定'
    
    def _extract_system(self, text: str) -> str:
        """提取系统"""
        if 'SAP' in text.upper():
            return 'SAP ERP'
        elif 'Oracle' in text.upper():
            return 'Oracle'
        else:
            return '未指定'
    
    def _extract_tech_stack(self, text: str) -> str:
        """提取技术栈"""
        if 'SAP' in text.upper():
            return 'SAP'
        else:
            return '未指定'
    
    def _extract_business_context(self, text: str) -> Dict[str, Any]:
        """提取业务上下文"""
        return {
            'scenario': '未指定',
            'target_users': [],
            'applicable_conditions': '未指定',
            'exceptions': '未指定'
        }
    
    def _extract_business_term_mapping(self, text: str) -> Dict[str, str]:
        """提取业务术语映射"""
        return {}
    
    def _extract_ai_keywords(self, text: str) -> List[str]:
        """提取AI关键词"""
        enhanced_metadata = self.metadata_enhancer.enhance(text)
        return enhanced_metadata.keywords[:5]  # Top 5
    
    def _auto_classify(self, text: str) -> str:
        """自动分类"""
        # 基于业务域和功能模块
        business_domain = self._extract_business_domain(text)
        function_module = self._extract_function_module(text)
        return f"{business_domain}/{function_module}"
    
    def _recognize_entities(self, text: str) -> Dict[str, Any]:
        """识别实体"""
        entities = []
        
        # 识别邮箱
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        for email in emails:
            entities.append({
                'text': email,
                'type': '邮箱',
                'confidence': 0.95
            })
        
        # 识别URL
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, text)
        for url in urls:
            entities.append({
                'text': url,
                'type': 'URL',
                'confidence': 0.90
            })
        
        return {
            'entities': entities,
            'entity_relations': [],
            'entity_links': []
        }
```

### 4. 知识关联服务

```python
# knowledge-base/src/services/knowledge_association_service.py

"""
知识关联服务
管理知识之间的关联关系
"""
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from ..repositories.knowledge_association_repository import KnowledgeAssociationRepository

logger = logging.getLogger(__name__)


class KnowledgeAssociationService:
    """知识关联服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.association_repo = KnowledgeAssociationRepository(db)
    
    def create_association(
        self,
        source_knowledge_id: str,
        target_knowledge_id: str,
        association_type: str,
        strength: str = '中',
        description: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建知识关联"""
        try:
            association = self.association_repo.create(
                source_knowledge_id=UUID(source_knowledge_id),
                target_knowledge_id=UUID(target_knowledge_id),
                association_type=association_type,
                strength=strength,
                description=description,
                properties=properties or {}
            )
            self.db.commit()
            
            return {
                'id': str(association.id),
                'source_knowledge_id': str(association.source_knowledge_id),
                'target_knowledge_id': str(association.target_knowledge_id),
                'association_type': association.association_type,
                'strength': association.strength,
                'description': association.description,
                'properties': association.properties
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating association: {str(e)}")
            raise
    
    def get_associations(
        self,
        knowledge_id: str,
        association_type: Optional[str] = None,
        direction: str = 'both'  # 'outgoing', 'incoming', 'both'
    ) -> List[Dict[str, Any]]:
        """获取知识关联"""
        associations = self.association_repo.get_by_knowledge_id(
            UUID(knowledge_id),
            association_type=association_type,
            direction=direction
        )
        
        return [
            {
                'id': str(a.id),
                'source_knowledge_id': str(a.source_knowledge_id),
                'target_knowledge_id': str(a.target_knowledge_id),
                'association_type': a.association_type,
                'strength': a.strength,
                'description': a.description,
                'properties': a.properties
            }
            for a in associations
        ]
    
    def delete_association(self, association_id: str) -> bool:
        """删除知识关联"""
        try:
            self.association_repo.delete(UUID(association_id))
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting association: {str(e)}")
            return False
    
    def suggest_associations(self, knowledge_id: str) -> List[Dict[str, Any]]:
        """推荐知识关联"""
        # 基于内容相似度、关键词匹配等推荐关联
        # 待实现
        return []
```

---

## 📝 总结

本路线图提供了完整的元数据体系完善方案，包括：

1. **详细的实施时间表**：分4个阶段，共32周
2. **数据库迁移脚本**：扩展文档和知识库元数据字段
3. **服务层实现**：元数据提取服务和知识关联服务
4. **技术实现细节**：具体的代码示例

通过分阶段实施，可以逐步将当前的知识库元数据体系升级为企业级元数据体系，提升知识管理的智能化水平。



/**
 * 元数据分类标准库
 * 定义标准化的分类值、业务领域、技术来源等维度
 */

// 业务领域标准
export const BUSINESS_DOMAINS = {
  finance: { name: '财务', description: '财务管理相关业务领域' },
  sales: { name: '销售', description: '销售业务领域' },
  marketing: { name: '营销', description: '市场营销业务领域' },
  hr: { name: '人力资源', description: '人力资源管理' },
  operations: { name: '运营', description: '运营管理' },
  it: { name: '信息技术', description: 'IT技术领域' },
  supply_chain: { name: '供应链', description: '供应链管理' },
  customer_service: { name: '客户服务', description: '客户服务和支持' },
  r_d: { name: '研发', description: '研发和创新' },
  legal: { name: '法务', description: '法律合规' },
} as const;

// 技术来源标准
export const TECHNICAL_SOURCES = {
  sap: { name: 'SAP系统', description: 'SAP ERP系统' },
  oracle_erp: { name: 'Oracle ERP', description: 'Oracle ERP系统' },
  salesforce: { name: 'Salesforce', description: 'Salesforce CRM系统' },
  dynamics: { name: 'Microsoft Dynamics', description: 'Microsoft Dynamics系统' },
  workday: { name: 'Workday', description: 'Workday HR系统' },
  servicenow: { name: 'ServiceNow', description: 'ServiceNow ITSM系统' },
  database: { name: '数据库', description: '关系型数据库' },
  data_lake: { name: '数据湖', description: '数据湖存储' },
  data_warehouse: { name: '数据仓库', description: '数据仓库' },
  api: { name: 'API接口', description: 'RESTful API或GraphQL接口' },
  file_system: { name: '文件系统', description: '文件存储系统' },
  stream: { name: '流数据', description: '实时数据流' },
  external: { name: '外部数据源', description: '第三方外部数据源' },
  custom: { name: '自定义', description: '自定义数据源' },
} as const;

// 生命周期阶段标准
export const LIFECYCLE_STAGES = {
  development: { name: '开发', description: '开发环境' },
  testing: { name: '测试', description: '测试环境' },
  staging: { name: '预发布', description: '预发布环境' },
  production: { name: '生产', description: '生产环境' },
  archive: { name: '归档', description: '已归档' },
} as const;

// 数据格式标准
export const DATA_FORMATS = {
  structured: { name: '结构化', description: '结构化数据（表、关系型）' },
  unstructured: { name: '非结构化', description: '非结构化数据（文档、图片、视频）' },
  semi_structured: { name: '半结构化', description: '半结构化数据（JSON、XML）' },
} as const;

// 安全等级标准
export const SECURITY_LEVELS = {
  public: { name: '公开', description: '公开可访问' },
  internal: { name: '内部', description: '内部使用' },
  confidential: { name: '机密', description: '机密数据' },
  restricted: { name: '受限', description: '受限访问' },
  secret: { name: '秘密', description: '高度机密' },
} as const;

// 质量等级标准
export const QUALITY_LEVELS = {
  certified: { name: '已认证', description: '经过认证的高质量数据' },
  validated: { name: '已验证', description: '已验证的数据' },
  unverified: { name: '未验证', description: '未经验证的数据' },
  needs_cleanup: { name: '需清理', description: '需要数据清理' },
} as const;

// 模型状态标准（用于AI模型）
export const MODEL_STATUSES = {
  training: { name: '训练中', description: '模型正在训练' },
  active: { name: '活跃', description: '模型已部署并活跃使用' },
  deprecated: { name: '已弃用', description: '模型已弃用' },
  archived: { name: '已归档', description: '模型已归档' },
} as const;

// 工作流执行模式标准
export const WORKFLOW_EXECUTION_MODES = {
  manual: { name: '手动执行', description: '需要手动触发' },
  automated: { name: '自动执行', description: '自动执行' },
  scheduled: { name: '定时执行', description: '按计划定时执行' },
  event_driven: { name: '事件驱动', description: '基于事件触发' },
} as const;

// 工作流业务领域标准
export const WORKFLOW_BUSINESS_DOMAINS = {
  data_integration: { name: '数据集成', description: '数据集成工作流' },
  data_quality: { name: '数据质量', description: '数据质量检查工作流' },
  data_governance: { name: '数据治理', description: '数据治理工作流' },
  ml_training: { name: '模型训练', description: '机器学习模型训练' },
  ml_inference: { name: '模型推理', description: '模型推理服务' },
  reporting: { name: '报表生成', description: '报表和报告生成' },
  monitoring: { name: '监控告警', description: '系统监控和告警' },
} as const;

// 分类映射规则（从旧分类映射到新分类）
export const CLASSIFICATION_MAPPING_RULES: Record<string, string> = {
  // 数据资产映射
  dataset: 'analytical_data',
  table: 'transaction_data',
  view: 'analytical_data',
  file: 'operational_data',
  stream: 'operational_data',
  api: 'operational_data',

  // AI模型映射（model_type直接作为主分类）
  // 工作流映射（workflow_type直接作为主分类）
  // 业务实体映射（entity_type直接作为主分类）
};

// 获取所有业务领域列表
export function getAllBusinessDomains(): string[] {
  return Object.keys(BUSINESS_DOMAINS);
}

// 获取所有技术来源列表
export function getAllTechnicalSources(): string[] {
  return Object.keys(TECHNICAL_SOURCES);
}

// 获取所有生命周期阶段列表
export function getAllLifecycleStages(): string[] {
  return Object.keys(LIFECYCLE_STAGES);
}

// 获取显示名称
export function getBusinessDomainDisplayName(key: string): string {
  return BUSINESS_DOMAINS[key as keyof typeof BUSINESS_DOMAINS]?.name || key;
}

export function getTechnicalSourceDisplayName(key: string): string {
  return TECHNICAL_SOURCES[key as keyof typeof TECHNICAL_SOURCES]?.name || key;
}

export function getLifecycleStageDisplayName(key: string): string {
  return LIFECYCLE_STAGES[key as keyof typeof LIFECYCLE_STAGES]?.name || key;
}

// 分类维度接口定义
export interface ClassificationDimensions {
  // 业务维度
  business?: {
    domain?: string; // 业务领域
    criticality?: string; // 关键性（critical, high, medium, low）
    business_value?: string; // 业务价值
  };

  // 技术维度
  technical?: {
    source?: string; // 技术来源
    format?: string; // 数据格式
    storage?: string; // 存储类型
    framework?: string; // 框架（AI模型用）
  };

  // 生命周期维度
  lifecycle?: {
    stage?: string; // 生命周期阶段
    freshness?: string; // 更新频率
    retention?: string; // 保留期限
    status?: string; // 状态（AI模型、工作流用）
  };

  // 治理维度
  governance?: {
    security?: string; // 安全等级
    quality?: string; // 质量等级
    compliance?: string[]; // 合规要求（多值）
  };
}

// 标准化标签前缀（用于标签分类）
export const TAG_PREFIXES = {
  business: 'biz:', // 业务标签
  technical: 'tech:', // 技术标签
  governance: 'gov:', // 治理标签
  custom: '', // 自定义标签（无前缀）
} as const;

// 标准标签列表（建议使用的标签）
export const STANDARD_TAGS = {
  // 业务标签
  'biz:financial_reporting': '财务报表',
  'biz:regulatory_required': '监管要求',
  'biz:customer_facing': '面向客户',
  'biz:high_volume': '高数据量',
  'biz:real_time': '实时',
  'biz:critical': '关键',

  // 技术标签
  'tech:high_performance': '高性能',
  'tech:scalable': '可扩展',
  'tech:cloud_native': '云原生',
  'tech:legacy': '遗留系统',

  // 治理标签
  'gov:gdpr': 'GDPR合规',
  'gov:hipaa': 'HIPAA合规',
  'gov:sox': 'SOX合规',
  'gov:pii': '个人身份信息',
  'gov:audited': '已审计',
} as const;

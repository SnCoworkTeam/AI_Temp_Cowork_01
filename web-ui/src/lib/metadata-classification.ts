/**
 * 元数据分类工具
 * 提供统一的分类体系和管理功能
 */

export type MetadataType = 'data-assets' | 'workflows' | 'ai-models' | 'business-entities';

// 导入分类标准库
export type { ClassificationDimensions } from './classification-standards';
export {
  BUSINESS_DOMAINS,
  TECHNICAL_SOURCES,
  LIFECYCLE_STAGES,
  DATA_FORMATS,
  SECURITY_LEVELS,
  QUALITY_LEVELS,
  MODEL_STATUSES,
  WORKFLOW_EXECUTION_MODES,
  WORKFLOW_BUSINESS_DOMAINS,
  STANDARD_TAGS,
  getAllBusinessDomains,
  getAllTechnicalSources,
  getAllLifecycleStages,
  getBusinessDomainDisplayName,
  getTechnicalSourceDisplayName,
  getLifecycleStageDisplayName,
} from './classification-standards';

export interface ClassificationHierarchy {
  primary: string;
  displayName: string;
  description?: string;
  children?: ClassificationHierarchy[];
}

/**
 * 数据资产分类体系
 */
export const DATA_ASSET_CLASSIFICATIONS: ClassificationHierarchy[] = [
  {
    primary: 'master_data',
    displayName: '主数据',
    description: '企业核心主数据',
    children: [
      { primary: 'master_data:customer', displayName: '客户主数据' },
      { primary: 'master_data:vendor', displayName: '供应商主数据' },
      { primary: 'master_data:material', displayName: '物料主数据' },
      { primary: 'master_data:employee', displayName: '员工主数据' },
      { primary: 'master_data:organization', displayName: '组织主数据' },
    ],
  },
  {
    primary: 'transaction_data',
    displayName: '事务数据',
    description: '业务交易数据',
    children: [
      { primary: 'transaction_data:sales_order', displayName: '销售订单' },
      { primary: 'transaction_data:purchase_order', displayName: '采购订单' },
      { primary: 'transaction_data:invoice', displayName: '发票' },
      { primary: 'transaction_data:delivery', displayName: '交货单' },
    ],
  },
  {
    primary: 'reference_data',
    displayName: '参考数据',
    description: '参考和配置数据',
  },
  {
    primary: 'analytical_data',
    displayName: '分析数据',
    description: '用于分析和报表的数据',
  },
  {
    primary: 'operational_data',
    displayName: '运营数据',
    description: '日常运营数据',
  },
  {
    primary: 'pii',
    displayName: '个人身份信息',
    description: '包含个人身份信息的数据',
  },
  {
    primary: 'confidential',
    displayName: '机密数据',
    description: '机密和敏感数据',
  },
  {
    primary: 'public',
    displayName: '公开数据',
    description: '公开可访问的数据',
  },
];

/**
 * AI模型分类体系
 */
export const AI_MODEL_CLASSIFICATIONS: ClassificationHierarchy[] = [
  {
    primary: 'llm',
    displayName: '大语言模型',
    description: 'Large Language Model',
  },
  {
    primary: 'embedding',
    displayName: '嵌入模型',
    description: 'Embedding Model',
  },
  {
    primary: 'classification',
    displayName: '分类模型',
    description: 'Classification Model',
  },
  {
    primary: 'regression',
    displayName: '回归模型',
    description: 'Regression Model',
  },
  {
    primary: 'clustering',
    displayName: '聚类模型',
    description: 'Clustering Model',
  },
  {
    primary: 'nlp',
    displayName: '自然语言处理',
    description: 'Natural Language Processing',
  },
  {
    primary: 'computer_vision',
    displayName: '计算机视觉',
    description: 'Computer Vision',
  },
  {
    primary: 'recommendation',
    displayName: '推荐模型',
    description: 'Recommendation Model',
  },
  {
    primary: 'custom',
    displayName: '自定义模型',
    description: 'Custom Model',
  },
];

/**
 * 工作流分类体系
 */
export const WORKFLOW_CLASSIFICATIONS: ClassificationHierarchy[] = [
  {
    primary: 'data_pipeline',
    displayName: '数据管道',
    description: '数据处理管道',
  },
  {
    primary: 'ml_pipeline',
    displayName: '机器学习管道',
    description: 'ML Pipeline',
  },
  {
    primary: 'etl',
    displayName: 'ETL流程',
    description: 'Extract, Transform, Load',
  },
  {
    primary: 'batch',
    displayName: '批处理',
    description: '批处理任务',
  },
  {
    primary: 'streaming',
    displayName: '流处理',
    description: '流式数据处理',
  },
  {
    primary: 'scheduled',
    displayName: '定时任务',
    description: '定时执行的任务',
  },
];

/**
 * 业务实体分类体系
 */
export const BUSINESS_ENTITY_CLASSIFICATIONS: ClassificationHierarchy[] = [
  {
    primary: 'domain',
    displayName: '业务域',
    description: '业务领域',
  },
  {
    primary: 'concept',
    displayName: '概念',
    description: '业务概念',
  },
  {
    primary: 'term',
    displayName: '术语',
    description: '业务术语',
  },
  {
    primary: 'glossary',
    displayName: '词汇表',
    description: '业务词汇表',
  },
  {
    primary: 'policy',
    displayName: '政策',
    description: '业务政策',
  },
  {
    primary: 'rule',
    displayName: '规则',
    description: '业务规则',
  },
];

/**
 * 根据元数据类型获取分类体系
 */
export function getClassificationHierarchy(type: MetadataType): ClassificationHierarchy[] {
  switch (type) {
    case 'data-assets':
      return DATA_ASSET_CLASSIFICATIONS;
    case 'ai-models':
      return AI_MODEL_CLASSIFICATIONS;
    case 'workflows':
      return WORKFLOW_CLASSIFICATIONS;
    case 'business-entities':
      return BUSINESS_ENTITY_CLASSIFICATIONS;
    default:
      return [];
  }
}

/**
 * 从元数据项中提取分类
 * 支持多种数据源：classification字段、type字段、metadata中的category等
 */
export function extractClassification(item: any, type: MetadataType): string | null {
  // 1. 优先使用 classification 字段
  if (item.classification && typeof item.classification === 'string') {
    return item.classification;
  }

  // 2. 根据类型从其他字段推断
  switch (type) {
    case 'data-assets':
      // 从 asset_type 推断
      if (item.asset_type) {
        const typeMap: Record<string, string> = {
          dataset: 'analytical_data',
          table: 'transaction_data',
          view: 'analytical_data',
          file: 'operational_data',
          stream: 'operational_data',
          api: 'operational_data',
        };
        return typeMap[item.asset_type] || 'operational_data';
      }
      // 从 metadata 中的 category 提取
      if (item.metadata?.category) {
        return item.metadata.category;
      }
      break;

    case 'ai-models':
      // 从 model_type 推断
      if (item.model_type) {
        return item.model_type;
      }
      // 从 type 字段推断
      if (item.type) {
        return item.type;
      }
      break;

    case 'workflows':
      // 从 workflow_type 推断
      if (item.workflow_type) {
        return item.workflow_type;
      }
      // 从 type 字段推断
      if (item.type) {
        return item.type;
      }
      break;

    case 'business-entities':
      // 从 entity_type 推断
      if (item.entity_type) {
        return item.entity_type;
      }
      // 从 type 字段推断
      if (item.type) {
        return item.type;
      }
      break;
  }

  // 3. 从 metadata 中提取
  if (item.metadata) {
    if (item.metadata.classification) {
      return item.metadata.classification;
    }
    if (item.metadata.category) {
      return item.metadata.category;
    }
  }

  // 4. 返回默认分类
  return 'uncategorized';
}

/**
 * 标准化分类值
 * 将各种格式的分类值转换为标准格式
 */
export function normalizeClassification(
  classification: string | null | undefined,
  type: MetadataType
): string {
  if (!classification) {
    return 'uncategorized';
  }

  // 如果是复合格式（primary:secondary），提取主分类
  if (classification.includes(':')) {
    return classification.split(':')[0];
  }

  // 如果是JSON格式，解析
  try {
    const parsed = JSON.parse(classification);
    if (parsed.primary) {
      return parsed.primary;
    }
  } catch {
    // 不是JSON，继续处理
  }

  return classification;
}

/**
 * 获取所有可用的分类列表（扁平化）
 */
export function getAllClassifications(type: MetadataType): string[] {
  const hierarchy = getClassificationHierarchy(type);
  const classifications: string[] = [];

  function traverse(items: ClassificationHierarchy[]) {
    for (const item of items) {
      classifications.push(item.primary);
      if (item.children) {
        traverse(item.children);
      }
    }
  }

  traverse(hierarchy);
  return classifications;
}

/**
 * 获取分类的显示名称
 */
export function getClassificationDisplayName(classification: string, type: MetadataType): string {
  const hierarchy = getClassificationHierarchy(type);

  function findInHierarchy(items: ClassificationHierarchy[]): string | null {
    for (const item of items) {
      // 如果是复合格式，匹配主分类
      const primary = classification.includes(':') ? classification.split(':')[0] : classification;

      if (item.primary === primary) {
        return item.displayName;
      }
      if (item.children) {
        const found = findInHierarchy(item.children);
        if (found) return found;
      }
    }
    return null;
  }

  return findInHierarchy(hierarchy) || classification;
}

/**
 * 从数据列表中提取所有唯一的分类
 */
export function extractUniqueClassifications(items: any[], type: MetadataType): string[] {
  const classifications = new Set<string>();

  items.forEach((item) => {
    const classification = extractClassification(item, type);
    if (classification) {
      const normalized = normalizeClassification(classification, type);
      if (normalized !== 'uncategorized') {
        classifications.add(normalized);
      }
    }
  });

  return Array.from(classifications).sort();
}

/**
 * 统计每个分类的数量
 */
export function countByClassification(items: any[], type: MetadataType): Record<string, number> {
  const counts: Record<string, number> = {};

  items.forEach((item) => {
    const classification = extractClassification(item, type);
    const normalized = normalizeClassification(classification, type);
    counts[normalized] = (counts[normalized] || 0) + 1;
  });

  return counts;
}

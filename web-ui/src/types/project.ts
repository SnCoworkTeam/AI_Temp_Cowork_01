// 项目相关类型定义

export interface ProjectTemplate {
  id: string;
  template_code: string;
  name: string;
  description?: string;
  category_id?: string;
  category_name?: string;
  template_structure?: TemplatePhaseStructure[];
  is_active: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

export interface TemplatePhaseStructure {
  category_id: string;
  name: string;
  sequence: number;
  description?: string;
}

export interface PlanTreeNode {
  id: string;
  type: 'phase' | 'task';
  name: string;
  category_id?: string;
  category_code?: string;
  sequence?: number;
  is_readonly: boolean;
  phase_id?: string;
  status?: string;
  progress_percent?: number;
  children: PlanTreeNode[];
}

export interface PlanTreeResponse {
  plan_id: string;
  plan_name: string;
  tree: PlanTreeNode[];
}


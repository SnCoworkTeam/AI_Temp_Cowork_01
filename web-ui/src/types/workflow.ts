/**
 * 工作流类型定义
 */
export interface NodePosition {
  x: number;
  y: number;
}

export interface NodeSize {
  width: number;
  height: number;
}

export interface WorkflowNode {
  id: string;
  name: string;
  type: string;
  node_type?: string; // 后端需要的字段，用于兼容
  config: Record<string, any>;
  position: NodePosition;
  size?: NodeSize;
  style?: Record<string, any>;
  label?: string;
  inputs?: string[];
  outputs?: string[];
  next_nodes?: string[];
  condition?: string;
}

export interface ConnectionPoint {
  node_id: string;
  port: string;
  position?: NodePosition;
}

export interface WorkflowConnection {
  id: string;
  source: ConnectionPoint;
  target: ConnectionPoint;
  condition?: string;
  label?: string;
  style?: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface WorkflowConfig {
  name: string;
  description: string;
  version: string;
  nodes: WorkflowNode[];
  connections: WorkflowConnection[];
  start_node_id: string;
  end_node_ids: string[];
  variables?: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface NodeTypeDefinition {
  type: string;
  label: string;
  icon?: string;
  color: string;
  category: string;
  defaultConfig: Record<string, any>;
}

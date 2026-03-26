/**
 * Neo4j图数据库服务
 * 用于从Neo4j获取图数据用于前端展示
 */
import { apiGatewayClient } from '@/lib/api/client';

const buildQuery = (params?: Record<string, any>) => {
  if (!params) return '';
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null) return;
    if (Array.isArray(value)) {
      value.forEach((item) => search.append(key, String(item)));
      return;
    }
    if (typeof value === 'object') {
      search.append(key, JSON.stringify(value));
      return;
    }
    search.append(key, String(value));
  });
  const qs = search.toString();
  return qs ? `?${qs}` : '';
};

export interface Neo4jNode {
  id: string;
  labels: string[];
  properties: Record<string, any>;
}

export interface Neo4jRelationship {
  id: string;
  type: string;
  startNode: string;
  endNode: string;
  properties: Record<string, any>;
}

export interface GraphData {
  nodes: Array<{
    id: string;
    label: string;
    type?: string;
    properties?: Record<string, any>;
    [key: string]: any;
  }>;
  links: Array<{
    id: string;
    source: string;
    target: string;
    type?: string;
    properties?: Record<string, any>;
    [key: string]: any;
  }>;
}

export const neo4jGraphService = {
  /**
   * 从Neo4j获取图数据
   */
  async getGraphData(params?: {
    limit?: number;
    nodeType?: string;
    relationshipType?: string;
  }): Promise<GraphData> {
    try {
      const query = buildQuery(params);
      return await apiGatewayClient.get(`/api/neo4j/graph${query}`);
    } catch (error) {
      console.error('Failed to get Neo4j graph data:', error);
      return { nodes: [], links: [] };
    }
  },

  /**
   * 查询节点
   */
  async queryNodes(params?: {
    labels?: string[];
    properties?: Record<string, any>;
    limit?: number;
  }): Promise<Neo4jNode[]> {
    try {
      const query = buildQuery(params);
      const response = await apiGatewayClient.get(`/api/neo4j/nodes${query}`);
      return (response as any).nodes || [];
    } catch (error) {
      console.error('Failed to query nodes:', error);
      return [];
    }
  },

  /**
   * 查询关系
   */
  async queryRelationships(params?: {
    types?: string[];
    startNode?: string;
    endNode?: string;
    limit?: number;
  }): Promise<Neo4jRelationship[]> {
    try {
      const query = buildQuery(params);
      const response = await apiGatewayClient.get(`/api/neo4j/relationships${query}`);
      return (response as any).relationships || [];
    } catch (error) {
      console.error('Failed to query relationships:', error);
      return [];
    }
  },

  /**
   * 执行Cypher查询
   */
  async executeCypher(query: string, params?: Record<string, any>): Promise<any> {
    try {
      return await apiGatewayClient.post(`/api/neo4j/cypher`, { query, params });
    } catch (error) {
      console.error('Failed to execute Cypher query:', error);
      return null;
    }
  },

  /**
   * 获取节点详情
   */
  async getNodeDetails(nodeId: string): Promise<Neo4jNode | null> {
    try {
      return await apiGatewayClient.get(`/api/neo4j/nodes/${nodeId}`);
    } catch (error) {
      console.error('Failed to get node details:', error);
      return null;
    }
  },

  /**
   * 获取节点的邻居节点
   */
  async getNodeNeighbors(
    nodeId: string,
    params?: {
      depth?: number;
      relationshipTypes?: string[];
      limit?: number;
    }
  ): Promise<GraphData> {
    try {
      const query = buildQuery(params);
      return await apiGatewayClient.get(`/api/neo4j/nodes/${nodeId}/neighbors${query}`);
    } catch (error) {
      console.error('Failed to get node neighbors:', error);
      return { nodes: [], links: [] };
    }
  },

  /**
   * 搜索节点（按名称或属性）
   */
  async searchNodes(query: string, limit: number = 20): Promise<Neo4jNode[]> {
    try {
      const queryString = buildQuery({ q: query, limit });
      const response = await apiGatewayClient.get(`/api/neo4j/nodes/search${queryString}`);
      return (response as any).nodes || [];
    } catch (error) {
      console.error('Failed to search nodes:', error);
      return [];
    }
  },
};

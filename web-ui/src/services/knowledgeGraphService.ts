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

export const knowledgeGraphService = {
  // 获取图谱数据
  async getGraphData(params?: any): Promise<{ nodes: any[]; links: any[] }> {
    try {
      const query = buildQuery(params);
      return await apiGatewayClient.get(`/api/knowledge-graph/graph${query}`);
    } catch (error) {
      console.error('Failed to get graph data:', error);
      return { nodes: [], links: [] };
    }
  },

  // 获取实体列表
  async getEntities(params?: any): Promise<any[]> {
    try {
      const query = buildQuery(params);
      return await apiGatewayClient.get(`/api/knowledge-graph/entities${query}`);
    } catch (error) {
      console.error('Failed to get entities:', error);
      return [];
    }
  },

  // 获取关系列表
  async getRelations(params?: any): Promise<any[]> {
    try {
      const query = buildQuery(params);
      return await apiGatewayClient.get(`/api/knowledge-graph/relations${query}`);
    } catch (error) {
      console.error('Failed to get relations:', error);
      return [];
    }
  },

  // 获取实体详情
  async getEntity(id: string): Promise<any> {
    try {
      return await apiGatewayClient.get(`/api/knowledge-graph/entities/${id}`);
    } catch (error) {
      console.error('Failed to get entity:', error);
      return null;
    }
  },

  // 查询图谱
  async queryGraph(query: string): Promise<any> {
    try {
      return await apiGatewayClient.post(`/api/knowledge-graph/query`, { query });
    } catch (error) {
      console.error('Failed to query graph:', error);
      return { nodes: [], links: [] };
    }
  },
};

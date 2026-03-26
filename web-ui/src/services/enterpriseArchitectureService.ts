import { apiGatewayClient } from '@/lib/api/client';

const buildQuery = (params?: Record<string, any> | string) => {
  if (!params) return '';
  if (typeof params === 'string') {
    if (!params.trim()) return '';
    return params.startsWith('?') ? params : `?${params}`;
  }
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

export const enterpriseArchitectureService = {
  // 获取企业架构总览
  async getOverview(): Promise<any> {
    try {
      return await apiGatewayClient.get('/api/enterprise-architecture/overview');
    } catch (error) {
      console.error('Failed to get EA overview:', error);
      return {
        organization_architecture: {
          organizations_count: 0,
          departments_count: 0,
          teams_count: 0,
          roles_count: 0,
        },
        business_architecture: { processes_count: 0, capabilities_count: 0, services_count: 0 },
        application_architecture: { systems_count: 0, services_count: 0, apis_count: 0 },
        data_architecture: { entities_count: 0, models_count: 0, flows_count: 0 },
        technology_architecture: { components_count: 0, stacks_count: 0, infrastructure_count: 0 },
      };
    }
  },

  // 获取业务架构
  async getBusinessArchitecture(): Promise<any> {
    try {
      return await apiGatewayClient.get('/api/enterprise-architecture/business');
    } catch (error) {
      console.error('Failed to get business architecture:', error);
      return { processes: [], capabilities: [], services: [] };
    }
  },

  // 获取应用架构
  async getApplicationArchitecture(): Promise<any> {
    try {
      return await apiGatewayClient.get('/api/enterprise-architecture/application');
    } catch (error) {
      console.error('Failed to get application architecture:', error);
      return { systems: [], services: [], apis: [] };
    }
  },

  // 获取数据架构
  async getDataArchitecture(): Promise<any> {
    try {
      return await apiGatewayClient.get('/api/enterprise-architecture/data');
    } catch (error) {
      console.error('Failed to get data architecture:', error);
      return { entities: [], models: [], flows: [] };
    }
  },

  // 获取技术架构
  async getTechnologyArchitecture(): Promise<any> {
    try {
      return await apiGatewayClient.get('/api/enterprise-architecture/technology');
    } catch (error) {
      console.error('Failed to get technology architecture:', error);
      return { components: [], stacks: [], infrastructure: [] };
    }
  },

  // 获取架构关系图
  async getGraph(): Promise<any> {
    try {
      return await apiGatewayClient.get('/api/enterprise-architecture/graph');
    } catch (error) {
      console.error('Failed to get architecture graph:', error);
      return { nodes: [], links: [] };
    }
  },

  // 影响分析
  async analyzeImpact(entityId: string, entityType: string): Promise<any> {
    try {
      return await apiGatewayClient.post('/api/enterprise-architecture/impact-analysis', {
        entity_id: entityId,
        entity_type: entityType,
      });
    } catch (error) {
      console.error('Failed to analyze impact:', error);
      return { dependencies: [], impacts: [], risk_level: 'low' };
    }
  },

  // ========== 组织架构API ==========

  // 获取组织列表
  async getOrganizations(params?: string | Record<string, any>): Promise<any> {
    try {
      const query = buildQuery(params);
      return await apiGatewayClient.get(`/api/enterprise-architecture/organizations${query}`);
    } catch (error) {
      console.error('Failed to get organizations:', error);
      return { organizations: [], total: 0 };
    }
  },

  // 获取组织详情
  async getOrganization(orgId: string): Promise<any> {
    try {
      return await apiGatewayClient.get(`/api/enterprise-architecture/organizations/${orgId}`);
    } catch (error) {
      console.error('Failed to get organization:', error);
      throw error;
    }
  },

  // 获取组织层级结构
  async getOrganizationHierarchy(orgId: string): Promise<any> {
    try {
      const response = await apiGatewayClient.get(
        `/api/enterprise-architecture/organizations/${orgId}/hierarchy`
      );
      // API返回格式: {hierarchy: {...}}，需要提取hierarchy字段
      return (response as any).hierarchy || response || {};
    } catch (error) {
      console.error('Failed to get organization hierarchy:', error);
      return {};
    }
  },

  // 获取组织责任范围
  async getOrganizationResponsibilities(orgId: string): Promise<any> {
    try {
      return await apiGatewayClient.get(
        `/api/enterprise-architecture/organizations/${orgId}/responsibilities`
      );
    } catch (error) {
      console.error('Failed to get organization responsibilities:', error);
      return { capabilities: [], processes: [], systems: [], technologies: [] };
    }
  },

  // 创建组织单元
  async createOrganization(data: any): Promise<any> {
    try {
      return await apiGatewayClient.post(`/api/enterprise-architecture/organizations`, data);
    } catch (error) {
      console.error('Failed to create organization:', error);
      throw error;
    }
  },

  // 更新组织单元
  async updateOrganization(orgId: string, data: any): Promise<any> {
    try {
      return await apiGatewayClient.put(`/api/enterprise-architecture/organizations/${orgId}`, data);
    } catch (error) {
      console.error('Failed to update organization:', error);
      throw error;
    }
  },

  // 删除组织单元
  async deleteOrganization(orgId: string): Promise<any> {
    try {
      return await apiGatewayClient.delete(`/api/enterprise-architecture/organizations/${orgId}`);
    } catch (error) {
      console.error('Failed to delete organization:', error);
      throw error;
    }
  },

  // ========== 技术实例API ==========

  // 获取技术实例列表
  async getTechnologyInstances(params?: string | Record<string, any>): Promise<any> {
    try {
      const query = buildQuery(params);
      return await apiGatewayClient.get(
        `/api/enterprise-architecture/technology/instances${query}`
      );
    } catch (error) {
      console.error('Failed to get technology instances:', error);
      return { instances: [], total: 0 };
    }
  },

  // 创建技术实例
  async createTechnologyInstance(data: any): Promise<any> {
    try {
      return await apiGatewayClient.post(
        `/api/enterprise-architecture/technology/instances`,
        data
      );
    } catch (error) {
      console.error('Failed to create technology instance:', error);
      throw error;
    }
  },

  // 更新技术实例
  async updateTechnologyInstance(instanceId: string, data: any): Promise<any> {
    try {
      return await apiGatewayClient.put(
        `/api/enterprise-architecture/technology/instances/${instanceId}`,
        data
      );
    } catch (error) {
      console.error('Failed to update technology instance:', error);
      throw error;
    }
  },

  // 删除技术实例
  async deleteTechnologyInstance(instanceId: string): Promise<any> {
    try {
      return await apiGatewayClient.delete(
        `/api/enterprise-architecture/technology/instances/${instanceId}`
      );
    } catch (error) {
      console.error('Failed to delete technology instance:', error);
      throw error;
    }
  },

  // 导入技术实例
  async importTechnologyInstances(formData: FormData): Promise<any> {
    try {
      return await apiGatewayClient.request(
        `/api/enterprise-architecture/technology/instances/import`,
        {
          method: 'POST',
          body: formData,
        }
      );
    } catch (error) {
      console.error('Failed to import technology instances:', error);
      throw error;
    }
  },

  // ========== 技术标准化API ==========

  // 获取技术标准化分析
  async getTechnologyStandardization(): Promise<any> {
    try {
      return await apiGatewayClient.get(
        `/api/enterprise-architecture/technology/standardization`
      );
    } catch (error) {
      console.error('Failed to get technology standardization:', error);
      return { technologies: [] };
    }
  },
};

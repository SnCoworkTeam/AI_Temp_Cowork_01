import { apiGatewayClient } from '@/lib/api/client';

export const analyticsService = {
  // 获取统计数据
  async getStats(): Promise<any> {
    try {
      return await apiGatewayClient.get('/api/analytics/stats');
    } catch (error) {
      console.error('Failed to get stats:', error);
      return {
        totalDocuments: 0,
        totalKnowledgeBases: 0,
        totalUsers: 0,
        totalSearches: 0,
      };
    }
  },

  // 获取趋势数据
  async getTrends(): Promise<any> {
    try {
      return await apiGatewayClient.get('/api/analytics/trends');
    } catch (error) {
      console.error('Failed to get trends:', error);
      return {
        documentGrowth: [],
        kbDistribution: [],
        searchTrends: [],
      };
    }
  },

  // 获取用户行为分析
  async getUserBehavior(): Promise<any> {
    try {
      return await apiGatewayClient.get('/api/analytics/user-behavior');
    } catch (error) {
      console.error('Failed to get user behavior:', error);
      return [];
    }
  },
};

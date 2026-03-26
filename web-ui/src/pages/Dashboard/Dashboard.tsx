import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Spin } from 'antd';
import { FileOutlined, DatabaseOutlined, UserOutlined, SearchOutlined } from '@ant-design/icons';
import { StatCard } from '@/components/charts/StatCard';
import { LineChart } from '@/components/charts/LineChart';
import { BarChart } from '@/components/charts/BarChart';
import { analyticsService } from '@/services/analyticsService';

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [trends, setTrends] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [statsData, trendsData] = await Promise.all([
        analyticsService.getStats(),
        analyticsService.getTrends(),
      ]);
      setStats(statsData);
      setTrends(trendsData);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <h1>仪表板</h1>

      <Spin spinning={loading}>
        <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
          <Col xs={24} sm={12} md={6}>
            <StatCard
              title="文档总数"
              value={stats?.totalDocuments || 0}
              icon={<FileOutlined />}
              color="#1890ff"
              loading={loading}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <StatCard
              title="知识库数"
              value={stats?.totalKnowledgeBases || 0}
              icon={<DatabaseOutlined />}
              color="#52c41a"
              loading={loading}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <StatCard
              title="用户数"
              value={stats?.totalUsers || 0}
              icon={<UserOutlined />}
              color="#faad14"
              loading={loading}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <StatCard
              title="搜索次数"
              value={stats?.totalSearches || 0}
              icon={<SearchOutlined />}
              color="#f5222d"
              loading={loading}
            />
          </Col>
        </Row>

        <Row gutter={[16, 16]}>
          <Col xs={24} lg={12}>
            <Card title="文档增长趋势">
              <LineChart
                data={trends?.documentGrowth || []}
                dataKey="value"
                xKey="name"
                height={300}
              />
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card title="知识库文档分布">
              <BarChart
                data={trends?.kbDistribution || []}
                dataKey="value"
                xKey="name"
                height={300}
              />
            </Card>
          </Col>
        </Row>
      </Spin>
    </div>
  );
};

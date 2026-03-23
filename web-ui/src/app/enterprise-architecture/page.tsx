'use client';

'use client';

import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Spin } from 'antd';
import { StatCard } from '@/components/charts/StatCard';
import { enterpriseArchitectureService } from '@/services/enterpriseArchitectureService';

export default function EnterpriseArchitecturePage() {
  const [overview, setOverview] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadOverview();
  }, []);

  const loadOverview = async () => {
    setLoading(true);
    try {
      const data = await enterpriseArchitectureService.getOverview();
      setOverview(data);
    } catch (error) {
      console.error('Failed to load overview:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <h1>企业架构总览</h1>

      <Spin spinning={loading}>
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={12}>
            <Card title="组织架构" style={{ marginBottom: '16px' }}>
              <Row gutter={[16, 16]}>
                <Col span={8}>
                  <StatCard
                    title="组织单元"
                    value={overview?.organization_architecture?.organizations_count || 0}
                    loading={loading}
                  />
                </Col>
                <Col span={8}>
                  <StatCard
                    title="部门"
                    value={overview?.organization_architecture?.departments_count || 0}
                    loading={loading}
                  />
                </Col>
                <Col span={8}>
                  <StatCard
                    title="团队"
                    value={overview?.organization_architecture?.teams_count || 0}
                    loading={loading}
                  />
                </Col>
              </Row>
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <Card title="业务架构" style={{ marginBottom: '16px' }}>
              <Row gutter={[16, 16]}>
                <Col span={8}>
                  <StatCard
                    title="业务流程"
                    value={overview?.business_architecture?.processes_count || 0}
                    loading={loading}
                  />
                </Col>
                <Col span={8}>
                  <StatCard
                    title="业务能力"
                    value={overview?.business_architecture?.capabilities_count || 0}
                    loading={loading}
                  />
                </Col>
                <Col span={8}>
                  <StatCard
                    title="业务服务"
                    value={overview?.business_architecture?.services_count || 0}
                    loading={loading}
                  />
                </Col>
              </Row>
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <Card title="应用架构" style={{ marginBottom: '16px' }}>
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <StatCard
                    title="应用系统"
                    value={overview?.application_architecture?.systems_count || 0}
                    loading={loading}
                  />
                </Col>
                <Col span={12}>
                  <StatCard
                    title="应用服务"
                    value={overview?.application_architecture?.services_count || 0}
                    loading={loading}
                  />
                </Col>
              </Row>
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <Card title="数据架构" style={{ marginBottom: '16px' }}>
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <StatCard
                    title="数据实体"
                    value={overview?.data_architecture?.entities_count || 0}
                    loading={loading}
                  />
                </Col>
                <Col span={12}>
                  <StatCard
                    title="数据模型"
                    value={overview?.data_architecture?.models_count || 0}
                    loading={loading}
                  />
                </Col>
                <Col span={12}>
                  <StatCard
                    title="数据流"
                    value={overview?.data_architecture?.flows_count || 0}
                    loading={loading}
                  />
                </Col>
              </Row>
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <Card title="技术架构" style={{ marginBottom: '16px' }}>
              <Row gutter={[16, 16]}>
                <Col span={8}>
                  <StatCard
                    title="技术组件"
                    value={overview?.technology_architecture?.components_count || 0}
                    loading={loading}
                  />
                </Col>
                <Col span={8}>
                  <StatCard
                    title="技术栈"
                    value={overview?.technology_architecture?.stacks_count || 0}
                    loading={loading}
                  />
                </Col>
                <Col span={8}>
                  <StatCard
                    title="基础设施"
                    value={overview?.technology_architecture?.infrastructure_count || 0}
                    loading={loading}
                  />
                </Col>
              </Row>
            </Card>
          </Col>
        </Row>
      </Spin>
    </div>
  );
}

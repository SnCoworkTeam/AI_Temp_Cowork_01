'use client';

import React, { useState, useEffect } from 'react';
import { Card, Table, Progress, Tag, Statistic, Row, Col, Spin } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { enterpriseArchitectureService } from '@/services/enterpriseArchitectureService';

interface StandardizationResult {
  technology: string;
  category: string;
  standard_version?: string;
  total_instances: number;
  compliant_instances: number;
  non_compliant_instances: number;
  compliance_rate: number;
  versions_in_use: Record<string, number>;
  lifecycle_status: string;
}

export default function TechnologyStandardizationPage() {
  const [data, setData] = useState<StandardizationResult[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchStandardization();
  }, []);

  const fetchStandardization = async () => {
    setLoading(true);
    try {
      const result = await enterpriseArchitectureService.getTechnologyStandardization();
      setData(result.technologies || []);
    } catch (error) {
      console.error('Failed to fetch standardization:', error);
    } finally {
      setLoading(false);
    }
  };

  const columns: ColumnsType<StandardizationResult> = [
    {
      title: '技术名称',
      dataIndex: 'technology',
      key: 'technology',
    },
    {
      title: '类别',
      dataIndex: 'category',
      key: 'category',
      render: (category) => <Tag>{category}</Tag>,
    },
    {
      title: '标准版本',
      dataIndex: 'standard_version',
      key: 'standard_version',
    },
    {
      title: '实例总数',
      dataIndex: 'total_instances',
      key: 'total_instances',
    },
    {
      title: '合规实例',
      dataIndex: 'compliant_instances',
      key: 'compliant_instances',
    },
    {
      title: '不合规实例',
      dataIndex: 'non_compliant_instances',
      key: 'non_compliant_instances',
    },
    {
      title: '合规率',
      dataIndex: 'compliance_rate',
      key: 'compliance_rate',
      render: (rate) => (
        <Progress
          percent={rate}
          status={rate >= 80 ? 'success' : rate >= 60 ? 'normal' : 'exception'}
        />
      ),
    },
    {
      title: '版本分布',
      dataIndex: 'versions_in_use',
      key: 'versions_in_use',
      render: (versions) => (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
          {Object.entries(versions || {}).map(([version, count]) => (
            <Tag key={version}>
              {version}: {count}
            </Tag>
          ))}
        </div>
      ),
    },
    {
      title: '生命周期',
      dataIndex: 'lifecycle_status',
      key: 'lifecycle_status',
      render: (status) => (
        <Tag color={status === 'strategic' ? 'green' : status === 'tactical' ? 'orange' : 'red'}>
          {status}
        </Tag>
      ),
    },
  ];

  const totalTechnologies = data.length;
  const avgComplianceRate =
    data.length > 0 ? data.reduce((sum, item) => sum + item.compliance_rate, 0) / data.length : 0;
  const highComplianceCount = data.filter((d) => d.compliance_rate >= 80).length;

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ marginBottom: '24px' }}>技术标准化分析</h1>

      <Spin spinning={loading}>
        <Card title="统计概览" style={{ marginBottom: '24px' }}>
          <Row gutter={16}>
            <Col span={8}>
              <Statistic title="技术总数" value={totalTechnologies} />
            </Col>
            <Col span={8}>
              <Statistic title="平均合规率" value={avgComplianceRate.toFixed(2)} suffix="%" />
            </Col>
            <Col span={8}>
              <Statistic
                title="高合规率技术"
                value={highComplianceCount}
                suffix={`/ ${totalTechnologies}`}
              />
            </Col>
          </Row>
        </Card>

        <Card>
          <Table
            columns={columns}
            dataSource={data}
            rowKey="technology"
            loading={loading}
            pagination={{ pageSize: 20 }}
          />
        </Card>
      </Spin>
    </div>
  );
}

'use client';

import React, { useState, useEffect } from 'react';
import { Card, Table, Spin, Tag, Space } from 'antd';
import { enterpriseArchitectureService } from '@/services/enterpriseArchitectureService';

export default function BusinessArchitecturePage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const result = await enterpriseArchitectureService.getBusinessArchitecture();
      setData(result);
    } catch (error) {
      console.error('Failed to load business architecture:', error);
    } finally {
      setLoading(false);
    }
  };

  const processColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '负责人', dataIndex: 'owner', key: 'owner' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'default'}>{status}</Tag>
      ),
    },
    { title: '分类', dataIndex: 'classification', key: 'classification' },
  ];

  const capabilityColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '层级', dataIndex: 'level', key: 'level' },
  ];

  const serviceColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '服务类型', dataIndex: 'service_type', key: 'service_type' },
    { title: '端点', dataIndex: 'endpoint', key: 'endpoint' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'default'}>{status}</Tag>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <h1>业务架构</h1>

      <Spin spinning={loading}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Card title="业务流程" extra={`共 ${data?.processes?.length || 0} 个流程`}>
            <Table
              dataSource={data?.processes || []}
              columns={processColumns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Card>

          <Card title="业务能力" extra={`共 ${data?.capabilities?.length || 0} 个能力`}>
            <Table
              dataSource={data?.capabilities || []}
              columns={capabilityColumns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Card>

          <Card title="业务服务" extra={`共 ${data?.services?.length || 0} 个服务`}>
            <Table
              dataSource={data?.services || []}
              columns={serviceColumns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </Space>
      </Spin>
    </div>
  );
}

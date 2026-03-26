'use client';

import React, { useState, useEffect } from 'react';
import { Card, Table, Spin, Tag, Space } from 'antd';
import { enterpriseArchitectureService } from '@/services/enterpriseArchitectureService';

export default function ApplicationArchitecturePage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const result = await enterpriseArchitectureService.getApplicationArchitecture();
      setData(result);
    } catch (error) {
      console.error('Failed to load application architecture:', error);
    } finally {
      setLoading(false);
    }
  };

  const systemColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '系统类型', dataIndex: 'system_type', key: 'system_type' },
    { title: '供应商', dataIndex: 'vendor', key: 'vendor' },
    { title: '版本', dataIndex: 'version', key: 'version' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'default'}>{status}</Tag>
      ),
    },
    { title: '负责人', dataIndex: 'owner', key: 'owner' },
  ];

  const serviceColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '服务类型', dataIndex: 'service_type', key: 'service_type' },
    { title: '协议', dataIndex: 'protocol', key: 'protocol' },
    { title: '端点', dataIndex: 'endpoint', key: 'endpoint' },
  ];

  const apiColumns = [
    { title: '路径', dataIndex: 'path', key: 'path' },
    {
      title: '方法',
      dataIndex: 'method',
      key: 'method',
      render: (method: string) => <Tag>{method}</Tag>,
    },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <h1>应用架构</h1>

      <Spin spinning={loading}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Card title="应用系统" extra={`共 ${data?.systems?.length || 0} 个系统`}>
            <Table
              dataSource={data?.systems || []}
              columns={systemColumns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Card>

          <Card title="应用服务" extra={`共 ${data?.services?.length || 0} 个服务`}>
            <Table
              dataSource={data?.services || []}
              columns={serviceColumns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Card>

          <Card title="API接口" extra={`共 ${data?.apis?.length || 0} 个接口`}>
            <Table
              dataSource={data?.apis || []}
              columns={apiColumns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </Space>
      </Spin>
    </div>
  );
}

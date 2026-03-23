'use client';

import React, { useState, useEffect } from 'react';
import { Card, Table, Spin, Space } from 'antd';
import { enterpriseArchitectureService } from '@/services/enterpriseArchitectureService';

export default function TechnologyArchitecturePage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const result = await enterpriseArchitectureService.getTechnologyArchitecture();
      setData(result);
    } catch (error) {
      console.error('Failed to load technology architecture:', error);
    } finally {
      setLoading(false);
    }
  };

  const componentColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '组件类型', dataIndex: 'component_type', key: 'component_type' },
    { title: '版本', dataIndex: 'version', key: 'version' },
  ];

  const stackColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '类别', dataIndex: 'category', key: 'category' },
  ];

  const infrastructureColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '组件类型', dataIndex: 'component_type', key: 'component_type' },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <h1>技术架构</h1>

      <Spin spinning={loading}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Card title="技术组件" extra={`共 ${data?.components?.length || 0} 个组件`}>
            <Table
              dataSource={data?.components || []}
              columns={componentColumns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Card>

          <Card title="技术栈" extra={`共 ${data?.stacks?.length || 0} 个技术栈`}>
            <Table
              dataSource={data?.stacks || []}
              columns={stackColumns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Card>

          <Card title="基础设施组件" extra={`共 ${data?.infrastructure?.length || 0} 个组件`}>
            <Table
              dataSource={data?.infrastructure || []}
              columns={infrastructureColumns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </Space>
      </Spin>
    </div>
  );
}

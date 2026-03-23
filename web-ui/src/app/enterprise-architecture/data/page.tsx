'use client';

import React, { useState, useEffect } from 'react';
import { Card, Table, Spin, Space } from 'antd';
import { enterpriseArchitectureService } from '@/services/enterpriseArchitectureService';

export default function DataArchitecturePage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const result = await enterpriseArchitectureService.getDataArchitecture();
      setData(result);
    } catch (error) {
      console.error('Failed to load data architecture:', error);
    } finally {
      setLoading(false);
    }
  };

  const entityColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '实体类型', dataIndex: 'entity_type', key: 'entity_type' },
  ];

  const modelColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '版本', dataIndex: 'version', key: 'version' },
  ];

  const flowColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '源实体', dataIndex: 'source_entity_id', key: 'source_entity_id' },
    { title: '目标实体', dataIndex: 'target_entity_id', key: 'target_entity_id' },
    { title: '转换规则', dataIndex: 'transformation', key: 'transformation', ellipsis: true },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <h1>数据架构</h1>

      <Spin spinning={loading}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Card title="数据实体" extra={`共 ${data?.entities?.length || 0} 个实体`}>
            <Table
              dataSource={data?.entities || []}
              columns={entityColumns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Card>

          <Card title="数据模型" extra={`共 ${data?.models?.length || 0} 个模型`}>
            <Table
              dataSource={data?.models || []}
              columns={modelColumns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Card>

          <Card title="数据流" extra={`共 ${data?.flows?.length || 0} 个数据流`}>
            <Table
              dataSource={data?.flows || []}
              columns={flowColumns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </Space>
      </Spin>
    </div>
  );
}

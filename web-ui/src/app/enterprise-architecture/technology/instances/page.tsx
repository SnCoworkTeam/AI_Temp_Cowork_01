'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Spin,
  Tag,
  Space,
  Button,
  Select,
  Upload,
  message,
  Modal,
  Form,
  Input,
} from 'antd';
import {
  UploadOutlined,
  DownloadOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { enterpriseArchitectureService } from '@/services/enterpriseArchitectureService';

interface TechnologyInstance {
  id: string;
  name: string;
  instance_id?: string;
  technology_type: string;
  technology_name: string;
  version?: string;
  vendor?: string;
  deployment_type: string;
  host?: string;
  port?: number;
  location?: string;
  status: string;
  application_system_id?: string;
}

export default function TechnologyInstancesPage() {
  const [instances, setInstances] = useState<TechnologyInstance[]>([]);
  const [loading, setLoading] = useState(false);
  const [systemFilter, setSystemFilter] = useState<string | undefined>();
  const [technologyFilter, setTechnologyFilter] = useState<string | undefined>();
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedInstance, setSelectedInstance] = useState<TechnologyInstance | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchInstances();
  }, [systemFilter, technologyFilter]);

  const fetchInstances = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (systemFilter) params.append('system_id', systemFilter);
      if (technologyFilter) params.append('technology_name', technologyFilter);

      const result = await enterpriseArchitectureService.getTechnologyInstances(params.toString());
      setInstances(result.instances || []);
    } catch (error) {
      console.error('Failed to fetch instances:', error);
      message.error('获取技术实例失败');
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const result = await enterpriseArchitectureService.importTechnologyInstances(formData);

      if (result.success > 0) {
        message.success(`成功导入 ${result.success} 条记录`);
        fetchInstances();
      } else {
        message.error(`导入失败: ${result.errors?.join(', ') || '未知错误'}`);
      }
    } catch (error) {
      message.error('导入失败');
    }
  };

  const handleCreate = () => {
    setSelectedInstance(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (instance: TechnologyInstance) => {
    setSelectedInstance(instance);
    form.setFieldsValue(instance);
    setModalVisible(true);
  };

  const handleDelete = async (instanceId: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个技术实例吗？',
      onOk: async () => {
        try {
          await enterpriseArchitectureService.deleteTechnologyInstance(instanceId);
          message.success('删除成功');
          fetchInstances();
        } catch (error) {
          message.error('删除失败');
        }
      },
    });
  };

  const handleSubmit = async (values: any) => {
    try {
      if (selectedInstance) {
        await enterpriseArchitectureService.updateTechnologyInstance(selectedInstance.id, values);
        message.success('更新成功');
      } else {
        await enterpriseArchitectureService.createTechnologyInstance(values);
        message.success('创建成功');
      }
      setModalVisible(false);
      form.resetFields();
      fetchInstances();
    } catch (error) {
      message.error(selectedInstance ? '更新失败' : '创建失败');
    }
  };

  const columns: ColumnsType<TechnologyInstance> = [
    {
      title: '实例名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '技术类型',
      dataIndex: 'technology_type',
      key: 'technology_type',
      render: (type) => <Tag>{type}</Tag>,
    },
    {
      title: '技术名称',
      dataIndex: 'technology_name',
      key: 'technology_name',
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
    },
    {
      title: '供应商',
      dataIndex: 'vendor',
      key: 'vendor',
    },
    {
      title: '部署类型',
      dataIndex: 'deployment_type',
      key: 'deployment_type',
      render: (type) => (
        <Tag color={type === 'independent' ? 'blue' : type === 'shared' ? 'green' : 'orange'}>
          {type}
        </Tag>
      ),
    },
    {
      title: '位置',
      dataIndex: 'location',
      key: 'location',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => <Tag color={status === 'active' ? 'green' : 'red'}>{status}</Tag>,
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: TechnologyInstance) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title="技术实例管理"
        extra={
          <Space>
            <Upload
              accept=".xlsx,.xls"
              beforeUpload={(file) => {
                handleImport(file);
                return false;
              }}
              showUploadList={false}
            >
              <Button icon={<UploadOutlined />}>导入Excel</Button>
            </Upload>
            <Button icon={<DownloadOutlined />}>下载模板</Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
              新建实例
            </Button>
          </Space>
        }
      >
        <Space style={{ marginBottom: '16px' }}>
          <Select
            placeholder="筛选系统"
            style={{ width: 200 }}
            allowClear
            onChange={setSystemFilter}
          >
            {/* 从API获取系统列表 */}
          </Select>
          <Select
            placeholder="筛选技术"
            style={{ width: 200 }}
            allowClear
            onChange={setTechnologyFilter}
          >
            {/* 从API获取技术列表 */}
          </Select>
        </Space>

        <Table
          columns={columns}
          dataSource={instances}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      <Modal
        title={selectedInstance ? '编辑技术实例' : '新建技术实例'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        width={700}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
            name="name"
            label="实例名称"
            rules={[{ required: true, message: '请输入实例名称' }]}
          >
            <Input placeholder="例如: Oracle-SAP-ERP-001" />
          </Form.Item>

          <Form.Item name="instance_id" label="实例标识">
            <Input placeholder="请输入实例标识" />
          </Form.Item>

          <Form.Item
            name="technology_type"
            label="技术类型"
            rules={[{ required: true, message: '请选择技术类型' }]}
          >
            <Select placeholder="请选择技术类型">
              <Select.Option value="Database">数据库</Select.Option>
              <Select.Option value="Middleware">中间件</Select.Option>
              <Select.Option value="Infrastructure">基础设施</Select.Option>
              <Select.Option value="AIPlatform">AI平台</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="technology_name"
            label="技术名称"
            rules={[{ required: true, message: '请输入技术名称' }]}
          >
            <Input placeholder="例如: Oracle, Redis, Docker" />
          </Form.Item>

          <Form.Item name="version" label="版本">
            <Input placeholder="例如: 12c, 6.0" />
          </Form.Item>

          <Form.Item name="vendor" label="供应商">
            <Input placeholder="请输入供应商" />
          </Form.Item>

          <Form.Item name="deployment_type" label="部署类型" initialValue="independent">
            <Select>
              <Select.Option value="independent">独立</Select.Option>
              <Select.Option value="dedicated">专用</Select.Option>
              <Select.Option value="shared">共享</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="host" label="主机地址">
            <Input placeholder="请输入主机地址" />
          </Form.Item>

          <Form.Item name="port" label="端口">
            <Input type="number" placeholder="请输入端口" />
          </Form.Item>

          <Form.Item name="location" label="部署位置">
            <Input placeholder="请输入部署位置" />
          </Form.Item>

          <Form.Item name="status" label="状态" initialValue="active">
            <Select>
              <Select.Option value="active">活跃</Select.Option>
              <Select.Option value="inactive">非活跃</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

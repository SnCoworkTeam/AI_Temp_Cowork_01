'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Spin,
  Tag,
  Space,
  Button,
  Tree,
  Row,
  Col,
  Statistic,
  Modal,
  Form,
  Input,
  Select,
  message,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UserOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import { enterpriseArchitectureService } from '@/services/enterpriseArchitectureService';
import type { DataNode } from 'antd/es/tree';

interface OrganizationUnit {
  id: string;
  name: string;
  code?: string;
  description?: string;
  organization_type?: string;
  level: number;
  parent_id?: string;
  manager_id?: string;
  location?: string;
  status?: string;
}

export default function OrganizationArchitecturePage() {
  const [organizations, setOrganizations] = useState<OrganizationUnit[]>([]);
  const [hierarchy, setHierarchy] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [selectedOrg, setSelectedOrg] = useState<OrganizationUnit | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    loadOrganizations();
    loadRootHierarchy();
  }, []);

  const loadOrganizations = async () => {
    setLoading(true);
    try {
      const result = await enterpriseArchitectureService.getOrganizations();
      setOrganizations(result.organizations || []);
    } catch (error) {
      console.error('Failed to load organizations:', error);
      message.error('加载组织列表失败');
    } finally {
      setLoading(false);
    }
  };

  const loadRootHierarchy = async () => {
    try {
      // 获取根组织
      const orgs = await enterpriseArchitectureService.getOrganizations();
      console.log('[Organization] Loaded organizations:', orgs);
      const rootOrgs = orgs.organizations?.filter((org: OrganizationUnit) => !org.parent_id) || [];
      console.log('[Organization] Root organizations:', rootOrgs);

      if (rootOrgs.length > 0) {
        const rootId = rootOrgs[0].id;
        console.log('[Organization] Loading hierarchy for root org:', rootId);
        const hierarchyData = await enterpriseArchitectureService.getOrganizationHierarchy(rootId);
        console.log('[Organization] Hierarchy data received:', hierarchyData);
        setHierarchy(hierarchyData);
      } else {
        console.warn('[Organization] No root organizations found');
        setHierarchy(null);
      }
    } catch (error) {
      console.error('Failed to load hierarchy:', error);
      setHierarchy(null);
    }
  };

  const loadOrganizationHierarchy = async (orgId: string) => {
    try {
      const hierarchyData = await enterpriseArchitectureService.getOrganizationHierarchy(orgId);
      setHierarchy(hierarchyData);
    } catch (error) {
      console.error('Failed to load hierarchy:', error);
      message.error('加载组织层级失败');
    }
  };

  const handleCreate = () => {
    setSelectedOrg(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (org: OrganizationUnit) => {
    setSelectedOrg(org);
    form.setFieldsValue(org);
    setModalVisible(true);
  };

  const handleDelete = async (orgId: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个组织单元吗？',
      onOk: async () => {
        try {
          await enterpriseArchitectureService.deleteOrganization(orgId);
          message.success('删除成功');
          loadOrganizations();
          loadRootHierarchy();
        } catch (error) {
          message.error('删除失败');
        }
      },
    });
  };

  const handleSubmit = async (values: any) => {
    try {
      if (selectedOrg) {
        await enterpriseArchitectureService.updateOrganization(selectedOrg.id, values);
        message.success('更新成功');
      } else {
        await enterpriseArchitectureService.createOrganization(values);
        message.success('创建成功');
      }
      setModalVisible(false);
      form.resetFields();
      loadOrganizations();
      loadRootHierarchy();
    } catch (error) {
      message.error(selectedOrg ? '更新失败' : '创建失败');
    }
  };

  const convertToTreeData = (data: any): DataNode[] => {
    if (!data || !data.id) {
      console.warn('[Organization] Invalid hierarchy data:', data);
      return [];
    }

    return [
      {
        key: data.id,
        title: (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>{data.name}</span>
            {data.code && <Tag size="small">{data.code}</Tag>}
            <Tag size="small">L{data.level || 1}</Tag>
          </div>
        ),
        children:
          data.children && data.children.length > 0
            ? data.children.map((child: any) => convertToTreeData(child)[0]).filter(Boolean)
            : undefined,
      },
    ];
  };

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '编码',
      dataIndex: 'code',
      key: 'code',
    },
    {
      title: '类型',
      dataIndex: 'organization_type',
      key: 'organization_type',
      render: (type: string) => <Tag>{type || '未分类'}</Tag>,
    },
    {
      title: '层级',
      dataIndex: 'level',
      key: 'level',
      render: (level: number) => <Tag>L{level}</Tag>,
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
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'default'}>{status || 'active'}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: OrganizationUnit) => (
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

  const stats = {
    total: organizations.length,
    active: organizations.filter((org) => org.status === 'active').length,
    departments: organizations.filter((org) => org.organization_type === 'department').length,
    teams: organizations.filter((org) => org.organization_type === 'team').length,
  };

  return (
    <div style={{ padding: '24px' }}>
      <div
        style={{
          marginBottom: '24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <h1>组织架构</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建组织单元
        </Button>
      </div>

      <Spin spinning={loading}>
        <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
          <Col span={6}>
            <Card>
              <Statistic title="组织总数" value={stats.total} prefix={<TeamOutlined />} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="活跃组织" value={stats.active} prefix={<UserOutlined />} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="部门" value={stats.departments} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="团队" value={stats.teams} />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Card
              title="组织层级结构"
              extra={
                <Button size="small" onClick={loadRootHierarchy}>
                  刷新
                </Button>
              }
            >
              {hierarchy ? (
                <Tree
                  defaultExpandAll
                  treeData={convertToTreeData(hierarchy)}
                  onSelect={(selectedKeys) => {
                    if (selectedKeys.length > 0) {
                      loadOrganizationHierarchy(selectedKeys[0] as string);
                    }
                  }}
                />
              ) : (
                <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                  暂无组织层级数据
                </div>
              )}
            </Card>
          </Col>

          <Col span={12}>
            <Card title="组织列表" extra={`共 ${organizations.length} 个组织`}>
              <Table
                dataSource={organizations}
                columns={columns}
                rowKey="id"
                pagination={{ pageSize: 10 }}
                size="small"
              />
            </Card>
          </Col>
        </Row>
      </Spin>

      <Modal
        title={selectedOrg ? '编辑组织单元' : '新建组织单元'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
            name="name"
            label="组织名称"
            rules={[{ required: true, message: '请输入组织名称' }]}
          >
            <Input placeholder="请输入组织名称" />
          </Form.Item>

          <Form.Item name="code" label="组织编码">
            <Input placeholder="请输入组织编码" />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="请输入描述" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="organization_type" label="组织类型">
                <Select placeholder="请选择组织类型">
                  <Select.Option value="department">部门</Select.Option>
                  <Select.Option value="team">团队</Select.Option>
                  <Select.Option value="division">事业部</Select.Option>
                  <Select.Option value="company">公司</Select.Option>
                </Select>
              </Form.Item>
            </Col>

            <Col span={12}>
              <Form.Item name="level" label="层级" initialValue={1}>
                <Input type="number" min={1} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="location" label="位置">
            <Input placeholder="请输入位置" />
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

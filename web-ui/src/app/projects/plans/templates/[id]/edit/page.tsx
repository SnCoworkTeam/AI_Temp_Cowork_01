'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Form, Input, Button, Select, message, Card, Spin, Switch } from 'antd';
import { ArrowLeft, Save } from 'lucide-react';
import { getAccessToken } from '@/lib/auth';
import { apiGatewayClient } from '@/lib/api/client';

const { TextArea } = Input;
const { Option } = Select;

interface BasicDataCategory {
  id: string;
  name: string;
  code: string;
  category_type: string;
}

interface ProjectTemplate {
  id: string;
  template_code: string;
  name: string;
  description?: string;
  category_id?: string;
  category_name?: string;
  template_structure?: {
    phases?: Array<{ category_id: string; sequence: number }>;
  };
  is_active: boolean;
}

export default function EditTemplatePage() {
  const router = useRouter();
  const params = useParams();
  const templateId = params.id as string;
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [loadingTemplate, setLoadingTemplate] = useState(true);
  const [categories, setCategories] = useState<BasicDataCategory[]>([]);
  const [phaseCategories, setPhaseCategories] = useState<BasicDataCategory[]>([]);
  const [loadingCategories, setLoadingCategories] = useState(false);
  const [template, setTemplate] = useState<ProjectTemplate | null>(null);

  useEffect(() => {
    if (templateId) {
      fetchTemplate();
      fetchCategories();
    }
  }, [templateId]);

  const fetchTemplate = async () => {
    setLoadingTemplate(true);
    try {
      const data = await apiGatewayClient.get<ProjectTemplate>(`/api/v1/project-templates/${templateId}`);
      setTemplate(data);

      // 从 template_structure 中提取 phase_category_ids
      const phaseCategoryIds = data.template_structure?.phases
        ?.sort((a, b) => (a.sequence || 0) - (b.sequence || 0))
        .map((phase) => phase.category_id) || [];

      // 设置表单初始值
      form.setFieldsValue({
        template_code: data.template_code,
        name: data.name,
        description: data.description,
        category_id: data.category_id,
        phase_category_ids: phaseCategoryIds,
        is_active: data.is_active,
      });
    } catch (error: any) {
      console.error('获取模板失败:', error);
      message.error(error?.message || '获取模板失败');
      router.push('/projects/plans/templates');
    } finally {
      setLoadingTemplate(false);
    }
  };

  const fetchCategories = async () => {
    setLoadingCategories(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      // 获取所有基础数据分类
      const response = await fetch(`${apiUrl}/api/v1/basic-data/categories`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        const allCategories = data.items || [];

        // 筛选模板分类
        setCategories(allCategories.filter((cat: BasicDataCategory) =>
          cat.category_type === 'project_template' || cat.category_type === 'template'
        ));

        // 筛选阶段分类
        setPhaseCategories(allCategories.filter((cat: BasicDataCategory) =>
          cat.category_type === 'project_phase'
        ));
      }
    } catch (error) {
      console.error('获取分类失败:', error);
      message.warning('获取分类失败，可以继续编辑模板');
    } finally {
      setLoadingCategories(false);
    }
  };

  const formatErrorMessage = (errorData: any): string => {
    if (!errorData) return '操作失败';

    if (typeof errorData.detail === 'string') {
      return errorData.detail;
    }

    if (Array.isArray(errorData.detail)) {
      return errorData.detail
        .map((err: any) => {
          if (typeof err === 'string') return err;
          if (err.msg) return err.msg;
          if (err.message) return err.message;
          return JSON.stringify(err);
        })
        .join('; ');
    }

    if (typeof errorData.detail === 'object') {
      if (errorData.detail.message) return errorData.detail.message;
      if (errorData.detail.msg) return errorData.detail.msg;
    }

    if (typeof errorData === 'string') {
      return errorData;
    }

    if (errorData.message) {
      return errorData.message;
    }

    return '操作失败';
  };

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const requestData = {
        name: values.name,
        description: values.description || null,
        category_id: values.category_id || null,
        phase_category_ids: values.phase_category_ids || [],
        is_active: values.is_active !== undefined ? values.is_active : true,
      };

      const response = await fetch(`${apiUrl}/api/v1/project-templates/${templateId}`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (response.ok) {
        message.success('模板更新成功');
        router.push('/projects/plans/templates');
      } else {
        const errorData = await response.json().catch(() => ({ detail: '更新模板失败' }));
        message.error(formatErrorMessage(errorData));
      }
    } catch (error) {
      console.error('更新模板失败:', error);
      message.error('更新模板失败');
    } finally {
      setLoading(false);
    }
  };

  if (loadingTemplate) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 p-6">
        <div className="flex justify-center items-center h-64">
          <Spin size="large" />
        </div>
      </div>
    );
  }

  if (!template) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 p-6">
        <div className="text-center py-12">
          <p className="text-gray-600">模板不存在</p>
          <Button onClick={() => router.push('/projects/plans/templates')} className="mt-4">
            返回模板列表
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 p-6">
      {/* 头部 */}
      <div className="flex items-center gap-4">
        <Button
          onClick={() => router.back()}
          icon={<ArrowLeft className="w-5 h-5" />}
        >
          返回
        </Button>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">编辑计划模板</h1>
          <p className="text-gray-600 mt-1">编辑项目计划模板：{template.name}</p>
        </div>
      </div>

      {/* 表单 */}
      <Card>
        <Spin spinning={loadingCategories}>
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            autoComplete="off"
          >
            <Form.Item
              label="模板编码"
              name="template_code"
            >
              <Input placeholder="例如: TEMPLATE_001" disabled />
              <div className="text-xs text-gray-500 mt-1">模板编码创建后不可修改</div>
            </Form.Item>

            <Form.Item
              label="模板名称"
              name="name"
              rules={[{ required: true, message: '请输入模板名称' }]}
            >
              <Input placeholder="例如: 标准软件开发项目模板" />
            </Form.Item>

            <Form.Item
              label="模板描述"
              name="description"
            >
              <TextArea
                rows={4}
                placeholder="请输入模板描述"
              />
            </Form.Item>

            <Form.Item
              label="模板分类"
              name="category_id"
            >
              <Select
                placeholder="选择模板分类（可选）"
                allowClear
                showSearch
                filterOption={(input, option) =>
                  (option?.children as string)?.toLowerCase().includes(input.toLowerCase())
                }
              >
                {categories.map((category) => (
                  <Option key={category.id} value={category.id}>
                    {category.name} ({category.code})
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              label="项目阶段"
              name="phase_category_ids"
              rules={[{ required: true, message: '请至少选择一个项目阶段' }]}
              extra="选择模板包含的项目阶段，将按顺序创建"
            >
              <Select
                mode="multiple"
                placeholder="选择项目阶段"
                showSearch
                filterOption={(input, option) =>
                  (option?.children as string)?.toLowerCase().includes(input.toLowerCase())
                }
              >
                {phaseCategories.map((category) => (
                  <Option key={category.id} value={category.id}>
                    {category.name} ({category.code})
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              label="是否启用"
              name="is_active"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>

            <Form.Item>
              <div className="flex gap-4 justify-end">
                <Button onClick={() => router.back()}>
                  取消
                </Button>
                <Button type="primary" htmlType="submit" loading={loading} icon={<Save className="w-4 h-4" />}>
                  保存更改
                </Button>
              </div>
            </Form.Item>
          </Form>
        </Spin>
      </Card>
    </div>
  );
}


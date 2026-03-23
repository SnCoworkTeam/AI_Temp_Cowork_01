'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Form, Input, Button, Select, message, Card, Spin } from 'antd';
import { ArrowLeft, Save } from 'lucide-react';
import { getAccessToken } from '@/lib/auth';

const { TextArea } = Input;
const { Option } = Select;

interface BasicDataCategory {
  id: string;
  name: string;
  code: string;
  category_type: string;
}

export default function CreateTemplatePage() {
  const router = useRouter();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState<BasicDataCategory[]>([]);
  const [phaseCategories, setPhaseCategories] = useState<BasicDataCategory[]>([]);
  const [loadingCategories, setLoadingCategories] = useState(false);

  useEffect(() => {
    fetchCategories();
  }, []);

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
      message.warning('获取分类失败，可以继续创建模板');
    } finally {
      setLoadingCategories(false);
    }
  };

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const requestData = {
        template_code: values.template_code,
        name: values.name,
        description: values.description || null,
        category_id: values.category_id || null,
        phase_category_ids: values.phase_category_ids || [],
      };

      const response = await fetch(`${apiUrl}/api/v1/project-templates`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (response.ok) {
        message.success('模板创建成功');
        router.push('/projects/plans/templates');
      } else {
        const errorData = await response.json().catch(() => ({ detail: '创建模板失败' }));
        // 安全地格式化错误消息
        let errorMessage = '创建模板失败';
        if (errorData.detail) {
          if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else if (Array.isArray(errorData.detail)) {
            errorMessage = errorData.detail
              .map((err: any) => {
                if (typeof err === 'string') return err;
                if (err.msg) return err.msg;
                if (err.message) return err.message;
                return JSON.stringify(err);
              })
              .join('; ');
          } else if (typeof errorData.detail === 'object') {
            errorMessage = errorData.detail.message || errorData.detail.msg || '创建模板失败';
          }
        }
        message.error(errorMessage);
      }
    } catch (error) {
      console.error('创建模板失败:', error);
      message.error('创建模板失败');
    } finally {
      setLoading(false);
    }
  };

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
          <h1 className="text-3xl font-bold text-gray-900">创建计划模板</h1>
          <p className="text-gray-600 mt-1">创建新的项目计划模板</p>
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
              rules={[
                { required: true, message: '请输入模板编码' },
                { pattern: /^[A-Z0-9_-]+$/, message: '模板编码只能包含大写字母、数字、下划线和连字符' },
              ]}
            >
              <Input placeholder="例如: TEMPLATE_001" />
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

            <Form.Item>
              <div className="flex gap-4 justify-end">
                <Button onClick={() => router.back()}>
                  取消
                </Button>
                <Button type="primary" htmlType="submit" loading={loading} icon={<Save className="w-4 h-4" />}>
                  创建模板
                </Button>
              </div>
            </Form.Item>
          </Form>
        </Spin>
      </Card>
    </div>
  );
}


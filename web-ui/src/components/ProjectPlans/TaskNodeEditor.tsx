'use client';

import { useState, useEffect } from 'react';
import {
  Modal,
  Form,
  Input,
  DatePicker,
  Select,
  InputNumber,
  Button,
  message,
} from 'antd';
import dayjs, { type Dayjs } from 'dayjs';
import type { PlanTreeNode } from '@/types/project';

const { TextArea } = Input;
const { RangePicker } = DatePicker;

interface TaskNodeEditorProps {
  visible: boolean;
  mode: 'create' | 'edit';
  phaseId?: string;
  task?: PlanTreeNode;
  onSave: (taskData: TaskFormData) => Promise<void>;
  onCancel: () => void;
}

export interface TaskFormData {
  name: string;
  description?: string;
  category_id: string;
  start_date?: string;
  end_date?: string;
  duration_days?: number;
  assignee_id?: string;
  estimated_hours?: number;
  priority?: string;
  status?: string;
}

export default function TaskNodeEditor({
  visible,
  mode,
  phaseId,
  task,
  onSave,
  onCancel,
}: TaskNodeEditorProps) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState<any[]>([]);

  useEffect(() => {
    if (visible) {
      fetchCategories();
      if (mode === 'edit' && task) {
        form.setFieldsValue({
          name: task.name,
          description: task.description,
          category_id: task.category_id,
          start_date: task.start_date ? dayjs(task.start_date) : undefined,
          end_date: task.end_date ? dayjs(task.end_date) : undefined,
          priority: task.priority || 'medium',
          status: task.status || 'planned',
        });
      } else {
        form.resetFields();
      }
    }
  }, [visible, mode, task, form]);

  const fetchCategories = async () => {
    try {
      const response = await fetch('/api/v1/basic-data/categories?type=task');
      if (response.ok) {
        const data = await response.json();
        setCategories(data.items || []);
      }
    } catch (error) {
      console.error('获取任务分类失败:', error);
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      const taskData: TaskFormData = {
        name: values.name,
        description: values.description,
        category_id: values.category_id,
        start_date: values.date_range
          ? values.date_range[0].format('YYYY-MM-DD')
          : undefined,
        end_date: values.date_range
          ? values.date_range[1].format('YYYY-MM-DD')
          : undefined,
        duration_days: values.duration_days,
        assignee_id: values.assignee_id,
        estimated_hours: values.estimated_hours,
        priority: values.priority || 'medium',
        status: values.status || 'planned',
      };

      await onSave(taskData);
      message.success(mode === 'create' ? '任务创建成功' : '任务更新成功');
      form.resetFields();
      onCancel();
    } catch (error: any) {
      if (error.errorFields) {
        // 表单验证错误
        return;
      }
      message.error(
        mode === 'create' ? '任务创建失败' : '任务更新失败'
      );
      console.error('保存任务失败:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title={mode === 'create' ? '创建任务' : '编辑任务'}
      open={visible}
      onCancel={onCancel}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          取消
        </Button>,
        <Button key="submit" type="primary" loading={loading} onClick={handleSubmit}>
          {mode === 'create' ? '创建' : '保存'}
        </Button>,
      ]}
      width={600}
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="name"
          label="任务名称"
          rules={[{ required: true, message: '请输入任务名称' }]}
        >
          <Input placeholder="请输入任务名称" />
        </Form.Item>

        <Form.Item name="description" label="任务描述">
          <TextArea rows={3} placeholder="请输入任务描述" />
        </Form.Item>

        <Form.Item
          name="category_id"
          label="任务类型"
          rules={[{ required: true, message: '请选择任务类型' }]}
        >
          <Select placeholder="请选择任务类型">
            {categories.map((cat) => (
              <Select.Option key={cat.id} value={cat.id}>
                {cat.name}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item name="date_range" label="计划日期">
          <RangePicker style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item name="duration_days" label="持续时间（天）">
          <InputNumber min={0} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item name="estimated_hours" label="预估工时（小时）">
          <InputNumber min={0} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item name="priority" label="优先级" initialValue="medium">
          <Select>
            <Select.Option value="low">低</Select.Option>
            <Select.Option value="medium">中</Select.Option>
            <Select.Option value="high">高</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item name="status" label="状态" initialValue="planned">
          <Select>
            <Select.Option value="planned">计划中</Select.Option>
            <Select.Option value="in_progress">进行中</Select.Option>
            <Select.Option value="completed">已完成</Select.Option>
            <Select.Option value="on_hold">暂停</Select.Option>
            <Select.Option value="cancelled">已取消</Select.Option>
          </Select>
        </Form.Item>
      </Form>
    </Modal>
  );
}


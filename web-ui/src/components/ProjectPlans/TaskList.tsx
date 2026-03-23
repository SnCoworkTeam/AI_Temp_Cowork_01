'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Table,
  Button,
  Tag,
  Space,
  Popconfirm,
  message,
  DatePicker,
  Select,
  Input,
  Modal,
  Form,
  InputNumber,
} from 'antd';
import {
  Plus,
  Edit,
  Trash2,
  User,
  Users,
  Calendar,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
} from 'lucide-react';
import { getAccessToken } from '@/lib/auth';
import { getUsers } from '@/lib/api/admin';
import dayjs from 'dayjs';
import type { PlanTreeNode } from '@/types/project';

const { TextArea } = Input;
const { RangePicker } = DatePicker;

interface Task {
  id: string;
  name: string;
  description?: string;
  status: string;
  start_date?: string;
  end_date?: string;
  assignee_id?: string;
  assignee_name?: string;
  participant_ids?: string[];
  participant_names?: string[];
  estimated_hours?: number;
  actual_hours?: number;
  progress_percent?: number;
  priority?: string;
  category_id?: string;
  category_name?: string;
  phase_id?: string;
}

interface TaskListProps {
  nodeId: string;
  nodeType: 'phase' | 'task';
  projectId: string;
  planId: string;
  tree?: any[];
  onRefresh?: () => void;
}

export default function TaskList({ nodeId, nodeType, projectId, planId, tree, onRefresh }: TaskListProps) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [users, setUsers] = useState<any[]>([]);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [form] = Form.useForm();

  // 将错误数据转换为字符串
  const formatErrorMessage = (errorData: any): string => {
    if (!errorData) return '操作失败';

    // 如果 detail 是字符串，直接返回
    if (typeof errorData.detail === 'string') {
      return errorData.detail;
    }

    // 如果 detail 是数组（验证错误），提取所有错误消息
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

    // 如果 detail 是对象，尝试提取消息
    if (typeof errorData.detail === 'object') {
      if (errorData.detail.message) return errorData.detail.message;
      if (errorData.detail.msg) return errorData.detail.msg;
    }

    // 如果 errorData 本身是字符串
    if (typeof errorData === 'string') {
      return errorData;
    }

    // 如果 errorData 有 message 属性
    if (errorData.message) {
      return errorData.message;
    }

    // 默认返回
    return '操作失败';
  };

  // 定义 handleCreate，使用 useCallback 确保稳定性
  const handleCreate = useCallback(() => {
    setEditingTask(null);
    form.resetFields();
    // 设置默认值
    form.setFieldsValue({
      status: 'todo',
      priority: 'medium',
      progress_percent: 0,
    });
    setShowTaskModal(true);
  }, [form]);

  useEffect(() => {
    if (nodeId) {
      fetchTasks();
      fetchUsers();
    }
  }, [nodeId]);

  // 监听创建任务事件
  useEffect(() => {
    const handleCreateTaskEvent = (event: CustomEvent) => {
      const { parentId, parentType } = event.detail;
      if (parentId === nodeId && parentType === nodeType) {
        handleCreate();
      }
    };
    window.addEventListener('createTask' as any, handleCreateTaskEvent as EventListener);
    return () => {
      window.removeEventListener('createTask' as any, handleCreateTaskEvent as EventListener);
    };
  }, [nodeId, nodeType, handleCreate]);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      // 从计划树中获取任务，而不是单独请求
      // 先获取计划树，然后从中提取任务
      const treeResponse = await fetch(`${apiUrl}/api/v1/projects/${projectId}/plans/${planId}/tree`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (treeResponse.ok) {
        const treeData = await treeResponse.json();
        const tree = treeData.tree || [];

        // 递归查找节点及其子任务
        const findNodeAndChildren = (nodes: PlanTreeNode[], targetId: string): PlanTreeNode[] => {
          for (const node of nodes) {
            if (node.id === targetId) {
              // 找到目标节点，返回其子任务
              return node.children || [];
            }
            if (node.children && node.children.length > 0) {
              const found = findNodeAndChildren(node.children, targetId);
              if (found.length > 0 || node.children.some(child => child.id === targetId)) {
                // 如果找到了，返回该节点的子任务
                if (node.id === targetId) {
                  return node.children || [];
                }
                // 继续在子节点中查找
                const childNode = node.children.find(child => child.id === targetId);
                if (childNode) {
                  return childNode.children || [];
                }
              }
            }
          }
          return [];
        };

        const taskNodes = findNodeAndChildren(tree, nodeId);

        // 将 PlanTreeNode 转换为 Task 格式
        const taskList: Task[] = taskNodes
          .filter(node => node.type === 'task')
          .map(node => ({
            id: node.id,
            name: node.name,
            description: node.description,
            status: node.status || 'pending',
            start_date: node.start_date,
            end_date: node.end_date,
            assignee_id: node.assignee_id,
            assignee_name: node.assignee_name,
            participant_ids: node.participants || [],
            estimated_hours: node.estimated_hours,
            actual_hours: node.actual_hours,
            progress_percent: node.progress_percent || 0,
            priority: node.priority,
            category_id: node.category_id,
            category_name: node.category_name,
            phase_id: node.phase_id,
          }));

        setTasks(taskList);
      } else {
        // 如果获取树失败，尝试直接获取任务（作为后备方案）
        console.warn('获取计划树失败，尝试直接获取任务');
        const url =
          nodeType === 'phase'
            ? `${apiUrl}/api/v1/projects/${projectId}/plans/${planId}/tasks?phase_id=${nodeId}`
            : `${apiUrl}/api/v1/projects/${projectId}/plans/${planId}/tasks?parent_task_id=${nodeId}`;

        const response = await fetch(url, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          setTasks(data.items || []);
        } else if (response.status === 405) {
          // 405 Method Not Allowed - API 不支持 GET，使用空列表
          console.warn('API 不支持 GET 方法获取任务列表，使用空列表');
          setTasks([]);
        }
      }
    } catch (error) {
      console.error('获取任务列表失败:', error);
      message.error('获取任务列表失败');
      setTasks([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await getUsers({ page: 1, page_size: 100 });
      const usersList = (response as any).users || (response as any).items || [];
      setUsers(usersList);
    } catch (error) {
      console.error('获取用户列表失败:', error);
    }
  };

  const handleEdit = (task: Task) => {
    setEditingTask(task);
    form.setFieldsValue({
      name: task.name,
      description: task.description,
      status: task.status || 'todo',
      start_date: task.start_date ? dayjs(task.start_date) : undefined,
      end_date: task.end_date ? dayjs(task.end_date) : undefined,
      assignee_id: task.assignee_id,
      participant_ids: task.participant_ids || [],
      estimated_hours: task.estimated_hours,
      actual_hours: task.actual_hours,
      progress_percent: task.progress_percent || 0,
      priority: task.priority || 'medium',
    });
    setShowTaskModal(true);
  };

  const handleDelete = async (taskId: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(
        `${apiUrl}/api/v1/projects/${projectId}/plans/${planId}/tasks/${taskId}`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        message.success('任务删除成功');
        fetchTasks();
        onRefresh?.();
      } else {
        const errorData = await response.json().catch(() => ({ detail: '删除失败' }));
        message.error(formatErrorMessage(errorData));
      }
    } catch (error) {
      console.error('删除任务失败:', error);
      message.error('删除任务失败');
    }
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const taskData = {
        name: values.name,
        description: values.description,
        status: values.status,
        start_date: values.start_date ? values.start_date.format('YYYY-MM-DD') : undefined,
        end_date: values.end_date ? values.end_date.format('YYYY-MM-DD') : undefined,
        assignee_id: values.assignee_id,
        participant_ids: values.participant_ids || [],
        estimated_hours: values.estimated_hours,
        actual_hours: values.actual_hours,
        progress_percent: values.progress_percent || 0,
        priority: values.priority || 'medium',
        phase_id: nodeType === 'phase' ? nodeId : undefined,
        parent_task_id: nodeType === 'task' ? nodeId : undefined,
      };

      const url = editingTask
        ? `${apiUrl}/api/v1/projects/${projectId}/plans/${planId}/tasks/${editingTask.id}`
        : `${apiUrl}/api/v1/projects/${projectId}/plans/${planId}/tasks`;

      const response = await fetch(url, {
        method: editingTask ? 'PUT' : 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(taskData),
      });

      if (response.ok) {
        message.success(editingTask ? '任务更新成功' : '任务创建成功');
        setShowTaskModal(false);
        fetchTasks();
        onRefresh?.();
      } else {
        const errorData = await response.json().catch(() => ({ detail: '保存失败' }));
        message.error(formatErrorMessage(errorData));
      }
    } catch (error: any) {
      if (error.errorFields) {
        return;
      }
      console.error('保存任务失败:', error);
      message.error('保存任务失败');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'todo':
        return 'default';
      case 'in_progress':
        return 'processing';
      case 'completed':
        return 'success';
      case 'on_hold':
        return 'warning';
      case 'cancelled':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusText = (status: string) => {
    const statusMap: Record<string, string> = {
      todo: '待办',
      in_progress: '进行中',
      completed: '已完成',
      on_hold: '暂停',
      cancelled: '已取消',
    };
    return statusMap[status] || status;
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'red';
      case 'medium':
        return 'orange';
      case 'low':
        return 'blue';
      default:
        return 'default';
    }
  };

  const getPriorityText = (priority: string) => {
    const priorityMap: Record<string, string> = {
      high: '高',
      medium: '中',
      low: '低',
    };
    return priorityMap[priority] || priority;
  };

  const columns = [
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>
      ),
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      render: (priority: string) => (
        <Tag color={getPriorityColor(priority)}>{getPriorityText(priority)}</Tag>
      ),
    },
    {
      title: '开始时间',
      dataIndex: 'start_date',
      key: 'start_date',
      width: 120,
      render: (date: string) => (date ? dayjs(date).format('YYYY-MM-DD') : '-'),
    },
    {
      title: '结束时间',
      dataIndex: 'end_date',
      key: 'end_date',
      width: 120,
      render: (date: string) => (date ? dayjs(date).format('YYYY-MM-DD') : '-'),
    },
    {
      title: '负责人',
      dataIndex: 'assignee_name',
      key: 'assignee_name',
      width: 100,
      render: (name: string) => (
        <div className="flex items-center gap-1">
          <User className="w-4 h-4 text-gray-400" />
          <span>{name || '-'}</span>
        </div>
      ),
    },
    {
      title: '参与人',
      dataIndex: 'participant_names',
      key: 'participant_names',
      width: 150,
      render: (names: string[]) => (
        <div className="flex items-center gap-1">
          <Users className="w-4 h-4 text-gray-400" />
          <span>{names && names.length > 0 ? names.join(', ') : '-'}</span>
        </div>
      ),
    },
    {
      title: '预估工时',
      dataIndex: 'estimated_hours',
      key: 'estimated_hours',
      width: 100,
      render: (hours: number) => (hours ? `${hours}小时` : '-'),
    },
    {
      title: '实际工时',
      dataIndex: 'actual_hours',
      key: 'actual_hours',
      width: 100,
      render: (hours: number) => (hours ? `${hours}小时` : '-'),
    },
    {
      title: '进度',
      dataIndex: 'progress_percent',
      key: 'progress_percent',
      width: 100,
      render: (percent: number) => (
        <div className="flex items-center gap-2">
          <div className="flex-1 bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all"
              style={{ width: `${percent || 0}%` }}
            />
          </div>
          <span className="text-sm text-gray-600">{percent || 0}%</span>
        </div>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      fixed: 'right' as const,
      render: (_: any, record: Task) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<Edit className="w-4 h-4" />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除此任务吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<Trash2 className="w-4 h-4" />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          {nodeType === 'phase' ? '阶段任务列表' : '子任务列表'}
        </h3>
        <Button type="primary" icon={<Plus className="w-4 h-4" />} onClick={handleCreate}>
          添加任务
        </Button>
      </div>

      <div className="flex-1 overflow-auto">
        <Table
          columns={columns}
          dataSource={tasks}
          loading={loading}
          rowKey="id"
          scroll={{ x: 1200 }}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </div>

      <Modal
        title={editingTask ? '编辑任务' : '创建任务'}
        open={showTaskModal}
        onCancel={() => {
          setShowTaskModal(false);
          form.resetFields();
        }}
        onOk={handleSave}
        width={700}
        okText="保存"
        cancelText="取消"
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

          <div className="grid grid-cols-2 gap-4">
            <Form.Item
              name="status"
              label="状态"
              initialValue="todo"
              rules={[{ required: true, message: '请选择状态' }]}
            >
              <Select>
                <Select.Option key="todo" value="todo">待办</Select.Option>
                <Select.Option key="in_progress" value="in_progress">进行中</Select.Option>
                <Select.Option key="completed" value="completed">已完成</Select.Option>
                <Select.Option key="on_hold" value="on_hold">暂停</Select.Option>
                <Select.Option key="cancelled" value="cancelled">已取消</Select.Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="priority"
              label="优先级"
              initialValue="medium"
              rules={[{ required: true, message: '请选择优先级' }]}
            >
              <Select>
                <Select.Option key="low" value="low">低</Select.Option>
                <Select.Option key="medium" value="medium">中</Select.Option>
                <Select.Option key="high" value="high">高</Select.Option>
              </Select>
            </Form.Item>

            <Form.Item name="start_date" label="开始时间">
              <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
            </Form.Item>

            <Form.Item name="end_date" label="结束时间">
              <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
            </Form.Item>

            <Form.Item name="assignee_id" label="负责人">
              <Select
                placeholder="请选择负责人"
                showSearch
                optionFilterProp="label"
                allowClear
                options={users.map((user) => ({
                  key: user.id,
                  value: user.id,
                  label: user.full_name || user.username,
                }))}
              />
            </Form.Item>

            <Form.Item name="participant_ids" label="参与人">
              <Select
                mode="multiple"
                placeholder="请选择参与人"
                showSearch
                optionFilterProp="label"
                allowClear
                options={users.map((user) => ({
                  key: user.id,
                  value: user.id,
                  label: user.full_name || user.username,
                }))}
              />
            </Form.Item>

            <Form.Item name="estimated_hours" label="预估工时（小时）">
              <InputNumber min={0} style={{ width: '100%' }} placeholder="请输入预估工时" />
            </Form.Item>

            <Form.Item name="actual_hours" label="实际工时（小时）">
              <InputNumber min={0} style={{ width: '100%' }} placeholder="请输入实际工时" />
            </Form.Item>

            <Form.Item name="progress_percent" label="进度（%）" initialValue={0}>
              <InputNumber
                min={0}
                max={100}
                style={{ width: '100%' }}
                placeholder="请输入进度"
              />
            </Form.Item>
          </div>
        </Form>
      </Modal>
    </div>
  );
}


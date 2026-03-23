'use client';

import { useState, useEffect } from 'react';
import { Card, Button, Input, Select, Empty, Spin, Tag } from 'antd';
import { Search, CheckCircle2, Eye } from 'lucide-react';
import type { ProjectTemplate } from '@/types/project';
import { apiGatewayClient } from '@/lib/api/client';

const { Search: SearchInput } = Input;
const { Option } = Select;

interface TemplateSelectorProps {
  onSelect: (templateId: string | null) => void;
  selectedTemplateId?: string | null;
}

export default function TemplateSelector({
  onSelect,
  selectedTemplateId,
}: TemplateSelectorProps) {
  const [templates, setTemplates] = useState<ProjectTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [filterActive, setFilterActive] = useState<boolean | null>(null);
  const [previewTemplate, setPreviewTemplate] = useState<ProjectTemplate | null>(null);

  useEffect(() => {
    fetchTemplates();
  }, [filterActive]);

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filterActive !== null) {
        params.append('is_active', String(filterActive));
      }
      const query = params.toString();
      const data = await apiGatewayClient.get<{ items: ProjectTemplate[] }>(
        `/api/v1/project-templates${query ? `?${query}` : ''}`
      );
      setTemplates(data.items || []);
    } catch (error) {
      console.error('获取模板列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredTemplates = templates.filter((template) => {
    if (searchText) {
      return (
        template.name.toLowerCase().includes(searchText.toLowerCase()) ||
        template.template_code?.toLowerCase().includes(searchText.toLowerCase())
      );
    }
    return true;
  });

  const handlePreview = (template: ProjectTemplate) => {
    setPreviewTemplate(template);
  };

  const handleSelect = (templateId: string | null) => {
    onSelect(templateId);
    setPreviewTemplate(null);
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <SearchInput
          placeholder="搜索模板名称或编码"
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          prefix={<Search className="w-4 h-4" />}
          className="flex-1"
        />
        <Select
          placeholder="筛选状态"
          value={filterActive}
          onChange={setFilterActive}
          allowClear
          style={{ width: 150 }}
        >
          <Option value={true}>启用</Option>
          <Option value={false}>禁用</Option>
        </Select>
      </div>

      <div className="flex gap-4">
        <div className="flex-1">
          <Spin spinning={loading}>
            {filteredTemplates.length === 0 ? (
              <Empty description="暂无模板" />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredTemplates.map((template) => (
                  <Card
                    key={template.id}
                    className={`cursor-pointer transition-all ${
                      selectedTemplateId === template.id
                        ? 'border-blue-500 shadow-lg'
                        : 'hover:shadow-md'
                    }`}
                    onClick={() => handleSelect(template.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="font-semibold text-lg">
                            {template.name}
                          </h3>
                          {selectedTemplateId === template.id && (
                            <CheckCircle2 className="w-5 h-5 text-blue-500" />
                          )}
                        </div>
                        {template.template_code && (
                          <Tag color="blue" className="mb-2">
                            {template.template_code}
                          </Tag>
                        )}
                        {template.description && (
                          <p className="text-gray-600 text-sm mb-2">
                            {template.description}
                          </p>
                        )}
                        <div className="flex items-center gap-4 text-sm text-gray-500">
                          <span>使用次数: {template.usage_count || 0}</span>
                          <Tag color={template.is_active ? 'green' : 'red'}>
                            {template.is_active ? '启用' : '禁用'}
                          </Tag>
                        </div>
                      </div>
                      <Button
                        type="text"
                        icon={<Eye className="w-4 h-4" />}
                        onClick={(e) => {
                          e.stopPropagation();
                          handlePreview(template);
                        }}
                      >
                        预览
                      </Button>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </Spin>
        </div>

        {previewTemplate && (
          <Card
            title="模板预览"
            className="w-96"
            extra={
              <Button
                type="text"
                onClick={() => setPreviewTemplate(null)}
              >
                关闭
              </Button>
            }
          >
            <div className="space-y-3">
              <div>
                <span className="font-semibold">模板名称:</span>{' '}
                {previewTemplate.name}
              </div>
              {previewTemplate.template_code && (
                <div>
                  <span className="font-semibold">模板编码:</span>{' '}
                  {previewTemplate.template_code}
                </div>
              )}
              {previewTemplate.description && (
                <div>
                  <span className="font-semibold">描述:</span>{' '}
                  {previewTemplate.description}
                </div>
              )}
              {previewTemplate.template_structure &&
                previewTemplate.template_structure.length > 0 && (
                  <div>
                    <span className="font-semibold">包含阶段:</span>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      {previewTemplate.template_structure.map((phase, idx) => (
                        <li key={idx} className="text-sm">
                          {phase.name} (顺序: {phase.sequence})
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              <div className="pt-2 border-t">
                <Button
                  type="primary"
                  block
                  onClick={() => handleSelect(previewTemplate.id)}
                >
                  选择此模板
                </Button>
              </div>
            </div>
          </Card>
        )}
      </div>

      <div className="flex justify-end">
        <Button onClick={() => handleSelect(null)}>不使用模板</Button>
      </div>
    </div>
  );
}

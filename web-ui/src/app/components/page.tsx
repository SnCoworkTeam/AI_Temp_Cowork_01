'use client';

'use client';

import React, { useState } from 'react';
import { Card, Input, Row, Col, Tag } from 'antd';
import { SearchOutlined } from '@ant-design/icons';

// 模拟组件数据
const components = [
  {
    name: 'Button',
    category: '基础组件',
    description: '按钮组件，用于触发操作',
    path: '/components/button',
  },
  {
    name: 'Input',
    category: '基础组件',
    description: '输入框组件，用于用户输入',
    path: '/components/input',
  },
  {
    name: 'Card',
    category: '布局组件',
    description: '卡片组件，用于内容展示',
    path: '/components/card',
  },
  {
    name: 'Table',
    category: '数据展示',
    description: '表格组件，用于数据列表展示',
    path: '/components/table',
  },
  {
    name: 'GraphVisualization',
    category: '可视化',
    description: '图谱可视化组件',
    path: '/components/graph',
  },
  {
    name: 'StatCard',
    category: '数据展示',
    description: '统计卡片组件',
    path: '/components/stat-card',
  },
];

export default function ComponentShowcasePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  const categories = ['all', ...new Set(components.map((c) => c.category))];

  const filteredComponents = components.filter((comp) => {
    const matchesSearch =
      comp.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      comp.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || comp.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div style={{ padding: '24px' }}>
      <h1>组件库</h1>

      <div style={{ marginBottom: '24px' }}>
        <Input
          placeholder="搜索组件..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          prefix={<SearchOutlined />}
          style={{ width: '300px', marginRight: '16px' }}
        />
        <div style={{ marginTop: '16px' }}>
          {categories.map((cat) => (
            <Tag
              key={cat}
              color={selectedCategory === cat ? 'blue' : 'default'}
              onClick={() => setSelectedCategory(cat)}
              style={{ cursor: 'pointer', marginBottom: '8px' }}
            >
              {cat === 'all' ? '全部' : cat}
            </Tag>
          ))}
        </div>
      </div>

      <Row gutter={[16, 16]}>
        {filteredComponents.map((comp) => (
          <Col xs={24} sm={12} md={8} lg={6} key={comp.name}>
            <Card hoverable title={comp.name} onClick={() => (window.location.href = comp.path)}>
              <Tag color="blue" style={{ marginBottom: '8px' }}>
                {comp.category}
              </Tag>
              <p style={{ color: '#8c8c8c', margin: 0 }}>{comp.description}</p>
            </Card>
          </Col>
        ))}
      </Row>

      {filteredComponents.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px', color: '#8c8c8c' }}>
          未找到匹配的组件
        </div>
      )}
    </div>
  );
}

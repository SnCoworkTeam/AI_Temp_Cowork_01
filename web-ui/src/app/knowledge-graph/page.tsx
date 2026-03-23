'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  Input,
  Button,
  Space,
  Spin,
  Tag,
  Descriptions,
  Empty,
  Statistic,
  Row,
  Col,
} from 'antd';
import {
  SearchOutlined,
  ReloadOutlined,
  CloseOutlined,
  NodeIndexOutlined,
  LinkOutlined,
} from '@ant-design/icons';
import dynamic from 'next/dynamic';
import { GraphVisualization } from '@/components/graph/GraphVisualization';
import { knowledgeGraphService } from '@/services/knowledgeGraphService';

export default function KnowledgeGraphPage() {
  const [graphData, setGraphData] = useState<{ nodes: any[]; links: any[] }>({
    nodes: [],
    links: [],
  });
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [dimensions, setDimensions] = useState({ width: 1000, height: 600 });

  useEffect(() => {
    loadGraphData();
    // 计算图谱容器的尺寸（仅在客户端）
    if (typeof window !== 'undefined') {
      const updateDimensions = () => {
        const container = document.getElementById('graph-container');
        if (container) {
          setDimensions({
            width: container.offsetWidth || 1000,
            height: Math.max(600, window.innerHeight - 300),
          });
        } else {
          // 如果容器不存在，使用默认值
          setDimensions({
            width: Math.max(800, window.innerWidth - 600),
            height: 600,
          });
        }
      };
      updateDimensions();
      window.addEventListener('resize', updateDimensions);
      return () => window.removeEventListener('resize', updateDimensions);
    }
  }, []);

  const loadGraphData = async () => {
    setLoading(true);
    try {
      // 使用合适的limit以获取更多数据（避免limit太大导致边数为0）
      const data = await knowledgeGraphService.getGraphData({ limit: 500 });
      setGraphData(data);
      console.log('Loaded graph data:', {
        nodes: data.nodes?.length || 0,
        links: data.links?.length || 0,
      });
    } catch (error) {
      console.error('Failed to load graph data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadGraphData();
      return;
    }

    setLoading(true);
    try {
      const data = await knowledgeGraphService.queryGraph(searchQuery);
      setGraphData(data);
    } catch (error) {
      console.error('Failed to search graph:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNodeClick = async (node: any) => {
    if (node.id) {
      try {
        const entity = await knowledgeGraphService.getEntity(node.id);
        setSelectedNode(entity || node);
      } catch (error) {
        console.error('Failed to get entity:', error);
        setSelectedNode(node);
      }
    } else {
      setSelectedNode(node);
    }
  };

  // 获取节点类型颜色
  const getTypeColor = (type: string) => {
    const colorMap: { [key: string]: string } = {
      sap_module: 'blue',
      sap_sub_module: 'green',
      concept: 'orange',
      entity: 'purple',
      agent: 'magenta',
      document: 'cyan',
      knowledge_base: 'red',
    };
    return colorMap[type] || 'default';
  };

  return (
    <div style={{ padding: '24px', background: '#f0f2f5', minHeight: '100vh' }}>
      <Card
        style={{
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        }}
      >
        {/* 页面标题和统计 */}
        <div style={{ marginBottom: '24px' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '16px',
            }}
          >
            <div>
              <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>
                <NodeIndexOutlined style={{ marginRight: '8px' }} />
                知识图谱
              </h1>
              <p style={{ margin: '8px 0 0 0', color: '#8c8c8c' }}>
                可视化展示知识实体之间的关系网络
              </p>
            </div>
            <Row gutter={16}>
              <Col>
                <Statistic
                  title="节点数"
                  value={graphData.nodes?.length || 0}
                  prefix={<NodeIndexOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
              <Col>
                <Statistic
                  title="关系数"
                  value={graphData.links?.length || 0}
                  prefix={<LinkOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
            </Row>
          </div>

          {/* 搜索栏 */}
          <Space.Compact style={{ width: '100%' }}>
            <Input
              placeholder="搜索实体、关系或关键词..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onPressEnter={handleSearch}
              size="large"
              prefix={<SearchOutlined />}
              style={{
                borderRadius: '6px 0 0 6px',
                fontSize: '14px',
              }}
            />
            <Button
              type="primary"
              icon={<SearchOutlined />}
              onClick={handleSearch}
              size="large"
              style={{ borderRadius: '0' }}
            >
              搜索
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadGraphData}
              size="large"
              style={{ borderRadius: '0 6px 6px 0' }}
            >
              刷新
            </Button>
          </Space.Compact>
        </div>

        {/* 图谱和详情 */}
        <div style={{ display: 'flex', gap: '16px', minHeight: '600px' }}>
          {/* 图谱可视化区域 */}
          <div id="graph-container" style={{ flex: 1, position: 'relative', width: '100%' }}>
            <Spin spinning={loading} tip="加载知识图谱数据...">
              <GraphVisualization
                data={graphData}
                onNodeClick={handleNodeClick}
                width={dimensions.width}
                height={dimensions.height}
                loading={loading}
              />
            </Spin>
          </div>

          {/* 节点详情面板 */}
          {selectedNode ? (
            <Card
              title={
                <div
                  style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                >
                  <span>节点详情</span>
                  <Button
                    type="text"
                    icon={<CloseOutlined />}
                    onClick={() => setSelectedNode(null)}
                    size="small"
                  />
                </div>
              }
              style={{
                width: '360px',
                borderRadius: '8px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              }}
              bodyStyle={{ padding: '16px' }}
            >
              <Descriptions column={1} bordered size="small">
                <Descriptions.Item label="名称">
                  <strong style={{ fontSize: '16px', color: '#1890ff' }}>
                    {selectedNode.name || selectedNode.label || selectedNode.id}
                  </strong>
                </Descriptions.Item>
                {selectedNode.type_cn && (
                  <Descriptions.Item label="类型">
                    <Tag color={getTypeColor(selectedNode.type || selectedNode.group)}>
                      {selectedNode.type_cn}
                    </Tag>
                  </Descriptions.Item>
                )}
                {selectedNode.description && (
                  <Descriptions.Item label="描述">
                    <div style={{ maxHeight: '100px', overflow: 'auto' }}>
                      {selectedNode.description}
                    </div>
                  </Descriptions.Item>
                )}
                {selectedNode.properties && (
                  <>
                    {selectedNode.properties.display_name &&
                      selectedNode.properties.display_name !== selectedNode.name && (
                        <Descriptions.Item label="显示名称">
                          {selectedNode.properties.display_name}
                        </Descriptions.Item>
                      )}
                    {selectedNode.properties.sap_module && (
                      <Descriptions.Item label="SAP模块">
                        {selectedNode.properties.sap_module}
                      </Descriptions.Item>
                    )}
                    {selectedNode.properties.sap_sub_module && (
                      <Descriptions.Item label="SAP子模块">
                        {selectedNode.properties.sap_sub_module}
                      </Descriptions.Item>
                    )}
                    {selectedNode.properties.entity_type && (
                      <Descriptions.Item label="实体类型">
                        {selectedNode.properties.entity_type}
                      </Descriptions.Item>
                    )}
                  </>
                )}
              </Descriptions>

              {selectedNode.properties && Object.keys(selectedNode.properties).length > 0 && (
                <div style={{ marginTop: '16px' }}>
                  <div style={{ marginBottom: '8px', fontWeight: 'bold' }}>其他属性：</div>
                  <div
                    style={{
                      background: '#f5f5f5',
                      padding: '12px',
                      borderRadius: '4px',
                      maxHeight: '200px',
                      overflow: 'auto',
                      fontSize: '12px',
                    }}
                  >
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                      {JSON.stringify(selectedNode.properties, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </Card>
          ) : (
            <Card
              style={{
                width: '360px',
                borderRadius: '8px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                minHeight: '600px',
              }}
            >
              <Empty description="点击图谱中的节点查看详情" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            </Card>
          )}
        </div>
      </Card>
    </div>
  );
}

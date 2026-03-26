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
  Select,
  message,
} from 'antd';
import {
  SearchOutlined,
  ReloadOutlined,
  CloseOutlined,
  NodeIndexOutlined,
  LinkOutlined,
  DatabaseOutlined,
} from '@ant-design/icons';
import dynamic from 'next/dynamic';
import { GraphVisualization } from '@/components/graph/GraphVisualization';
import { neo4jGraphService, GraphData } from '@/services/neo4jGraphService';

const { Option } = Select;

export default function Neo4jGraphPage() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [nodeTypeFilter, setNodeTypeFilter] = useState<string | undefined>(undefined);
  const [dimensions, setDimensions] = useState({ width: 1000, height: 600 });
  const [stats, setStats] = useState({ nodes: 0, links: 0 });

  useEffect(() => {
    loadGraphData();
    if (typeof window !== 'undefined') {
      const updateDimensions = () => {
        const container = document.getElementById('graph-container');
        if (container) {
          setDimensions({
            width: container.offsetWidth || 1000,
            height: Math.max(600, window.innerHeight - 300),
          });
        } else {
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
  }, [nodeTypeFilter]);

  const loadGraphData = async () => {
    setLoading(true);
    try {
      const data = await neo4jGraphService.getGraphData({
        limit: 500,
        nodeType: nodeTypeFilter,
      });
      setGraphData(data);
      setStats({
        nodes: data.nodes?.length || 0,
        links: data.links?.length || 0,
      });
      console.log('Loaded Neo4j graph data:', {
        nodes: data.nodes?.length || 0,
        links: data.links?.length || 0,
      });
    } catch (error) {
      console.error('Failed to load Neo4j graph data:', error);
      message.error('加载图数据失败，请检查Neo4j服务是否正常运行');
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
      const nodes = await neo4jGraphService.searchNodes(searchQuery, 50);
      if (nodes.length === 0) {
        message.info('未找到匹配的节点');
        return;
      }

      // 获取搜索到的节点的邻居
      const nodeIds = nodes.map((n) => n.id);
      const graphData: GraphData = { nodes: [], links: [] };

      // 添加搜索到的节点
      for (const node of nodes) {
        graphData.nodes.push({
          id: node.id,
          label: node.properties?.label || node.properties?.name || node.id,
          type: node.labels?.[0] || 'Unknown',
          properties: node.properties,
        });

        // 获取每个节点的邻居
        const neighbors = await neo4jGraphService.getNodeNeighbors(node.id, {
          depth: 1,
          limit: 10,
        });
        graphData.nodes.push(...neighbors.nodes);
        graphData.links.push(...neighbors.links);
      }

      // 去重节点
      const uniqueNodes = new Map();
      graphData.nodes.forEach((node) => {
        if (!uniqueNodes.has(node.id)) {
          uniqueNodes.set(node.id, node);
        }
      });
      graphData.nodes = Array.from(uniqueNodes.values());

      setGraphData(graphData);
      setStats({
        nodes: graphData.nodes.length,
        links: graphData.links.length,
      });
    } catch (error) {
      console.error('Failed to search nodes:', error);
      message.error('搜索失败');
    } finally {
      setLoading(false);
    }
  };

  const handleNodeClick = async (node: any) => {
    if (node.id) {
      try {
        const nodeDetails = await neo4jGraphService.getNodeDetails(node.id);
        if (nodeDetails) {
          setSelectedNode({
            ...node,
            ...nodeDetails,
            labels: nodeDetails.labels || [node.type],
            properties: nodeDetails.properties || node.properties,
          });
        } else {
          setSelectedNode(node);
        }
      } catch (error) {
        console.error('Failed to get node details:', error);
        setSelectedNode(node);
      }
    } else {
      setSelectedNode(node);
    }
  };

  const getTypeColor = (type: string) => {
    const colorMap: { [key: string]: string } = {
      Entity: 'blue',
      BusinessProcess: 'green',
      ApplicationSystem: 'orange',
      DataEntity: 'purple',
      TechnologyComponent: 'cyan',
      BusinessCapability: 'magenta',
      ApplicationService: 'red',
      DataModel: 'gold',
      TechnologyStack: 'lime',
      InfrastructureComponent: 'geekblue',
    };
    return colorMap[type] || 'default';
  };

  return (
    <div style={{ padding: '24px', background: '#f0f2f5', minHeight: '100vh' }}>
      {/* 标题和统计 */}
      <Card style={{ marginBottom: '16px' }}>
        <Row gutter={16} align="middle">
          <Col flex="auto">
            <Space>
              <DatabaseOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
              <div>
                <h2 style={{ margin: 0 }}>Neo4j图数据库可视化</h2>
                <p style={{ margin: 0, color: '#666', fontSize: '14px' }}>
                  实时查看和探索Neo4j中的图数据
                </p>
              </div>
            </Space>
          </Col>
          <Col>
            <Space>
              <Statistic
                title="节点数"
                value={stats.nodes}
                prefix={<NodeIndexOutlined />}
                valueStyle={{ fontSize: '18px' }}
              />
              <Statistic
                title="关系数"
                value={stats.links}
                prefix={<LinkOutlined />}
                valueStyle={{ fontSize: '18px' }}
              />
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 搜索和控制栏 */}
      <Card style={{ marginBottom: '16px' }}>
        <Space style={{ width: '100%' }} size="large">
          <Input
            placeholder="搜索节点（按名称或属性）"
            prefix={<SearchOutlined />}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onPressEnter={handleSearch}
            style={{ width: '300px' }}
            allowClear
          />
          <Select
            placeholder="节点类型过滤"
            style={{ width: '200px' }}
            allowClear
            value={nodeTypeFilter}
            onChange={setNodeTypeFilter}
          >
            <Option value="Entity">实体</Option>
            <Option value="BusinessProcess">业务流程</Option>
            <Option value="ApplicationSystem">应用系统</Option>
            <Option value="DataEntity">数据实体</Option>
            <Option value="TechnologyComponent">技术组件</Option>
            <Option value="BusinessCapability">业务能力</Option>
          </Select>
          <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch} loading={loading}>
            搜索
          </Button>
          <Button icon={<ReloadOutlined />} onClick={loadGraphData} loading={loading}>
            刷新
          </Button>
        </Space>
      </Card>

      {/* 图谱和详情 */}
      <div style={{ display: 'flex', gap: '16px', minHeight: '600px' }}>
        {/* 图谱可视化区域 */}
        <div id="graph-container" style={{ flex: 1, position: 'relative', width: '100%' }}>
          <Spin spinning={loading} tip="加载Neo4j图数据...">
            {graphData.nodes.length === 0 ? (
              <Empty
                description="暂无图数据"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                style={{ marginTop: '100px' }}
              />
            ) : (
              <GraphVisualization
                data={graphData}
                onNodeClick={handleNodeClick}
                width={dimensions.width}
                height={dimensions.height}
                loading={loading}
              />
            )}
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
            bodyStyle={{ padding: '16px', maxHeight: '600px', overflowY: 'auto' }}
          >
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="ID">{selectedNode.id}</Descriptions.Item>
              <Descriptions.Item label="标签">
                <Space>
                  {(selectedNode.labels || [selectedNode.type]).map((label: string) => (
                    <Tag key={label} color={getTypeColor(label)}>
                      {label}
                    </Tag>
                  ))}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="名称">
                {selectedNode.label ||
                  selectedNode.properties?.name ||
                  selectedNode.properties?.label ||
                  'N/A'}
              </Descriptions.Item>
              {selectedNode.properties && Object.keys(selectedNode.properties).length > 0 && (
                <Descriptions.Item label="属性">
                  <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                    {Object.entries(selectedNode.properties).map(([key, value]) => (
                      <div key={key} style={{ marginBottom: '8px' }}>
                        <strong>{key}:</strong> {String(value)}
                      </div>
                    ))}
                  </div>
                </Descriptions.Item>
              )}
            </Descriptions>
            <div style={{ marginTop: '16px' }}>
              <Button
                type="link"
                onClick={async () => {
                  if (selectedNode.id) {
                    setLoading(true);
                    try {
                      const neighbors = await neo4jGraphService.getNodeNeighbors(selectedNode.id, {
                        depth: 1,
                        limit: 20,
                      });
                      setGraphData(neighbors);
                      setStats({
                        nodes: neighbors.nodes.length,
                        links: neighbors.links.length,
                      });
                      message.success('已加载节点邻居');
                    } catch (error) {
                      message.error('加载邻居节点失败');
                    } finally {
                      setLoading(false);
                    }
                  }
                }}
              >
                查看邻居节点
              </Button>
            </div>
          </Card>
        ) : null}
      </div>
    </div>
  );
}

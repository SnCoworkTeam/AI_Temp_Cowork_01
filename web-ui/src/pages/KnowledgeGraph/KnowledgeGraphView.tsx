import React, { useState, useEffect } from 'react';
import { Card, Input, Button, Space, Spin } from 'antd';
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons';
import { GraphVisualization } from '@/components/graph/GraphVisualization';
import { knowledgeGraphService } from '@/services/knowledgeGraphService';

export const KnowledgeGraphView: React.FC = () => {
  const [graphData, setGraphData] = useState<{ nodes: any[]; links: any[] }>({
    nodes: [],
    links: [],
  });
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadGraphData();
  }, []);

  const loadGraphData = async () => {
    setLoading(true);
    try {
      const data = await knowledgeGraphService.getGraphData();
      setGraphData(data);
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
      const entity = await knowledgeGraphService.getEntity(node.id);
      setSelectedNode(entity || node);
    } else {
      setSelectedNode(node);
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: '16px' }}>
          <h1>知识图谱</h1>
          <Space style={{ marginTop: '16px', width: '100%' }}>
            <Input
              placeholder="搜索实体或关系..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onPressEnter={handleSearch}
              style={{ width: '300px' }}
              prefix={<SearchOutlined />}
            />
            <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
              搜索
            </Button>
            <Button icon={<ReloadOutlined />} onClick={loadGraphData}>
              刷新
            </Button>
          </Space>
        </div>

        <div style={{ display: 'flex', gap: '16px' }}>
          <div style={{ flex: 1 }}>
            <Spin spinning={loading}>
              <GraphVisualization
                data={graphData}
                onNodeClick={handleNodeClick}
                width={800}
                height={600}
                loading={loading}
              />
            </Spin>
          </div>

          {selectedNode && (
            <Card
              title="节点详情"
              style={{ width: '300px' }}
              extra={
                <Button size="small" onClick={() => setSelectedNode(null)}>
                  关闭
                </Button>
              }
            >
              <div>
                <p>
                  <strong>名称:</strong> {selectedNode.name || selectedNode.id}
                </p>
                {selectedNode.type && (
                  <p>
                    <strong>类型:</strong> {selectedNode.type}
                  </p>
                )}
                {selectedNode.description && (
                  <p>
                    <strong>描述:</strong> {selectedNode.description}
                  </p>
                )}
                {selectedNode.properties && (
                  <div>
                    <strong>属性:</strong>
                    <pre style={{ fontSize: '12px', maxHeight: '200px', overflow: 'auto' }}>
                      {JSON.stringify(selectedNode.properties, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </Card>
          )}
        </div>
      </Card>
    </div>
  );
};

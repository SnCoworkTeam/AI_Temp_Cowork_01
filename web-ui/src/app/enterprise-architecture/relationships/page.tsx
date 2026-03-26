'use client';

import React, { useState, useEffect } from 'react';
import { Card, Spin } from 'antd';
import { enterpriseArchitectureService } from '@/services/enterpriseArchitectureService';
import { GraphVisualization } from '@/components/graph/GraphVisualization';

export default function ArchitectureRelationshipsPage() {
  const [graphData, setGraphData] = useState<{ nodes: any[]; links: any[] }>({
    nodes: [],
    links: [],
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadGraphData();
  }, []);

  const loadGraphData = async () => {
    setLoading(true);
    try {
      const data = await enterpriseArchitectureService.getGraph();
      setGraphData(data);
    } catch (error) {
      console.error('Failed to load graph data:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <h1>架构关系图</h1>
        <Spin spinning={loading}>
          <GraphVisualization
            data={graphData}
            onNodeClick={(node) => {
              console.log('Node clicked:', node);
            }}
            loading={loading}
            width={1200}
            height={700}
          />
        </Spin>
      </Card>
    </div>
  );
}

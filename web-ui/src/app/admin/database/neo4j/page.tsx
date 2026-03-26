'use client';

import React, { useState } from 'react';
import { Card, Button, Space } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';

export default function Neo4jDatabasePage() {
  const [loading, setLoading] = useState(false);

  const neo4jWebUrl = process.env.NEXT_PUBLIC_NEO4J_WEB_URL || 'http://43.143.90.179:7474/browser/';
  const neo4jBoltUrl = process.env.NEXT_PUBLIC_NEO4J_BOLT_URL || 'bolt://43.143.90.179:7687';

  const handleOpenNeo4jBrowser = () => {
    window.open(neo4jWebUrl, '_blank');
  };

  const handleRefresh = () => {
    setLoading(true);
    // 刷新iframe
    const iframe = document.getElementById('neo4j-iframe') as HTMLIFrameElement;
    if (iframe) {
      iframe.src = iframe.src;
    }
    setTimeout(() => setLoading(false), 1000);
  };

  return (
    <div className="p-6">
      <Card
        title={
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span>Neo4j图数据库</span>
            </div>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={handleRefresh} loading={loading}>
                刷新
              </Button>
              <Button type="primary" onClick={handleOpenNeo4jBrowser}>
                在新窗口打开
              </Button>
            </Space>
          </div>
        }
      >
        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-blue-900 mb-2">连接信息</h3>
            <div className="space-y-1 text-sm text-blue-800">
              <p>
                <strong>Web界面:</strong> {neo4jWebUrl}
              </p>
              <p>
                <strong>Bolt连接:</strong> {neo4jBoltUrl}
              </p>
              <p>
                <strong>用户名:</strong> neo4j
              </p>
              <p>
                <strong>密码:</strong> Neo4j@2024
              </p>
            </div>
          </div>

          <div
            className="border rounded-lg overflow-hidden bg-gray-50 flex items-center justify-center"
            style={{ height: 'calc(100vh - 300px)', minHeight: '600px' }}
          >
            <div className="text-center p-8">
              <p className="text-gray-600 mb-4">
                由于安全策略限制，无法在此页面直接嵌入Neo4j浏览器
              </p>
              <Button type="primary" size="large" onClick={handleOpenNeo4jBrowser}>
                在新窗口打开Neo4j浏览器
              </Button>
            </div>
          </div>

          <div className="text-sm text-gray-600">
            <p>💡 提示：</p>
            <ul className="list-disc list-inside space-y-1 ml-4">
              <li>如果无法加载，请检查Neo4j服务是否正常运行</li>
              <li>
                首次登录需要使用用户名 <code className="bg-gray-100 px-1 rounded">neo4j</code>{' '}
                和密码 <code className="bg-gray-100 px-1 rounded">Neo4j@2024</code>
              </li>
              <li>建议在新窗口中打开以获得更好的体验</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
}

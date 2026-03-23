'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { Card, Spin, Tag, Descriptions, Button } from 'antd';
import { EditOutlined } from '@ant-design/icons';
 

export default function DocumentDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [document, setDocument] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (id) {
      loadDocument(id);
    }
  }, [id]);

  const loadDocument = async (docId: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/knowledge/documents/${docId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setDocument(data);
    } catch (error) {
      console.error('Failed to load document:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !document) {
    return <Spin size="large" style={{ display: 'block', textAlign: 'center', padding: '40px' }} />;
  }

  if (!document) {
    return <div>文档不存在</div>;
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={document.filename || document.title}
        extra={
          <Button
            icon={<EditOutlined />}
            onClick={() => (window.location.href = `/documents/${id}/edit`)}
          >
            编辑
          </Button>
        }
      >
        <Descriptions column={2} bordered>
          <Descriptions.Item label="状态">
            <Tag color={document.status === 'processed' ? 'green' : 'orange'}>
              {document.status}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="文件类型">{document.file_type}</Descriptions.Item>
          <Descriptions.Item label="文件大小">
            {document.file_size ? `${(document.file_size / 1024).toFixed(2)} KB` : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="总Chunks">{document.total_chunks || 0}</Descriptions.Item>
          <Descriptions.Item label="上传时间">
            {document.uploaded_at ? new Date(document.uploaded_at).toLocaleString() : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="处理时间">
            {document.processed_at ? new Date(document.processed_at).toLocaleString() : '-'}
          </Descriptions.Item>
          {document.tags && document.tags.length > 0 && (
            <Descriptions.Item label="标签" span={2}>
              {document.tags.map((tag: string, index: number) => (
                <Tag key={index}>{tag}</Tag>
              ))}
            </Descriptions.Item>
          )}
        </Descriptions>

        {document.metadata && Object.keys(document.metadata).length > 0 && (
          <Card title="元数据" style={{ marginTop: '24px' }}>
            <pre style={{ fontSize: '12px', maxHeight: '400px', overflow: 'auto' }}>
              {JSON.stringify(document.metadata, null, 2)}
            </pre>
          </Card>
        )}
      </Card>
    </div>
  );
}

'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { Card, Spin, Table, Tag, Button, Modal } from 'antd';
import { EyeOutlined } from '@ant-design/icons';
import { StatCard } from '@/components/charts/StatCard';
import { DocumentChunksPage } from '@/components/DocumentChunksPage';
 

export default function KnowledgeBaseDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [kb, setKb] = useState<any>(null);
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<any>(null);
  const [chunksModalVisible, setChunksModalVisible] = useState(false);

  useEffect(() => {
    if (id) {
      loadKnowledgeBase(id);
    }
  }, [id]);

  const loadKnowledgeBase = async (kbId: string) => {
    setLoading(true);
    try {
      const [kbResponse, docsResponse] = await Promise.all([
        fetch(`/api/knowledge/knowledge-bases/${kbId}`),
        fetch(`/api/knowledge/knowledge-bases/${kbId}/documents`),
      ]);
      if (!kbResponse.ok || !docsResponse.ok) {
        throw new Error(
          `HTTP error! status: kb=${kbResponse.status}, docs=${docsResponse.status}`
        );
      }
      const kbData = await kbResponse.json();
      const docsData = await docsResponse.json();
      setKb(kbData);
      setDocuments(docsData.documents || []);
    } catch (error) {
      console.error('Failed to load knowledge base:', error);
    } finally {
      setLoading(false);
    }
  };

  const showDocumentChunks = (document: any) => {
    setSelectedDocument(document);
    setChunksModalVisible(true);
  };

  const documentColumns = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colorMap: { [key: string]: string } = {
          processed: 'green',
          processing: 'orange',
          failed: 'red',
          uploading: 'blue',
        };
        return <Tag color={colorMap[status] || 'default'}>{status}</Tag>;
      },
    },
    {
      title: 'Chunks',
      dataIndex: 'total_chunks',
      key: 'total_chunks',
    },
    {
      title: '上传时间',
      dataIndex: 'uploaded_at',
      key: 'uploaded_at',
      render: (date: string) => (date ? new Date(date).toLocaleString() : '-'),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: any) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => showDocumentChunks(record)}
          disabled={!record.total_chunks || record.total_chunks === 0}
        >
          查看分块
        </Button>
      ),
    },
  ];

  if (loading && !kb) {
    return <Spin size="large" style={{ display: 'block', textAlign: 'center', padding: '40px' }} />;
  }

  if (!kb) {
    return <div>知识库不存在</div>;
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <h1>{kb.name}</h1>
        <p style={{ color: '#8c8c8c', marginBottom: '24px' }}>{kb.description}</p>

        <div style={{ marginBottom: '24px', display: 'flex', gap: '16px' }}>
          <div style={{ flex: 1 }}>
            <StatCard title="文档数" value={kb.document_count || 0} />
          </div>
          <div style={{ flex: 1 }}>
            <StatCard title="总Chunks" value={kb.total_chunks || 0} />
          </div>
          <div style={{ flex: 1 }}>
            <StatCard title="状态" value={kb.status || 'unknown'} />
          </div>
        </div>

        <Card title="文档列表" style={{ marginTop: '24px' }}>
          <Table
            dataSource={documents}
            columns={documentColumns}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 10 }}
          />
        </Card>
      </Card>

      <Modal
        title={`文档分块 - ${selectedDocument?.filename}`}
        open={chunksModalVisible}
        onCancel={() => setChunksModalVisible(false)}
        footer={null}
        width={1200}
        style={{ top: 20 }}
      >
        {selectedDocument && (
          <DocumentChunksPage
            documentId={selectedDocument.id}
            documentName={selectedDocument.filename}
          />
        )}
      </Modal>
    </div>
  );
}

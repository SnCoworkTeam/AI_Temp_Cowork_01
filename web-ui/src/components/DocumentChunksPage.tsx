'use client';

import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Input, Button, Spin, Modal } from 'antd';
import { SearchOutlined, EyeOutlined } from '@ant-design/icons';
 

interface DocumentChunk {
  id: string;
  chunk_index: number;
  content: string;
  start_char: number;
  end_char: number;
  page_number: number | null;
  embedding_model: string;
  metadata: any;
  created_at: string;
}

interface DocumentChunksPageProps {
  documentId: string;
  documentName?: string;
}

export function DocumentChunksPage({ documentId, documentName }: DocumentChunksPageProps) {
  const [chunks, setChunks] = useState<DocumentChunk[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [selectedChunk, setSelectedChunk] = useState<DocumentChunk | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);

  useEffect(() => {
    loadChunks();
  }, [documentId]);

  const loadChunks = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/knowledge/documents/${documentId}/chunks`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setChunks(data.chunks || []);
    } catch (error) {
      console.error('Failed to load chunks:', error);
      // 如果API不存在，可以尝试其他路径
      try {
        const fallbackResponse = await fetch(`/api/knowledge-base/documents/${documentId}`);
        if (!fallbackResponse.ok) {
          throw new Error(`HTTP error! status: ${fallbackResponse.status}`);
        }
        // 从文档详情中提取chunks信息（如果有的话）
        const fallbackData = await fallbackResponse.json();
        setChunks(fallbackData.chunks || []);
      } catch (fallbackError) {
        console.error('Fallback also failed:', fallbackError);
      }
    } finally {
      setLoading(false);
    }
  };

  const showChunkDetail = (chunk: DocumentChunk) => {
    setSelectedChunk(chunk);
    setDetailModalVisible(true);
  };

  const filteredChunks = chunks.filter((chunk) =>
    chunk.content.toLowerCase().includes(searchText.toLowerCase())
  );

  const columns = [
    {
      title: '索引',
      dataIndex: 'chunk_index',
      key: 'chunk_index',
      width: 80,
      sorter: (a: DocumentChunk, b: DocumentChunk) => a.chunk_index - b.chunk_index,
    },
    {
      title: '内容预览',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (text: string) => (
        <div style={{ maxWidth: '400px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {text.substring(0, 100)}
          {text.length > 100 ? '...' : ''}
        </div>
      ),
    },
    {
      title: '字符范围',
      key: 'char_range',
      width: 120,
      render: (_: any, record: DocumentChunk) => (
        <span>
          {record.start_char} - {record.end_char}
        </span>
      ),
    },
    {
      title: '页码',
      dataIndex: 'page_number',
      key: 'page_number',
      width: 80,
      render: (page: number | null) => (page !== null ? page : '-'),
    },
    {
      title: '嵌入模型',
      dataIndex: 'embedding_model',
      key: 'embedding_model',
      width: 200,
      ellipsis: true,
      render: (model: string) => <Tag color="blue">{model || 'N/A'}</Tag>,
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_: any, record: DocumentChunk) => (
        <Button type="link" icon={<EyeOutlined />} onClick={() => showChunkDetail(record)}>
          详情
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Card
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>文档分块列表 {documentName && `- ${documentName}`}</span>
            <Tag color="green">{chunks.length} 个分块</Tag>
          </div>
        }
        extra={
          <Input
            placeholder="搜索分块内容"
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 300 }}
          />
        }
      >
        <Table
          dataSource={filteredChunks}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 20,
            showTotal: (total) => `共 ${total} 个分块`,
            showSizeChanger: true,
            pageSizeOptions: ['10', '20', '50', '100'],
          }}
          scroll={{ y: 600 }}
        />
      </Card>

      <Modal
        title={`分块详情 #${selectedChunk?.chunk_index}`}
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>,
        ]}
        width={800}
      >
        {selectedChunk && (
          <div>
            <Card size="small" title="基本信息" style={{ marginBottom: 16 }}>
              <p>
                <strong>分块索引:</strong> {selectedChunk.chunk_index}
              </p>
              <p>
                <strong>字符范围:</strong> {selectedChunk.start_char} - {selectedChunk.end_char}
              </p>
              <p>
                <strong>页码:</strong>{' '}
                {selectedChunk.page_number !== null ? selectedChunk.page_number : '未指定'}
              </p>
              <p>
                <strong>嵌入模型:</strong> {selectedChunk.embedding_model || 'N/A'}
              </p>
              <p>
                <strong>创建时间:</strong> {new Date(selectedChunk.created_at).toLocaleString()}
              </p>
            </Card>

            <Card size="small" title="分块内容" style={{ marginBottom: 16 }}>
              <div
                style={{
                  maxHeight: '300px',
                  overflow: 'auto',
                  padding: '12px',
                  backgroundColor: '#f5f5f5',
                  borderRadius: '4px',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {selectedChunk.content}
              </div>
            </Card>

            {selectedChunk.metadata && Object.keys(selectedChunk.metadata).length > 0 && (
              <Card size="small" title="元数据">
                <pre
                  style={{
                    maxHeight: '200px',
                    overflow: 'auto',
                    backgroundColor: '#f5f5f5',
                    padding: '12px',
                    borderRadius: '4px',
                  }}
                >
                  {JSON.stringify(selectedChunk.metadata, null, 2)}
                </pre>
              </Card>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}

export default DocumentChunksPage;

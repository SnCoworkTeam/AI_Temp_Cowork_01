/**
 * 知识库API客户端
 */
import { knowledgeBaseClient } from './client';

// 类型定义
export interface SearchResult {
  chunk_id: string;
  document_id: string;
  document_name: string;
  content: string;
  score: number;
  metadata?: Record<string, any>;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
  search_type: string;
}

export interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: string;
  metadata: {
    title?: string;
    author?: string;
    page_count?: number;
    word_count?: number;
  };
  tags: string[];
  uploaded_at: string;
  processed_at?: string;
}

export interface KnowledgeGraphNode {
  id: string;
  label: string;
  type: string;
  properties: Record<string, any>;
}

export interface KnowledgeGraphEdge {
  id: string;
  source: string;
  target: string;
  label: string;
  properties: Record<string, any>;
}

export interface KnowledgeGraph {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
  total_nodes: number;
  total_edges: number;
}

// API函数
export const knowledgeApi = {
  // 语义搜索
  async semanticSearch(
    query: string,
    limit: number = 5,
    filters?: Record<string, any>
  ): Promise<SearchResponse> {
    return knowledgeBaseClient.post('/search/semantic', {
      query,
      top_k: limit,
      min_score: 0.1,
      filters,
    });
  },

  // 关键词搜索
  async keywordSearch(
    keywords: string[],
    matchAll: boolean = false,
    page: number = 1,
    pageSize: number = 10
  ): Promise<SearchResponse> {
    const baseUrl = (knowledgeBaseClient as any).baseUrl || '';
    const endpoint = baseUrl.includes('/api/knowledge') ? '/search/keyword' : '/api/search/keyword';
    return knowledgeBaseClient.post(endpoint, {
      keywords,
      match_all: matchAll,
      page,
      page_size: pageSize,
    });
  },

  // 混合搜索
  async hybridSearch(
    query: string,
    keywords: string[] = [],
    topK: number = 10,
    semanticWeight: number = 0.7,
    keywordWeight: number = 0.3
  ): Promise<SearchResponse> {
    const params = new URLSearchParams({
      query,
      keywords: keywords.join(','),
      top_k: topK.toString(),
      semantic_weight: semanticWeight.toString(),
      keyword_weight: keywordWeight.toString(),
    });
    const baseUrl = (knowledgeBaseClient as any).baseUrl || '';
    const endpoint = baseUrl.includes('/api/knowledge')
      ? `/search/hybrid?${params}`
      : `/api/search/hybrid?${params}`;
    return knowledgeBaseClient.get(endpoint);
  },

  // 获取文档信息
  async getDocument(documentId: string): Promise<Document> {
    const baseUrl = (knowledgeBaseClient as any).baseUrl || '';
    const endpoint = baseUrl.includes('/api/knowledge')
      ? `/documents/${documentId}`
      : `/api/documents/${documentId}`;
    return knowledgeBaseClient.get(endpoint);
  },

  // 列出文档
  async listDocuments(params?: {
    file_type?: string;
    status?: string;
    tags?: string;
    search?: string;
    page?: number;
    page_size?: number;
  }): Promise<{
    documents: Document[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
  }> {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    // 如果使用 API Gateway，base URL 已经是 /api/knowledge，所以路径应该是 /documents
    // 如果不使用 API Gateway，base URL 是服务地址，路径应该是 /api/documents
    // 检查 base URL 是否包含 /api/knowledge 来判断是否使用 API Gateway
    const baseUrl = (knowledgeBaseClient as any).baseUrl || '';
    const endpoint = baseUrl.includes('/api/knowledge')
      ? `/documents?${queryParams}`
      : `/api/documents?${queryParams}`;
    return knowledgeBaseClient.get(endpoint);
  },

  // 获取知识图谱
  async getKnowledgeGraph(nodeType?: string, limit: number = 100): Promise<KnowledgeGraph> {
    const params = new URLSearchParams();
    if (nodeType) params.append('node_type', nodeType);
    params.append('limit', limit.toString());
    const baseUrl = (knowledgeBaseClient as any).baseUrl || '';
    const endpoint = baseUrl.includes('/api/knowledge')
      ? `/knowledge-graph?${params}`
      : `/api/knowledge-graph?${params}`;
    return knowledgeBaseClient.get(endpoint);
  },

  // 获取相关概念
  async getRelatedConcepts(
    concept: string,
    limit: number = 10
  ): Promise<{
    success: boolean;
    concept: string;
    matching_nodes: KnowledgeGraphNode[];
    related_concepts: KnowledgeGraphNode[];
    relationships: KnowledgeGraphEdge[];
    total_related: number;
  }> {
    const baseUrl = (knowledgeBaseClient as any).baseUrl || '';
    const graphEndpoint = baseUrl.includes('/api/knowledge')
      ? `/knowledge-graph?limit=${Math.max(limit * 5, 50)}`
      : `/api/knowledge-graph?limit=${Math.max(limit * 5, 50)}`;

    const graph = await knowledgeBaseClient.get<KnowledgeGraph>(graphEndpoint);
    const normalizedConcept = concept.trim().toLowerCase();
    const matchingNodes = (graph.nodes || []).filter((node) =>
      node.label?.toLowerCase().includes(normalizedConcept)
    );

    if (!matchingNodes.length) {
      return {
        success: true,
        concept,
        matching_nodes: [],
        related_concepts: [],
        relationships: [],
        total_related: 0,
      };
    }

    const targetNode = matchingNodes[0];
    const relatedEndpoint = baseUrl.includes('/api/knowledge')
      ? `/knowledge-graph/nodes/${targetNode.id}/related?max_depth=1`
      : `/api/knowledge-graph/nodes/${targetNode.id}/related?max_depth=1`;

    const relatedResponse = await knowledgeBaseClient.get<{
      related_nodes: KnowledgeGraphNode[];
    }>(relatedEndpoint);

    const relatedNodes = (relatedResponse.related_nodes || []).slice(0, limit);

    return {
      success: true,
      concept,
      matching_nodes: matchingNodes,
      related_concepts: relatedNodes,
      relationships: [],
      total_related: relatedNodes.length,
    };
  },
};

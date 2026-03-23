import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  knowledgeApi,
  SearchResponse,
  Document,
  KnowledgeGraph,
  KnowledgeGraphNode,
  KnowledgeGraphEdge
} from '../knowledge'
import * as clientModule from '../client'

// Mock the knowledgeBaseClient
vi.mock('../client', () => ({
  knowledgeBaseClient: {
    baseUrl: 'http://test-api.com/api/knowledge',
    get: vi.fn(),
    post: vi.fn()
  }
}))

describe('knowledge API', () => {
  const mockClient = clientModule.knowledgeBaseClient as any

  beforeEach(() => {
    vi.clearAllMocks()
    // Set default baseUrl for API Gateway mode
    mockClient.baseUrl = 'http://test-api.com/api/knowledge'
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('semanticSearch', () => {
    it('should perform semantic search with default parameters', async () => {
      const mockResponse: SearchResponse = {
        results: [
          {
            chunk_id: 'chunk1',
            document_id: 'doc1',
            document_name: 'test.pdf',
            content: 'test content',
            score: 0.95
          }
        ],
        total: 1,
        query: 'test query',
        search_type: 'semantic'
      }

      mockClient.post.mockResolvedValueOnce(mockResponse)

      const result = await knowledgeApi.semanticSearch('test query')

      expect(mockClient.post).toHaveBeenCalledWith('/search/semantic', {
        query: 'test query',
        top_k: 5,
        min_score: 0.1,
        filters: undefined
      })
      expect(result).toEqual(mockResponse)
    })

    it('should perform semantic search with custom parameters', async () => {
      const mockResponse: SearchResponse = {
        results: [],
        total: 0,
        query: 'custom query',
        search_type: 'semantic'
      }

      mockClient.post.mockResolvedValueOnce(mockResponse)

      const filters = { document_type: 'pdf' }
      const result = await knowledgeApi.semanticSearch('custom query', 10, filters)

      expect(mockClient.post).toHaveBeenCalledWith('/search/semantic', {
        query: 'custom query',
        top_k: 10,
        min_score: 0.1,
        filters
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('keywordSearch', () => {
    it('should perform keyword search with default parameters', async () => {
      const mockResponse: SearchResponse = {
        results: [],
        total: 0,
        query: '',
        search_type: 'keyword'
      }

      mockClient.post.mockResolvedValueOnce(mockResponse)

      const result = await knowledgeApi.keywordSearch(['test', 'search'])

      expect(mockClient.post).toHaveBeenCalledWith('/search/keyword', {
        keywords: ['test', 'search'],
        match_all: false,
        page: 1,
        page_size: 10
      })
      expect(result).toEqual(mockResponse)
    })

    it('should perform keyword search with match_all true', async () => {
      const mockResponse: SearchResponse = {
        results: [],
        total: 0,
        query: '',
        search_type: 'keyword'
      }

      mockClient.post.mockResolvedValueOnce(mockResponse)

      const result = await knowledgeApi.keywordSearch(['word1', 'word2'], true, 2, 20)

      expect(mockClient.post).toHaveBeenCalledWith('/search/keyword', {
        keywords: ['word1', 'word2'],
        match_all: true,
        page: 2,
        page_size: 20
      })
      expect(result).toEqual(mockResponse)
    })

    it('should use correct endpoint in direct access mode', async () => {
      mockClient.baseUrl = 'http://127.0.0.1:8004'
      mockClient.post.mockResolvedValueOnce({ results: [], total: 0, query: '', search_type: 'keyword' })

      await knowledgeApi.keywordSearch(['test'])

      expect(mockClient.post).toHaveBeenCalledWith('/api/search/keyword', expect.any(Object))
    })
  })

  describe('hybridSearch', () => {
    it('should perform hybrid search with default parameters', async () => {
      const mockResponse: SearchResponse = {
        results: [],
        total: 0,
        query: 'hybrid query',
        search_type: 'hybrid'
      }

      mockClient.get.mockResolvedValueOnce(mockResponse)

      const result = await knowledgeApi.hybridSearch('hybrid query')

      expect(mockClient.get).toHaveBeenCalledWith(
        expect.stringContaining('/search/hybrid?')
      )
      expect(result).toEqual(mockResponse)
    })

    it('should perform hybrid search with custom parameters', async () => {
      const mockResponse: SearchResponse = {
        results: [],
        total: 0,
        query: 'custom hybrid',
        search_type: 'hybrid'
      }

      mockClient.get.mockResolvedValueOnce(mockResponse)

      const result = await knowledgeApi.hybridSearch(
        'custom hybrid',
        ['keyword1', 'keyword2'],
        20,
        0.6,
        0.4
      )

      const call = mockClient.get.mock.calls[0][0]
      expect(call).toContain('query=custom+hybrid')
      expect(call).toContain('keywords=keyword1%2Ckeyword2')
      expect(call).toContain('top_k=20')
      expect(call).toContain('semantic_weight=0.6')
      expect(call).toContain('keyword_weight=0.4')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getDocument', () => {
    it('should get document by ID', async () => {
      const mockDocument: Document = {
        id: 'doc-123',
        filename: 'test.pdf',
        file_type: 'pdf',
        file_size: 1024,
        status: 'processed',
        metadata: {
          title: 'Test Document',
          page_count: 10
        },
        tags: ['test'],
        uploaded_at: '2024-01-01T00:00:00Z'
      }

      mockClient.get.mockResolvedValueOnce(mockDocument)

      const result = await knowledgeApi.getDocument('doc-123')

      expect(mockClient.get).toHaveBeenCalledWith('/documents/doc-123')
      expect(result).toEqual(mockDocument)
    })

    it('should handle document not found', async () => {
      const error = new Error('Document not found')
      mockClient.get.mockRejectedValueOnce(error)

      await expect(knowledgeApi.getDocument('non-existent'))
        .rejects.toThrow('Document not found')
    })
  })

  describe('listDocuments', () => {
    it('should list documents without parameters', async () => {
      const mockResponse = {
        documents: [],
        total: 0,
        page: 1,
        page_size: 10,
        total_pages: 0
      }

      mockClient.get.mockResolvedValueOnce(mockResponse)

      const result = await knowledgeApi.listDocuments()

      expect(mockClient.get).toHaveBeenCalledWith('/documents?')
      expect(result).toEqual(mockResponse)
    })

    it('should list documents with filters', async () => {
      const mockDocuments: Document[] = [
        {
          id: 'doc1',
          filename: 'test.pdf',
          file_type: 'pdf',
          file_size: 1024,
          status: 'processed',
          metadata: {},
          tags: [],
          uploaded_at: '2024-01-01T00:00:00Z'
        }
      ]

      const mockResponse = {
        documents: mockDocuments,
        total: 1,
        page: 1,
        page_size: 10,
        total_pages: 1
      }

      mockClient.get.mockResolvedValueOnce(mockResponse)

      const result = await knowledgeApi.listDocuments({
        file_type: 'pdf',
        status: 'processed',
        page: 1,
        page_size: 10
      })

      const call = mockClient.get.mock.calls[0][0]
      expect(call).toContain('file_type=pdf')
      expect(call).toContain('status=processed')
      expect(call).toContain('page=1')
      expect(call).toContain('page_size=10')
      expect(result).toEqual(mockResponse)
    })

    it('should handle search parameter', async () => {
      mockClient.get.mockResolvedValueOnce({
        documents: [],
        total: 0,
        page: 1,
        page_size: 10,
        total_pages: 0
      })

      await knowledgeApi.listDocuments({ search: 'test query' })

      const call = mockClient.get.mock.calls[0][0]
      expect(call).toContain('search=test+query')
    })
  })

  describe('getKnowledgeGraph', () => {
    it('should get knowledge graph without filters', async () => {
      const mockGraph: KnowledgeGraph = {
        nodes: [
          {
            id: 'node1',
            label: 'Concept 1',
            type: 'concept',
            properties: {}
          }
        ],
        edges: [
          {
            id: 'edge1',
            source: 'node1',
            target: 'node2',
            label: 'relates_to',
            properties: {}
          }
        ],
        total_nodes: 1,
        total_edges: 1
      }

      mockClient.get.mockResolvedValueOnce(mockGraph)

      const result = await knowledgeApi.getKnowledgeGraph()

      const call = mockClient.get.mock.calls[0][0]
      expect(call).toContain('/knowledge-graph?')
      expect(call).toContain('limit=100')
      expect(result).toEqual(mockGraph)
    })

    it('should get knowledge graph with node type filter', async () => {
      const mockGraph: KnowledgeGraph = {
        nodes: [],
        edges: [],
        total_nodes: 0,
        total_edges: 0
      }

      mockClient.get.mockResolvedValueOnce(mockGraph)

      const result = await knowledgeApi.getKnowledgeGraph('person', 50)

      const call = mockClient.get.mock.calls[0][0]
      expect(call).toContain('node_type=person')
      expect(call).toContain('limit=50')
      expect(result).toEqual(mockGraph)
    })
  })

  describe('getRelatedConcepts', () => {
    it('should get related concepts', async () => {
      const mockResponse = {
        success: true,
        concept: 'AI',
        matching_nodes: [
          {
            id: 'node1',
            label: 'AI',
            type: 'concept',
            properties: {}
          }
        ],
        related_concepts: [
          {
            id: 'node2',
            label: 'Machine Learning',
            type: 'concept',
            properties: {}
          }
        ],
        relationships: [
          {
            id: 'rel1',
            source: 'node1',
            target: 'node2',
            label: 'includes',
            properties: {}
          }
        ],
        total_related: 1
      }

      mockClient.post.mockResolvedValueOnce(mockResponse)

      const result = await knowledgeApi.getRelatedConcepts('AI')

      expect(mockClient.post).toHaveBeenCalledWith('/knowledge-graph/nodes', {
        operation: 'get_related',
        concept: 'AI',
        limit: 10
      })
      expect(result).toEqual(mockResponse)
    })

    it('should get related concepts with custom limit', async () => {
      const mockResponse = {
        success: true,
        concept: 'Python',
        matching_nodes: [],
        related_concepts: [],
        relationships: [],
        total_related: 0
      }

      mockClient.post.mockResolvedValueOnce(mockResponse)

      const result = await knowledgeApi.getRelatedConcepts('Python', 20)

      expect(mockClient.post).toHaveBeenCalledWith('/knowledge-graph/nodes', {
        operation: 'get_related',
        concept: 'Python',
        limit: 20
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('direct access mode', () => {
    beforeEach(() => {
      mockClient.baseUrl = 'http://127.0.0.1:8004'
    })

    it('should use /api prefix for getDocument', async () => {
      mockClient.get.mockResolvedValueOnce({} as Document)

      await knowledgeApi.getDocument('doc-123')

      expect(mockClient.get).toHaveBeenCalledWith('/api/documents/doc-123')
    })

    it('should use /api prefix for hybridSearch', async () => {
      mockClient.get.mockResolvedValueOnce({ results: [], total: 0, query: '', search_type: 'hybrid' })

      await knowledgeApi.hybridSearch('test')

      expect(mockClient.get).toHaveBeenCalledWith(expect.stringContaining('/api/search/hybrid?'))
    })

    it('should use /api prefix for getKnowledgeGraph', async () => {
      mockClient.get.mockResolvedValueOnce({ nodes: [], edges: [], total_nodes: 0, total_edges: 0 })

      await knowledgeApi.getKnowledgeGraph()

      expect(mockClient.get).toHaveBeenCalledWith(expect.stringContaining('/api/knowledge-graph?'))
    })
  })
})

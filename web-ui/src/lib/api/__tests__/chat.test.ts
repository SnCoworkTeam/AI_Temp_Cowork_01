import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { IntelligentChatRequest, IntelligentChatResponse } from '../chat'

describe('chat API', () => {
  beforeEach(() => {
    // Mock global fetch for these tests
    global.fetch = vi.fn()
  })

  describe('intelligentChat', () => {
    it('should send intelligent chat request successfully', async () => {
      const chatRequest: IntelligentChatRequest = {
        message: 'Hello, how are you?',
        conversation_history: [
          { role: 'user', content: 'Hi' },
          { role: 'assistant', content: 'Hello! How can I help you?' }
        ],
        user_context: { session_id: 'session-123' }
      }

      const mockResponse: IntelligentChatResponse = {
        success: true,
        output: 'I am doing well, thank you!',
        intent_analysis: {
          task_type: 'casual_conversation',
          confidence: 0.95,
          reasoning: 'Simple greeting'
        },
        strategy: 'direct_llm'
      }

      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse
      } as Response)

      // Import after mocking
      const { intelligentChat } = await import('../chat')
      const result = await intelligentChat(chatRequest)

      expect(result).toEqual(mockResponse)
    })

    it('should handle simple message without history', async () => {
      const chatRequest: IntelligentChatRequest = {
        message: 'What is the weather today?'
      }

      const mockResponse: IntelligentChatResponse = {
        success: true,
        output: 'I can help you check the weather.',
        intent_analysis: {
          task_type: 'weather_query',
          confidence: 0.88,
          reasoning: 'Weather information request'
        }
      }

      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse
      } as Response)

      const { intelligentChat } = await import('../chat')
      const result = await intelligentChat(chatRequest)

      expect(result).toEqual(mockResponse)
    })

    it('should handle stream request', async () => {
      const chatRequest: IntelligentChatRequest = {
        message: 'Tell me a story',
        stream: true
      }

      const mockResponse: IntelligentChatResponse = {
        success: true,
        output: 'Once upon a time...',
        strategy: 'streaming_llm'
      }

      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse
      } as Response)

      const { intelligentChat } = await import('../chat')
      const result = await intelligentChat(chatRequest)

      expect(result.success).toBe(true)
    })

    it('should handle error response from API', async () => {
      const chatRequest: IntelligentChatRequest = {
        message: 'invalid input'
      }

      const mockResponse: IntelligentChatResponse = {
        success: false,
        error: 'Invalid message format'
      }

      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse
      } as Response)

      const { intelligentChat } = await import('../chat')
      const result = await intelligentChat(chatRequest)

      expect(result.success).toBe(false)
      expect(result.error).toBe('Invalid message format')
    })

    it('should handle API error', async () => {
      const chatRequest: IntelligentChatRequest = {
        message: 'test'
      }

      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Server error' })
      } as Response)

      const { intelligentChat } = await import('../chat')

      await expect(intelligentChat(chatRequest)).rejects.toThrow()
    })
  })

  describe('agentChat', () => {
    it('should send agent chat request successfully', async () => {
      const chatRequest: IntelligentChatRequest = {
        message: 'Analyze this data',
        user_context: { task_type: 'data_analysis' }
      }

      const mockResponse: IntelligentChatResponse = {
        success: true,
        output: 'Analysis complete',
        intent_analysis: {
          task_type: 'data_analysis',
          confidence: 0.92,
          reasoning: 'Data analysis request identified'
        }
      }

      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse
      } as Response)

      const { agentChat } = await import('../chat')
      const result = await agentChat(chatRequest)

      expect(result).toEqual(mockResponse)
    })

    it('should handle agent chat without context', async () => {
      const chatRequest: IntelligentChatRequest = {
        message: 'Help me with a task'
      }

      const mockResponse: IntelligentChatResponse = {
        success: true,
        output: 'How can I assist you?'
      }

      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse
      } as Response)

      const { agentChat } = await import('../chat')
      const result = await agentChat(chatRequest)

      expect(result).toEqual(mockResponse)
    })

    it('should handle agent failure response', async () => {
      const chatRequest: IntelligentChatRequest = {
        message: 'invalid request'
      }

      const mockResponse: IntelligentChatResponse = {
        success: false,
        error: 'Agent execution failed'
      }

      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse
      } as Response)

      const { agentChat } = await import('../chat')
      const result = await agentChat(chatRequest)

      expect(result.success).toBe(false)
      expect(result.error).toBe('Agent execution failed')
    })

    it('should handle agent service error', async () => {
      const chatRequest: IntelligentChatRequest = {
        message: 'test'
      }

      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        status: 503,
        json: async () => ({ detail: 'Service unavailable' })
      } as Response)

      const { agentChat } = await import('../chat')

      await expect(agentChat(chatRequest)).rejects.toThrow()
    })
  })
})

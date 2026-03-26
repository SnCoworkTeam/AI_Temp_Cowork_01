import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  getWorkflows,
  getWorkflowInfo,
  executeWorkflow,
  getExecutionStatus,
  saveWorkflow,
  getWorkflow,
  listWorkflows,
  executeWorkflowById,
  Workflow,
  WorkflowExecutionResponse,
  WorkflowListItem
} from '../workflow'
import * as clientModule from '../client'

// Mock the workflowEngineClient
vi.mock('../client', () => ({
  workflowEngineClient: {
    baseUrl: 'http://test-api.com/api/workflows',
    get: vi.fn(),
    post: vi.fn()
  }
}))

describe('workflow API', () => {
  const mockClient = clientModule.workflowEngineClient as any

  beforeEach(() => {
    vi.clearAllMocks()
    // Set default baseUrl for API Gateway mode
    mockClient.baseUrl = 'http://test-api.com/api/workflows'
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('getWorkflows', () => {
    it('should get list of workflows', async () => {
      const mockWorkflows: Workflow[] = [
        { name: 'workflow1', description: 'Test workflow 1', version: '1.0' },
        { name: 'workflow2', description: 'Test workflow 2', version: '2.0' }
      ]

      mockClient.get.mockResolvedValueOnce(mockWorkflows)

      const result = await getWorkflows()

      // getWorkflowPath removes /workflows prefix, so final path is empty string
      expect(mockClient.get).toHaveBeenCalledWith('')
      expect(result).toEqual(mockWorkflows)
    })

    it('should handle empty workflow list', async () => {
      mockClient.get.mockResolvedValueOnce([])

      const result = await getWorkflows()

      expect(result).toEqual([])
    })
  })

  describe('getWorkflowInfo', () => {
    it('should get workflow info by name', async () => {
      const mockWorkflow: Workflow = {
        name: 'test-workflow',
        description: 'Test workflow',
        version: '1.0'
      }

      mockClient.get.mockResolvedValueOnce(mockWorkflow)

      const result = await getWorkflowInfo('test-workflow')

      // getWorkflowPath cleans up /workflows prefix
      expect(mockClient.get).toHaveBeenCalledWith('/test-workflow')
      expect(result).toEqual(mockWorkflow)
    })

    it('should handle workflow not found', async () => {
      const error = new Error('Workflow not found')
      mockClient.get.mockRejectedValueOnce(error)

      await expect(getWorkflowInfo('non-existent'))
        .rejects.toThrow('Workflow not found')
    })
  })

  describe('executeWorkflow', () => {
    it('should execute workflow successfully', async () => {
      const mockResponse: WorkflowExecutionResponse = {
        success: true,
        execution_id: 'exec-123',
        result: { output: 'test result' },
        workflow_name: 'test-workflow'
      }

      mockClient.post.mockResolvedValueOnce(mockResponse)

      const result = await executeWorkflow(
        'test-workflow',
        { input: 'test' },
        { context: 'value' }
      )

      // getWorkflowPath removes /workflows prefix, so /workflows/execute becomes /execute
      expect(mockClient.post).toHaveBeenCalledWith(
        '/execute',
        {
          workflow_name: 'test-workflow',
          input_data: { input: 'test' },
          context: { context: 'value' }
        }
      )
      expect(result).toEqual(mockResponse)
    })

    it('should execute workflow without context', async () => {
      const mockResponse: WorkflowExecutionResponse = {
        success: true,
        execution_id: 'exec-456',
        result: {},
        workflow_name: 'simple-workflow'
      }

      mockClient.post.mockResolvedValueOnce(mockResponse)

      const result = await executeWorkflow('simple-workflow', { data: 'value' })

      expect(mockClient.post).toHaveBeenCalledWith(
        '/execute',
        {
          workflow_name: 'simple-workflow',
          input_data: { data: 'value' },
          context: undefined
        }
      )
      expect(result).toEqual(mockResponse)
    })

    it('should handle execution failure', async () => {
      const mockResponse: WorkflowExecutionResponse = {
        success: false,
        result: null,
        workflow_name: 'failing-workflow',
        error: 'Execution failed'
      }

      mockClient.post.mockResolvedValueOnce(mockResponse)

      const result = await executeWorkflow('failing-workflow', {})

      expect(result.success).toBe(false)
      expect(result.error).toBe('Execution failed')
    })
  })

  describe('getExecutionStatus', () => {
    it('should get execution status', async () => {
      const mockStatus = {
        execution_id: 'exec-123',
        status: 'completed',
        progress: 100,
        result: { output: 'done' }
      }

      mockClient.get.mockResolvedValueOnce(mockStatus)

      const result = await getExecutionStatus('exec-123')

      // getWorkflowPath removes /workflows prefix, so /workflows/executions/exec-123 becomes /executions/exec-123
      expect(mockClient.get).toHaveBeenCalledWith('/executions/exec-123')
      expect(result).toEqual(mockStatus)
    })

    it('should handle running execution', async () => {
      const mockStatus = {
        execution_id: 'exec-456',
        status: 'running',
        progress: 50
      }

      mockClient.get.mockResolvedValueOnce(mockStatus)

      const result = await getExecutionStatus('exec-456')

      expect(result.status).toBe('running')
      expect(result.progress).toBe(50)
    })
  })

  describe('saveWorkflow', () => {
    it('should save workflow successfully', async () => {
      const mockResponse = {
        workflow_id: 'wf-123',
        workflow_name: 'new-workflow',
        message: 'Workflow saved successfully'
      }

      mockClient.post.mockResolvedValueOnce(mockResponse)

      const workflowConfig = {
        name: 'new-workflow',
        description: 'A new workflow',
        steps: []
      }

      const result = await saveWorkflow(workflowConfig)

      expect(mockClient.post).toHaveBeenCalledWith(
        '',
        {
          workflow: workflowConfig,
          overwrite: false
        }
      )
      expect(result).toEqual(mockResponse)
    })

    it('should save workflow with overwrite=true', async () => {
      const mockResponse = {
        workflow_id: 'wf-123',
        workflow_name: 'existing-workflow',
        message: 'Workflow updated successfully'
      }

      mockClient.post.mockResolvedValueOnce(mockResponse)

      const workflowConfig = { name: 'existing-workflow' }

      const result = await saveWorkflow(workflowConfig, true)

      expect(mockClient.post).toHaveBeenCalledWith(
        '',
        {
          workflow: workflowConfig,
          overwrite: true
        }
      )
      expect(result).toEqual(mockResponse)
    })

    it('should handle 404 error with friendly message', async () => {
      const error: any = new Error('Not Found')
      error.statusCode = 404

      mockClient.post.mockRejectedValueOnce(error)

      try {
        await saveWorkflow({ name: 'test' })
        expect.fail('Should have thrown an error')
      } catch (e: any) {
        expect(e.message).toBe('工作流保存功能暂未实现（API端点不存在）')
        expect(e.statusCode).toBe(404)
        expect(e.details).toContain('工作流引擎的保存接口尚未实现')
      }
    })

    it('should auto-retry with overwrite=true when workflow exists', async () => {
      const error: any = new Error('Workflow already exists')
      error.statusCode = 400

      const mockResponse = {
        workflow_id: 'wf-123',
        workflow_name: 'duplicate-workflow',
        message: 'Workflow overwritten successfully'
      }

      mockClient.post
        .mockRejectedValueOnce(error)
        .mockResolvedValueOnce(mockResponse)

      const workflowConfig = { name: 'duplicate-workflow' }

      const result = await saveWorkflow(workflowConfig, false)

      expect(mockClient.post).toHaveBeenCalledTimes(2)
      expect(mockClient.post).toHaveBeenNthCalledWith(2, '', {
        workflow: workflowConfig,
        overwrite: true
      })
      expect(result).toEqual(mockResponse)
    })

    it('should not retry for other 400 errors', async () => {
      const error: any = new Error('Invalid workflow configuration')
      error.statusCode = 400

      mockClient.post.mockRejectedValueOnce(error)

      await expect(saveWorkflow({ name: 'invalid' }))
        .rejects.toThrow('Invalid workflow configuration')

      expect(mockClient.post).toHaveBeenCalledTimes(1)
    })
  })

  describe('getWorkflow', () => {
    it('should get workflow by ID', async () => {
      const mockWorkflow = {
        workflow_id: 'wf-123',
        name: 'test-workflow',
        description: 'Test',
        config: {}
      }

      mockClient.get.mockResolvedValueOnce(mockWorkflow)

      const result = await getWorkflow('wf-123')

      expect(mockClient.get).toHaveBeenCalledWith('/wf-123')
      expect(result).toEqual(mockWorkflow)
    })
  })

  describe('listWorkflows', () => {
    it('should list all workflows', async () => {
      const mockWorkflows: WorkflowListItem[] = [
        {
          workflow_id: 'wf-1',
          name: 'workflow1',
          description: 'First workflow',
          status: 'active',
          version: '1.0'
        },
        {
          workflow_id: 'wf-2',
          name: 'workflow2',
          description: 'Second workflow',
          status: 'active',
          version: '2.0'
        }
      ]

      mockClient.get.mockResolvedValueOnce({ workflows: mockWorkflows })

      const result = await listWorkflows()

      expect(mockClient.get).toHaveBeenCalledWith('')
      expect(result.workflows).toEqual(mockWorkflows)
    })

    it('should return empty list on 404 error', async () => {
      const error: any = new Error('Not found')
      error.statusCode = 404

      mockClient.get.mockRejectedValueOnce(error)

      const result = await listWorkflows()

      expect(result.workflows).toEqual([])
    })

    it('should return empty list on API error with 404 in message', async () => {
      const error = new Error('HTTP 404 Not Found')

      mockClient.get.mockRejectedValueOnce(error)

      const result = await listWorkflows()

      expect(result.workflows).toEqual([])
    })

    it('should return empty list for other errors', async () => {
      const error = new Error('Network error')

      mockClient.get.mockRejectedValueOnce(error)

      const result = await listWorkflows()

      expect(result.workflows).toEqual([])
    })
  })

  describe('executeWorkflowById', () => {
    it('should execute workflow by ID', async () => {
      const mockResponse: WorkflowExecutionResponse = {
        success: true,
        execution_id: 'exec-789',
        result: { data: 'result' },
        workflow_name: 'workflow-by-id'
      }

      mockClient.post.mockResolvedValueOnce(mockResponse)

      const result = await executeWorkflowById(
        'wf-456',
        { input: 'data' },
        { ctx: 'value' }
      )

      // executeWorkflowById uses full path which gets cleaned by getWorkflowPath
      // /api/v1/workflows/wf-456/execute becomes /wf-456/execute
      expect(mockClient.post).toHaveBeenCalledWith(
        '/wf-456/execute',
        {
          input_data: { input: 'data' },
          context: { ctx: 'value' }
        }
      )
      expect(result).toEqual(mockResponse)
    })

    it('should execute workflow by ID without context', async () => {
      const mockResponse: WorkflowExecutionResponse = {
        success: true,
        execution_id: 'exec-999',
        result: {},
        workflow_name: 'simple-workflow'
      }

      mockClient.post.mockResolvedValueOnce(mockResponse)

      const result = await executeWorkflowById('wf-789', { data: 'test' })

      expect(mockClient.post).toHaveBeenCalledWith(
        '/wf-789/execute',
        {
          input_data: { data: 'test' },
          context: undefined
        }
      )
      expect(result).toEqual(mockResponse)
    })
  })

  describe('path handling in direct access mode', () => {
    beforeEach(() => {
      // Set baseUrl for direct access mode (no API Gateway)
      mockClient.baseUrl = 'http://127.0.0.1:8002'
    })

    it('should use /api/v1/workflows prefix in direct mode', async () => {
      const mockWorkflows: Workflow[] = []
      mockClient.get.mockResolvedValueOnce(mockWorkflows)

      await getWorkflows()

      // In direct mode, getWorkflowPath adds /api/v1/workflows prefix
      // /workflows becomes /api/v1/workflows
      expect(mockClient.get).toHaveBeenCalledWith('/api/v1/workflows')
    })

    it('should handle workflow ID in direct mode', async () => {
      const mockWorkflow = { workflow_id: 'wf-123' }
      mockClient.get.mockResolvedValueOnce(mockWorkflow)

      await getWorkflow('wf-123')

      expect(mockClient.get).toHaveBeenCalledWith('/api/v1/workflows/wf-123')
    })
  })
})

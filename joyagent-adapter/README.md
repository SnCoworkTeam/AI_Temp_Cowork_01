# JoyAgent Adapter Service

This service provides REST API integration between JoyAgent-JDGenie and the Enterprise AI Platform.

## Overview

JoyAgent-JDGenie is an open-source multi-agent framework from JD.com that provides:

- **High Completion Rate**: 75.15% accuracy on GAIA Validation set, 65.12% on Test set
- **Lightweight & Cloud-agnostic**: No dependency on specific cloud platforms
- **End-to-end Product**: Direct query processing and task completion
- **Multiple Agent Modes**: React, Plan and Executor, Auto mode
- **Rich Capabilities**: Report generation, code analysis, PPT creation, data analysis

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Enterprise AI Platform                   │
├─────────────────────────────────────────────────────────────┤
│  API Gateway (8080) → JoyAgent Adapter (8007)             │
│                           ↓                                 │
│  ┌─────────────────────────────────────────────────────────┐│
│  │           JoyAgent-JDGenie Components                   ││
│  │  ┌─────────────┬─────────────┬─────────────┬──────────┐││
│  │  │ Frontend UI │ Backend API │ Python      │ Python   │││
│  │  │ (3000)      │ (8080)      │ Client      │ Tools    │││
│  │  │             │             │ (1601)      │          │││
│  │  └─────────────┴─────────────┴─────────────┴──────────┘││
│  └─────────────────────────────────────────────────────────┘│
│                           ↓                                 │
│  Platform Integration:                                      │
│  • MCP Gateway (8001) - Tool coordination                  │
│  • Workflow Engine (8002) - Process integration            │
│  • Knowledge Base (8004) - Knowledge enhancement           │
│  • Metadata Service (8005) - Context management           │
└─────────────────────────────────────────────────────────────┘
```

## Features

### Core Capabilities
- **Multi-Agent Task Management**: Create and manage complex AI tasks
- **Real-time Status Tracking**: Monitor task progress and results
- **Multiple Task Types**: Query, report generation, code analysis, PPT creation
- **Agent Mode Selection**: React, Plan and Execute, or Auto mode

### Platform Integration
- **Workflow Integration**: Seamlessly integrate with workflow engine steps
- **Knowledge Enhancement**: Enhance knowledge base with AI analysis
- **MCP Tool Coordination**: Combine MCP tools with JoyAgent capabilities
- **Context Management**: Maintain conversation and task context

### Enterprise Features
- **Authentication & Authorization**: Secure API access
- **Distributed Task Queue**: Redis-based task management
- **Health Monitoring**: Comprehensive health checks
- **Structured Logging**: JSON-formatted logs for monitoring
- **Auto-scaling**: Support for horizontal scaling

## API Endpoints

### Core Task Management
```
POST   /api/joyagent/tasks              Create new task
GET    /api/joyagent/tasks/{task_id}    Get task status
GET    /api/joyagent/tasks              List all tasks
DELETE /api/joyagent/tasks/{task_id}    Cancel task
GET    /api/joyagent/status             Get service status
```

### Platform Integration
```
POST /api/joyagent/integrations/workflow   Workflow step integration
POST /api/joyagent/integrations/knowledge  Knowledge base enhancement
POST /api/joyagent/integrations/mcp        MCP tool coordination
```

### Monitoring
```
GET /api/joyagent/health    Detailed health check
GET /health                 Simple health check
```

## Task Types

| Type | Description | Use Cases |
|------|-------------|-----------|
| `query` | Natural language query processing | Q&A, information retrieval |
| `report_generation` | Analytical report creation | Business reports, trend analysis |
| `code_generation` | Code analysis and generation | Code review, development assistance |
| `ppt_generation` | PowerPoint presentation creation | Business presentations |
| `data_analysis` | Data analysis and insights | Data exploration, pattern recognition |
| `document_processing` | Document analysis | Document summarization, extraction |
| `workflow_execution` | Workflow task execution | Process automation |

## Agent Modes

| Mode | Description | Best For |
|------|-------------|----------|
| `react` | Reactive reasoning | Simple queries, direct responses |
| `plan_and_execute` | Planning then execution | Complex tasks, multi-step processes |
| `auto` | Automatic mode selection | General purpose, adaptive behavior |

## Usage Examples

### Basic Task Creation
```bash
curl -X POST http://localhost:8007/api/joyagent/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "query": "生成一个关于人工智能发展趋势的报告",
    "task_type": "report_generation",
    "mode": "auto",
    "parameters": {
      "output_format": "pdf",
      "include_charts": true
    }
  }'
```

### Workflow Integration
```bash
curl -X POST http://localhost:8007/api/joyagent/integrations/workflow \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "workflow-123",
    "step_name": "ai_analysis",
    "joyagent_task": {
      "query": "分析上一步骤的数据结果",
      "task_type": "data_analysis"
    },
    "integration_context": {
      "workflow_id": "workflow-123",
      "user_id": "user-456"
    },
    "callback_url": "http://workflow-engine:8002/callbacks/joyagent"
  }'
```

### Knowledge Enhancement
```bash
curl -X POST http://localhost:8007/api/joyagent/integrations/knowledge \
  -H "Content-Type: application/json" \
  -d '{
    "query": "总结企业知识库中关于AI技术的文档",
    "knowledge_base_id": "kb-789",
    "enhancement_type": "summary",
    "parameters": {
      "max_documents": 10,
      "include_references": true
    }
  }'
```

## Configuration

### Environment Variables
See `.env.example` for all available configuration options.

### Key Settings
- `JOYAGENT_ADAPTER_SERVICE_PORT`: Adapter service port (default: 8007)
- `JOYAGENT_ADAPTER_JOYAGENT_HOST`: JoyAgent backend host
- `JOYAGENT_ADAPTER_TASK_TIMEOUT`: Maximum task execution time
- `JOYAGENT_START_FRONTEND`: Whether to start JoyAgent UI (for demos)

## Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt
pip install -e ../shared_libs

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Start the service
python -m src.main
```

### Docker Development
```bash
# Build the image
docker build -t joyagent-adapter .

# Run with docker-compose (recommended)
docker-compose up joyagent-adapter
```

## Monitoring

### Health Checks
The service provides multiple health check endpoints:
- `/health`: Simple status check
- `/api/joyagent/health`: Detailed health with dependencies

### Logging
Structured JSON logging includes:
- Request/response tracing
- Task execution monitoring
- Integration status
- Performance metrics

### Metrics
When enabled, Prometheus metrics are available on port 9090:
- Task creation/completion rates
- Response times
- Error rates
- Active task count

## Security

### Authentication
- JWT-based authentication for API access
- Integration with platform auth service
- Configurable token expiration

### Data Privacy
- Task results stored temporarily in Redis
- Configurable TTL for sensitive data
- No persistent storage of user queries

### Network Security
- Internal service communication only
- CORS configuration for frontend integration
- Request size limits

## Performance

### Scalability
- Horizontal scaling support
- Redis-based distributed task queue
- Stateless service design

### Optimization
- Async/await throughout codebase
- Connection pooling for HTTP clients
- Efficient task status tracking

## Troubleshooting

### Common Issues

1. **JoyAgent Backend Not Starting**
   ```bash
   # Check Java installation
   java -version

   # Check backend logs
   docker logs joyagent-adapter
   ```

2. **Task Timeout**
   ```bash
   # Increase timeout in configuration
   JOYAGENT_ADAPTER_TASK_TIMEOUT=900
   ```

3. **Redis Connection Issues**
   ```bash
   # Verify Redis connectivity
   redis-cli -h redis ping
   ```

### Debug Mode
Enable debug logging:
```bash
JOYAGENT_ADAPTER_DEBUG=true
JOYAGENT_ADAPTER_LOG_LEVEL=debug
```

## Contributing

1. Follow the existing code structure
2. Add comprehensive tests
3. Update documentation
4. Ensure compatibility with platform services

## License

This adapter service is part of the Enterprise AI Platform. JoyAgent-JDGenie is licensed under Apache 2.0.

## Support

- Check service health: `GET /api/joyagent/health`
- View API documentation: `http://localhost:8007/docs`
- Monitor logs for detailed error information
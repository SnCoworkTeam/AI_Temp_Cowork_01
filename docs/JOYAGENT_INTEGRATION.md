# JoyAgent Integration Guide

## Overview

This document describes the integration of JoyAgent-JDGenie with the Enterprise AI Platform.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                Enterprise AI Platform (Port 8080)            │
├─────────────────────────────────────────────────────────────┤
│                     API Gateway                              │
│                         ↓                                    │
│         ┌───────────────────────────────┐                   │
│         │ JoyAgent Adapter (Port 8007)  │                   │
│         │  - REST API Adapter           │                   │
│         │  - Task Management            │                   │
│         │  - Platform Integration       │                   │
│         └───────────────┬───────────────┘                   │
│                         ↓                                    │
│         ┌───────────────────────────────┐                   │
│         │ JoyAgent-JDGenie Components   │                   │
│         ├───────────────────────────────┤                   │
│         │ • Backend API (8080)          │                   │
│         │ • Python Client (1601)        │                   │
│         │ • Python Tools                │                   │
│         │ • Frontend UI (3000) [opt]    │                   │
│         └───────────────┬───────────────┘                   │
│                         ↓                                    │
│         ┌───────────────────────────────┐                   │
│         │ Platform Services Integration │                   │
│         ├───────────────────────────────┤                   │
│         │ • MCP Gateway (8001)          │                   │
│         │ • Workflow Engine (8002)      │                   │
│         │ • Knowledge Base (8004)       │                   │
│         │ • Metadata Service (8005)     │                   │
│         └───────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. JoyAgent-JDGenie (Open Source)
- **Source**: https://github.com/jd-opensource/joyagent-jdgenie
- **License**: Apache 2.0
- **Features**:
  - Multi-agent framework with 75.15% accuracy on GAIA
  - Report generation, code analysis, PPT creation
  - Multiple agent modes: React, Plan and Execute, Auto
  - Lightweight, no cloud platform dependency

### 2. JoyAgent Adapter Service (Custom)
- **Port**: 8007
- **Purpose**: REST API adapter for platform integration
- **Features**:
  - Task creation and management
  - Real-time status tracking
  - Platform service integration
  - Context management with Redis
  - Authentication & security

## Deployment

### Docker Compose Integration

#### Option 1: Include in Main docker-compose.yml

Add the JoyAgent service configuration to the main `docker-compose.yml` file.

#### Option 2: Use Separate Compose File (Recommended)

```bash
# Start all services including JoyAgent
docker-compose -f docker-compose.yml -f docker-compose.joyagent.yml up -d

# Or use the docker compose plugin (recommended)
docker compose -f docker-compose.yml -f docker-compose.joyagent.yml up -d
```

### Environment Configuration

Add to `.env` file:

```bash
# JoyAgent Configuration
JOYAGENT_ADAPTER_PORT=8007
JOYAGENT_START_FRONTEND=false
JWT_SECRET_KEY=your-secret-key-here

# AI Configuration (if not already present)
OPENAI_API_KEY=your-deepseek-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

### Build and Start

```bash
# Build the JoyAgent adapter image
docker compose -f docker-compose.yml -f docker-compose.joyagent.yml build joyagent-adapter

# Start JoyAgent service
docker compose -f docker-compose.yml -f docker-compose.joyagent.yml up -d joyagent-adapter

# View logs
docker compose logs -f joyagent-adapter

# Check health
curl http://localhost:8007/health
```

## API Integration

### API Gateway Routes

Add to `api-gateway/src/config.py`:

```python
# JoyAgent Adapter Service
JOYAGENT_URL = os.getenv("JOYAGENT_ADAPTER_URL", "http://joyagent-adapter:8007")

# Route configuration
{
    "prefix": "/api/joyagent",
    "target": JOYAGENT_URL,
    "strip_prefix": False,
    "timeout": 300,  # 5 minutes for long-running tasks
    "description": "JoyAgent AI Agent Service"
}
```

### Usage Examples

#### 1. Create a Report Generation Task

```bash
curl -X POST http://localhost:8080/api/joyagent/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "query": "生成一个关于AI发展趋势的报告",
    "task_type": "report_generation",
    "mode": "auto",
    "parameters": {
      "output_format": "pdf",
      "include_charts": true,
      "time_period": "2024"
    }
  }'
```

Response:
```json
{
  "task_id": "task-uuid-here",
  "status": "running",
  "created_at": "2025-11-18T10:00:00Z",
  "progress": 10
}
```

#### 2. Check Task Status

```bash
curl http://localhost:8080/api/joyagent/tasks/{task_id}
```

#### 3. Workflow Integration

```bash
curl -X POST http://localhost:8080/api/joyagent/integrations/workflow \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "workflow-123",
    "step_name": "ai_analysis",
    "joyagent_task": {
      "query": "分析数据并生成洞察",
      "task_type": "data_analysis"
    },
    "integration_context": {
      "workflow_id": "workflow-123",
      "user_id": "user-456"
    }
  }'
```

## Service Discovery Integration

JoyAgent adapter automatically registers with the registry service:

```json
{
  "service_name": "joyagent-adapter",
  "service_id": "joyagent-adapter-1",
  "address": "joyagent-adapter",
  "port": 8007,
  "tags": [
    "ai",
    "agent",
    "joyagent",
    "multi-agent",
    "report-generation"
  ],
  "meta": {
    "version": "1.0.0",
    "joyagent_version": "latest",
    "capabilities": "query,report,code,ppt,data_analysis"
  },
  "check": {
    "http": "http://joyagent-adapter:8007/health",
    "interval": "30s",
    "timeout": "10s"
  }
}
```

## Monitoring

### Health Checks

```bash
# Adapter health
curl http://localhost:8007/health

# Detailed health with dependencies
curl http://localhost:8007/api/joyagent/health

# Service status and capabilities
curl http://localhost:8007/api/joyagent/status
```

### Logs

```bash
# View JoyAgent adapter logs
docker compose logs -f joyagent-adapter

# View JoyAgent backend logs (Java)
docker exec enterprise-ai-joyagent-adapter tail -f /app/joyagent-jdgenie/genie-backend/logs/application.log

# View all JoyAgent component logs
docker exec enterprise-ai-joyagent-adapter ps aux | grep -E "java|python|node"
```

### Metrics

If metrics are enabled (port 9090):

```bash
curl http://localhost:9090/metrics
```

## Troubleshooting

### Common Issues

#### 1. JoyAgent Backend Not Starting

**Symptom**: Service health check fails, logs show Java errors

**Solution**:
```bash
# Check Java version
docker exec enterprise-ai-joyagent-adapter java -version

# Restart the service
docker compose -f docker-compose.yml -f docker-compose.joyagent.yml restart joyagent-adapter

# Check memory allocation
docker stats enterprise-ai-joyagent-adapter
```

#### 2. Task Timeout

**Symptom**: Tasks always fail with timeout error

**Solution**:
```bash
# Increase task timeout in .env
JOYAGENT_ADAPTER_TASK_TIMEOUT=900  # 15 minutes

# Restart service
docker compose -f docker-compose.yml -f docker-compose.joyagent.yml restart joyagent-adapter
```

#### 3. Redis Connection Issues

**Symptom**: Cannot create tasks, Redis connection errors in logs

**Solution**:
```bash
# Check Redis connectivity
docker exec enterprise-ai-joyagent-adapter nc -zv redis 6379

# Verify Redis is healthy
docker compose ps redis
```

#### 4. Platform Service Integration Failures

**Symptom**: Cannot access MCP Gateway, Workflow Engine, etc.

**Solution**:
```bash
# Check service URLs in logs
docker compose logs joyagent-adapter | grep "platform"

# Verify services are running
docker compose ps

# Test connectivity
docker exec enterprise-ai-joyagent-adapter curl -f http://mcp-gateway:8001/health
```

### Debug Mode

Enable debug logging:

```bash
# Edit .env
JOYAGENT_ADAPTER_DEBUG=true
JOYAGENT_ADAPTER_LOG_LEVEL=debug

# Restart service
docker compose -f docker-compose.yml -f docker-compose.joyagent.yml restart joyagent-adapter

# Watch logs
docker compose logs -f joyagent-adapter
```

## Performance Tuning

### Resource Allocation

Adjust in `docker-compose.joyagent.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'      # Increase for better performance
      memory: 8192M    # Increase for large tasks
    reservations:
      cpus: '1.0'
      memory: 2048M
```

### Concurrent Tasks

Adjust in `.env`:

```bash
JOYAGENT_ADAPTER_MAX_CONCURRENT_TASKS=20  # Increase for higher throughput
JOYAGENT_ADAPTER_WORKER_PROCESSES=2       # Add more workers
```

### Redis Cache

Adjust context TTL:

```bash
JOYAGENT_ADAPTER_CONTEXT_TTL=7200  # 2 hours
JOYAGENT_ADAPTER_CONTEXT_MAX_SIZE=200
```

## Security Considerations

### API Authentication

JoyAgent adapter integrates with the platform's auth service:

```bash
# JWT token configuration
JOYAGENT_ADAPTER_JWT_SECRET_KEY=<strong-random-key>
JOYAGENT_ADAPTER_JWT_EXPIRE_MINUTES=30
```

### Network Security

- JoyAgent services communicate only within the Docker network
- External access only through API Gateway (port 8080)
- Internal ports (8007, 8080, 1601, 3000) not exposed publicly

### Data Privacy

- Task results stored temporarily in Redis with configurable TTL
- No persistent storage of user queries by default
- Secure communication between services

## Backup and Recovery

### Data Backup

```bash
# Backup JoyAgent data volumes
docker run --rm \
  -v joyagent_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/joyagent-data-backup.tar.gz /data

# Backup JoyAgent tool data
docker run --rm \
  -v joyagent_tool_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/joyagent-tool-data-backup.tar.gz /data
```

### Restore

```bash
# Restore JoyAgent data
docker run --rm \
  -v joyagent_data:/data \
  -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/joyagent-data-backup.tar.gz --strip 1"
```

## Upgrading

### Update JoyAgent-JDGenie

```bash
# Pull latest JoyAgent-JDGenie
cd joyagent-jdgenie
git pull origin main

# Rebuild the image
cd ..
docker compose -f docker-compose.yml -f docker-compose.joyagent.yml build joyagent-adapter

# Restart service
docker compose -f docker-compose.yml -f docker-compose.joyagent.yml up -d joyagent-adapter
```

### Update Adapter Service

```bash
# Update adapter code
cd joyagent-adapter

# Rebuild and restart
docker compose -f docker-compose.yml -f docker-compose.joyagent.yml build joyagent-adapter
docker compose -f docker-compose.yml -f docker-compose.joyagent.yml up -d joyagent-adapter
```

## API Documentation

Full API documentation available at:
- Swagger UI: http://localhost:8007/docs
- ReDoc: http://localhost:8007/redoc
- OpenAPI JSON: http://localhost:8007/openapi.json

## Support

For issues or questions:
1. Check service logs: `docker compose logs joyagent-adapter`
2. Verify health: `curl http://localhost:8007/health`
3. Review this integration guide
4. Check JoyAgent-JDGenie docs: https://github.com/jd-opensource/joyagent-jdgenie

---

**Last Updated**: 2025-11-18
**Version**: 1.0.0
#!/bin/bash
# Combined startup script for JoyAgent Adapter + JoyAgent-JDGenie

set -e

# Activate Python virtual environment
source /app/.venv/bin/activate

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to start JoyAgent backend (Java)
start_joyagent_backend() {
    log "Starting JoyAgent backend (Java Spring Boot)..."
    cd /app/joyagent-jdgenie/genie-backend
    ./start.sh &
    BACKEND_PID=$!
    log "JoyAgent backend started with PID: $BACKEND_PID"
}

# Function to start JoyAgent Python client
start_joyagent_client() {
    log "Starting JoyAgent Python client..."
    cd /app/joyagent-jdgenie/genie-client
    source .venv/bin/activate
    ./start.sh &
    CLIENT_PID=$!
    log "JoyAgent client started with PID: $CLIENT_PID"
}

# Function to start JoyAgent Python tools
start_joyagent_tools() {
    log "Starting JoyAgent Python tools..."
    cd /app/joyagent-jdgenie/genie-tool
    source .venv/bin/activate
    ./start.sh &
    TOOLS_PID=$!
    log "JoyAgent tools started with PID: $TOOLS_PID"
}

# Function to start JoyAgent frontend (if in development mode)
start_joyagent_frontend() {
    if [ "${JOYAGENT_START_FRONTEND:-false}" = "true" ]; then
        log "Starting JoyAgent frontend (Node.js)..."
        cd /app/joyagent-jdgenie/ui
        npm run serve &
        FRONTEND_PID=$!
        log "JoyAgent frontend started with PID: $FRONTEND_PID"
    fi
}

# Function to start JoyAgent adapter service
start_adapter_service() {
    log "Starting JoyAgent Adapter Service..."
    cd /app
    # Wait for JoyAgent backend to be ready
    while ! curl -sf http://localhost:8080/health > /dev/null 2>&1; do
        log "Waiting for JoyAgent backend to be ready..."
        sleep 2
    done

    # Start the adapter service
    python -m src.main &
    ADAPTER_PID=$!
    log "JoyAgent Adapter Service started with PID: $ADAPTER_PID"
}

# Function to wait for all services
wait_for_services() {
    log "Waiting for all services to be ready..."

    # Wait for backend
    timeout 120 bash -c 'while ! curl -sf http://localhost:8080/health >/dev/null 2>&1; do sleep 1; done' || {
        log "ERROR: JoyAgent backend failed to start within 120 seconds"
        exit 1
    }
    log "✓ JoyAgent backend is ready"

    # Wait for client (if started)
    if [ ! -z "$CLIENT_PID" ]; then
        timeout 60 bash -c 'while ! curl -sf http://localhost:1601/health >/dev/null 2>&1; do sleep 1; done' || {
            log "WARNING: JoyAgent client not responding"
        }
        log "✓ JoyAgent client is ready"
    fi

    # Wait for adapter service
    timeout 60 bash -c 'while ! curl -sf http://localhost:8007/health >/dev/null 2>&1; do sleep 1; done' || {
        log "ERROR: JoyAgent Adapter Service failed to start within 60 seconds"
        exit 1
    }
    log "✓ JoyAgent Adapter Service is ready"

    # Wait for frontend (if started)
    if [ "${JOYAGENT_START_FRONTEND:-false}" = "true" ]; then
        timeout 60 bash -c 'while ! curl -sf http://localhost:3000 >/dev/null 2>&1; do sleep 1; done' || {
            log "WARNING: JoyAgent frontend not responding"
        }
        log "✓ JoyAgent frontend is ready"
    fi
}

# Function to handle shutdown
shutdown() {
    log "Received shutdown signal, stopping all services..."

    # Kill all child processes
    if [ ! -z "$ADAPTER_PID" ]; then
        log "Stopping JoyAgent Adapter Service (PID: $ADAPTER_PID)..."
        kill $ADAPTER_PID 2>/dev/null || true
    fi

    if [ ! -z "$BACKEND_PID" ]; then
        log "Stopping JoyAgent backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi

    if [ ! -z "$CLIENT_PID" ]; then
        log "Stopping JoyAgent client (PID: $CLIENT_PID)..."
        kill $CLIENT_PID 2>/dev/null || true
    fi

    if [ ! -z "$TOOLS_PID" ]; then
        log "Stopping JoyAgent tools (PID: $TOOLS_PID)..."
        kill $TOOLS_PID 2>/dev/null || true
    fi

    if [ ! -z "$FRONTEND_PID" ]; then
        log "Stopping JoyAgent frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi

    # Wait for graceful shutdown
    sleep 5

    # Force kill if necessary
    pkill -f "java.*genie-backend" 2>/dev/null || true
    pkill -f "python.*genie-client" 2>/dev/null || true
    pkill -f "python.*genie-tool" 2>/dev/null || true
    pkill -f "node.*ui" 2>/dev/null || true
    pkill -f "python.*src.main" 2>/dev/null || true

    log "All services stopped"
    exit 0
}

# Set up signal handlers
trap shutdown SIGTERM SIGINT

# Check environment variables
log "JoyAgent Adapter Service Configuration:"
log "  Service Host: ${JOYAGENT_ADAPTER_SERVICE_HOST:-0.0.0.0}"
log "  Service Port: ${JOYAGENT_ADAPTER_SERVICE_PORT:-8007}"
log "  Debug Mode: ${JOYAGENT_ADAPTER_DEBUG:-false}"
log "  Start Frontend: ${JOYAGENT_START_FRONTEND:-false}"

# Start all services
log "Starting all JoyAgent services..."

start_joyagent_backend
start_joyagent_client
start_joyagent_tools
start_joyagent_frontend
start_adapter_service

# Wait for services to be ready
wait_for_services

log "All services are running successfully!"
log "JoyAgent Adapter Service: http://localhost:8007"
log "JoyAgent Backend API: http://localhost:8080"
log "JoyAgent Python Client: http://localhost:1601"
if [ "${JOYAGENT_START_FRONTEND:-false}" = "true" ]; then
    log "JoyAgent Frontend UI: http://localhost:3000"
fi

# Keep the container running and monitor processes
while true; do
    # Check if critical processes are still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        log "ERROR: JoyAgent backend process died"
        exit 1
    fi

    if ! kill -0 $ADAPTER_PID 2>/dev/null; then
        log "ERROR: JoyAgent Adapter Service process died"
        exit 1
    fi

    # Health check every 30 seconds
    sleep 30

    # Optional: Health check endpoints
    if ! curl -sf http://localhost:8007/health >/dev/null 2>&1; then
        log "WARNING: JoyAgent Adapter Service health check failed"
    fi

    if ! curl -sf http://localhost:8080/health >/dev/null 2>&1; then
        log "WARNING: JoyAgent backend health check failed"
    fi
done
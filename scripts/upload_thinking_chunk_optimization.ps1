# Upload thinking chunk optimization fixes
# Fixes: Backend throttling for thinking chunks, Frontend optimization for streaming updates

$SERVER = "43.143.139.197"
$SSH_KEY = "enterprise_ai_platform.pem"
$USER = "root"

Write-Host "Uploading thinking chunk optimization fixes..."

# Upload backend fix
scp -i $SSH_KEY "agent-service/src/core/dynamic_workflow_designer.py" "${USER}@${SERVER}:/root/enterprise-ai-platform/agent-service/src/core/dynamic_workflow_designer.py"

# Upload frontend fix
scp -i $SSH_KEY "web-ui/src/components/ChatInterface.tsx" "${USER}@${SERVER}:/root/enterprise-ai-platform/web-ui/src/components/ChatInterface.tsx"

Write-Host "Restarting services..."

# Restart agent-service
ssh -i $SSH_KEY ${USER}@${SERVER} "cd /root/enterprise-ai-platform && docker compose restart agent-service"

# Restart web-ui
ssh -i $SSH_KEY ${USER}@${SERVER} "cd /root/enterprise-ai-platform && docker compose restart web-ui"

Write-Host "Done! Services restarted."


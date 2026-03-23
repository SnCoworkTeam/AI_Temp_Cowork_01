# Upload organization service fix and initialize data
$ErrorActionPreference = "Stop"

$APP_SERVER = "43.143.139.197"
$APP_SERVER_KEY = ".\enterprise_ai_platform.pem"
$APP_SERVER_USER = "ubuntu"
$REMOTE_BASE = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Uploading organization service fix and initializing data" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Change to project root
Set-Location (Split-Path -Parent $PSScriptRoot)

$sshTarget = "${APP_SERVER_USER}@${APP_SERVER}"

# Step 1: Upload fixed service file
Write-Host "`n[1/3] Uploading fixed service file..." -ForegroundColor Yellow
$serviceFile = "metadata-service/src/services/organization_architecture_service.py"
$remoteFile = "$REMOTE_BASE/$serviceFile"
$remoteDir = Split-Path -Path $remoteFile -Parent

try {
    ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget "mkdir -p $remoteDir" 2>&1 | Out-Null
    scp -i $APP_SERVER_KEY -o ConnectTimeout=10 $serviceFile "${sshTarget}:$remoteFile" 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Service file uploaded successfully" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Service file upload failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ❌ Upload failed: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Restart metadata-service
Write-Host "`n[2/3] Restarting metadata-service..." -ForegroundColor Yellow
try {
    $restartCmd = "cd $REMOTE_BASE; docker compose restart metadata-service"
    ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget $restartCmd 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Service restarted successfully" -ForegroundColor Green
        Write-Host "  ⏳ Waiting 5 seconds for service to start..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
    } else {
        Write-Host "  ❌ Service restart failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ❌ Restart failed: $_" -ForegroundColor Red
    exit 1
}

# Step 3: Initialize organization architecture data
Write-Host "`n[3/3] Initializing organization architecture data..." -ForegroundColor Yellow
try {
    $initCmd = @"
cd $REMOTE_BASE
docker compose exec -T metadata-service python -c "
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, '/opt/enterprise-ai-platform')
from database.src.core.database import get_database_manager
from database.src.core.session import get_db, init_session_factory
from database.src.models.enterprise_architecture_models import OrganizationUnit
from uuid import uuid4

async def init_org_data():
    db_manager = get_database_manager()
    await db_manager.init_db()
    db = next(get_db())
    
    # Check if data exists
    existing_count = db.query(OrganizationUnit).count()
    if existing_count > 0:
        print(f'Organization data already exists: {existing_count} units')
        return
    
    # Create demo organizations
    orgs = [
        {'name': 'LuminaOS集团', 'code': 'LUMINA_GROUP', 'description': 'LuminaOS企业AI平台总部', 'organization_type': '集团', 'level': 1},
        {'name': '技术中心', 'code': 'TECH_CENTER', 'description': '技术研发中心', 'organization_type': '部门', 'level': 2, 'parent_code': 'LUMINA_GROUP'},
        {'name': '产品部', 'code': 'PRODUCT_DEPT', 'description': '产品管理部门', 'organization_type': '部门', 'level': 2, 'parent_code': 'LUMINA_GROUP'},
        {'name': 'AI平台团队', 'code': 'AI_PLATFORM_TEAM', 'description': 'AI平台开发团队', 'organization_type': '团队', 'level': 3, 'parent_code': 'TECH_CENTER'},
        {'name': '企业架构团队', 'code': 'EA_TEAM', 'description': '企业架构管理团队', 'organization_type': '团队', 'level': 3, 'parent_code': 'TECH_CENTER'},
    ]
    
    org_map = {}
    for org_data in orgs:
        parent_id = None
        if 'parent_code' in org_data:
            parent = org_map.get(org_data['parent_code'])
            if parent:
                parent_id = parent.id
        
        org = OrganizationUnit(
            id=uuid4(),
            name=org_data['name'],
            code=org_data['code'],
            description=org_data['description'],
            organization_type=org_data['organization_type'],
            level=org_data['level'],
            parent_id=parent_id,
            status='active'
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        org_map[org_data['code']] = org
        print(f'Created: {org.name} ({org.code})')
    
    print(f'Successfully created {len(orgs)} organization units')

asyncio.run(init_org_data())
"
"@
    
    ssh -i $APP_SERVER_KEY -o ConnectTimeout=10 $sshTarget $initCmd 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Data initialization completed" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Data initialization may have issues, but continuing..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠️  Data initialization error: $_" -ForegroundColor Yellow
    Write-Host "  You may need to run the initialization script manually" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Deployment completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Check the organization page: http://43.143.139.197:3000/enterprise-architecture/organization" -ForegroundColor White
Write-Host "2. If data is still missing, run the initialization script manually on the server" -ForegroundColor White
Write-Host "`n"


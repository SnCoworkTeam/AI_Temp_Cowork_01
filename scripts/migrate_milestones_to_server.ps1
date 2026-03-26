# Milestone 1-4 Code and Data Migration Script
# Sync stage 1-4 code and data to server

param(
    [string]$AppServerHost = "43.143.139.197",
    [string]$AppServerUser = "ubuntu",
    [string]$AppServerKey = "E:\enterprise-ai-platform\enterprise_ai_platform.pem",
    [string]$Neo4jServerHost = "",
    [string]$Neo4jServerUser = "ubuntu",
    [string]$Neo4jServerKey = "E:\enterprise-ai-platform\Neo4j.pem",
    [string]$RemotePath = "/opt/enterprise-ai-platform",
    [switch]$SkipCode = $false,
    [switch]$SkipData = $false,
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Milestone 1-4 Code and Data Migration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check key files
if (-not (Test-Path $AppServerKey)) {
    Write-Host "[ERROR] Application server key file not found: $AppServerKey" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $Neo4jServerKey)) {
    Write-Host "[WARN] Neo4j server key file not found: $Neo4jServerKey" -ForegroundColor Yellow
    Write-Host "[INFO] Will skip Neo4j data migration" -ForegroundColor Yellow
    $SkipNeo4j = $true
} else {
    $SkipNeo4j = $false
}

# Set key file permissions
Write-Host "[INFO] Setting key file permissions..." -ForegroundColor Yellow
try {
    icacls $AppServerKey /inheritance:r /grant:r "${env:USERNAME}:R" | Out-Null
    if (-not $SkipNeo4j) {
        icacls $Neo4jServerKey /inheritance:r /grant:r "${env:USERNAME}:R" | Out-Null
    }
    Write-Host "[OK] Key file permissions set" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Failed to set key file permissions: $_" -ForegroundColor Yellow
}

# Test SSH connection
Write-Host ""
Write-Host "[INFO] Testing application server SSH connection..." -ForegroundColor Yellow
try {
    $testResult = ssh -i $AppServerKey -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$AppServerUser@$AppServerHost" "echo 'Connection OK'" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Application server connection successful" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Application server connection failed: $testResult" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "[ERROR] SSH connection test failed: $_" -ForegroundColor Red
    exit 1
}

if (-not $SkipNeo4j -and $Neo4jServerHost) {
    Write-Host "[INFO] Testing Neo4j server SSH connection..." -ForegroundColor Yellow
    try {
        $testResult = ssh -i $Neo4jServerKey -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$Neo4jServerUser@$Neo4jServerHost" "echo 'Connection OK'" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] Neo4j server connection successful" -ForegroundColor Green
        } else {
            Write-Host "[WARN] Neo4j server connection failed, will skip Neo4j data migration" -ForegroundColor Yellow
            $SkipNeo4j = $true
        }
    } catch {
        Write-Host "[WARN] Neo4j server connection failed, will skip Neo4j data migration: $_" -ForegroundColor Yellow
        $SkipNeo4j = $true
    }
}

# Define items to sync
$PROJECT_ROOT = if ($PSScriptRoot) { 
    Split-Path -Parent $PSScriptRoot | Split-Path -Parent 
} else { 
    $PWD.Path 
}
if (-not (Test-Path (Join-Path $PROJECT_ROOT "os-core"))) {
    $PROJECT_ROOT = "E:\enterprise-ai-platform"
}
Write-Host "[INFO] Project root: $PROJECT_ROOT" -ForegroundColor Yellow

$syncItems = @(
    @{Path = "os-core"; Description = "OS Core Module (Milestone 1)"},
    @{Path = "services/unified_intent_service.py"; Description = "Unified Intent Service"},
    @{Path = "metadata-service/src/services/ea_vectorization_service.py"; Description = "EA Vectorization Service (Milestone 2)"},
    @{Path = "metadata-service/src/services/ea_knowledge_graph.py"; Description = "EA Knowledge Graph Service (Milestone 2)"},
    @{Path = "metadata-service/src/services/ea_hybrid_query.py"; Description = "EA Hybrid Query Engine (Milestone 2)"},
    @{Path = "services/enterprise_semantic_engine.py"; Description = "Enterprise Semantic Engine"},
    @{Path = "metadata-service/src/scripts/ea_data_initializer.py"; Description = "EA Data Initializer Script"},
    @{Path = "os-core/policy_engine.py"; Description = "Policy Engine (Milestone 3)"},
    @{Path = "os-core/audit_logger.py"; Description = "Audit Logger (Milestone 3)"},
    @{Path = "os-core/governance_dashboard.py"; Description = "Governance Dashboard (Milestone 3)"},
    @{Path = "api-gateway/src/routes/policy_management.py"; Description = "Policy Management API (Milestone 3)"},
    @{Path = "config/policies.yaml"; Description = "Policy Configuration File"},
    @{Path = "os-core/behavior_collector.py"; Description = "Behavior Collector (Milestone 4)"},
    @{Path = "os-core/optimization_engine.py"; Description = "Optimization Engine (Milestone 4)"},
    @{Path = "os-core/evolution_manager.py"; Description = "Evolution Manager (Milestone 4)"},
    @{Path = "os-core/scenario_recommender.py"; Description = "Scenario Recommender (Milestone 4)"},
    @{Path = "tests/os_core"; Description = "OS Core Tests"},
    @{Path = "tests/milestone_integration_test.py"; Description = "Milestone Integration Tests"},
    @{Path = "docker-compose.yml"; Description = "Docker Compose Configuration"},
    @{Path = "os-core/__init__.py"; Description = "OS Core Module Init"}
)

# Sync code
if (-not $SkipCode) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Syncing Code Files" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($item in $syncItems) {
        $localPath = Join-Path $PROJECT_ROOT $item.Path
        $normalizedPath = $item.Path -replace '\\', '/'
        $itemRemotePath = "$RemotePath/$normalizedPath"
        
        if ($item.Path -match '\.[^/\\]+$') {
            # Single file
            if (Test-Path $localPath) {
                Write-Host "[INFO] Syncing: $($item.Description)" -ForegroundColor Yellow
                Write-Host "       Local: $localPath" -ForegroundColor Gray
                Write-Host "       Remote: $itemRemotePath" -ForegroundColor Gray
                
                if (-not $DryRun) {
                    $remoteDir = Split-Path -Parent $itemRemotePath -ErrorAction SilentlyContinue
                    if ($remoteDir) {
                        ssh -i $AppServerKey -o StrictHostKeyChecking=no "$AppServerUser@$AppServerHost" "mkdir -p `"$remoteDir`"" | Out-Null
                    }
                    
                    scp -i $AppServerKey -o StrictHostKeyChecking=no "$localPath" "$AppServerUser@${AppServerHost}:$itemRemotePath" 2>&1 | Out-Null
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "[OK] Sync successful" -ForegroundColor Green
                    } else {
                        Write-Host "[ERROR] Sync failed" -ForegroundColor Red
                    }
                } else {
                    Write-Host "[DRY-RUN] Would sync this file" -ForegroundColor Cyan
                }
            } else {
                Write-Host "[WARN] File not found, skipping: $localPath" -ForegroundColor Yellow
            }
        } else {
            # Directory
            if (Test-Path $localPath) {
                Write-Host "[INFO] Syncing directory: $($item.Description)" -ForegroundColor Yellow
                Write-Host "       Local: $localPath" -ForegroundColor Gray
                Write-Host "       Remote: $remotePath" -ForegroundColor Gray
                
                if (-not $DryRun) {
                    ssh -i $AppServerKey -o StrictHostKeyChecking=no "$AppServerUser@$AppServerHost" "mkdir -p `"$remotePath`"" | Out-Null
                    
                    $files = Get-ChildItem -Path $localPath -Recurse -File
                    $fileCount = 0
                    foreach ($file in $files) {
                        $relativePath = $file.FullName.Substring($localPath.Length + 1)
                        $targetPath = "$remotePath/$relativePath" -replace '\\', '/'
                        $targetDir = Split-Path -Parent $targetPath
                        
                        ssh -i $AppServerKey -o StrictHostKeyChecking=no "$AppServerUser@$AppServerHost" "mkdir -p `"$targetDir`"" | Out-Null
                        scp -i $AppServerKey -o StrictHostKeyChecking=no "$($file.FullName)" "$AppServerUser@${AppServerHost}:$targetPath" 2>&1 | Out-Null
                        $fileCount++
                    }
                    
                    Write-Host "[OK] Directory sync completed ($fileCount files)" -ForegroundColor Green
                } else {
                    Write-Host "[DRY-RUN] Would sync this directory" -ForegroundColor Cyan
                }
            } else {
                Write-Host "[WARN] Directory not found, skipping: $localPath" -ForegroundColor Yellow
            }
        }
    }
    
    Write-Host ""
    Write-Host "[OK] Code sync completed" -ForegroundColor Green
}

# Sync database data
if (-not $SkipData) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Syncing Database Data" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "[INFO] Preparing PostgreSQL data migration..." -ForegroundColor Yellow
    $pgDumpFile = Join-Path $env:TEMP "milestones_pg_dump_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"
    
    Write-Host "[INFO] To export local PostgreSQL data, run:" -ForegroundColor Yellow
    Write-Host "      pg_dump -h localhost -U ai_user -d ai_platform > $pgDumpFile" -ForegroundColor Gray
    
    if (-not $DryRun -and (Test-Path $pgDumpFile)) {
        Write-Host "[INFO] Uploading PostgreSQL data to server..." -ForegroundColor Yellow
        scp -i $AppServerKey -o StrictHostKeyChecking=no "$pgDumpFile" "$AppServerUser@${AppServerHost}:$RemotePath/pg_dump.sql" 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] PostgreSQL data uploaded successfully" -ForegroundColor Green
            Write-Host "[INFO] On server, run to import data:" -ForegroundColor Yellow
            Write-Host "      psql -h localhost -U ai_user -d ai_platform < $RemotePath/pg_dump.sql" -ForegroundColor Gray
        }
    }
    
    if (-not $SkipNeo4j) {
        Write-Host ""
        Write-Host "[INFO] Preparing Neo4j data migration..." -ForegroundColor Yellow
        
        if ($Neo4jServerHost) {
            Write-Host "[INFO] Neo4j is on separate server: $Neo4jServerHost" -ForegroundColor Yellow
        } else {
            Write-Host "[INFO] Neo4j is on the same server as application" -ForegroundColor Yellow
        }
    }
}

# Server-side initialization
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Server-side Initialization" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not $DryRun) {
    Write-Host "[INFO] Executing initialization commands on server..." -ForegroundColor Yellow
    
    $initScript = @"
cd $RemotePath
find os-core -type f -name '*.py' -exec chmod 644 {} \;
find services -type f -name '*.py' -exec chmod 644 {} \;
find metadata-service -type f -name '*.py' -exec chmod 644 {} \;
export PYTHONPATH=$RemotePath`:`$PYTHONPATH
echo '[OK] Initialization completed'
"@
    
    $initScript | ssh -i $AppServerKey -o StrictHostKeyChecking=no "$AppServerUser@$AppServerHost" bash
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Server-side initialization completed" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Server-side initialization may have issues, please check" -ForegroundColor Yellow
    }
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Migration Completed" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Check files on server to ensure correct upload" -ForegroundColor White
Write-Host "2. Import database data if needed" -ForegroundColor White
Write-Host "3. Restart related services: docker-compose restart" -ForegroundColor White
Write-Host "4. Run tests to verify: pytest tests/milestone_integration_test.py" -ForegroundColor White
Write-Host ""


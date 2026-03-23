# Docker API Version Compatibility Fix

## Problem
You're encountering an error:
```
request returned Internal Server Error for API route and version http://%2F%2F.%2Fpipe%2FdockerDesktopLinuxEngine/v1.46/containers/json?all=1&filters=...
check if the server supports the requested API version
```

This happens when your Docker client (version 27.1.1) is trying to use API version 1.46, but your Docker Desktop daemon doesn't support it.

## Solutions

### Solution 1: Set Environment Variable (Quick Fix)

**For PowerShell (Current Session):**
```powershell
$env:DOCKER_API_VERSION = "1.40"
```

**For PowerShell (Permanent - Add to Profile):**
```powershell
# Open your PowerShell profile
notepad $PROFILE

# Add this line:
$env:DOCKER_API_VERSION = "1.40"
```

**For Command Prompt:**
```cmd
set DOCKER_API_VERSION=1.40
```

**For System-Wide (Windows):**
1. Open System Properties → Environment Variables
2. Add new System Variable:
   - Name: `DOCKER_API_VERSION`
   - Value: `1.40`

### Solution 2: Use the Fix Script

Run the provided PowerShell script:
```powershell
.\fix-docker-api-version.ps1
```

### Solution 3: Update Docker Desktop

The best long-term solution is to update Docker Desktop to a version that supports API 1.46:

1. Open Docker Desktop
2. Go to Settings → General
3. Check for updates
4. Or download the latest version from: https://www.docker.com/products/docker-desktop

### Solution 4: Restart Docker Desktop

Sometimes Docker Desktop needs a restart:

1. Right-click Docker Desktop icon in system tray
2. Select "Quit Docker Desktop"
3. Wait a few seconds
4. Start Docker Desktop again
5. Wait for it to fully start (green icon in system tray)

### Solution 5: Switch Docker Context

If you have multiple Docker contexts, try switching:

```powershell
# List available contexts
docker context ls

# Switch to default context
docker context use default

# Or switch back to desktop-linux
docker context use desktop-linux
```

## Verify the Fix

After applying any solution, verify it works:

```powershell
docker ps
docker version
```

You should see the server version information without errors.

## Recommended API Versions

- **1.40** - Widely supported, safe choice
- **1.41** - Good compatibility
- **1.42** - Modern Docker Desktop versions
- **1.43** - Recent Docker Desktop versions
- **1.44+** - Latest Docker Desktop versions

Start with 1.40 and increase if your Docker Desktop version supports it.

## Troubleshooting

If the issue persists even after setting `DOCKER_API_VERSION`, the Docker Desktop daemon may not be running properly:

### Step 1: Verify Docker Desktop is Running
1. Check the system tray for Docker Desktop icon
2. It should be green/active (not yellow/starting)
3. Right-click → "Troubleshoot" if available

### Step 2: Restart Docker Desktop Completely
1. **Quit Docker Desktop:**
   - Right-click Docker Desktop icon in system tray
   - Select "Quit Docker Desktop"
   - Wait 10-15 seconds

2. **Start Docker Desktop:**
   - Open Docker Desktop from Start Menu
   - Wait for it to fully start (green icon)
   - This can take 1-2 minutes

3. **Verify it's running:**
   ```powershell
   docker ps
   ```

### Step 3: Check Docker Desktop Service
If Docker Desktop won't start:

1. **Check Windows Services:**
   ```powershell
   Get-Service | Where-Object {$_.Name -like "*docker*"}
   ```

2. **Restart Docker services:**
   ```powershell
   # Run as Administrator
   Restart-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
   ```

### Step 4: Check Docker Desktop Logs
1. Open Docker Desktop
2. Go to Settings → Troubleshoot
3. Click "View logs" to see any errors

### Step 5: Reinstall Docker Desktop (Last Resort)
If nothing works:
1. Uninstall Docker Desktop
2. Download latest version from https://www.docker.com/products/docker-desktop
3. Install and restart your computer
4. Start Docker Desktop

### Step 6: Check Named Pipe Access
The error shows it's trying to use `\\.\pipe\dockerDesktopLinuxEngine`. Ensure:
- Docker Desktop is using WSL 2 backend (Settings → General → Use WSL 2)
- WSL 2 is properly installed and running
- The named pipe is accessible (usually automatic)

### Step 7: Try Different Docker Context
```powershell
# List contexts
docker context ls

# Try default context
docker context use default

# Test
docker ps
```

## Additional Notes

- The API version mismatch is common when Docker client is newer than the Docker daemon
- Setting `DOCKER_API_VERSION` forces the client to use a compatible version
- Docker Desktop updates usually resolve this automatically
- The fix script (`fix-docker-api-version.ps1`) automates the process

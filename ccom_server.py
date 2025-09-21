#!/usr/bin/env python3
"""
CCOM Remote Server v0.3
Enables CCOM commands from iOS/mobile devices via REST API
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import subprocess
import os
import json
from pathlib import Path
from typing import Optional

app = FastAPI(
    title="CCOM Remote Server",
    description="Execute CCOM commands remotely from iOS/mobile devices",
    version="0.3.0"
)

class CCOMCommand(BaseModel):
    command: str
    project_path: Optional[str] = None

class CCOMResponse(BaseModel):
    success: bool
    output: str
    error: str
    project_info: Optional[dict] = None

@app.get("/", response_class=HTMLResponse)
def dashboard():
    """Mobile-first CCOM dashboard"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CCOM Mobile</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; min-height: 100vh; padding: 20px;
        }
        .container { max-width: 400px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .project-selector {
            background: rgba(255,255,255,0.1); border-radius: 12px;
            padding: 20px; margin-bottom: 20px; backdrop-filter: blur(10px);
        }
        .status {
            display: flex; align-items: center; gap: 10px; margin-bottom: 15px;
            font-size: 18px; font-weight: 600;
        }
        .status-dot { width: 12px; height: 12px; border-radius: 50%; background: #4ade80; }
        .actions { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 20px; }
        .btn {
            background: rgba(255,255,255,0.2); border: none; border-radius: 12px;
            padding: 15px; color: white; font-weight: 600; cursor: pointer;
            backdrop-filter: blur(10px); transition: all 0.3s ease;
        }
        .btn:hover { background: rgba(255,255,255,0.3); transform: translateY(-2px); }
        .btn-primary { background: rgba(74, 222, 128, 0.3); }
        .btn-warning { background: rgba(251, 191, 36, 0.3); }
        .btn-danger { background: rgba(239, 68, 68, 0.3); }
        .quick-chat {
            background: rgba(255,255,255,0.1); border-radius: 12px;
            padding: 20px; margin-top: 20px; backdrop-filter: blur(10px);
        }
        .chat-input {
            width: 100%; background: rgba(255,255,255,0.1); border: none;
            border-radius: 8px; padding: 12px; color: white; margin-bottom: 10px;
        }
        .chat-input::placeholder { color: rgba(255,255,255,0.6); }
        .loading { display: none; text-align: center; padding: 20px; }
        .spinner { width: 30px; height: 30px; border: 3px solid rgba(255,255,255,0.3);
                   border-top: 3px solid white; border-radius: 50%; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .result { background: rgba(0,0,0,0.2); border-radius: 8px; padding: 15px; margin-top: 15px; display: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 CCOM Mobile</h1>
            <p>Enterprise Development Command Center</p>
        </div>

        <div class="project-selector">
            <select id="project-select" style="width: 100%; padding: 8px; background: rgba(255,255,255,0.2); border: none; border-radius: 8px; color: white; margin-bottom: 10px;">
                <option value="todo">TODO</option>
                <option value="ccom">CCOM</option>
                <option value="uwa">UWA</option>
            </select>
            <div class="status">
                <span class="status-dot"></span>
                <span id="project-name">Loading...</span>
            </div>
            <div id="project-status">Checking project status...</div>
        </div>

        <div class="actions">
            <button class="btn btn-primary" onclick="runWorkflow('context')">📊 Context</button>
            <button class="btn btn-warning" onclick="runWorkflow('quality')">🔍 Quality</button>
            <button class="btn btn-danger" onclick="runWorkflow('security')">🛡️ Security</button>
            <button class="btn btn-primary" onclick="runWorkflow('deploy')">🚀 Deploy</button>
        </div>

        <div class="quick-chat">
            <h3>💬 Quick Command</h3>
            <input type="text" class="chat-input" id="chatInput" placeholder="Natural language command..." />
            <button class="btn" style="width: 100%;" onclick="sendChat()">Send Command</button>
        </div>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Executing command...</p>
        </div>

        <div class="result" id="result"></div>
    </div>

    <script>
        let currentProject = 'todo';

        // Handle project selector change
        document.getElementById('project-select').addEventListener('change', function(e) {
            currentProject = e.target.value;
            loadProjectStatus();
        });

        async function loadProjectStatus() {
            try {
                const response = await fetch('/context', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ project_path: `C:/Users/DR/OneDrive/projects/${currentProject}` })
                });
                const data = await response.json();

                document.getElementById('project-name').textContent = currentProject.toUpperCase();
                document.getElementById('project-status').textContent =
                    data.success ? '✅ Production Ready' : '⚠️ Needs Attention';
            } catch (error) {
                document.getElementById('project-status').textContent = '❌ Connection Error';
            }
        }

        async function runWorkflow(action) {
            showLoading(true);
            try {
                const response = await fetch('/ccom', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        command: action === 'context' ? 'context' : `workflow ${action}`,
                        project_path: `C:/Users/DR/OneDrive/projects/${currentProject}`
                    })
                });
                const data = await response.json();
                showResult(data);
            } catch (error) {
                showResult({ success: false, error: 'Connection failed: ' + error.message });
            }
            showLoading(false);
        }

        async function sendChat() {
            const input = document.getElementById('chatInput');
            const command = input.value.trim();
            if (!command) return;

            showLoading(true);
            try {
                const response = await fetch('/ccom', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        command: command,
                        project_path: `C:/Users/DR/OneDrive/projects/${currentProject}`
                    })
                });
                const data = await response.json();
                showResult(data);
                input.value = '';
            } catch (error) {
                showResult({ success: false, error: 'Command failed' });
            }
            showLoading(false);
        }

        function showLoading(show) {
            document.getElementById('loading').style.display = show ? 'block' : 'none';
            if (show) {
                document.getElementById('result').style.display = 'none';
            }
        }

        function showResult(data) {
            const resultDiv = document.getElementById('result');
            if (!resultDiv) {
                console.error('ERROR: result div not found!');
                return;
            }
            resultDiv.innerHTML = `
                <h4>${data.success ? '✅ Success' : '❌ Error'}</h4>
                <pre style="white-space: pre-wrap; margin-top: 10px;">${data.output || data.error || JSON.stringify(data, null, 2)}</pre>
            `;
            resultDiv.style.display = 'block';
        }

        // Load project status on page load
        loadProjectStatus();

        // Allow Enter key in chat input
        document.getElementById('chatInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendChat();
        });
    </script>
</body>
</html>
    """

@app.get("/api/health")
def health_check():
    """Health check endpoint for API"""
    return {"status": "CCOM Remote Server v0.3 - Ready", "endpoints": ["/ccom", "/projects", "/context"]}

@app.post("/ccom", response_model=CCOMResponse)
def execute_ccom(cmd: CCOMCommand):
    """Execute CCOM command remotely"""
    try:
        # Default to current directory if no project path specified
        project_path = cmd.project_path or "."

        # Validate project path exists
        if not os.path.exists(project_path):
            raise HTTPException(status_code=400, detail=f"Project path does not exist: {project_path}")

        # Execute CCOM command using Popen for better output capture
        import sys
        original_cwd = os.getcwd()
        os.chdir(project_path)

        proc = subprocess.Popen(
            [sys.executable, "-m", "ccom.cli", cmd.command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=dict(os.environ, PYTHONIOENCODING='utf-8:replace')
        )

        stdout, stderr = proc.communicate(timeout=60)
        os.chdir(original_cwd)

        result = subprocess.CompletedProcess(
            args=None,
            returncode=proc.returncode,
            stdout=stdout,
            stderr=stderr
        )

        # Get project info if available
        project_info = None
        try:
            memory_file = Path(project_path) / ".claude" / "memory.json"
            if memory_file.exists():
                with open(memory_file) as f:
                    memory_data = json.load(f)
                    project_info = {
                        "name": memory_data.get("project", {}).get("name", "Unknown"),
                        "features": len(memory_data.get("features", {})),
                        "version": memory_data.get("metadata", {}).get("version", "Unknown")
                    }
        except:
            pass

        # CCOM outputs to both stdout and stderr - combine and clean
        output_lines = []

        # Add stdout if present
        if result.stdout and result.stdout.strip():
            output_lines.append(result.stdout.strip())

        # Add stderr but filter out warnings
        if result.stderr and result.stderr.strip():
            stderr_lines = result.stderr.split('\n')
            clean_stderr = []
            for line in stderr_lines:
                if ('RuntimeWarning' not in line and
                    'frozen runpy' not in line and
                    'INFO:' not in line and
                    line.strip()):
                    clean_stderr.append(line)
            if clean_stderr:
                output_lines.extend(clean_stderr)

        full_output = '\n'.join(output_lines).strip()


        # If we don't get output but have project info, create a summary
        if not full_output and project_info and result.returncode == 0:
            full_output = f"✅ Project: {project_info['name']}\n"
            full_output += f"📊 Features: {project_info['features']}\n"
            full_output += f"🔧 Version: {project_info['version']}\n"
            full_output += "\nCommand executed successfully. Check .claude/memory.json for details."

        return CCOMResponse(
            success=result.returncode == 0,
            output=full_output,
            error="" if result.returncode == 0 else "",
            project_info=project_info
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Command timed out after 60 seconds")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.get("/projects")
def list_projects():
    """List available CCOM projects"""
    projects = []

    # Common project locations
    search_paths = [
        Path.home() / "OneDrive" / "projects",
        Path.home() / "projects",
        Path.home() / "code",
        Path.home() / "dev",
        Path.cwd()
    ]

    for search_path in search_paths:
        if search_path.exists():
            for item in search_path.iterdir():
                if item.is_dir() and (item / ".claude").exists():
                    try:
                        memory_file = item / ".claude" / "memory.json"
                        if memory_file.exists():
                            with open(memory_file) as f:
                                memory_data = json.load(f)
                                projects.append({
                                    "name": memory_data.get("project", {}).get("name", item.name),
                                    "path": str(item),
                                    "features": len(memory_data.get("features", {})),
                                    "created": memory_data.get("project", {}).get("created", "Unknown")
                                })
                    except:
                        projects.append({
                            "name": item.name,
                            "path": str(item),
                            "features": 0,
                            "created": "Unknown"
                        })

    return {"projects": projects}

@app.post("/context")
def get_project_context(request: dict):
    """Get project context for iOS display"""
    project_path = request.get("project_path", ".")

    try:
        # Execute context command using Popen for better output capture
        import sys
        original_cwd = os.getcwd()
        os.chdir(project_path)

        proc = subprocess.Popen(
            [sys.executable, "-m", "ccom.orchestrator", "context"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=dict(os.environ, PYTHONIOENCODING='utf-8:replace')
        )

        stdout, stderr = proc.communicate(timeout=30)
        os.chdir(original_cwd)

        result = subprocess.CompletedProcess(
            args=None,
            returncode=proc.returncode,
            stdout=stdout,
            stderr=stderr
        )

        if result.returncode == 0:
            return {
                "success": True,
                "context": result.stdout,
                "formatted_for_mobile": True
            }
        else:
            return {
                "success": False,
                "error": result.stderr
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import sys

    # Handle Windows console encoding
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

    print("🚀 Starting CCOM Remote Server v0.3")
    print("📱 Access from iOS: http://100.115.44.58:9001")
    print("🔧 Health check: http://localhost:9001")
    uvicorn.run(app, host="0.0.0.0", port=9001)
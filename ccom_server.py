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
from typing import Optional, Set
import sys

app = FastAPI(
    title="CCOM Remote Server",
    description="Execute CCOM commands remotely from iOS/mobile devices",
    version="0.3.0",
)

# Security: Command allowlist
ALLOWED_COMMANDS = {"context", "quality", "security", "deploy", "build", "principles", "validate"}
ALLOWED_WORKFLOW_ACTIONS = {"context", "quality", "security", "deploy", "build", "setup"}

def is_allowed_command(cmd: str) -> bool:
    """Validate command against allowlist"""
    cmd = cmd.strip().lower()

    # Direct commands
    if cmd in ALLOWED_COMMANDS:
        return True

    # Workflow commands
    if cmd.startswith("workflow "):
        action = cmd.split(" ", 1)[1].strip()
        return action in ALLOWED_WORKFLOW_ACTIONS

    # Principles-related commands
    if any(keyword in cmd for keyword in ["principles", "kiss", "dry", "solid", "yagni", "complexity"]):
        return True

    return False

def get_trusted_projects() -> Set[str]:
    """Get set of trusted project paths"""
    try:
        projects_data = list_projects()
        return {p["path"] for p in projects_data["projects"]}
    except Exception:
        return set()

def is_trusted_path(project_path: str) -> bool:
    """Validate project path is trusted"""
    if not project_path:
        return False

    trusted_paths = get_trusted_projects()
    normalized_path = os.path.normpath(os.path.abspath(project_path))

    return normalized_path in trusted_paths


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
            <select id="project-select" style="width: 100%; padding: 8px; background: rgba(255,255,255,0.9); border: none; border-radius: 8px; color: #333; margin-bottom: 10px;">
                <option value="">Loading projects...</option>
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

        <div class="result" id="result" role="region" aria-live="polite" tabindex="-1"></div>
    </div>

    <script>
        let projects = [];
        let currentProjectPath = null;

        // Load projects from server
        async function loadProjects() {
            try {
                const response = await fetch('/projects');
                const data = await response.json();
                projects = data.projects || [];

                const select = document.getElementById('project-select');
                select.innerHTML = projects.map(p =>
                    `<option value="${p.path}">${p.name}</option>`
                ).join('');

                // Restore last selected project or use first
                const lastSelected = localStorage.getItem('ccom.selectedProject');
                if (lastSelected && projects.some(p => p.path === lastSelected)) {
                    select.value = lastSelected;
                    currentProjectPath = lastSelected;
                } else if (projects.length > 0) {
                    currentProjectPath = projects[0].path;
                }

                loadProjectStatus();
            } catch (error) {
                console.error('Failed to load projects:', error);
                document.getElementById('project-select').innerHTML =
                    '<option value="">Error loading projects</option>';
            }
        }

        // Handle project selector change
        document.getElementById('project-select').addEventListener('change', function(e) {
            currentProjectPath = e.target.value;
            localStorage.setItem('ccom.selectedProject', currentProjectPath);
            loadProjectStatus();
        });

        async function loadProjectStatus() {
            if (!currentProjectPath) return;

            try {
                const response = await fetch('/context', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ project_path: currentProjectPath })
                });
                const data = await response.json();

                const projectName = projects.find(p => p.path === currentProjectPath)?.name || 'Unknown';
                document.getElementById('project-name').textContent = projectName.toUpperCase();
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
                        project_path: currentProjectPath
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
                        project_path: currentProjectPath
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
            setBusy(show); // Disable/enable buttons during execution
        }

        function setBusy(busy) {
            document.querySelectorAll('.actions .btn, .quick-chat .btn').forEach(b => b.disabled = busy);
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
            resultDiv.focus(); // Accessibility: bring into screen-reader and keyboard focus
        }

        // Load project status on page load
        loadProjectStatus();

        // Allow Enter key in chat input
        document.getElementById('chatInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendChat();
        });

        // Initialize on page load
        loadProjects();
    </script>
</body>
</html>
    """


@app.get("/api/health")
def health_check():
    """Health check endpoint for API"""
    return {
        "status": "CCOM Remote Server v0.3 - Ready",
        "endpoints": ["/ccom", "/projects", "/context"],
    }


def _validate_command_security(cmd: CCOMCommand):
    """Validate command security requirements"""
    if not is_allowed_command(cmd.command):
        raise HTTPException(
            status_code=400, detail=f"Command not allowed: {cmd.command}"
        )

    project_path = cmd.project_path or "."

    if cmd.project_path and not is_trusted_path(project_path):
        raise HTTPException(
            status_code=400, detail="Unknown or untrusted project path"
        )

    if not os.path.exists(project_path):
        raise HTTPException(
            status_code=400, detail=f"Project path does not exist: {project_path}"
        )

    return project_path


def _execute_ccom_subprocess(project_path: str, command: str):
    """Execute CCOM command in subprocess"""
    import sys

    original_cwd = os.getcwd()
    os.chdir(project_path)

    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "ccom.cli", command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=dict(os.environ, PYTHONIOENCODING="utf-8:replace"),
        )

        stdout, stderr = proc.communicate(timeout=60)

        return subprocess.CompletedProcess(
            args=None, returncode=proc.returncode, stdout=stdout, stderr=stderr
        )
    finally:
        os.chdir(original_cwd)


def _load_project_info(project_path: str):
    """Load project information from memory file"""
    try:
        memory_file = Path(project_path) / ".claude" / "memory.json"
        if memory_file.exists():
            with open(memory_file) as f:
                memory_data = json.load(f)
                return {
                    "name": memory_data.get("project", {}).get("name", "Unknown"),
                    "features": len(memory_data.get("features", {})),
                    "version": memory_data.get("metadata", {}).get("version", "Unknown"),
                }
    except:
        pass
    return None


def _clean_output(result):
    """Clean and combine stdout/stderr output"""
    output_lines = []

    if result.stdout and result.stdout.strip():
        output_lines.append(result.stdout.strip())

    if result.stderr and result.stderr.strip():
        stderr_lines = result.stderr.split("\n")
        clean_stderr = [
            line for line in stderr_lines
            if ("RuntimeWarning" not in line and "frozen runpy" not in line
                and "INFO:" not in line and line.strip())
        ]
        if clean_stderr:
            output_lines.extend(clean_stderr)

    return "\n".join(output_lines).strip()


def _create_fallback_output(project_info):
    """Create fallback output when no command output available"""
    output = f"✅ Project: {project_info['name']}\n"
    output += f"📊 Features: {project_info['features']}\n"
    output += f"🔧 Version: {project_info['version']}\n"
    output += "\nCommand executed successfully. Check .claude/memory.json for details."
    return output


@app.post("/ccom", response_model=CCOMResponse)
def execute_ccom(cmd: CCOMCommand):
    """Execute CCOM command remotely"""
    try:
        # Validate security requirements
        project_path = _validate_command_security(cmd)

        # Execute command in subprocess
        result = _execute_ccom_subprocess(project_path, cmd.command)

        # Load project information
        project_info = _load_project_info(project_path)

        # Clean and combine output
        full_output = _clean_output(result)

        # Create fallback output if needed
        if not full_output and project_info and result.returncode == 0:
            full_output = _create_fallback_output(project_info)

        return CCOMResponse(
            success=result.returncode == 0,
            output=full_output,
            error="" if result.returncode == 0 else "",
            project_info=project_info,
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=408, detail="Command timed out after 60 seconds"
        )
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
        Path.cwd(),
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
                                projects.append(
                                    {
                                        "name": memory_data.get("project", {}).get(
                                            "name", item.name
                                        ),
                                        "path": str(item),
                                        "features": len(
                                            memory_data.get("features", {})
                                        ),
                                        "created": memory_data.get("project", {}).get(
                                            "created", "Unknown"
                                        ),
                                    }
                                )
                    except:
                        projects.append(
                            {
                                "name": item.name,
                                "path": str(item),
                                "features": 0,
                                "created": "Unknown",
                            }
                        )

    return {"projects": projects}


@app.post("/context")
def get_project_context(request: dict):
    """Get project context for iOS display"""
    project_path = request.get("project_path", ".")

    # Security: Validate project path is trusted
    if request.get("project_path") and not is_trusted_path(project_path):
        raise HTTPException(
            status_code=400, detail="Unknown or untrusted project path"
        )

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
            encoding="utf-8",
            errors="replace",
            env=dict(os.environ, PYTHONIOENCODING="utf-8:replace"),
        )

        stdout, stderr = proc.communicate(timeout=30)
        os.chdir(original_cwd)

        result = subprocess.CompletedProcess(
            args=None, returncode=proc.returncode, stdout=stdout, stderr=stderr
        )

        if result.returncode == 0:
            return {
                "success": True,
                "context": result.stdout,
                "formatted_for_mobile": True,
            }
        else:
            return {"success": False, "error": result.stderr}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    import sys

    # Handle Windows console encoding
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    print("🚀 Starting CCOM Remote Server v0.3")
    print("📱 Access from iOS: http://100.115.44.58:9001")
    print("🔧 Health check: http://localhost:9001")
    uvicorn.run(app, host="0.0.0.0", port=9001)

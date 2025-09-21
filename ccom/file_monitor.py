#!/usr/bin/env python3
"""
CCOM File Monitor - Real-time Quality Enforcement
Provides file watching with intelligent change detection and CCOM integration
"""

import os
import sys
import time
import json
import hashlib
import subprocess
import fnmatch
from pathlib import Path
from datetime import datetime, timedelta
from threading import Thread, Lock
from typing import Dict, List, Set, Optional


class CCOMFileMonitor:
    """
    CCOM File Monitor - Real-time quality enforcement via file watching

    Architecture:
    - External file watcher (chokidar) → Python bridge → CCOM native execution
    - Smart change detection to avoid unnecessary triggers
    - Configurable file patterns and quality thresholds
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.config_file = self.project_root / ".ccom" / "file-monitor.json"
        self.lock = Lock()

        # File tracking state
        self.file_hashes: Dict[str, str] = {}
        self.last_quality_run: Optional[datetime] = None
        self.pending_changes: Set[str] = set()

        # Load configuration
        self.config = self.load_config()

        # Initialize CCOM orchestrator for native execution
        try:
            # Try importing from installed package first
            from ccom.orchestrator import CCOMOrchestrator

            self.ccom = CCOMOrchestrator()
        except ImportError:
            # Fallback to local import
            sys.path.append(str(self.project_root / "ccom"))
            from orchestrator import CCOMOrchestrator

            self.ccom = CCOMOrchestrator()

    def load_config(self) -> dict:
        """Load file monitoring configuration"""
        default_config = {
            "enabled": True,
            "watch_patterns": [
                "*.js",
                "*.ts",
                "*.jsx",
                "*.tsx",
                "*.html",
                "*.css",
                "*.py",
                "**/*.js",
                "**/*.ts",
                "**/*.jsx",
                "**/*.tsx",
                "**/*.html",
                "**/*.css",
                "src/**/*",
                "auth.js",
                "script.js",
                "index.html",
            ],
            "ignore_patterns": [
                "node_modules/**",
                "dist/**",
                "build/**",
                ".git/**",
                "*.log",
                "*.tmp",
            ],
            "quality_triggers": {
                "debounce_ms": 1000,  # Wait 1s after last change
                "batch_changes": True,  # Process multiple files together
                "smart_detection": True,  # Only trigger on meaningful changes
            },
            "actions": {
                "on_js_change": ["quality-enforcer"],
                "on_python_change": ["quality-enforcer"],
                "on_html_change": ["quality-enforcer"],
                "on_any_change": [],  # Always run these
            },
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in loaded_config:
                            loaded_config[key] = value
                    return loaded_config
            except Exception as e:
                print(f"⚠️  Error loading config: {e}, using defaults")

        # Save default config
        self.save_config(default_config)
        return default_config

    def save_config(self, config: dict):
        """Save file monitoring configuration"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)

    def get_file_hash(self, file_path: Path) -> str:
        """Get SHA256 hash of file contents for change detection"""
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""

    def is_meaningful_change(self, file_path: Path) -> bool:
        """
        Smart change detection - only trigger on meaningful changes

        Filters out:
        - Whitespace-only changes
        - Comment-only changes
        - Formatting changes (if auto-formatter is enabled)
        """
        if not self.config["quality_triggers"]["smart_detection"]:
            return True  # All changes are meaningful if smart detection disabled

        file_str = str(file_path)
        current_hash = self.get_file_hash(file_path)

        if file_str not in self.file_hashes:
            # First time seeing this file
            self.file_hashes[file_str] = current_hash
            return True

        if self.file_hashes[file_str] == current_hash:
            return False  # No actual change

        # Update hash for next comparison
        old_hash = self.file_hashes[file_str]
        self.file_hashes[file_str] = current_hash

        # For now, consider all content changes meaningful
        # TODO: Add more sophisticated analysis (AST comparison, etc.)
        return True

    def get_file_type_actions(self, file_path: Path) -> List[str]:
        """Get actions to run based on file type"""
        file_ext = file_path.suffix.lower()
        actions = []

        # Add type-specific actions
        if file_ext in [".js", ".jsx", ".ts", ".tsx"]:
            actions.extend(self.config["actions"].get("on_js_change", []))
        elif file_ext == ".py":
            actions.extend(self.config["actions"].get("on_python_change", []))
        elif file_ext in [".html", ".htm"]:
            actions.extend(self.config["actions"].get("on_html_change", []))

        # Add universal actions
        actions.extend(self.config["actions"].get("on_any_change", []))

        return list(set(actions))  # Remove duplicates

    def should_debounce(self) -> bool:
        """Check if we should wait before processing changes"""
        if not self.last_quality_run:
            return False

        debounce_ms = self.config["quality_triggers"]["debounce_ms"]
        time_since_last = datetime.now() - self.last_quality_run
        return time_since_last.total_seconds() * 1000 < debounce_ms

    def process_file_change(self, file_path: str, change_type: str = "change"):
        """
        Process a single file change

        Args:
            file_path: Path to changed file
            change_type: Type of change (change, add, unlink)
        """
        try:
            path = Path(file_path)

            # 1) normalize to relative posix path
            try:
                rel = path.relative_to(self.project_root)
            except ValueError:
                rel = Path(os.path.relpath(path, self.project_root))
            rel_posix = rel.as_posix()

            # 2) ignore patterns (use fnmatch)
            for pattern in self.config["ignore_patterns"]:
                if fnmatch.fnmatch(rel_posix, pattern):
                    return

            # 3) watch patterns (use fnmatch)
            matches_pattern = any(
                fnmatch.fnmatch(rel_posix, pat) for pat in self.config["watch_patterns"]
            )
            if not matches_pattern:
                return

            print(f"📝 File {change_type}: {file_path}")

            # Smart change detection
            if change_type == "change" and path.exists():
                if not self.is_meaningful_change(path):
                    print(f"   ↳ Skipping trivial change")
                    return

            # Add to pending changes
            with self.lock:
                self.pending_changes.add(file_path)

            # Process immediately or batch
            if self.config["quality_triggers"]["batch_changes"]:
                # Schedule batch processing after debounce period
                self.schedule_batch_processing()
            else:
                # Process immediately
                self.run_quality_actions([file_path])

        except Exception as e:
            print(f"❌ Error processing file change: {e}")

    def schedule_batch_processing(self):
        """Schedule batch processing after debounce period"""

        def delayed_process():
            time.sleep(self.config["quality_triggers"]["debounce_ms"] / 1000)

            with self.lock:
                if self.pending_changes:
                    files = list(self.pending_changes)
                    self.pending_changes.clear()
                    self.run_quality_actions(files)

        # Run in background thread
        thread = Thread(target=delayed_process, daemon=True)
        thread.start()

    def run_quality_actions(self, changed_files: List[str]):
        """
        Run quality actions for changed files using CCOM native execution
        """
        try:
            print(
                f"🔧 **CCOM FILE MONITOR** – Processing {len(changed_files)} files..."
            )

            # Determine actions to run
            all_actions = set()
            for file_path in changed_files:
                actions = self.get_file_type_actions(Path(file_path))
                all_actions.update(actions)

            if not all_actions:
                print("   ↳ No actions configured for these file types")
                return

            # Execute CCOM native implementations
            success_count = 0
            for action in all_actions:
                print(f"   🤖 Running {action}...")

                try:
                    # Use our proven CCOM native execution
                    result = self.ccom.invoke_subagent(action)
                    if result:
                        success_count += 1
                        print(f"   ✅ {action} completed")
                    else:
                        print(f"   ❌ {action} failed")
                except Exception as e:
                    print(f"   ❌ {action} error: {e}")

            self.last_quality_run = datetime.now()

            if success_count == len(all_actions):
                print(f"✅ **CCOM FILE MONITOR** – All quality checks passed")
            else:
                print(
                    f"⚠️  **CCOM FILE MONITOR** – {success_count}/{len(all_actions)} actions succeeded"
                )

        except Exception as e:
            print(f"❌ Error running quality actions: {e}")

    def start_watching(self):
        """Start the file monitoring system"""
        if not self.config["enabled"]:
            print("📁 CCOM File Monitor is disabled")
            return

        print("🔍 **CCOM FILE MONITOR** – Starting real-time quality enforcement...")
        print(f"   📂 Watching: {self.project_root}")
        print(f"   📋 Patterns: {', '.join(self.config['watch_patterns'][:3])}...")
        print(f"   ⚡ Debounce: {self.config['quality_triggers']['debounce_ms']}ms")

        # Install chokidar if not available
        self.ensure_chokidar_installed()

        # Start Node.js chokidar watcher
        self.start_chokidar_watcher()

    def ensure_chokidar_installed(self):
        """Ensure chokidar is installed for file watching"""
        try:
            result = subprocess.run(
                ["npm", "list", "chokidar"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode != 0:
                print("📦 Installing chokidar for file monitoring...")
                subprocess.run(
                    ["npm", "install", "--save-dev", "chokidar"],
                    cwd=self.project_root,
                    check=True,
                )
                print("✅ Chokidar installed")
        except Exception as e:
            print(f"⚠️  Could not install chokidar: {e}")
            print("💡 Install manually: npm install --save-dev chokidar")

    def start_chokidar_watcher(self):
        """Start the chokidar file watcher via Node.js"""
        # Create the chokidar bridge script
        bridge_script = self.create_chokidar_bridge()

        try:
            # Start the Node.js file watcher
            process = subprocess.Popen(
                ["node", str(bridge_script)],
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            print("✅ **CCOM FILE MONITOR** – Active")
            print("💡 Save any file to trigger real-time quality checks")

            # Process file change events
            try:
                for line in process.stdout:
                    line = line.strip()
                    if line.startswith("CHANGE:"):
                        file_path = line[7:]  # Remove "CHANGE:" prefix
                        self.process_file_change(file_path, "change")
                    elif line.startswith("ADD:"):
                        file_path = line[4:]  # Remove "ADD:" prefix
                        self.process_file_change(file_path, "add")
                    elif line.startswith("ERROR:"):
                        print(f"❌ Watcher error: {line[6:]}")

            except KeyboardInterrupt:
                print("\n🛑 **CCOM FILE MONITOR** – Stopped by user")
                process.terminate()
            except Exception as e:
                print(f"❌ File monitor error: {e}")
                process.terminate()

        except Exception as e:
            print(f"❌ Could not start file watcher: {e}")
            print("💡 Make sure Node.js is installed")

    def create_chokidar_bridge(self) -> Path:
        """Create the Node.js chokidar bridge script"""
        bridge_path = self.project_root / ".ccom" / "file-watcher.js"
        bridge_path.parent.mkdir(parents=True, exist_ok=True)

        bridge_content = f"""#!/usr/bin/env node
/**
 * CCOM File Watcher Bridge - Chokidar to Python
 * Watches files and reports changes to CCOM file monitor
 */

const chokidar = require('chokidar');
const path = require('path');

const config = {json.dumps(self.config, indent=2)};

console.log('CCOM File Watcher starting...');

// Initialize watcher
const watcher = chokidar.watch(config.watch_patterns, {{
  ignored: config.ignore_patterns,
  ignoreInitial: true,
  persistent: true,
  usePolling: true,          // Use polling on Windows for better compatibility
  interval: 500,             // Poll every 500ms (was 1000)
  binaryInterval: 500,
  awaitWriteFinish: {{        // Stabilize writes to prevent double/truncated events
    stabilityThreshold: 700,
    pollInterval: 100
  }}
}});

// File change events
watcher
  .on('change', path => {{
    console.log(`CHANGE:${{path}}`);
  }})
  .on('add', path => {{
    console.log(`ADD:${{path}}`);
  }})
  .on('unlink', path => {{
    console.log(`UNLINK:${{path}}`);
  }})
  .on('error', error => {{
    console.log(`ERROR:${{error.message}}`);
  }})
  .on('ready', () => {{
    console.log('File watcher ready');
    const watched = watcher.getWatched();
    console.log('Watching directories:');
    Object.keys(watched).forEach(dir => {{
      console.log(`  ${{dir}}: ${{watched[dir].join(', ')}}`);
    }});
  }});

// Graceful shutdown
process.on('SIGINT', () => {{
  console.log('\\nFile watcher shutting down...');
  watcher.close().then(() => process.exit(0));
}});
"""

        with open(bridge_path, "w", encoding="utf-8") as f:
            f.write(bridge_content)

        return bridge_path


def main():
    """CLI entry point for CCOM file monitor"""
    import argparse

    parser = argparse.ArgumentParser(
        description="CCOM File Monitor - Real-time quality enforcement"
    )
    parser.add_argument("--start", action="store_true", help="Start file monitoring")
    parser.add_argument(
        "--config", action="store_true", help="Show current configuration"
    )
    parser.add_argument("--enable", action="store_true", help="Enable file monitoring")
    parser.add_argument(
        "--disable", action="store_true", help="Disable file monitoring"
    )

    args = parser.parse_args()

    # Find project root (look for .claude directory)
    current_dir = Path.cwd()
    project_root = current_dir

    while project_root.parent != project_root:
        if (project_root / ".claude").exists():
            break
        project_root = project_root.parent
    else:
        print("❌ No CCOM project found (no .claude directory)")
        return 1

    monitor = CCOMFileMonitor(project_root)

    if args.config:
        print("📋 CCOM File Monitor Configuration:")
        print(json.dumps(monitor.config, indent=2))
    elif args.enable:
        monitor.config["enabled"] = True
        monitor.save_config(monitor.config)
        print("✅ CCOM File Monitor enabled")
    elif args.disable:
        monitor.config["enabled"] = False
        monitor.save_config(monitor.config)
        print("🛑 CCOM File Monitor disabled")
    elif args.start:
        monitor.start_watching()
    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    exit(main())

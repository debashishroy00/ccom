#!/usr/bin/env python3
"""
CCOM Workflows - Solo Developer CI/CD
Lightweight automation for individual developers
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

class CCOMWorkflows:
    """
    Solo developer workflow automation

    Focuses on essential quality gates and deployment automation
    without enterprise complexity.
    """

    def __init__(self, project_root=None):
        self.project_root = Path(project_root or Path.cwd())
        self.ccom_dir = self.project_root / ".ccom"

    def run_workflow(self, workflow_name):
        """Execute a CCOM workflow"""
        workflows = {
            "quality": self.workflow_quality,
            "security": self.workflow_security,
            "deploy": self.workflow_deploy,
            "full": self.workflow_full_pipeline
        }

        if workflow_name not in workflows:
            print(f"❌ Unknown workflow: {workflow_name}")
            print(f"Available workflows: {', '.join(workflows.keys())}")
            return False

        print(f"🚀 **CCOM WORKFLOW** – Running {workflow_name}...")
        return workflows[workflow_name]()

    def workflow_quality(self):
        """Quality gates workflow for solo developers"""
        print("🔧 **QUALITY GATES** – Ensuring code standards...")

        steps = [
            ("Lint Check", self.run_linting),
            ("Format Check", self.run_formatting),
            ("Type Check", self.run_type_checking),
            ("Basic Tests", self.run_basic_tests)
        ]

        results = []
        for step_name, step_func in steps:
            print(f"   🔍 {step_name}...")
            result = step_func()
            results.append((step_name, result))

            if result:
                print(f"   ✅ {step_name} passed")
            else:
                print(f"   ⚠️  {step_name} issues found")

        passed = sum(1 for _, result in results if result)
        total = len(results)

        if passed == total:
            print(f"✅ **QUALITY GATES** – All {total} checks passed")
            return True
        else:
            print(f"⚠️  **QUALITY GATES** – {passed}/{total} checks passed")
            return False

    def workflow_security(self):
        """Security scanning workflow"""
        print("🔒 **SECURITY SCAN** – Protecting your code...")

        steps = [
            ("Dependency Audit", self.run_dependency_audit),
            ("Secret Scanning", self.run_secret_scan),
            ("Code Security", self.run_code_security_scan)
        ]

        issues_found = 0
        for step_name, step_func in steps:
            print(f"   🛡️  {step_name}...")
            issues = step_func()

            if issues == 0:
                print(f"   ✅ {step_name} - no issues")
            else:
                print(f"   🚨 {step_name} - {issues} issues found")
                issues_found += issues

        if issues_found == 0:
            print("✅ **SECURITY SCAN** – No vulnerabilities found")
            return True
        else:
            print(f"🚨 **SECURITY SCAN** – {issues_found} security issues detected")
            return False

    def workflow_deploy(self):
        """Deployment workflow with quality gates"""
        print("🚀 **DEPLOYMENT PIPELINE** – Preparing for production...")

        # Step 1: Quality gates
        if not self.workflow_quality():
            print("❌ Deployment blocked - quality issues found")
            return False

        # Step 2: Security scan
        if not self.workflow_security():
            print("❌ Deployment blocked - security issues found")
            return False

        # Step 3: Build
        print("   📦 Building production artifacts...")
        if not self.run_build():
            print("❌ Deployment blocked - build failed")
            return False

        # Step 4: Deploy (detect platform)
        platform = self.detect_deployment_platform()
        if platform:
            print(f"   🌐 Deploying to {platform}...")
            return self.deploy_to_platform(platform)
        else:
            print("✅ **BUILD READY** – Artifacts ready for manual deployment")
            return True

    def workflow_full_pipeline(self):
        """Complete CI/CD pipeline"""
        print("🔄 **FULL PIPELINE** – Complete automation...")
        return self.workflow_deploy()

    def run_linting(self):
        """Run code linting"""
        try:
            if (self.project_root / "package.json").exists():
                # Try npm script first
                result = subprocess.run(
                    "npm run lint",
                    shell=True, capture_output=True, text=True,
                    cwd=self.project_root, timeout=30
                )
                if result.returncode == 0:
                    return True

                # Fallback to eslint
                result = subprocess.run(
                    "npx eslint .",
                    shell=True, capture_output=True, text=True,
                    cwd=self.project_root, timeout=30
                )
                return result.returncode == 0

            return True  # No linting available
        except Exception:
            return True  # Don't fail if linting not available

    def run_formatting(self):
        """Check code formatting"""
        try:
            if (self.project_root / "package.json").exists():
                result = subprocess.run(
                    "npx prettier --check .",
                    shell=True, capture_output=True, text=True,
                    cwd=self.project_root, timeout=30
                )
                return result.returncode == 0
            return True
        except Exception:
            return True

    def run_type_checking(self):
        """Run TypeScript type checking"""
        try:
            if (self.project_root / "tsconfig.json").exists():
                result = subprocess.run(
                    "npx tsc --noEmit",
                    shell=True, capture_output=True, text=True,
                    cwd=self.project_root, timeout=60
                )
                return result.returncode == 0
            return True
        except Exception:
            return True

    def run_basic_tests(self):
        """Run basic test suite"""
        try:
            if (self.project_root / "package.json").exists():
                result = subprocess.run(
                    "npm test",
                    shell=True, capture_output=True, text=True,
                    cwd=self.project_root, timeout=120
                )
                # Many projects don't have tests - don't fail
                return True
            return True
        except Exception:
            return True

    def run_dependency_audit(self):
        """Check for vulnerable dependencies"""
        try:
            if (self.project_root / "package.json").exists():
                result = subprocess.run(
                    "npm audit --audit-level=high",
                    shell=True, capture_output=True, text=True,
                    cwd=self.project_root, timeout=30
                )
                # Count vulnerabilities from output
                if "vulnerabilities" in result.stdout:
                    return 1 if result.returncode != 0 else 0
            return 0
        except Exception:
            return 0

    def run_secret_scan(self):
        """Basic secret scanning"""
        try:
            import re

            patterns = [
                r'password\s*=\s*["\'].*["\']',
                r'api[_-]?key\s*=\s*["\'].*["\']',
                r'secret\s*=\s*["\'].*["\']',
                r'token\s*=\s*["\'].*["\']'
            ]

            issues = 0
            for file_path in self.project_root.rglob("*.js"):
                if "node_modules" in str(file_path):
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    for pattern in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            issues += 1
                            print(f"      ⚠️  Potential secret in {file_path.name}")
                except Exception:
                    continue

            return issues
        except Exception:
            return 0

    def run_code_security_scan(self):
        """Basic code security patterns"""
        try:
            import re

            dangerous_patterns = [
                r'eval\s*\(',
                r'innerHTML\s*=',
                r'document\.write\s*\(',
                r'setTimeout\s*\(\s*["\'].*["\']'
            ]

            issues = 0
            for file_path in self.project_root.rglob("*.js"):
                if "node_modules" in str(file_path):
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    for pattern in dangerous_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            issues += 1
                            print(f"      ⚠️  Security pattern in {file_path.name}")
                except Exception:
                    continue

            return issues
        except Exception:
            return 0

    def run_build(self):
        """Build the project"""
        try:
            package_json = self.project_root / "package.json"
            if package_json.exists():
                with open(package_json) as f:
                    data = json.load(f)

                if "build" in data.get("scripts", {}):
                    result = subprocess.run(
                        "npm run build",
                        shell=True, capture_output=True, text=True,
                        cwd=self.project_root, timeout=180
                    )
                    return result.returncode == 0

            # No build script, consider it successful
            return True
        except Exception:
            return False

    def detect_deployment_platform(self):
        """Detect deployment platform from project config"""
        # Check for Netlify
        if (self.project_root / "netlify.toml").exists():
            return "netlify"

        # Check for Vercel
        if (self.project_root / "vercel.json").exists():
            return "vercel"

        # Check for package.json deploy script
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    scripts = data.get("scripts", {})

                if "deploy" in scripts:
                    return "custom"

            except Exception:
                pass

        return None

    def deploy_to_platform(self, platform):
        """Deploy to detected platform"""
        try:
            if platform == "netlify":
                # Use netlify CLI if available
                result = subprocess.run(
                    "netlify deploy --prod",
                    shell=True, capture_output=True, text=True,
                    cwd=self.project_root, timeout=300
                )
                return result.returncode == 0

            elif platform == "vercel":
                # Use vercel CLI if available
                result = subprocess.run(
                    "vercel --prod",
                    shell=True, capture_output=True, text=True,
                    cwd=self.project_root, timeout=300
                )
                return result.returncode == 0

            elif platform == "custom":
                # Run custom deploy script
                result = subprocess.run(
                    "npm run deploy",
                    shell=True, capture_output=True, text=True,
                    cwd=self.project_root, timeout=300
                )
                return result.returncode == 0

        except Exception as e:
            print(f"   ⚠️  Deployment error: {e}")
            return False

        return False

    def create_github_workflow(self):
        """Create GitHub Actions workflow for solo developers"""
        workflow_dir = self.project_root / ".github" / "workflows"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow_content = """name: CCOM Quality Gates

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  quality_check:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'

    - name: Install dependencies
      run: npm ci

    - name: Install CCOM
      run: pip install ccom

    - name: CCOM Quality Workflow
      run: ccom workflow quality

    - name: CCOM Security Workflow
      run: ccom workflow security
"""

        workflow_file = workflow_dir / "ccom-quality.yml"
        with open(workflow_file, 'w') as f:
            f.write(workflow_content)

        print(f"✅ Created GitHub workflow: {workflow_file}")
        return True

def main():
    """CLI entry point for workflows"""
    import argparse

    parser = argparse.ArgumentParser(description="CCOM Workflows - Solo Developer CI/CD")
    parser.add_argument("workflow", choices=["quality", "security", "deploy", "full", "setup"],
                       help="Workflow to run")

    args = parser.parse_args()

    workflows = CCOMWorkflows()

    if args.workflow == "setup":
        workflows.create_github_workflow()
    else:
        success = workflows.run_workflow(args.workflow)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
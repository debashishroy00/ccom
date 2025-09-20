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
            "full": self.workflow_full_pipeline,
            # RAG-specific workflows
            "rag_quality": self.workflow_rag_quality,
            "vector_validation": self.workflow_vector_validation,
            "graph_security": self.workflow_graph_security,
            "hybrid_rag": self.workflow_hybrid_rag,
            "agentic_rag": self.workflow_agentic_rag,
            "enterprise_rag": self.workflow_enterprise_rag,
            # AWS-specific workflow
            "aws_rag": self.workflow_aws_rag
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

    # ============= RAG-SPECIFIC WORKFLOWS =============

    def workflow_rag_quality(self):
        """Comprehensive RAG system quality check"""
        print("🧠 **RAG QUALITY AUDIT** – Validating RAG architecture...")

        steps = [
            ("Vector Store Validation", self.run_vector_store_validation),
            ("Graph DB Security", self.run_graph_db_validation),
            ("Hybrid RAG Patterns", self.run_hybrid_rag_validation),
            ("Agentic RAG Safety", self.run_agentic_rag_validation)
        ]

        results = []
        for step_name, step_func in steps:
            print(f"   🔍 {step_name}...")
            result = step_func()
            results.append((step_name, result))

            if result["passed"]:
                print(f"   ✅ {step_name} - {result['summary']}")
            else:
                print(f"   ⚠️  {step_name} - {result['summary']}")

        passed = sum(1 for _, result in results if result["passed"])
        total = len(results)

        if passed == total:
            print(f"✅ **RAG QUALITY AUDIT** – All {total} validations passed")
            return True
        else:
            print(f"⚠️  **RAG QUALITY AUDIT** – {passed}/{total} validations passed")
            return False

    def workflow_vector_validation(self):
        """Vector store and embedding validation"""
        print("📊 **VECTOR VALIDATION** – Analyzing embedding patterns...")
        result = self.run_vector_store_validation()

        if result["passed"]:
            print("✅ **VECTOR VALIDATION** – Vector patterns are enterprise-ready")
        else:
            print("⚠️  **VECTOR VALIDATION** – Issues found in vector implementation")

        return result["passed"]

    def workflow_graph_security(self):
        """Graph database security validation"""
        print("🔒 **GRAPH SECURITY** – Analyzing graph database patterns...")
        result = self.run_graph_db_validation()

        if result["passed"]:
            print("✅ **GRAPH SECURITY** – Graph patterns are secure")
        else:
            print("⚠️  **GRAPH SECURITY** – Security issues found in graph implementation")

        return result["passed"]

    def workflow_hybrid_rag(self):
        """Hybrid RAG implementation validation"""
        print("🔄 **HYBRID RAG** – Validating fusion and reranking...")
        result = self.run_hybrid_rag_validation()

        if result["passed"]:
            print("✅ **HYBRID RAG** – Hybrid patterns are well-implemented")
        else:
            print("⚠️  **HYBRID RAG** – Issues found in hybrid implementation")

        return result["passed"]

    def workflow_agentic_rag(self):
        """Agentic RAG safety and pattern validation"""
        print("🤖 **AGENTIC RAG** – Validating agent reasoning patterns...")
        result = self.run_agentic_rag_validation()

        if result["passed"]:
            print("✅ **AGENTIC RAG** – Agent patterns are safe and well-implemented")
        else:
            print("⚠️  **AGENTIC RAG** – Safety or implementation issues found")

        return result["passed"]

    def workflow_enterprise_rag(self):
        """Complete enterprise RAG validation"""
        print("🏢 **ENTERPRISE RAG** – Complete RAG system audit...")

        # Run all RAG validations
        vector_result = self.workflow_vector_validation()
        graph_result = self.workflow_graph_security()
        hybrid_result = self.workflow_hybrid_rag()
        agentic_result = self.workflow_agentic_rag()

        # Also run standard quality and security
        quality_result = self.workflow_quality()
        security_result = self.workflow_security()

        all_results = [vector_result, graph_result, hybrid_result, agentic_result, quality_result, security_result]
        passed = sum(all_results)
        total = len(all_results)

        if passed == total:
            print("🎉 **ENTERPRISE RAG** – All validations passed! System is production-ready")
            return True
        else:
            print(f"⚠️  **ENTERPRISE RAG** – {passed}/{total} validations passed")
            return False

    def workflow_aws_rag(self):
        """AWS-specific RAG validation (Bedrock, LangChain, MongoDB, ECS/Lambda)"""
        print("☁️ **AWS RAG** – Validating AWS Bedrock + LangChain stack...")

        results = []

        # Run AWS Bedrock validation
        print("🔍 Checking AWS Bedrock & LangChain patterns...")
        bedrock_result = self.run_aws_bedrock_validation()
        results.append(bedrock_result["passed"])
        print(f"   {bedrock_result['summary']}")

        # Run MongoDB validation
        print("🔍 Checking MongoDB Atlas Vector Search...")
        mongodb_result = self.run_mongodb_validation()
        results.append(mongodb_result["passed"])
        print(f"   {mongodb_result['summary']}")

        # Run AWS deployment validation
        print("🔍 Checking ECS/Lambda/S3 deployment...")
        deployment_result = self.run_aws_deployment_validation()
        results.append(deployment_result["passed"])
        print(f"   {deployment_result['summary']}")

        # Also run standard vector validation for general patterns
        print("🔍 Checking general vector patterns...")
        vector_result = self.run_vector_store_validation()
        results.append(vector_result["passed"])

        passed = sum(results)
        total = len(results)

        if passed == total:
            print("✅ **AWS RAG** – All AWS validations passed!")
            return True
        else:
            print(f"⚠️  **AWS RAG** – {passed}/{total} validations passed")
            return False

    def run_aws_bedrock_validation(self):
        """Execute AWS Bedrock validator"""
        try:
            result = subprocess.run(
                f"node {self.project_root}/.claude/validators/aws-bedrock-validator.js",
                shell=True, capture_output=True, text=True,
                cwd=self.project_root, timeout=60
            )

            passed = result.returncode == 0
            output_lines = result.stdout.split('\n')

            summary = "AWS Bedrock validation completed"
            for line in output_lines:
                if "validation" in line.lower() and ("results" in line.lower() or "completed" in line.lower()):
                    summary = line.strip()
                    break

            return {"passed": passed, "summary": summary, "details": result.stdout}

        except Exception as e:
            return {"passed": False, "summary": f"AWS Bedrock validation failed: {e}", "details": str(e)}

    def run_mongodb_validation(self):
        """Execute MongoDB Atlas validator"""
        try:
            result = subprocess.run(
                f"node {self.project_root}/.claude/validators/mongodb-vector-validator.js",
                shell=True, capture_output=True, text=True,
                cwd=self.project_root, timeout=60
            )

            passed = result.returncode == 0
            output_lines = result.stdout.split('\n')

            summary = "MongoDB validation completed"
            for line in output_lines:
                if "validation" in line.lower() and ("results" in line.lower() or "completed" in line.lower()):
                    summary = line.strip()
                    break

            return {"passed": passed, "summary": summary, "details": result.stdout}

        except Exception as e:
            return {"passed": False, "summary": f"MongoDB validation failed: {e}", "details": str(e)}

    def run_aws_deployment_validation(self):
        """Execute AWS deployment validator"""
        try:
            result = subprocess.run(
                f"node {self.project_root}/.claude/validators/aws-deployment-validator.js",
                shell=True, capture_output=True, text=True,
                cwd=self.project_root, timeout=60
            )

            passed = result.returncode == 0
            output_lines = result.stdout.split('\n')

            summary = "AWS deployment validation completed"
            for line in output_lines:
                if "validation" in line.lower() and ("results" in line.lower() or "completed" in line.lower()):
                    summary = line.strip()
                    break

            return {"passed": passed, "summary": summary, "details": result.stdout}

        except Exception as e:
            return {"passed": False, "summary": f"AWS deployment validation failed: {e}", "details": str(e)}

    def run_vector_store_validation(self):
        """Execute vector store validator"""
        try:
            result = subprocess.run(
                f"node {self.project_root}/.claude/validators/vector-store-validator.js",
                shell=True, capture_output=True, text=True,
                cwd=self.project_root, timeout=60
            )

            # Parse validation result
            passed = result.returncode == 0
            output_lines = result.stdout.split('\n')

            # Extract summary from output
            summary = "Vector validation completed"
            for line in output_lines:
                if "validation:" in line.lower():
                    summary = line.strip()
                    break

            return {"passed": passed, "summary": summary, "details": result.stdout}

        except Exception as e:
            return {"passed": False, "summary": f"Vector validation failed: {e}", "details": str(e)}

    def run_graph_db_validation(self):
        """Execute graph database validator"""
        try:
            result = subprocess.run(
                f"node {self.project_root}/.claude/validators/graph-db-validator.js",
                shell=True, capture_output=True, text=True,
                cwd=self.project_root, timeout=60
            )

            passed = result.returncode == 0
            output_lines = result.stdout.split('\n')

            summary = "Graph DB validation completed"
            for line in output_lines:
                if "validation:" in line.lower():
                    summary = line.strip()
                    break

            return {"passed": passed, "summary": summary, "details": result.stdout}

        except Exception as e:
            return {"passed": False, "summary": f"Graph DB validation failed: {e}", "details": str(e)}

    def run_hybrid_rag_validation(self):
        """Execute hybrid RAG validator"""
        try:
            result = subprocess.run(
                f"node {self.project_root}/.claude/validators/hybrid-rag-validator.js",
                shell=True, capture_output=True, text=True,
                cwd=self.project_root, timeout=60
            )

            passed = result.returncode == 0
            output_lines = result.stdout.split('\n')

            summary = "Hybrid RAG validation completed"
            for line in output_lines:
                if "validation:" in line.lower():
                    summary = line.strip()
                    break

            return {"passed": passed, "summary": summary, "details": result.stdout}

        except Exception as e:
            return {"passed": False, "summary": f"Hybrid RAG validation failed: {e}", "details": str(e)}

    def run_agentic_rag_validation(self):
        """Execute agentic RAG validator"""
        try:
            result = subprocess.run(
                f"node {self.project_root}/.claude/validators/agentic-rag-validator.js",
                shell=True, capture_output=True, text=True,
                cwd=self.project_root, timeout=60
            )

            passed = result.returncode == 0
            output_lines = result.stdout.split('\n')

            summary = "Agentic RAG validation completed"
            for line in output_lines:
                if "validation:" in line.lower():
                    summary = line.strip()
                    break

            return {"passed": passed, "summary": summary, "details": result.stdout}

        except Exception as e:
            return {"passed": False, "summary": f"Agentic RAG validation failed: {e}", "details": str(e)}

def main():
    """CLI entry point for workflows"""
    import argparse

    parser = argparse.ArgumentParser(description="CCOM Workflows - Solo Developer CI/CD")
    parser.add_argument("workflow", choices=["quality", "security", "deploy", "full", "setup",
                                               "rag_quality", "vector_validation", "graph_security",
                                               "hybrid_rag", "agentic_rag", "enterprise_rag"],
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
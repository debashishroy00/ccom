# CCOM v0.3 - Claude Code Orchestrator and Memory

🚀 **Complete development automation platform for solo developers**

CCOM transforms Claude Code into a powerful development assistant with real-time file monitoring, automated CI/CD workflows, and enterprise-grade quality gates - all through natural language commands.

## ✨ Key Features

### 🎯 **Smart Activation**
- Only commands starting with `"ccom"` activate automation
- Regular Claude Code behavior for all other interactions
- Clear visual distinction between CCOM and standard responses

### 🔄 **Real-Time File Monitoring**
```bash
ccom "watch files"          # Real-time quality enforcement
ccom "monitor config"       # Show monitoring settings
```
- **Smart change detection** - only triggers on meaningful changes
- **Automatic quality checks** when you save files
- **Cross-platform** file watching (Windows, macOS, Linux)

### 🤖 **Automated CI/CD Workflows**
```bash
ccom "workflow quality"     # Lint, format, type check, tests
ccom "workflow security"    # Security scan, secrets, vulnerabilities
ccom "workflow deploy"      # Full pipeline with quality gates
ccom "workflow setup"       # Create GitHub Actions
```

### 🛡️ **Enterprise Security**
- **Dependency auditing** with npm audit
- **Secret detection** for API keys, passwords
- **Code security scanning** for dangerous patterns
- **GitHub Actions integration** for automated checks

## 🚀 Quick Start

### Installation
```bash
# Install from PyPI (coming soon)
pip install ccom

# Or clone for development
git clone https://github.com/debashishroy00/ccom.git
cd ccom
pip install -e .
```

### Initialize Your Project
```bash
# Setup CCOM in any project
ccom --init

# Natural language commands
ccom "workflow quality"     # Check code quality
ccom "workflow setup"       # Create GitHub Actions
ccom "watch files"          # Start real-time monitoring
```

## 📋 Complete Command Reference

### 🔧 **Quality & Testing**
```bash
ccom "workflow quality"     # Complete quality audit
ccom "quality audit"        # Alternative syntax
ccom "fix all issues"       # Quality enforcement
```

### 🔒 **Security**
```bash
ccom "workflow security"    # Security scan
ccom "check vulnerabilities"# Dependency audit
ccom "scan for secrets"     # Secret detection
```

### 🚀 **Deployment**
```bash
ccom "workflow deploy"      # Full deployment pipeline
ccom "deploy to production" # Alternative syntax
ccom "ship it"              # Quick deploy
```

### 📁 **File Monitoring**
```bash
ccom "watch files"          # Start real-time monitoring
ccom "monitor config"       # Show configuration
ccom "stop watching"        # Stop monitoring
```

### 🧠 **Memory & Status**
```bash
ccom "remember auth system" # Save feature to memory
ccom "show project status"  # Display project info
ccom "what have we built"   # List remembered features
```

### ⚙️ **Automation Setup**
```bash
ccom "workflow setup"       # Create GitHub Actions
ccom --init                 # Initialize project
ccom --status               # Show CCOM status
```

## 🏗️ Architecture

### **Real-Time File Monitoring**
- **Chokidar integration** for cross-platform file watching
- **Smart change detection** using SHA256 hashing
- **Debounced processing** to prevent spam during bulk edits
- **Pattern-based filtering** for relevant files only

### **Multi-Agent Workflow System**
- **Quality Enforcer**: ESLint, Prettier, TypeScript checks
- **Security Guardian**: Vulnerability scanning, secret detection
- **Builder Agent**: Production build optimization
- **Deployment Specialist**: Safe deployment coordination

### **Claude Code Integration**
- **Prefix-based activation** - only "ccom" commands trigger automation
- **Visual engagement indicators** for clear feedback
- **TodoWrite integration** for systematic workflow tracking
- **Memory persistence** across sessions

## 🔄 Solo Developer Workflow

```bash
# 1. Setup project
ccom --init
✅ CCOM v0.3 initialized successfully!

# 2. Create GitHub Actions for automated checks
ccom "workflow setup"
✅ Created GitHub workflow: .github/workflows/ccom-quality.yml

# 3. Start real-time monitoring
ccom "watch files"
🔍 CCOM FILE MONITOR – Starting real-time quality enforcement...

# 4. Work on your code... when you save, CCOM automatically runs quality checks

# 5. Before committing, run full quality check
ccom "workflow quality"
🔧 QUALITY GATES – Ensuring code standards...
✅ All 4 checks passed

# 6. Security scan before deployment
ccom "workflow security"
🔒 SECURITY SCAN – Protecting your code...
✅ No vulnerabilities found

# 7. Deploy with confidence
ccom "workflow deploy"
🚀 DEPLOYMENT PIPELINE – Quality gates passed, deploying...
🎉 Your app is live!

# 8. Remember what you built
ccom "remember user authentication system"
✅ Saved to memory: user_authentication_system
```

## 🛡️ GitHub Actions Integration

CCOM automatically creates `.github/workflows/ccom-quality.yml`:

```yaml
name: CCOM Quality Gates

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
    - name: Install dependencies
      run: npm ci
    - name: Install CCOM
      run: pip install ccom
    - name: CCOM Quality Workflow
      run: ccom workflow quality
    - name: CCOM Security Workflow
      run: ccom workflow security
```

**Result**: Every push/PR automatically runs quality and security checks!

## 📊 What Each Workflow Does

### **Quality Workflow**
- ✅ **Lint Check**: ESLint for code standards
- ✅ **Format Check**: Prettier for consistent formatting
- ✅ **Type Check**: TypeScript type validation
- ✅ **Basic Tests**: npm test execution

### **Security Workflow**
- 🛡️ **Dependency Audit**: npm audit for vulnerable packages
- 🛡️ **Secret Scanning**: Detect hardcoded API keys/passwords
- 🛡️ **Code Security**: Scan for dangerous patterns (eval, innerHTML)

### **Deploy Workflow**
- 🚀 **Quality Gates**: Must pass quality checks
- 🚀 **Security Gates**: Must pass security scan
- 🚀 **Build Process**: Production artifact generation
- 🚀 **Platform Detection**: Auto-detect Netlify/Vercel/custom

## 🔧 Configuration

### **File Monitoring**
CCOM creates `.ccom/file-monitor.json`:
```json
{
  "enabled": true,
  "watch_patterns": ["*.js", "*.ts", "*.html", "*.css"],
  "ignore_patterns": ["node_modules/**", "dist/**"],
  "quality_triggers": {
    "debounce_ms": 1000,
    "batch_changes": true,
    "smart_detection": true
  }
}
```

### **Project Memory**
CCOM maintains `.claude/memory.json`:
```json
{
  "project": {"name": "my-app", "created": "2025-01-15"},
  "features": {
    "auth_system": {
      "created": "2025-01-15T10:30:00Z",
      "description": "User authentication with JWT tokens"
    }
  }
}
```

## 🎯 Use Cases

### **Solo Developers**
- **Automated Quality**: Never forget to run lint/format/tests
- **Security Safety Net**: Catch vulnerabilities before deployment
- **One-Command Deploy**: `ccom "workflow deploy"` handles everything
- **Real-Time Feedback**: File monitoring catches issues as you code

### **Small Teams**
- **Consistent Standards**: GitHub Actions enforce quality on every PR
- **Shared Memory**: Track what features have been built
- **Deployment Safety**: Multiple validation layers before production

### **Learning Developers**
- **Best Practices**: CCOM teaches enterprise-grade development habits
- **Natural Language**: No need to memorize complex CLI commands
- **Instant Feedback**: Learn from quality issues as they're detected

## 🛠️ Development

### **Requirements**
- Python 3.8+
- Node.js 16+ (for file monitoring and quality tools)
- Git (for memory persistence and GitHub integration)

### **Project Structure**
```
ccom/
├── ccom/
│   ├── cli.py              # Enhanced CLI with workflow support
│   ├── orchestrator.py     # Multi-agent coordination
│   ├── workflows.py        # CI/CD workflow automation
│   └── file_monitor.py     # Real-time file watching
├── .claude/
│   └── agents/             # Behavior specifications
│       ├── quality-enforcer.md
│       ├── security-guardian.md
│       ├── builder-agent.md
│       └── deployment-specialist.md
├── CLAUDE.md               # Claude Code integration config
└── README.md
```

### **Contributing**
1. Fork the repository
2. Create a feature branch
3. Run `ccom "workflow quality"` before committing
4. Ensure GitHub Actions pass
5. Submit a pull request

## 🔍 Troubleshooting

### **File Monitoring Not Working?**
- **Windows + OneDrive**: Files in OneDrive sync may not trigger events immediately
- **Solution**: Test in `C:\temp` or similar non-synced location
- **Alternative**: File monitoring works best with direct editor saves (VS Code, etc.)

### **GitHub Actions Failing?**
```bash
# Check if CCOM is properly installed
pip show ccom

# Test workflows locally first
ccom "workflow quality"
ccom "workflow security"
```

### **Quality Checks Failing?**
```bash
# See specific issues
ccom "workflow quality"

# Common fixes
npm run lint --fix    # Auto-fix linting issues
npm run format        # Fix formatting
```

## 📈 Roadmap

### **v0.4 (Next Release)**
- [ ] PyPI package distribution
- [ ] VS Code extension integration
- [ ] More deployment platforms (Docker, AWS)
- [ ] Enhanced error reporting

### **v0.5 (Future)**
- [ ] Web dashboard for project overview
- [ ] Team collaboration features
- [ ] Custom workflow templates
- [ ] Multi-language support (Python, Go, Rust)

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/debashishroy00/ccom/issues)
- **Discussions**: [GitHub Discussions](https://github.com/debashishroy00/ccom/discussions)
- **Documentation**: [docs.ccom.dev](https://docs.ccom.dev) (coming soon)

---

**Made with 💻 for developers who want enterprise-grade automation without enterprise-grade complexity**

*One command. Quality assured. Deploy with confidence.*
// Agentic RAG Validator for Enterprise Systems
// Validates: ReAct, Chain-of-Thought, Tool Usage, Agent Orchestration, Self-Reflection

const fs = require('fs');
const path = require('path');

// Agentic RAG patterns and their validation rules
const AGENTIC_PATTERNS = {
  // ReAct pattern (Reasoning + Acting)
  react: {
    patterns: [
      /react|re-act/i,
      /reason.*act|think.*act/i,
      /observation.*thought.*action/i,
      /thought.*action.*observation/i
    ],
    validations: [
      {
        check: (content) => content.includes('thought') && content.includes('action') && content.includes('observation'),
        message: 'ReAct pattern requires explicit thought, action, and observation steps'
      },
      {
        check: (content) => content.includes('stop') || content.includes('final') || content.includes('answer'),
        message: 'ReAct loops need termination conditions to prevent infinite reasoning'
      }
    ]
  },

  // Chain of Thought patterns
  chainOfThought: {
    patterns: [
      /chain.*of.*thought|cot/i,
      /step.*by.*step|reasoning.*chain/i,
      /let.*think.*step/i,
      /think.*through.*this/i
    ],
    validations: [
      {
        check: (content) => content.includes('step') || content.includes('reasoning'),
        message: 'Chain-of-thought should explicitly break down reasoning into steps'
      },
      {
        check: (content) => content.includes('validate') || content.includes('check'),
        message: 'Include reasoning validation to prevent logical errors'
      }
    ]
  },

  // Tool usage patterns
  toolUsage: {
    patterns: [
      /tool.*use|use.*tool/i,
      /function.*call|call.*function/i,
      /agent.*tool|tool.*agent/i,
      /external.*api|api.*call/i
    ],
    validations: [
      {
        check: (content) => content.includes('timeout') || content.includes('error') || content.includes('retry'),
        message: 'Tool calls need timeout handling and error recovery'
      },
      {
        check: (content) => content.includes('validate') || content.includes('schema'),
        message: 'Validate tool outputs before using in reasoning chain'
      }
    ]
  },

  // Multi-agent orchestration
  multiAgent: {
    patterns: [
      /multi.*agent|agent.*orchestr/i,
      /agent.*coordination|coordinate.*agent/i,
      /agent.*workflow|workflow.*agent/i,
      /swarm|crew|team.*agent/i
    ],
    validations: [
      {
        check: (content) => content.includes('state') || content.includes('memory') || content.includes('context'),
        message: 'Multi-agent systems need shared state and context management'
      },
      {
        check: (content) => content.includes('deadlock') || content.includes('conflict') || content.includes('priority'),
        message: 'Handle agent conflicts and coordination deadlocks'
      }
    ]
  },

  // Self-reflection and planning
  selfReflection: {
    patterns: [
      /self.*reflect|reflect.*on/i,
      /self.*correct|self.*eval/i,
      /meta.*reason|reason.*about.*reason/i,
      /plan.*execution|planning.*agent/i
    ],
    validations: [
      {
        check: (content) => content.includes('evaluate') || content.includes('assess') || content.includes('quality'),
        message: 'Self-reflection requires evaluation criteria and quality assessment'
      },
      {
        check: (content) => content.includes('improve') || content.includes('adjust') || content.includes('revise'),
        message: 'Include mechanisms to improve based on reflection'
      }
    ]
  }
};

// Performance and safety limits for agentic systems
const AGENTIC_LIMITS = {
  max_reasoning_steps: 20,        // Prevent infinite reasoning loops
  max_tool_calls: 10,            // Limit tool usage per query
  max_agent_interactions: 15,     // Multi-agent conversation limits
  max_reflection_depth: 5,        // Self-reflection recursion limit
  max_context_length: 32000,      // Context window management
  max_execution_time_ms: 30000,   // Total agent execution time
  min_confidence_threshold: 0.7,  // Minimum confidence for decisions
  max_retry_attempts: 3          // Tool call retry limits
};

// Common agentic RAG vulnerabilities
const SAFETY_PATTERNS = [
  {
    pattern: /while.*true|for.*true|loop.*infinite/i,
    severity: 'error',
    message: 'Infinite loops can cause agent to run indefinitely'
  },
  {
    pattern: /exec|eval|system|shell/i,
    severity: 'error',
    message: 'Dynamic code execution in agents creates security risks'
  },
  {
    pattern: /delete.*file|rm.*-rf|DROP.*TABLE/i,
    severity: 'error',
    message: 'Destructive operations should not be accessible to agents'
  },
  {
    pattern: /password|secret|token.*=.*['"]/i,
    severity: 'error',
    message: 'Hardcoded secrets accessible to agents'
  }
];

class AgenticRAGValidator {
  constructor(projectPath) {
    this.projectPath = projectPath;
    this.issues = [];
    this.stats = {
      filesScanned: 0,
      agentFiles: 0,
      reactPatterns: 0,
      chainOfThoughtPatterns: 0,
      toolUsagePatterns: 0,
      multiAgentPatterns: 0,
      reflectionPatterns: 0,
      safetyIssues: 0
    };
  }

  validateProject() {
    console.log('🔍 CCOM AGENTIC RAG VALIDATION – Analyzing agent reasoning patterns...');

    this.scanAgentFiles();
    this.validateReasoningPatterns();
    this.validateToolIntegrations();
    this.validateAgentSafety();
    this.validatePerformanceLimits();
    this.validateContextManagement();

    return this.generateReport();
  }

  scanAgentFiles() {
    // Find agent-related files
    const agentFiles = this.findFiles([
      '**/agents/**/*.js', '**/agents/**/*.ts', '**/agents/**/*.py',
      '**/tools/**/*.js', '**/tools/**/*.ts', '**/tools/**/*.py',
      '**/*agent*.js', '**/*agent*.ts', '**/*agent*.py',
      '**/*react*.js', '**/*react*.ts', '**/*react*.py'
    ]);

    agentFiles.forEach(file => {
      this.validateAgentFile(file);
    });
  }

  validateAgentFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      this.stats.filesScanned++;
      this.stats.agentFiles++;

      // Detect agentic patterns
      this.detectAgenticPatterns(content, filePath);

      // Validate agent structure
      this.validateAgentStructure(content, filePath);

      // Check safety patterns
      this.checkAgentSafety(content, filePath);

      // Validate error handling
      this.validateAgentErrorHandling(content, filePath);

    } catch (error) {
      this.addIssue('error', `Cannot read agent file: ${filePath}`, error.message);
    }
  }

  detectAgenticPatterns(content, filePath) {
    Object.entries(AGENTIC_PATTERNS).forEach(([patternType, config]) => {
      const { patterns, validations } = config;

      // Check if any pattern matches
      const hasPattern = patterns.some(pattern => pattern.test(content));

      if (hasPattern) {
        // Increment specific counters
        if (patternType === 'react') this.stats.reactPatterns++;
        if (patternType === 'chainOfThought') this.stats.chainOfThoughtPatterns++;
        if (patternType === 'toolUsage') this.stats.toolUsagePatterns++;
        if (patternType === 'multiAgent') this.stats.multiAgentPatterns++;
        if (patternType === 'selfReflection') this.stats.reflectionPatterns++;

        // Run validations for this pattern
        validations.forEach(({ check, message }) => {
          if (!check(content)) {
            this.addIssue(
              'warning',
              `${patternType} validation in ${filePath}`,
              message
            );
          }
        });
      }
    });
  }

  validateAgentStructure(content, filePath) {
    // Check for proper agent class or function structure
    if (content.includes('agent') || content.includes('Agent')) {
      // Look for essential methods
      const essentialMethods = [
        { method: 'run', message: 'Agent should have a run/execute method' },
        { method: 'execute', message: 'Agent should have a run/execute method' },
        { method: 'think', message: 'Consider adding explicit thinking/reasoning method' },
        { method: 'act', message: 'Consider adding explicit action execution method' }
      ];

      const hasRunMethod = essentialMethods.slice(0, 2).some(({ method }) =>
        content.includes(method + '(') || content.includes(method + ' (')
      );

      if (!hasRunMethod) {
        this.addIssue(
          'warning',
          `Agent structure in ${filePath}`,
          'Agent should have a clear execution entry point (run/execute method)'
        );
      }
    }
  }

  checkAgentSafety(content, filePath) {
    // Check for safety anti-patterns
    SAFETY_PATTERNS.forEach(({ pattern, severity, message }) => {
      if (pattern.test(content)) {
        this.addIssue(severity, `Safety issue in ${filePath}`, message);
        this.stats.safetyIssues++;
      }
    });

    // Check for input validation
    if (content.includes('input') || content.includes('query') || content.includes('request')) {
      if (!content.includes('validate') && !content.includes('sanitize') && !content.includes('escape')) {
        this.addIssue(
          'warning',
          `Input validation missing in ${filePath}`,
          'Validate and sanitize all agent inputs to prevent injection attacks'
        );
      }
    }
  }

  validateAgentErrorHandling(content, filePath) {
    // Check for proper error handling in agent loops
    const agentOperations = ['think', 'act', 'observe', 'tool', 'reason'];

    agentOperations.forEach(operation => {
      if (content.includes(operation)) {
        // Look for error handling
        const hasErrorHandling = content.includes('try') ||
                                content.includes('catch') ||
                                content.includes('.catch') ||
                                content.includes('error');

        if (!hasErrorHandling) {
          this.addIssue(
            'warning',
            `Missing error handling for ${operation} in ${filePath}`,
            `Add error handling for ${operation} operations to prevent agent crashes`
          );
        }
      }
    });
  }

  validateReasoningPatterns() {
    const jsFiles = this.findFiles(['*.js', '*.ts']);

    jsFiles.forEach(file => {
      this.validateReasoningInFile(file);
    });
  }

  validateReasoningInFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');

      // Check ReAct pattern implementation
      this.validateReActPattern(content, filePath);

      // Check Chain-of-Thought implementation
      this.validateChainOfThought(content, filePath);

      // Check reasoning loop controls
      this.validateReasoningLoops(content, filePath);

    } catch (error) {
      this.addIssue('error', `Cannot read reasoning file: ${filePath}`, error.message);
    }
  }

  validateReActPattern(content, filePath) {
    if (content.includes('react') || content.includes('ReAct')) {
      // Check for proper ReAct cycle implementation
      const reactComponents = ['thought', 'action', 'observation'];
      const missingComponents = reactComponents.filter(comp => !content.includes(comp));

      if (missingComponents.length > 0) {
        this.addIssue(
          'warning',
          `Incomplete ReAct pattern in ${filePath}`,
          `Missing ReAct components: ${missingComponents.join(', ')}`
        );
      }

      // Check for loop termination
      if (!content.includes('final') && !content.includes('stop') && !content.includes('answer')) {
        this.addIssue(
          'warning',
          `ReAct termination in ${filePath}`,
          'ReAct pattern needs clear termination conditions'
        );
      }
    }
  }

  validateChainOfThought(content, filePath) {
    if (content.includes('chain') && content.includes('thought')) {
      // Check for step-by-step reasoning
      if (!content.includes('step') && !content.includes('reasoning')) {
        this.addIssue(
          'warning',
          `Chain-of-thought structure in ${filePath}`,
          'Chain-of-thought should explicitly enumerate reasoning steps'
        );
      }

      // Check for reasoning validation
      if (!content.includes('validate') && !content.includes('verify') && !content.includes('check')) {
        this.addIssue(
          'info',
          `Chain-of-thought validation in ${filePath}`,
          'Consider adding reasoning validation to catch logical errors'
        );
      }
    }
  }

  validateReasoningLoops(content, filePath) {
    // Check for potential infinite loops in reasoning
    if (content.includes('while') || content.includes('for')) {
      // Look for loop counters or limits
      const hasLoopControl = content.includes('max') ||
                           content.includes('limit') ||
                           content.includes('counter') ||
                           content.includes('break');

      if (!hasLoopControl) {
        this.addIssue(
          'warning',
          `Loop control in ${filePath}`,
          'Add loop counters or limits to prevent infinite reasoning loops'
        );
      }
    }
  }

  validateToolIntegrations() {
    const jsFiles = this.findFiles(['*.js', '*.ts']);

    jsFiles.forEach(file => {
      this.validateToolsInFile(file);
    });
  }

  validateToolsInFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');

      if (content.includes('tool') || content.includes('function_call')) {
        this.validateToolDefinitions(content, filePath);
        this.validateToolExecution(content, filePath);
        this.validateToolSafety(content, filePath);
      }

    } catch (error) {
      this.addIssue('error', `Cannot read tool file: ${filePath}`, error.message);
    }
  }

  validateToolDefinitions(content, filePath) {
    // Check for proper tool schema definitions
    if (content.includes('function') && content.includes('description')) {
      // Look for parameter validation
      if (!content.includes('parameters') && !content.includes('schema')) {
        this.addIssue(
          'warning',
          `Tool schema in ${filePath}`,
          'Tools should have well-defined parameter schemas'
        );
      }

      // Check for return type specification
      if (!content.includes('return') && !content.includes('output')) {
        this.addIssue(
          'info',
          `Tool output specification in ${filePath}`,
          'Specify expected tool output format for better agent understanding'
        );
      }
    }
  }

  validateToolExecution(content, filePath) {
    // Check for tool execution safety
    if (content.includes('execute') || content.includes('call')) {
      // Look for timeout handling
      if (!content.includes('timeout') && !content.includes('abort')) {
        this.addIssue(
          'warning',
          `Tool timeout handling in ${filePath}`,
          'Add timeout handling for tool executions'
        );
      }

      // Check for retry logic
      if (!content.includes('retry') && !content.includes('attempt')) {
        this.addIssue(
          'info',
          `Tool retry logic in ${filePath}`,
          'Consider adding retry logic for unreliable tool calls'
        );
      }
    }
  }

  validateToolSafety(content, filePath) {
    // Check for dangerous tool capabilities
    const dangerousOperations = [
      'file_delete', 'file_remove', 'system_command',
      'exec', 'shell', 'run_command', 'execute_code'
    ];

    dangerousOperations.forEach(operation => {
      if (content.includes(operation)) {
        this.addIssue(
          'error',
          `Dangerous tool operation in ${filePath}`,
          `Tool '${operation}' poses security risks - implement strict access controls`
        );
      }
    });
  }

  validateAgentSafety() {
    const jsFiles = this.findFiles(['*.js', '*.ts']);

    jsFiles.forEach(file => {
      this.validateSafetyInFile(file);
    });
  }

  validateSafetyInFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');

      // Check for privilege escalation risks
      this.checkPrivilegeEscalation(content, filePath);

      // Check for data leakage risks
      this.checkDataLeakage(content, filePath);

      // Check for injection vulnerabilities
      this.checkInjectionRisks(content, filePath);

    } catch (error) {
      this.addIssue('error', `Cannot read safety file: ${filePath}`, error.message);
    }
  }

  checkPrivilegeEscalation(content, filePath) {
    // Check for escalation patterns
    const escalationPatterns = [
      /sudo|admin|root|elevated/i,
      /privilege|permission|access.*control/i
    ];

    escalationPatterns.forEach(pattern => {
      if (pattern.test(content)) {
        this.addIssue(
          'warning',
          `Privilege escalation risk in ${filePath}`,
          'Ensure agents operate with minimal necessary privileges'
        );
      }
    });
  }

  checkDataLeakage(content, filePath) {
    // Check for potential data exposure
    if (content.includes('log') || content.includes('console') || content.includes('debug')) {
      if (content.includes('password') || content.includes('secret') || content.includes('token')) {
        this.addIssue(
          'error',
          `Data leakage risk in ${filePath}`,
          'Avoid logging sensitive information in agent operations'
        );
      }
    }
  }

  checkInjectionRisks(content, filePath) {
    // Check for prompt injection vulnerabilities
    if (content.includes('prompt') || content.includes('instruction')) {
      if (!content.includes('sanitize') && !content.includes('validate')) {
        this.addIssue(
          'warning',
          `Prompt injection risk in ${filePath}`,
          'Sanitize and validate prompt inputs to prevent injection attacks'
        );
      }
    }
  }

  validatePerformanceLimits() {
    // Check for performance-related configuration
    const configFiles = this.findFiles(['*.config.js', '*.json']);

    configFiles.forEach(file => {
      this.checkAgenticPerformanceLimits(file);
    });
  }

  checkAgenticPerformanceLimits(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');

      // Check against agentic limits
      Object.entries(AGENTIC_LIMITS).forEach(([key, limit]) => {
        const pattern = new RegExp(`${key.replace(/_/g, '[_-]')}.*?([0-9]+)`, 'i');
        const match = content.match(pattern);

        if (match) {
          const value = parseInt(match[1]);
          if (value > limit) {
            this.addIssue(
              'warning',
              `Agentic limit exceeded in ${filePath}`,
              `${key} value ${value} exceeds recommended limit of ${limit}`
            );
          }
        }
      });

    } catch (error) {
      this.addIssue('error', `Cannot read agentic config: ${filePath}`, error.message);
    }
  }

  validateContextManagement() {
    const jsFiles = this.findFiles(['*.js', '*.ts']);

    jsFiles.forEach(file => {
      this.validateContextInFile(file);
    });
  }

  validateContextInFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');

      // Check for context window management
      if (content.includes('context') || content.includes('memory')) {
        this.checkContextWindowManagement(content, filePath);
        this.checkMemoryManagement(content, filePath);
      }

    } catch (error) {
      this.addIssue('error', `Cannot read context file: ${filePath}`, error.message);
    }
  }

  checkContextWindowManagement(content, filePath) {
    // Check for context length tracking
    if (!content.includes('length') && !content.includes('size') && !content.includes('tokens')) {
      this.addIssue(
        'warning',
        `Context length tracking in ${filePath}`,
        'Track context length to prevent exceeding model limits'
      );
    }

    // Check for context pruning
    if (!content.includes('prune') && !content.includes('truncate') && !content.includes('summarize')) {
      this.addIssue(
        'info',
        `Context pruning in ${filePath}`,
        'Implement context pruning strategies for long conversations'
      );
    }
  }

  checkMemoryManagement(content, filePath) {
    // Check for memory persistence
    if (content.includes('memory')) {
      if (!content.includes('save') && !content.includes('persist') && !content.includes('store')) {
        this.addIssue(
          'info',
          `Memory persistence in ${filePath}`,
          'Consider persisting agent memory across sessions'
        );
      }

      // Check for memory retrieval strategies
      if (!content.includes('retrieve') && !content.includes('recall') && !content.includes('search')) {
        this.addIssue(
          'info',
          `Memory retrieval in ${filePath}`,
          'Implement efficient memory retrieval for relevant context'
        );
      }
    }
  }

  findFiles(patterns) {
    const files = [];

    function walkDir(dir) {
      try {
        const items = fs.readdirSync(dir);

        items.forEach(item => {
          const fullPath = path.join(dir, item);
          const stat = fs.statSync(fullPath);

          if (stat.isDirectory() && !item.startsWith('.') && item !== 'node_modules') {
            walkDir(fullPath);
          } else if (stat.isFile()) {
            const matches = patterns.some(pattern => {
              if (pattern.includes('**')) {
                // Handle glob patterns with **
                const regex = new RegExp(pattern.replace(/\*\*/g, '.*').replace(/\*/g, '[^/]*'));
                return regex.test(fullPath.replace(/\\/g, '/'));
              } else if (pattern.includes('*')) {
                const regex = new RegExp(pattern.replace('*', '.*'));
                return regex.test(item);
              }
              return item === pattern;
            });

            if (matches) {
              files.push(fullPath);
            }
          }
        });
      } catch (error) {
        // Skip inaccessible directories
      }
    }

    walkDir(this.projectPath);
    return files;
  }

  addIssue(level, title, description) {
    this.issues.push({ level, title, description });
  }

  generateReport() {
    const errorCount = this.issues.filter(i => i.level === 'error').length;
    const warningCount = this.issues.filter(i => i.level === 'warning').length;
    const infoCount = this.issues.filter(i => i.level === 'info').length;

    console.log('\n📊 AGENTIC RAG VALIDATION REPORT');
    console.log('=' .repeat(50));

    console.log(`🤖 Agent Statistics:`);
    console.log(`   Files scanned: ${this.stats.filesScanned}`);
    console.log(`   Agent files: ${this.stats.agentFiles}`);
    console.log(`   ReAct patterns: ${this.stats.reactPatterns}`);
    console.log(`   Chain-of-thought patterns: ${this.stats.chainOfThoughtPatterns}`);
    console.log(`   Tool usage patterns: ${this.stats.toolUsagePatterns}`);
    console.log(`   Multi-agent patterns: ${this.stats.multiAgentPatterns}`);
    console.log(`   Reflection patterns: ${this.stats.reflectionPatterns}`);
    console.log(`   Safety issues: ${this.stats.safetyIssues}`);

    if (errorCount === 0 && warningCount === 0) {
      console.log('✅ EXCELLENT: Agentic RAG patterns are safe and well-implemented');
    } else {
      console.log(`🔍 Found ${errorCount} errors, ${warningCount} warnings, ${infoCount} suggestions`);
    }

    // Group issues by level
    ['error', 'warning', 'info'].forEach(level => {
      const levelIssues = this.issues.filter(i => i.level === level);
      if (levelIssues.length > 0) {
        console.log(`\n${level.toUpperCase()}S:`);
        levelIssues.forEach((issue, index) => {
          console.log(`${index + 1}. ${issue.title}`);
          console.log(`   ${issue.description}`);
        });
      }
    });

    return {
      passed: errorCount === 0,
      summary: `Agentic RAG validation: ${errorCount} errors, ${warningCount} warnings`,
      details: this.issues,
      stats: this.stats
    };
  }
}

module.exports = AgenticRAGValidator;

// CLI usage
if (require.main === module) {
  const projectPath = process.argv[2] || process.cwd();
  const validator = new AgenticRAGValidator(projectPath);
  const result = validator.validateProject();
  process.exit(result.passed ? 0 : 1);
}
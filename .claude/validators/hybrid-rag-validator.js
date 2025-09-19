// Hybrid RAG Workflow Validator for Enterprise Systems
// Validates: Vector + Keyword + Graph fusion, Reranking, Score normalization

const fs = require('fs');
const path = require('path');

// Common hybrid RAG patterns and their validation rules
const HYBRID_PATTERNS = {
  // Score fusion patterns
  fusion: {
    patterns: [
      /reciprocal.*rank.*fusion|rrf/i,
      /weighted.*fusion|score.*fusion/i,
      /linear.*combination|score.*combination/i,
      /harmonic.*mean|geometric.*mean/i
    ],
    validations: [
      {
        check: (content) => content.includes('normalize') || content.includes('normalization'),
        message: 'Score normalization is critical for proper fusion'
      },
      {
        check: (content) => /weight.*[0-9.]+/.test(content),
        message: 'Fusion weights should be configurable and tunable'
      }
    ]
  },

  // Reranking patterns
  reranking: {
    patterns: [
      /rerank|re-rank/i,
      /cross.*encoder/i,
      /cohere.*rerank|openai.*rerank/i,
      /sentence.*transformers.*rerank/i
    ],
    validations: [
      {
        check: (content) => content.includes('top_k') || content.includes('limit'),
        message: 'Reranking should limit input size for performance'
      },
      {
        check: (content) => content.includes('batch') || content.includes('concurrent'),
        message: 'Consider batch reranking for efficiency'
      }
    ]
  },

  // Vector + keyword retrieval
  vectorKeyword: {
    patterns: [
      /vector.*keyword|keyword.*vector/i,
      /dense.*sparse|sparse.*dense/i,
      /elasticsearch.*vector|opensearch.*vector/i,
      /bm25.*vector|vector.*bm25/i
    ],
    validations: [
      {
        check: (content) => /alpha.*[0-9.]+|weight.*[0-9.]+/.test(content),
        message: 'Vector-keyword fusion needs tunable alpha/weight parameters'
      },
      {
        check: (content) => content.includes('normalize') || content.includes('min_max'),
        message: 'Normalize scores before combining vector and keyword results'
      }
    ]
  },

  // Knowledge graph integration
  graphRag: {
    patterns: [
      /knowledge.*graph.*rag|kg.*rag/i,
      /graph.*retrieval|neo4j.*rag/i,
      /entity.*linking|entity.*extraction/i,
      /graph.*traversal.*rag/i
    ],
    validations: [
      {
        check: (content) => content.includes('hop') || content.includes('depth'),
        message: 'Graph traversal should limit hop count to prevent exponential expansion'
      },
      {
        check: (content) => content.includes('entity') && content.includes('filter'),
        message: 'Filter irrelevant entities before graph traversal'
      }
    ]
  }
};

// Performance limits for hybrid systems
const PERFORMANCE_LIMITS = {
  max_retrieval_candidates: 1000,  // Before reranking
  max_rerank_candidates: 100,      // Input to reranker
  max_final_results: 20,           // Final k for generation
  max_graph_hops: 3,              // Graph traversal depth
  max_fusion_sources: 5,          // Number of retrieval sources
  min_score_threshold: 0.1,       // Filter low-quality results
  max_processing_time_ms: 5000    // Total retrieval time limit
};

class HybridRAGValidator {
  constructor(projectPath) {
    this.projectPath = projectPath;
    this.issues = [];
    this.stats = {
      filesScanned: 0,
      hybridPatterns: 0,
      fusionMethods: 0,
      rerankingMethods: 0,
      graphIntegrations: 0
    };
  }

  validateProject() {
    console.log('🔍 CCOM HYBRID RAG VALIDATION – Analyzing hybrid retrieval patterns...');

    this.scanHybridConfigurations();
    this.scanRetrievalPipelines();
    this.validateFusionMethods();
    this.validateRerankingPipelines();
    this.validateGraphIntegration();
    this.validatePerformanceLimits();

    return this.generateReport();
  }

  scanHybridConfigurations() {
    // Look for hybrid RAG configuration files
    const configFiles = this.findFiles([
      'hybrid.config.js', 'rag.config.js', 'retrieval.config.js',
      'fusion.config.js', 'rerank.config.js'
    ]);

    configFiles.forEach(file => {
      this.validateHybridConfig(file);
    });
  }

  validateHybridConfig(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      this.stats.filesScanned++;

      // Check for required hybrid configuration elements
      this.checkHybridConfigCompleteness(content, filePath);
      this.checkConfigSecurity(content, filePath);
      this.checkPerformanceSettings(content, filePath);

    } catch (error) {
      this.addIssue('error', `Cannot read config file: ${filePath}`, error.message);
    }
  }

  checkHybridConfigCompleteness(content, filePath) {
    const requiredElements = [
      { key: 'vector', message: 'Vector retrieval configuration missing' },
      { key: 'keyword', message: 'Keyword retrieval configuration missing' },
      { key: 'fusion', message: 'Score fusion method not configured' },
      { key: 'weights', message: 'Fusion weights not configured' }
    ];

    requiredElements.forEach(({ key, message }) => {
      if (!content.includes(key)) {
        this.addIssue('warning', `Missing ${key} in ${filePath}`, message);
      }
    });

    // Check for advanced features
    if (content.includes('rerank') || content.includes('reranking')) {
      this.stats.rerankingMethods++;
      if (!content.includes('top_k') && !content.includes('candidate_count')) {
        this.addIssue(
          'warning',
          `Reranking without candidate limits in ${filePath}`,
          'Specify candidate limits for reranking performance'
        );
      }
    }
  }

  checkConfigSecurity(content, filePath) {
    // Check for hardcoded API keys for reranking services
    const secretPatterns = [
      /cohere.*api.*key.*['"`][^'"`]+['"`]/i,
      /openai.*api.*key.*['"`][^'"`]+['"`]/i,
      /huggingface.*token.*['"`][^'"`]+['"`]/i
    ];

    secretPatterns.forEach(pattern => {
      if (pattern.test(content)) {
        this.addIssue(
          'error',
          `Hardcoded API key in ${filePath}`,
          'Use environment variables for reranking service API keys'
        );
      }
    });
  }

  checkPerformanceSettings(content, filePath) {
    // Check for performance-related settings
    const performanceChecks = [
      {
        pattern: /timeout.*[0-9]+/i,
        exists: content.includes('timeout'),
        message: 'Consider adding timeout configuration for retrieval services'
      },
      {
        pattern: /concurrent.*[0-9]+/i,
        exists: content.includes('concurrent') || content.includes('parallel'),
        message: 'Configure concurrency limits for parallel retrieval'
      }
    ];

    performanceChecks.forEach(({ exists, message }) => {
      if (!exists) {
        this.addIssue('info', `Performance optimization in ${filePath}`, message);
      }
    });
  }

  scanRetrievalPipelines() {
    const jsFiles = this.findFiles(['*.js', '*.ts', '*.py']);

    jsFiles.forEach(file => {
      this.validateRetrievalPipeline(file);
    });
  }

  validateRetrievalPipeline(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      this.stats.filesScanned++;

      // Detect hybrid patterns
      this.detectHybridPatterns(content, filePath);

      // Validate pipeline structure
      this.validatePipelineStructure(content, filePath);

      // Check error handling
      this.validateErrorHandling(content, filePath);

    } catch (error) {
      this.addIssue('error', `Cannot read pipeline file: ${filePath}`, error.message);
    }
  }

  detectHybridPatterns(content, filePath) {
    Object.entries(HYBRID_PATTERNS).forEach(([patternType, config]) => {
      const { patterns, validations } = config;

      // Check if any pattern matches
      const hasPattern = patterns.some(pattern => pattern.test(content));

      if (hasPattern) {
        this.stats.hybridPatterns++;

        // Increment specific counters
        if (patternType === 'fusion') this.stats.fusionMethods++;
        if (patternType === 'reranking') this.stats.rerankingMethods++;
        if (patternType === 'graphRag') this.stats.graphIntegrations++;

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

  validatePipelineStructure(content, filePath) {
    // Check for proper async/await usage in retrieval pipelines
    if (content.includes('async') && content.includes('retrieve')) {
      // Look for Promise.all for parallel retrieval
      if (!content.includes('Promise.all') && !content.includes('Promise.allSettled')) {
        this.addIssue(
          'info',
          `Parallel retrieval optimization in ${filePath}`,
          'Consider using Promise.all for parallel retrieval from multiple sources'
        );
      }
    }

    // Check for result validation
    if (content.includes('retrieve') || content.includes('search')) {
      if (!content.includes('validate') && !content.includes('filter') && !content.includes('threshold')) {
        this.addIssue(
          'warning',
          `Missing result validation in ${filePath}`,
          'Add quality filters and score thresholds for retrieval results'
        );
      }
    }
  }

  validateErrorHandling(content, filePath) {
    // Check for fallback mechanisms
    const retrievalMethods = ['vector', 'keyword', 'graph', 'rerank'];

    retrievalMethods.forEach(method => {
      if (content.includes(method)) {
        // Look for error handling
        const hasErrorHandling = content.includes('try') || content.includes('catch') || content.includes('.catch');

        if (!hasErrorHandling) {
          this.addIssue(
            'warning',
            `Missing error handling for ${method} in ${filePath}`,
            `Add error handling and fallback for ${method} retrieval failures`
          );
        }
      }
    });
  }

  validateFusionMethods() {
    const jsFiles = this.findFiles(['*.js', '*.ts']);

    jsFiles.forEach(file => {
      this.validateFusionInFile(file);
    });
  }

  validateFusionInFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');

      // Check for score fusion implementations
      this.checkScoreFusion(content, filePath);
      this.checkWeightValidation(content, filePath);
      this.checkNormalizationMethods(content, filePath);

    } catch (error) {
      this.addIssue('error', `Cannot read fusion file: ${filePath}`, error.message);
    }
  }

  checkScoreFusion(content, filePath) {
    // Look for fusion method implementations
    const fusionMethods = [
      { name: 'RRF', pattern: /reciprocal.*rank|rrf/i },
      { name: 'Weighted Sum', pattern: /weighted.*sum|linear.*combination/i },
      { name: 'Harmonic Mean', pattern: /harmonic.*mean/i },
      { name: 'Geometric Mean', pattern: /geometric.*mean/i }
    ];

    fusionMethods.forEach(({ name, pattern }) => {
      if (pattern.test(content)) {
        // Check for proper implementation
        this.validateFusionImplementation(content, filePath, name);
      }
    });
  }

  validateFusionImplementation(content, filePath, methodName) {
    // Common issues in fusion implementations
    const validations = [
      {
        check: content.includes('Math.max') || content.includes('Math.min'),
        message: `${methodName} should handle score ranges properly`
      },
      {
        check: content.includes('isNaN') || content.includes('Number.isFinite'),
        message: `${methodName} should validate numeric scores`
      },
      {
        check: !content.includes('divide') || content.includes('!== 0'),
        message: `${methodName} should handle division by zero`
      }
    ];

    validations.forEach(({ check, message }) => {
      if (!check) {
        this.addIssue('warning', `${methodName} implementation in ${filePath}`, message);
      }
    });
  }

  checkWeightValidation(content, filePath) {
    // Check for weight validation in fusion
    if (content.includes('weight') && (content.includes('fusion') || content.includes('combine'))) {
      const hasValidation = [
        content.includes('sum') && content.includes('1'),  // Weights sum to 1
        content.includes('normalize'),                      // Weight normalization
        content.includes('> 0') || content.includes('positive') // Positive weights
      ].some(Boolean);

      if (!hasValidation) {
        this.addIssue(
          'warning',
          `Weight validation missing in ${filePath}`,
          'Validate that fusion weights are positive and sum to 1'
        );
      }
    }
  }

  checkNormalizationMethods(content, filePath) {
    // Check for score normalization implementations
    if (content.includes('normalize') || content.includes('normalization')) {
      const normalizationMethods = [
        { name: 'Min-Max', pattern: /min.*max|minmax/i },
        { name: 'Z-Score', pattern: /z.?score|standard.*score/i },
        { name: 'Sigmoid', pattern: /sigmoid/i },
        { name: 'Softmax', pattern: /softmax/i }
      ];

      const hasMethod = normalizationMethods.some(({ pattern }) => pattern.test(content));

      if (!hasMethod) {
        this.addIssue(
          'info',
          `Normalization method in ${filePath}`,
          'Consider implementing min-max or z-score normalization for consistent fusion'
        );
      }
    }
  }

  validateRerankingPipelines() {
    const jsFiles = this.findFiles(['*.js', '*.ts']);

    jsFiles.forEach(file => {
      this.validateRerankingInFile(file);
    });
  }

  validateRerankingInFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');

      if (content.includes('rerank') || content.includes('reranking')) {
        this.checkRerankingEfficiency(content, filePath);
        this.checkRerankingServices(content, filePath);
        this.checkRerankingFallbacks(content, filePath);
      }

    } catch (error) {
      this.addIssue('error', `Cannot read reranking file: ${filePath}`, error.message);
    }
  }

  checkRerankingEfficiency(content, filePath) {
    // Check for candidate count limits
    if (!content.includes('top_k') && !content.includes('limit') && !content.includes('candidates')) {
      this.addIssue(
        'warning',
        `Reranking efficiency in ${filePath}`,
        'Limit reranking candidates to improve performance'
      );
    }

    // Check for batch processing
    if (content.includes('for') && content.includes('rerank') && !content.includes('batch')) {
      this.addIssue(
        'info',
        `Batch reranking in ${filePath}`,
        'Consider batch reranking for better efficiency'
      );
    }
  }

  checkRerankingServices(content, filePath) {
    // Check for service configuration
    const services = ['cohere', 'openai', 'huggingface', 'sentence-transformers'];

    services.forEach(service => {
      if (content.includes(service) && content.includes('rerank')) {
        // Check for proper API key handling
        if (content.includes('api_key') && !content.includes('process.env')) {
          this.addIssue(
            'error',
            `API key security in ${filePath}`,
            `Use environment variables for ${service} API keys`
          );
        }
      }
    });
  }

  checkRerankingFallbacks(content, filePath) {
    // Check for fallback mechanisms when reranking fails
    if (content.includes('rerank')) {
      const hasFallback = content.includes('fallback') ||
                         content.includes('catch') ||
                         content.includes('default');

      if (!hasFallback) {
        this.addIssue(
          'warning',
          `Reranking fallback in ${filePath}`,
          'Add fallback mechanism when reranking service is unavailable'
        );
      }
    }
  }

  validateGraphIntegration() {
    const jsFiles = this.findFiles(['*.js', '*.ts']);

    jsFiles.forEach(file => {
      this.validateGraphRAGInFile(file);
    });
  }

  validateGraphRAGInFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');

      if (content.includes('graph') && content.includes('rag')) {
        this.checkGraphTraversalLimits(content, filePath);
        this.checkEntityLinking(content, filePath);
        this.checkGraphScoring(content, filePath);
      }

    } catch (error) {
      this.addIssue('error', `Cannot read graph RAG file: ${filePath}`, error.message);
    }
  }

  checkGraphTraversalLimits(content, filePath) {
    // Check for hop/depth limits
    if (!content.includes('hop') && !content.includes('depth') && !content.includes('limit')) {
      this.addIssue(
        'warning',
        `Graph traversal limits in ${filePath}`,
        'Add hop count limits to prevent exponential graph expansion'
      );
    }

    // Check for relationship filtering
    if (content.includes('relationship') && !content.includes('filter') && !content.includes('type')) {
      this.addIssue(
        'info',
        `Relationship filtering in ${filePath}`,
        'Filter relationships by type for more relevant graph traversal'
      );
    }
  }

  checkEntityLinking(content, filePath) {
    // Check for entity extraction and linking
    if (content.includes('entity')) {
      if (!content.includes('extract') && !content.includes('link')) {
        this.addIssue(
          'info',
          `Entity processing in ${filePath}`,
          'Implement entity extraction and linking for better graph integration'
        );
      }
    }
  }

  checkGraphScoring(content, filePath) {
    // Check for graph-specific scoring
    if (content.includes('graph') && content.includes('score')) {
      const hasGraphScoring = content.includes('pagerank') ||
                             content.includes('centrality') ||
                             content.includes('relationship_strength');

      if (!hasGraphScoring) {
        this.addIssue(
          'info',
          `Graph scoring in ${filePath}`,
          'Consider graph-specific scoring metrics (PageRank, centrality, etc.)'
        );
      }
    }
  }

  validatePerformanceLimits() {
    // Check for performance-related configuration
    const configFiles = this.findFiles(['*.config.js', '*.json']);

    configFiles.forEach(file => {
      this.checkPerformanceLimits(file);
    });
  }

  checkPerformanceLimits(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');

      // Check against performance limits
      Object.entries(PERFORMANCE_LIMITS).forEach(([key, limit]) => {
        const pattern = new RegExp(`${key.replace(/_/g, '[_-]')}.*?([0-9]+)`, 'i');
        const match = content.match(pattern);

        if (match) {
          const value = parseInt(match[1]);
          if (value > limit) {
            this.addIssue(
              'warning',
              `Performance limit exceeded in ${filePath}`,
              `${key} value ${value} exceeds recommended limit of ${limit}`
            );
          }
        }
      });

    } catch (error) {
      this.addIssue('error', `Cannot read performance config: ${filePath}`, error.message);
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
              if (pattern.includes('*')) {
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

    console.log('\n📊 HYBRID RAG VALIDATION REPORT');
    console.log('=' .repeat(50));

    console.log(`📈 Hybrid RAG Statistics:`);
    console.log(`   Files scanned: ${this.stats.filesScanned}`);
    console.log(`   Hybrid patterns detected: ${this.stats.hybridPatterns}`);
    console.log(`   Fusion methods: ${this.stats.fusionMethods}`);
    console.log(`   Reranking methods: ${this.stats.rerankingMethods}`);
    console.log(`   Graph integrations: ${this.stats.graphIntegrations}`);

    if (errorCount === 0 && warningCount === 0) {
      console.log('✅ EXCELLENT: Hybrid RAG patterns are well-implemented');
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
      summary: `Hybrid RAG validation: ${errorCount} errors, ${warningCount} warnings`,
      details: this.issues,
      stats: this.stats
    };
  }
}

module.exports = HybridRAGValidator;

// CLI usage
if (require.main === module) {
  const projectPath = process.argv[2] || process.cwd();
  const validator = new HybridRAGValidator(projectPath);
  const result = validator.validateProject();
  process.exit(result.passed ? 0 : 1);
}
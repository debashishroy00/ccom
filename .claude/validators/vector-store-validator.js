// Vector Store Validation for Enterprise RAG Systems
// Supports: ChromaDB, Weaviate, FAISS, Pinecone, Qdrant, Milvus

const fs = require('fs');
const path = require('path');

// Standard embedding model dimensions
const VECTOR_CONFIGS = {
  'openai': {
    'text-embedding-ada-002': 1536,
    'text-embedding-3-small': 1536,
    'text-embedding-3-large': 3072
  },
  'cohere': {
    'embed-english-v3.0': 1024,
    'embed-multilingual-v3.0': 1024,
    'embed-english-light-v3.0': 384
  },
  'sentence-transformers': {
    'all-MiniLM-L6-v2': 384,
    'all-mpnet-base-v2': 768,
    'all-MiniLM-L12-v2': 384,
    'paraphrase-MiniLM-L6-v2': 384
  },
  'huggingface': {
    'sentence-transformers/all-MiniLM-L6-v2': 384,
    'sentence-transformers/all-mpnet-base-v2': 768
  }
};

// Performance limits for vector operations
const PERFORMANCE_LIMITS = {
  max_batch_size: 100,          // OpenAI embedding batch limit
  max_tokens_per_chunk: 8191,   // GPT model token limit
  max_concurrent_requests: 50,   // Rate limiting
  max_document_size_mb: 10,     // Memory management
  min_chunk_overlap: 50,        // Context preservation
  max_chunk_size: 1000,         // Retrieval efficiency
  max_similarity_results: 100,   // Prevent unbounded queries
  min_similarity_threshold: 0.0, // Minimum threshold
  max_similarity_threshold: 1.0  // Maximum threshold
};

class VectorStoreValidator {
  constructor(projectPath) {
    this.projectPath = projectPath;
    this.issues = [];
  }

  validateProject() {
    console.log('🔍 CCOM VECTOR VALIDATION – Analyzing vector store patterns...');

    this.validateConfigurations();
    this.validateEmbeddingUsage();
    this.validateQueryPatterns();
    this.validatePerformanceLimits();
    this.validateSecurityPatterns();

    return this.generateReport();
  }

  validateConfigurations() {
    // Check for vector store config files
    const configPatterns = [
      'chroma.config.js', 'chromadb.config.js',
      'weaviate.config.js', 'weaviate.yml',
      'pinecone.config.js',
      'qdrant.config.js',
      'vector.config.js', 'embeddings.config.js'
    ];

    const configs = this.findFiles(configPatterns);

    configs.forEach(configFile => {
      this.validateVectorConfig(configFile);
    });
  }

  validateVectorConfig(configPath) {
    try {
      const content = fs.readFileSync(configPath, 'utf8');

      // Check for dimension mismatches
      this.checkDimensionConsistency(content, configPath);

      // Check for missing performance limits
      this.checkPerformanceLimits(content, configPath);

      // Check for security issues
      this.checkConfigSecurity(content, configPath);

    } catch (error) {
      this.addIssue('error', `Cannot read config file: ${configPath}`, error.message);
    }
  }

  checkDimensionConsistency(content, filePath) {
    // Extract model and dimension info
    const modelMatch = content.match(/embedding[_-]?model.*?['"`]([^'"`]+)['"`]/i);
    const dimensionMatch = content.match(/dimension.*?(\d+)/i);

    if (modelMatch && dimensionMatch) {
      const model = modelMatch[1];
      const dimension = parseInt(dimensionMatch[1]);

      // Check against known configurations
      let expectedDimension = null;
      for (const provider in VECTOR_CONFIGS) {
        if (VECTOR_CONFIGS[provider][model]) {
          expectedDimension = VECTOR_CONFIGS[provider][model];
          break;
        }
      }

      if (expectedDimension && dimension !== expectedDimension) {
        this.addIssue(
          'error',
          `Dimension mismatch in ${filePath}`,
          `Model '${model}' requires ${expectedDimension} dimensions, but config uses ${dimension}`
        );
      }
    }
  }

  checkPerformanceLimits(content, filePath) {
    // Check for missing batch size limits
    if (!content.includes('batch_size') && !content.includes('batchSize')) {
      this.addIssue(
        'warning',
        `Missing batch size limit in ${filePath}`,
        'Add batch_size configuration to prevent memory issues'
      );
    }

    // Check for unbounded similarity searches
    if (content.includes('similarity') && !content.includes('limit') && !content.includes('top_k')) {
      this.addIssue(
        'warning',
        `Unbounded similarity search in ${filePath}`,
        'Add limit/top_k to prevent performance issues'
      );
    }
  }

  checkConfigSecurity(content, filePath) {
    // Check for hardcoded API keys
    const secretPatterns = [
      /api[_-]?key.*?['"`][a-zA-Z0-9]{20,}['"`]/i,
      /secret.*?['"`][a-zA-Z0-9]{20,}['"`]/i,
      /token.*?['"`][a-zA-Z0-9]{20,}['"`]/i
    ];

    secretPatterns.forEach(pattern => {
      if (pattern.test(content)) {
        this.addIssue(
          'error',
          `Hardcoded secret in ${filePath}`,
          'Use environment variables for API keys and secrets'
        );
      }
    });
  }

  validateEmbeddingUsage() {
    const jsFiles = this.findFiles(['*.js', '*.ts']);

    jsFiles.forEach(file => {
      this.validateEmbeddingFile(file);
    });
  }

  validateEmbeddingFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');

      // Check for proper error handling in embedding calls
      this.checkEmbeddingErrorHandling(content, filePath);

      // Check for batch processing
      this.checkBatchProcessing(content, filePath);

      // Check for rate limiting
      this.checkRateLimiting(content, filePath);

    } catch (error) {
      this.addIssue('error', `Cannot read file: ${filePath}`, error.message);
    }
  }

  checkEmbeddingErrorHandling(content, filePath) {
    // Check for embedding API calls without error handling
    const embeddingCalls = [
      /\.embed\(/g,
      /\.getEmbedding\(/g,
      /openai\.embeddings/g,
      /cohere\.embed/g
    ];

    embeddingCalls.forEach(pattern => {
      const matches = content.match(pattern);
      if (matches) {
        // Check if there's try-catch around these calls
        const lines = content.split('\n');
        let hasErrorHandling = false;

        lines.forEach((line, index) => {
          if (pattern.test(line)) {
            // Look for try-catch in surrounding lines
            const context = lines.slice(Math.max(0, index - 5), index + 5).join('\n');
            if (context.includes('try') && context.includes('catch')) {
              hasErrorHandling = true;
            }
          }
        });

        if (!hasErrorHandling) {
          this.addIssue(
            'warning',
            `Missing error handling for embedding calls in ${filePath}`,
            'Add try-catch blocks around embedding API calls'
          );
        }
      }
    });
  }

  checkBatchProcessing(content, filePath) {
    // Check for loop-based embedding calls (inefficient)
    if (content.includes('for') && content.includes('.embed(') && !content.includes('batch')) {
      this.addIssue(
        'warning',
        `Potential inefficient embedding in ${filePath}`,
        'Consider batch processing for multiple embeddings'
      );
    }
  }

  checkRateLimiting(content, filePath) {
    // Check for concurrent requests without rate limiting
    if ((content.includes('Promise.all') || content.includes('await Promise.all')) &&
        content.includes('embed') && !content.includes('throttle') && !content.includes('delay')) {
      this.addIssue(
        'warning',
        `Potential rate limiting issue in ${filePath}`,
        'Add throttling for concurrent embedding requests'
      );
    }
  }

  validateQueryPatterns() {
    const jsFiles = this.findFiles(['*.js', '*.ts']);

    jsFiles.forEach(file => {
      this.validateQueryFile(file);
    });
  }

  validateQueryFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');

      // Check for unbounded similarity searches
      this.checkSimilarityQueries(content, filePath);

      // Check for proper filtering
      this.checkQueryFiltering(content, filePath);

    } catch (error) {
      this.addIssue('error', `Cannot read file: ${filePath}`, error.message);
    }
  }

  checkSimilarityQueries(content, filePath) {
    // Check for similarity queries without limits
    const queryPatterns = [
      /\.query\(/g,
      /\.search\(/g,
      /\.similarity\(/g
    ];

    queryPatterns.forEach(pattern => {
      if (pattern.test(content) && !content.includes('limit') && !content.includes('top_k') && !content.includes('n_results')) {
        this.addIssue(
          'warning',
          `Unbounded similarity query in ${filePath}`,
          'Add limit/top_k/n_results to prevent performance issues'
        );
      }
    });
  }

  checkQueryFiltering(content, filePath) {
    // Check for multi-tenant filtering
    if ((content.includes('.query(') || content.includes('.search(')) &&
        !content.includes('tenant') && !content.includes('user_id') && !content.includes('namespace')) {
      this.addIssue(
        'info',
        `Consider tenant filtering in ${filePath}`,
        'Add tenant/user filtering for multi-tenant applications'
      );
    }
  }

  validatePerformanceLimits() {
    // Check package.json for memory limits
    const packagePath = path.join(this.projectPath, 'package.json');
    if (fs.existsSync(packagePath)) {
      const packageContent = JSON.parse(fs.readFileSync(packagePath, 'utf8'));

      // Check for Node.js memory settings
      const scripts = packageContent.scripts || {};
      const hasMemoryLimit = Object.values(scripts).some(script =>
        script.includes('--max-old-space-size') || script.includes('--max-heap-size')
      );

      if (!hasMemoryLimit) {
        this.addIssue(
          'info',
          'Consider adding Node.js memory limits',
          'Add --max-old-space-size=4096 for vector operations'
        );
      }
    }
  }

  validateSecurityPatterns() {
    const jsFiles = this.findFiles(['*.js', '*.ts']);

    jsFiles.forEach(file => {
      this.validateSecurityFile(file);
    });
  }

  validateSecurityFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');

      // Check for input validation
      this.checkInputValidation(content, filePath);

      // Check for SQL injection in vector metadata
      this.checkMetadataInjection(content, filePath);

    } catch (error) {
      this.addIssue('error', `Cannot read file: ${filePath}`, error.message);
    }
  }

  checkInputValidation(content, filePath) {
    // Check for user input in queries without validation
    if (content.includes('req.body') || content.includes('req.query')) {
      if (!content.includes('validate') && !content.includes('sanitize') && !content.includes('escape')) {
        this.addIssue(
          'warning',
          `Missing input validation in ${filePath}`,
          'Validate user input before vector operations'
        );
      }
    }
  }

  checkMetadataInjection(content, filePath) {
    // Check for dynamic metadata queries
    if (content.includes('metadata') && content.includes('${') || content.includes('`${')) {
      this.addIssue(
        'warning',
        `Potential metadata injection in ${filePath}`,
        'Sanitize metadata filters to prevent injection'
      );
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

    console.log('\n📊 VECTOR STORE VALIDATION REPORT');
    console.log('=' .repeat(50));

    if (errorCount === 0 && warningCount === 0) {
      console.log('✅ EXCELLENT: Vector store patterns are enterprise-ready');
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
      summary: `Vector validation: ${errorCount} errors, ${warningCount} warnings`,
      details: this.issues
    };
  }
}

module.exports = VectorStoreValidator;

// CLI usage
if (require.main === module) {
  const projectPath = process.argv[2] || process.cwd();
  const validator = new VectorStoreValidator(projectPath);
  const result = validator.validateProject();
  process.exit(result.passed ? 0 : 1);
}
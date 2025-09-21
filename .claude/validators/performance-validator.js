// Performance Validator for RAG Applications
// Validates: Monitoring, caching, latency, throughput, resource optimization

const fs = require("fs");
const path = require("path");

// Performance monitoring patterns
const PERFORMANCE_PATTERNS = {
  monitoring: {
    cloudwatch: [
      /CloudWatch/g,
      /cloudwatch/g,
      /AWS.*CloudWatch/g,
      /MetricData/g,
      /putMetricData/g,
    ],
    xray: [/X-Ray/g, /xray/g, /AWS.*X-Ray/g, /AWSXRay/g, /trace/gi],
    custom: [
      /performance\.mark/g,
      /performance\.measure/g,
      /performance\.now/g,
      /console\.time/g,
    ],
  },
  caching: {
    redis: [/redis/gi, /elasticache/gi, /Redis/g, /REDIS/g],
    memory: [/cache/gi, /Cache/g, /memoiz/gi, /lru.*cache/gi],
    cdn: [/CloudFront/g, /cloudfront/g, /CDN/g, /edge.*cache/gi],
  },
  database: {
    optimization: [
      /index/gi,
      /query.*optim/gi,
      /connection.*pool/gi,
      /batch.*query/gi,
    ],
    monitoring: [
      /slow.*query/gi,
      /query.*time/gi,
      /db.*performance/gi,
      /explain.*plan/gi,
    ],
  },
  rag: {
    embedding: [
      /embedding.*cache/gi,
      /vector.*cache/gi,
      /semantic.*cache/gi,
      /similarity.*cache/gi,
    ],
    retrieval: [
      /retrieval.*time/gi,
      /search.*performance/gi,
      /index.*performance/gi,
      /faiss.*performance/gi,
    ],
    generation: [
      /generation.*time/gi,
      /llm.*latency/gi,
      /token.*per.*second/gi,
      /response.*time/gi,
    ],
  },
};

// Performance thresholds
const PERFORMANCE_THRESHOLDS = {
  latency: {
    api: 200, // 200ms for API responses
    embedding: 500, // 500ms for embedding generation
    retrieval: 100, // 100ms for vector search
    generation: 2000, // 2s for LLM generation
  },
  throughput: {
    embeddings: 1000, // 1000 embeddings/minute
    queries: 100, // 100 queries/second
    documents: 10, // 10 documents/second processing
  },
  resource: {
    memory: 80, // 80% memory usage threshold
    cpu: 70, // 70% CPU usage threshold
    disk: 85, // 85% disk usage threshold
  },
};

// Resource optimization patterns
const OPTIMIZATION_PATTERNS = {
  lambda: {
    coldStart: [
      /warm.*up/gi,
      /keep.*alive/gi,
      /provisioned.*concurrency/gi,
      /container.*reuse/gi,
    ],
    memory: [
      /memory.*optimization/gi,
      /lambda.*layer/gi,
      /shared.*dependencies/gi,
    ],
  },
  database: {
    connection: [/connection.*pool/gi, /pool.*size/gi, /connection.*reuse/gi],
    query: [/prepared.*statement/gi, /batch.*operation/gi, /bulk.*insert/gi],
  },
  frontend: {
    bundling: [
      /code.*splitting/gi,
      /lazy.*load/gi,
      /tree.*shaking/gi,
      /bundle.*size/gi,
    ],
    caching: [/service.*worker/gi, /cache.*strategy/gi, /offline.*cache/gi],
  },
};

class PerformanceValidator {
  constructor(projectRoot) {
    this.projectRoot = projectRoot;
    this.issues = [];
    this.metrics = {};
  }

  validate() {
    console.log("🔍 Validating performance patterns for RAG applications...");

    this.validateMonitoring();
    this.validateCaching();
    this.validateRAGPerformance();
    this.validateResourceOptimization();
    this.validateLatencyPatterns();
    this.validateThroughputOptimization();
    this.analyzePerformanceMetrics();

    return this.generateReport();
  }

  validateMonitoring() {
    const files = this.findFiles([
      "*.js",
      "*.ts",
      "*.py",
      "*.yml",
      "*.yaml",
      "*.json",
    ]);

    let hasCloudWatch = false;
    let hasXRay = false;
    let hasCustomMetrics = false;

    files.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check for CloudWatch monitoring
        if (
          PERFORMANCE_PATTERNS.monitoring.cloudwatch.some((pattern) =>
            pattern.test(content),
          )
        ) {
          hasCloudWatch = true;
        }

        // Check for X-Ray tracing
        if (
          PERFORMANCE_PATTERNS.monitoring.xray.some((pattern) =>
            pattern.test(content),
          )
        ) {
          hasXRay = true;
        }

        // Check for custom performance metrics
        if (
          PERFORMANCE_PATTERNS.monitoring.custom.some((pattern) =>
            pattern.test(content),
          )
        ) {
          hasCustomMetrics = true;
          this.checkCustomMetrics(content, file);
        }
      } catch (error) {
        this.addIssue("error", `Cannot read file: ${file}`, error.message);
      }
    });

    if (!hasCloudWatch) {
      this.addIssue(
        "warning",
        "No CloudWatch monitoring detected",
        "Implement CloudWatch metrics for production monitoring",
      );
    }

    if (!hasXRay) {
      this.addIssue(
        "info",
        "No X-Ray tracing detected",
        "Consider X-Ray for distributed tracing in RAG pipelines",
      );
    }

    if (!hasCustomMetrics) {
      this.addIssue(
        "info",
        "No custom performance metrics detected",
        "Add performance measurements for RAG operations",
      );
    }
  }

  checkCustomMetrics(content, filePath) {
    // Check for comprehensive metrics
    const ragMetrics = [
      "embedding_time",
      "retrieval_time",
      "generation_time",
      "total_latency",
    ];
    const foundMetrics = ragMetrics.filter((metric) =>
      content.includes(metric),
    );

    if (foundMetrics.length < ragMetrics.length / 2) {
      this.addIssue(
        "info",
        `Limited RAG performance metrics: ${filePath}`,
        `Consider tracking: ${ragMetrics.join(", ")}`,
      );
    }

    // Check for error rate tracking
    if (!content.includes("error_rate") && !content.includes("failure_rate")) {
      this.addIssue(
        "warning",
        `No error rate tracking: ${filePath}`,
        "Track error rates for reliability monitoring",
      );
    }

    // Check for percentile tracking
    if (
      !content.includes("p95") &&
      !content.includes("p99") &&
      !content.includes("percentile")
    ) {
      this.addIssue(
        "info",
        `No percentile tracking: ${filePath}`,
        "Track p95/p99 latencies for performance SLAs",
      );
    }
  }

  validateCaching() {
    const files = this.findFiles(["*.js", "*.ts", "*.py"]);

    let hasRedis = false;
    let hasMemoryCache = false;
    let hasCDN = false;

    files.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check for Redis/ElastiCache
        if (
          PERFORMANCE_PATTERNS.caching.redis.some((pattern) =>
            pattern.test(content),
          )
        ) {
          hasRedis = true;
          this.checkRedisCaching(content, file);
        }

        // Check for memory caching
        if (
          PERFORMANCE_PATTERNS.caching.memory.some((pattern) =>
            pattern.test(content),
          )
        ) {
          hasMemoryCache = true;
          this.checkMemoryCaching(content, file);
        }

        // Check for CDN usage
        if (
          PERFORMANCE_PATTERNS.caching.cdn.some((pattern) =>
            pattern.test(content),
          )
        ) {
          hasCDN = true;
        }
      } catch (error) {
        this.addIssue("error", `Cannot read file: ${file}`, error.message);
      }
    });

    if (!hasRedis && !hasMemoryCache) {
      this.addIssue(
        "warning",
        "No caching strategy detected",
        "Implement caching for embeddings and search results",
      );
    }

    if (!hasCDN) {
      this.addIssue(
        "info",
        "No CDN detected",
        "Consider CloudFront for static asset delivery",
      );
    }
  }

  checkRedisCaching(content, filePath) {
    // Check for connection pooling
    if (!content.includes("pool") && !content.includes("Pool")) {
      this.addIssue(
        "warning",
        `Redis without connection pooling: ${filePath}`,
        "Use connection pooling for better Redis performance",
      );
    }

    // Check for cache expiration
    if (
      !content.includes("expire") &&
      !content.includes("ttl") &&
      !content.includes("EX")
    ) {
      this.addIssue(
        "error",
        `Redis cache without expiration: ${filePath}`,
        "Set appropriate TTL for cached data",
      );
    }

    // Check for error handling
    if (!content.includes("catch") && !content.includes("error")) {
      this.addIssue(
        "warning",
        `Redis operations without error handling: ${filePath}`,
        "Handle Redis connection failures gracefully",
      );
    }
  }

  checkMemoryCaching(content, filePath) {
    // Check for cache size limits
    if (
      !content.includes("maxSize") &&
      !content.includes("max.*size") &&
      !content.includes("limit")
    ) {
      this.addIssue(
        "warning",
        `Memory cache without size limits: ${filePath}`,
        "Set memory cache size limits to prevent memory leaks",
      );
    }

    // Check for LRU eviction
    if (
      content.includes("cache") &&
      !content.includes("lru") &&
      !content.includes("LRU")
    ) {
      this.addIssue(
        "info",
        `Memory cache without LRU eviction: ${filePath}`,
        "Consider LRU cache for automatic cleanup",
      );
    }
  }

  validateRAGPerformance() {
    const files = this.findFiles(["*.js", "*.ts", "*.py"]);

    files.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check embedding performance
        this.checkEmbeddingPerformance(content, file);

        // Check retrieval performance
        this.checkRetrievalPerformance(content, file);

        // Check generation performance
        this.checkGenerationPerformance(content, file);
      } catch (error) {
        this.addIssue("error", `Cannot read file: ${file}`, error.message);
      }
    });
  }

  checkEmbeddingPerformance(content, filePath) {
    if (
      PERFORMANCE_PATTERNS.rag.embedding.some((pattern) =>
        pattern.test(content),
      ) ||
      content.includes("embedding") ||
      content.includes("embed")
    ) {
      // Check for batch processing
      if (
        !content.includes("batch") &&
        content.includes("for") &&
        content.includes("embed")
      ) {
        this.addIssue(
          "error",
          `Individual embedding calls: ${filePath}`,
          "Use batch embedding for better performance",
        );
      }

      // Check for embedding caching
      if (!content.includes("cache") && !content.includes("Cache")) {
        this.addIssue(
          "warning",
          `No embedding caching: ${filePath}`,
          "Cache embeddings to avoid recomputation",
        );
      }

      // Check for async processing
      if (
        !content.includes("async") &&
        !content.includes("await") &&
        !content.includes("Promise")
      ) {
        this.addIssue(
          "info",
          `Synchronous embedding processing: ${filePath}`,
          "Use async processing for better throughput",
        );
      }
    }
  }

  checkRetrievalPerformance(content, filePath) {
    if (
      PERFORMANCE_PATTERNS.rag.retrieval.some((pattern) =>
        pattern.test(content),
      ) ||
      content.includes("search") ||
      content.includes("retriev")
    ) {
      // Check for index optimization
      if (!content.includes("index") && !content.includes("Index")) {
        this.addIssue(
          "warning",
          `No search index optimization: ${filePath}`,
          "Optimize vector search indexes for performance",
        );
      }

      // Check for result limiting
      if (
        !content.includes("limit") &&
        !content.includes("top_k") &&
        !content.includes("topK")
      ) {
        this.addIssue(
          "error",
          `No result limiting in search: ${filePath}`,
          "Limit search results to improve performance",
        );
      }

      // Check for parallel search
      if (
        content.includes("multiple") &&
        !content.includes("parallel") &&
        !content.includes("concurrent")
      ) {
        this.addIssue(
          "info",
          `Sequential multiple searches: ${filePath}`,
          "Use parallel search for multiple queries",
        );
      }
    }
  }

  checkGenerationPerformance(content, filePath) {
    if (
      PERFORMANCE_PATTERNS.rag.generation.some((pattern) =>
        pattern.test(content),
      ) ||
      content.includes("generate") ||
      content.includes("llm") ||
      content.includes("claude")
    ) {
      // Check for streaming
      if (!content.includes("stream") && !content.includes("Stream")) {
        this.addIssue(
          "info",
          `No streaming for generation: ${filePath}`,
          "Use streaming for better perceived performance",
        );
      }

      // Check for timeout handling
      if (!content.includes("timeout") && !content.includes("Timeout")) {
        this.addIssue(
          "warning",
          `No timeout for generation: ${filePath}`,
          "Set timeouts for LLM generation calls",
        );
      }

      // Check for token optimization
      if (!content.includes("maxTokens") && !content.includes("max_tokens")) {
        this.addIssue(
          "warning",
          `No token limits for generation: ${filePath}`,
          "Set appropriate token limits for performance",
        );
      }
    }
  }

  validateResourceOptimization() {
    const files = this.findFiles(["*.js", "*.ts", "*.py", "*.json", "*.yml"]);

    files.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check Lambda optimizations
        this.checkLambdaOptimization(content, file);

        // Check database optimizations
        this.checkDatabaseOptimization(content, file);

        // Check frontend optimizations
        this.checkFrontendOptimization(content, file);
      } catch (error) {
        this.addIssue("error", `Cannot read file: ${file}`, error.message);
      }
    });
  }

  checkLambdaOptimization(content, filePath) {
    if (content.includes("lambda") || content.includes("Lambda")) {
      // Check for cold start optimization
      if (
        !OPTIMIZATION_PATTERNS.lambda.coldStart.some((pattern) =>
          pattern.test(content),
        )
      ) {
        this.addIssue(
          "info",
          `No cold start optimization: ${filePath}`,
          "Implement Lambda warming or provisioned concurrency",
        );
      }

      // Check for memory optimization
      if (
        !OPTIMIZATION_PATTERNS.lambda.memory.some((pattern) =>
          pattern.test(content),
        )
      ) {
        this.addIssue(
          "info",
          `No memory optimization patterns: ${filePath}`,
          "Use Lambda layers and optimize memory allocation",
        );
      }
    }
  }

  checkDatabaseOptimization(content, filePath) {
    if (
      content.includes("database") ||
      content.includes("db") ||
      content.includes("mongo") ||
      content.includes("sql")
    ) {
      // Check for connection pooling
      if (
        !OPTIMIZATION_PATTERNS.database.connection.some((pattern) =>
          pattern.test(content),
        )
      ) {
        this.addIssue(
          "warning",
          `No database connection pooling: ${filePath}`,
          "Use connection pooling for better database performance",
        );
      }

      // Check for query optimization
      if (
        !OPTIMIZATION_PATTERNS.database.query.some((pattern) =>
          pattern.test(content),
        )
      ) {
        this.addIssue(
          "info",
          `No query optimization patterns: ${filePath}`,
          "Use prepared statements and batch operations",
        );
      }
    }
  }

  checkFrontendOptimization(content, filePath) {
    if (
      filePath.includes("angular") ||
      filePath.includes("component") ||
      filePath.includes("service")
    ) {
      // Check for bundling optimizations
      if (
        !OPTIMIZATION_PATTERNS.frontend.bundling.some((pattern) =>
          pattern.test(content),
        )
      ) {
        this.addIssue(
          "info",
          `No frontend bundling optimizations: ${filePath}`,
          "Implement code splitting and lazy loading",
        );
      }

      // Check for caching strategies
      if (
        !OPTIMIZATION_PATTERNS.frontend.caching.some((pattern) =>
          pattern.test(content),
        )
      ) {
        this.addIssue(
          "info",
          `No frontend caching strategy: ${filePath}`,
          "Implement service worker and cache strategies",
        );
      }
    }
  }

  validateLatencyPatterns() {
    const files = this.findFiles(["*.js", "*.ts", "*.py"]);

    files.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check for latency measurement
        if (
          content.includes("performance") ||
          content.includes("time") ||
          content.includes("latency")
        ) {
          this.checkLatencyMeasurement(content, file);
        }
      } catch (error) {
        this.addIssue("error", `Cannot read file: ${file}`, error.message);
      }
    });
  }

  checkLatencyMeasurement(content, filePath) {
    // Check for comprehensive timing
    const timingMethods = [
      "performance.now",
      "Date.now",
      "process.hrtime",
      "time.time",
    ];
    const hasTimingMethod = timingMethods.some((method) =>
      content.includes(method),
    );

    if (!hasTimingMethod) {
      this.addIssue(
        "info",
        `No precise timing measurement: ${filePath}`,
        "Use high-resolution timing for accurate measurements",
      );
    }

    // Check for latency thresholds
    if (
      !content.includes("threshold") &&
      !content.includes("sla") &&
      !content.includes("target")
    ) {
      this.addIssue(
        "warning",
        `No latency thresholds defined: ${filePath}`,
        "Define performance SLAs and alert thresholds",
      );
    }
  }

  validateThroughputOptimization() {
    const files = this.findFiles(["*.js", "*.ts", "*.py"]);

    files.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check for concurrent processing
        if (
          content.includes("process") &&
          !content.includes("parallel") &&
          !content.includes("concurrent")
        ) {
          this.addIssue(
            "info",
            `Sequential processing detected: ${filePath}`,
            "Consider parallel processing for higher throughput",
          );
        }

        // Check for queue-based processing
        if (
          content.includes("process") &&
          !content.includes("queue") &&
          !content.includes("Queue")
        ) {
          this.addIssue(
            "info",
            `No queue-based processing: ${filePath}`,
            "Use queues for better throughput and reliability",
          );
        }
      } catch (error) {
        this.addIssue("error", `Cannot read file: ${file}`, error.message);
      }
    });
  }

  analyzePerformanceMetrics() {
    // Analyze collected metrics and provide insights
    this.metrics = {
      monitoring: {
        hasCloudWatch: false,
        hasXRay: false,
        hasCustomMetrics: false,
      },
      caching: {
        hasRedis: false,
        hasMemoryCache: false,
        hasCDN: false,
      },
      optimization: {
        hasAsyncProcessing: false,
        hasBatching: false,
        hasParallelization: false,
      },
    };

    // This would be populated during validation
    // For now, we'll provide general recommendations
  }

  findFiles(patterns) {
    const files = [];

    const searchDir = (dir) => {
      try {
        const entries = fs.readdirSync(dir, { withFileTypes: true });

        entries.forEach((entry) => {
          const fullPath = path.join(dir, entry.name);

          if (
            entry.isDirectory() &&
            !entry.name.startsWith(".") &&
            entry.name !== "node_modules"
          ) {
            searchDir(fullPath);
          } else if (entry.isFile()) {
            patterns.forEach((pattern) => {
              if (pattern.startsWith("*")) {
                if (entry.name.endsWith(pattern.slice(1))) {
                  files.push(fullPath);
                }
              } else if (entry.name === pattern) {
                files.push(fullPath);
              }
            });
          }
        });
      } catch (error) {
        // Directory not accessible
      }
    };

    searchDir(this.projectRoot);
    return files;
  }

  addIssue(severity, message, suggestion = "") {
    this.issues.push({ severity, message, suggestion });
  }

  generateReport() {
    const report = {
      validator: "Performance Validator",
      timestamp: new Date().toISOString(),
      summary: {
        total: this.issues.length,
        critical: this.issues.filter((i) => i.severity === "critical").length,
        errors: this.issues.filter((i) => i.severity === "error").length,
        warnings: this.issues.filter((i) => i.severity === "warning").length,
        info: this.issues.filter((i) => i.severity === "info").length,
      },
      thresholds: PERFORMANCE_THRESHOLDS,
      metrics: this.metrics,
      issues: this.issues,
    };

    // Print summary
    console.log("\n📊 Performance Validation Results:");
    console.log(`  Critical: ${report.summary.critical}`);
    console.log(`  Errors: ${report.summary.errors}`);
    console.log(`  Warnings: ${report.summary.warnings}`);
    console.log(`  Info: ${report.summary.info}`);

    // Print performance recommendations
    console.log("\n🚀 Performance Recommendations:");
    console.log("  - Cache embeddings and search results");
    console.log("  - Use batch processing for embeddings");
    console.log("  - Implement streaming for LLM responses");
    console.log("  - Monitor latency with CloudWatch");
    console.log("  - Set up performance alerts");

    // Print critical and error issues
    this.issues.forEach((issue) => {
      if (issue.severity === "critical" || issue.severity === "error") {
        console.log(`\n❌ ${issue.severity.toUpperCase()}: ${issue.message}`);
        if (issue.suggestion) {
          console.log(`   💡 ${issue.suggestion}`);
        }
      }
    });

    return report;
  }
}

// Export for use in CCOM workflows
module.exports = PerformanceValidator;

// Allow direct execution
if (require.main === module) {
  const validator = new PerformanceValidator(process.cwd());
  const report = validator.validate();

  if (report.summary.critical > 0 || report.summary.errors > 0) {
    process.exit(1);
  }
}

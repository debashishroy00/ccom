// AWS Cost Optimization Validator for RAG Applications
// Validates: Bedrock costs, S3 storage costs, ECS pricing, Lambda optimization

const fs = require("fs");
const path = require("path");

// AWS service pricing (as of 2024, approximate)
const AWS_PRICING = {
  bedrock: {
    "claude-3-opus": {
      inputCost: 0.015, // per 1K input tokens
      outputCost: 0.075, // per 1K output tokens
    },
    "claude-3-sonnet": {
      inputCost: 0.003, // per 1K input tokens
      outputCost: 0.015, // per 1K output tokens
    },
    "claude-3-haiku": {
      inputCost: 0.00025, // per 1K input tokens
      outputCost: 0.00125, // per 1K output tokens
    },
    "titan-embed-text-v1": {
      cost: 0.0001, // per 1K input tokens
    },
    "titan-embed-text-v2": {
      cost: 0.00002, // per 1K input tokens
    },
  },
  s3: {
    storage: 0.023, // per GB/month Standard
    requests: 0.0004, // per 1K PUT requests
    transfer: 0.09, // per GB data transfer out
  },
  ecs: {
    fargate: {
      cpu: 0.04048, // per vCPU/hour
      memory: 0.004445, // per GB/hour
    },
  },
  lambda: {
    requests: 0.0000002, // per request
    duration: 0.0000166667, // per GB-second
  },
  apiGateway: {
    requests: 0.0000035, // per request
  },
};

// Cost optimization patterns
const COST_PATTERNS = {
  bedrock: {
    inefficient: [
      /claude-3-opus.*batch/i, // Using expensive model for bulk
      /maxTokens:\s*[5-9]\d{3,}/, // Very high token limits
      /temperature:\s*0\.9[5-9]/, // Unnecessarily high temperature
    ],
    optimization: [
      /claude-3-haiku/i, // Using cheaper model
      /batch.*embed/i, // Batch embedding calls
      /cache.*response/i, // Response caching
    ],
  },
  monitoring: {
    required: [
      /CloudWatch.*Cost/i,
      /AWS.*Budget/i,
      /billing.*alert/i,
      /cost.*explorer/i,
    ],
    tags: [/cost.*center/i, /project.*tag/i, /environment.*tag/i],
  },
  s3: {
    inefficient: [
      /Standard.*storage/i, // Not using cheaper storage classes
      /frequent.*access/i, // Frequent access for infrequent data
      /no.*lifecycle/i, // No lifecycle policies
    ],
    optimization: [
      /lifecycle.*policy/i,
      /intelligent.*tiering/i,
      /glacier/i,
      /deep.*archive/i,
    ],
  },
  lambda: {
    inefficient: [
      /memory.*3008/, // Maximum memory allocation
      /timeout.*900/, // Maximum timeout
      /provisioned.*concurrency/, // Unnecessary provisioned concurrency
    ],
    optimization: [
      /memory.*optimization/i,
      /cold.*start.*optimization/i,
      /layer.*reuse/i,
    ],
  },
};

// Resource usage thresholds
const THRESHOLDS = {
  bedrock: {
    dailyTokens: 1000000, // 1M tokens/day
    monthlyRequests: 100000, // 100K requests/month
    avgResponseTokens: 1000, // Average response size
  },
  s3: {
    monthlyGB: 1000, // 1TB/month
    requestsPerGB: 10000, // Requests per GB
    transferGB: 100, // 100GB transfer/month
  },
  lambda: {
    monthlyInvocations: 1000000, // 1M invocations/month
    avgDurationMs: 5000, // 5 second average
    memoryMB: 1024, // 1GB memory
  },
};

class AWSCostValidator {
  constructor(projectRoot) {
    this.projectRoot = projectRoot;
    this.issues = [];
    this.costEstimates = {};
  }

  validate() {
    console.log("🔍 Validating AWS cost optimization patterns...");

    this.validateBedrockCosts();
    this.validateS3Costs();
    this.validateLambdaCosts();
    this.validateECSCosts();
    this.validateMonitoring();
    this.calculateCostEstimates();

    return this.generateReport();
  }

  validateBedrockCosts() {
    const files = this.findFiles(["*.js", "*.ts", "*.py"]);

    files.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check Bedrock model usage
        this.checkBedrockModelUsage(content, file);

        // Check token limits
        this.checkTokenLimits(content, file);

        // Check batch processing
        this.checkBatchProcessing(content, file);

        // Check caching strategies
        this.checkCachingStrategies(content, file);
      } catch (error) {
        this.addIssue("error", `Cannot read file: ${file}`, error.message);
      }
    });
  }

  checkBedrockModelUsage(content, filePath) {
    // Check for expensive model usage
    if (content.includes("claude-3-opus")) {
      this.addIssue(
        "warning",
        `Using expensive Claude-3-Opus model: ${filePath}`,
        "Consider Claude-3-Sonnet or Haiku for cost optimization",
      );

      // Check if used for simple tasks
      if (
        content.includes("simple") ||
        content.includes("basic") ||
        content.includes("summary")
      ) {
        this.addIssue(
          "error",
          `Claude-3-Opus used for simple tasks: ${filePath}`,
          "Use Claude-3-Haiku for simple tasks to reduce costs by 60x",
        );
      }
    }

    // Check for model selection logic
    if (!content.includes("model") || !content.includes("selection")) {
      if (content.includes("bedrock") || content.includes("claude")) {
        this.addIssue(
          "info",
          `No dynamic model selection: ${filePath}`,
          "Implement logic to choose cheaper models for simpler tasks",
        );
      }
    }

    // Check for cost tracking
    if (
      content.includes("claude") &&
      !content.includes("cost") &&
      !content.includes("track")
    ) {
      this.addIssue(
        "warning",
        `No cost tracking for Bedrock usage: ${filePath}`,
        "Add cost tracking to monitor AI spending",
      );
    }
  }

  checkTokenLimits(content, filePath) {
    // Check for excessive token limits
    const maxTokensMatch = content.match(/maxTokens?\s*:?\s*(\d+)/i);
    if (maxTokensMatch) {
      const tokens = parseInt(maxTokensMatch[1]);

      if (tokens > 4000) {
        this.addIssue(
          "warning",
          `High token limit (${tokens}): ${filePath}`,
          "High token limits increase costs significantly",
        );
      }

      if (tokens > 8000) {
        this.addIssue(
          "error",
          `Very high token limit (${tokens}): ${filePath}`,
          "Reduce maxTokens or implement pagination for cost control",
        );
      }
    }

    // Check for dynamic token adjustment
    if (
      content.includes("maxTokens") &&
      !content.includes("adjust") &&
      !content.includes("dynamic")
    ) {
      this.addIssue(
        "info",
        `Static token limits: ${filePath}`,
        "Consider dynamic token adjustment based on request complexity",
      );
    }
  }

  checkBatchProcessing(content, filePath) {
    // Check for individual embedding calls
    if (
      content.includes("embed") &&
      content.includes("for") &&
      !content.includes("batch")
    ) {
      this.addIssue(
        "error",
        `Individual embedding calls in loop: ${filePath}`,
        "Use batch embedding to reduce API calls and costs",
      );
    }

    // Check for proper batching
    if (content.includes("batch") && content.includes("embed")) {
      // Check batch size
      const batchSizeMatch = content.match(/batch.*size.*?(\d+)/i);
      if (batchSizeMatch) {
        const batchSize = parseInt(batchSizeMatch[1]);

        if (batchSize < 10) {
          this.addIssue(
            "warning",
            `Small batch size (${batchSize}): ${filePath}`,
            "Increase batch size to reduce per-request overhead",
          );
        }

        if (batchSize > 25) {
          this.addIssue(
            "error",
            `Batch size exceeds limit (${batchSize}): ${filePath}`,
            "Titan embedding batch limit is 25",
          );
        }
      }
    }
  }

  checkCachingStrategies(content, filePath) {
    // Check for embedding caching
    if (content.includes("embedding") && !content.includes("cache")) {
      this.addIssue(
        "warning",
        `No embedding caching: ${filePath}`,
        "Cache embeddings to avoid recomputing identical content",
      );
    }

    // Check for response caching
    if (content.includes("bedrock") && content.includes("chat")) {
      if (!content.includes("cache") && !content.includes("memoiz")) {
        this.addIssue(
          "info",
          `No response caching for chat: ${filePath}`,
          "Cache responses for identical queries to reduce costs",
        );
      }
    }

    // Check cache expiration
    if (
      content.includes("cache") &&
      !content.includes("ttl") &&
      !content.includes("expir")
    ) {
      this.addIssue(
        "warning",
        `Cache without expiration: ${filePath}`,
        "Set cache TTL to balance freshness and cost savings",
      );
    }
  }

  validateS3Costs() {
    const configFiles = this.findFiles(["*.yml", "*.yaml", "*.json", "*.tf"]);

    configFiles.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        if (content.includes("s3") || content.includes("S3")) {
          this.checkS3StorageClass(content, file);
          this.checkS3LifecyclePolicies(content, file);
          this.checkS3RequestOptimization(content, file);
        }
      } catch (error) {
        // File reading error
      }
    });
  }

  checkS3StorageClass(content, filePath) {
    // Check for Standard storage class usage
    if (content.includes("STANDARD") && !content.includes("INTELLIGENT")) {
      this.addIssue(
        "warning",
        `Using S3 Standard storage: ${filePath}`,
        "Consider Intelligent Tiering for automatic cost optimization",
      );
    }

    // Check for infrequent access patterns
    if (content.includes("archive") || content.includes("backup")) {
      if (!content.includes("GLACIER") && !content.includes("DEEP_ARCHIVE")) {
        this.addIssue(
          "error",
          `Archive data in expensive storage: ${filePath}`,
          "Use Glacier or Deep Archive for long-term storage",
        );
      }
    }
  }

  checkS3LifecyclePolicies(content, filePath) {
    // Check for lifecycle policies
    if (content.includes("s3") && !content.includes("lifecycle")) {
      this.addIssue(
        "warning",
        `S3 bucket without lifecycle policies: ${filePath}`,
        "Implement lifecycle policies for automatic cost optimization",
      );
    }

    // Check for intelligent tiering
    if (!content.includes("INTELLIGENT_TIERING")) {
      this.addIssue(
        "info",
        `No Intelligent Tiering configured: ${filePath}`,
        "Enable Intelligent Tiering for automatic storage optimization",
      );
    }
  }

  checkS3RequestOptimization(content, filePath) {
    // Check for frequent small uploads
    if (content.includes("putObject") && content.includes("small")) {
      this.addIssue(
        "warning",
        `Frequent small S3 uploads: ${filePath}`,
        "Batch small uploads to reduce request costs",
      );
    }

    // Check for multipart upload usage
    if (content.includes("upload") && !content.includes("multipart")) {
      this.addIssue(
        "info",
        `No multipart upload: ${filePath}`,
        "Use multipart upload for large files (>100MB)",
      );
    }
  }

  validateLambdaCosts() {
    const lambdaFiles = this.findFiles([
      "*lambda*.js",
      "*lambda*.py",
      "serverless.yml",
    ]);

    lambdaFiles.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        this.checkLambdaMemoryAllocation(content, file);
        this.checkLambdaTimeout(content, file);
        this.checkLambdaColdStarts(content, file);
      } catch (error) {
        this.addIssue(
          "error",
          `Cannot read Lambda file: ${file}`,
          error.message,
        );
      }
    });
  }

  checkLambdaMemoryAllocation(content, filePath) {
    const memoryMatch = content.match(/memory.*?(\d+)/i);
    if (memoryMatch) {
      const memory = parseInt(memoryMatch[1]);

      if (memory > 2048) {
        this.addIssue(
          "warning",
          `High Lambda memory allocation (${memory}MB): ${filePath}`,
          "Optimize memory allocation based on actual usage",
        );
      }

      if (memory === 3008) {
        this.addIssue(
          "error",
          `Maximum Lambda memory allocation: ${filePath}`,
          "Review if maximum memory is truly needed",
        );
      }
    }

    // Check for memory optimization
    if (!content.includes("memory") && content.includes("lambda")) {
      this.addIssue(
        "info",
        `No explicit memory configuration: ${filePath}`,
        "Configure optimal memory to balance performance and cost",
      );
    }
  }

  checkLambdaTimeout(content, filePath) {
    const timeoutMatch = content.match(/timeout.*?(\d+)/i);
    if (timeoutMatch) {
      const timeout = parseInt(timeoutMatch[1]);

      if (timeout > 300) {
        this.addIssue(
          "warning",
          `Long Lambda timeout (${timeout}s): ${filePath}`,
          "Long timeouts increase cost for hanging functions",
        );
      }

      if (timeout === 900) {
        this.addIssue(
          "error",
          `Maximum Lambda timeout: ${filePath}`,
          "Consider breaking down into smaller functions",
        );
      }
    }
  }

  checkLambdaColdStarts(content, filePath) {
    // Check for provisioned concurrency
    if (content.includes("provisionedConcurrency")) {
      this.addIssue(
        "warning",
        `Provisioned concurrency configured: ${filePath}`,
        "Provisioned concurrency is expensive, ensure its necessary",
      );
    }

    // Check for cold start optimization
    if (!content.includes("warm") && !content.includes("keepAlive")) {
      this.addIssue(
        "info",
        `No cold start optimization: ${filePath}`,
        "Implement warming strategies to reduce cold start costs",
      );
    }
  }

  validateECSCosts() {
    const ecsFiles = this.findFiles([
      "*ecs*.json",
      "*task-def*.json",
      "*fargate*.json",
    ]);

    ecsFiles.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");
        const config = JSON.parse(content);

        this.checkECSResourceAllocation(config, file);
      } catch (error) {
        // Not JSON or parsing error
      }
    });
  }

  checkECSResourceAllocation(config, filePath) {
    // Check CPU and memory allocation
    if (config.cpu && config.memory) {
      const cpu = parseInt(config.cpu);
      const memory = parseInt(config.memory);

      // Check for oversized allocations
      if (cpu >= 2048 || memory >= 8192) {
        this.addIssue(
          "warning",
          `Large ECS resource allocation: ${filePath}`,
          "Review if large resources are needed for RAG workloads",
        );
      }

      // Check CPU:Memory ratio efficiency
      const ratio = memory / cpu;
      if (ratio < 2 || ratio > 8) {
        this.addIssue(
          "info",
          `Inefficient CPU:Memory ratio (${ratio.toFixed(1)}): ${filePath}`,
          "Optimize CPU:Memory ratio for cost efficiency",
        );
      }
    }

    // Check for auto-scaling
    if (
      !JSON.stringify(config).includes("autoScaling") &&
      !JSON.stringify(config).includes("scaling")
    ) {
      this.addIssue(
        "warning",
        `No auto-scaling configured: ${filePath}`,
        "Configure auto-scaling to optimize costs based on demand",
      );
    }
  }

  validateMonitoring() {
    const files = this.findFiles(["*.yml", "*.yaml", "*.json", "*.tf"]);

    let hasMonitoring = false;
    let hasBudgets = false;
    let hasAlerts = false;

    files.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check for cost monitoring
        if (content.includes("CloudWatch") && content.includes("cost")) {
          hasMonitoring = true;
        }

        if (content.includes("Budget") || content.includes("billing")) {
          hasBudgets = true;
        }

        if (content.includes("alarm") && content.includes("cost")) {
          hasAlerts = true;
        }
      } catch (error) {
        // File reading error
      }
    });

    if (!hasMonitoring) {
      this.addIssue(
        "error",
        "No cost monitoring configured",
        "Set up CloudWatch billing metrics and Cost Explorer",
      );
    }

    if (!hasBudgets) {
      this.addIssue(
        "warning",
        "No AWS budgets configured",
        "Create budgets to track and limit spending",
      );
    }

    if (!hasAlerts) {
      this.addIssue(
        "warning",
        "No cost alerts configured",
        "Set up billing alarms for cost overruns",
      );
    }
  }

  calculateCostEstimates() {
    // Estimate based on typical RAG usage patterns
    this.costEstimates = {
      bedrock: {
        monthly: {
          "claude-3-sonnet": 150, // $150/month typical
          "titan-embed": 20, // $20/month for embeddings
        },
      },
      s3: {
        monthly: 50, // $50/month for document storage
      },
      lambda: {
        monthly: 25, // $25/month for processing
      },
      total: 245, // $245/month estimated
    };
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
              } else if (pattern.endsWith("*")) {
                if (entry.name.startsWith(pattern.slice(0, -1))) {
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
      validator: "AWS Cost Optimization Validator",
      timestamp: new Date().toISOString(),
      summary: {
        total: this.issues.length,
        critical: this.issues.filter((i) => i.severity === "critical").length,
        errors: this.issues.filter((i) => i.severity === "error").length,
        warnings: this.issues.filter((i) => i.severity === "warning").length,
        info: this.issues.filter((i) => i.severity === "info").length,
      },
      costEstimates: this.costEstimates,
      issues: this.issues,
    };

    // Print summary
    console.log("\n📊 AWS Cost Optimization Results:");
    console.log(`  Critical: ${report.summary.critical}`);
    console.log(`  Errors: ${report.summary.errors}`);
    console.log(`  Warnings: ${report.summary.warnings}`);
    console.log(`  Info: ${report.summary.info}`);

    // Print cost estimates
    if (this.costEstimates.total) {
      console.log(`\n💰 Estimated Monthly Cost: $${this.costEstimates.total}`);
      console.log(
        `  Bedrock: $${this.costEstimates.bedrock.monthly["claude-3-sonnet"] + this.costEstimates.bedrock.monthly["titan-embed"]}`,
      );
      console.log(`  S3: $${this.costEstimates.s3.monthly}`);
      console.log(`  Lambda: $${this.costEstimates.lambda.monthly}`);
    }

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
module.exports = AWSCostValidator;

// Allow direct execution
if (require.main === module) {
  const validator = new AWSCostValidator(process.cwd());
  const report = validator.validate();

  if (report.summary.critical > 0 || report.summary.errors > 0) {
    process.exit(1);
  }
}

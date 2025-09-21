// AWS Bedrock & LangChain Validation for Enterprise RAG Systems
// Validates: Bedrock configuration, LangChain patterns, Titan embeddings, Claude models

const fs = require("fs");
const path = require("path");

// AWS Bedrock configuration patterns
const BEDROCK_PATTERNS = {
  client: {
    patterns: [
      /new\s+BedrockClient/i,
      /new\s+BedrockRuntimeClient/i,
      /BedrockEmbeddings/i,
      /BedrockChat/i,
    ],
    required: ["region", "credentials"],
  },
  models: {
    "claude-3-sonnet": {
      maxTokens: 200000,
      temperature: [0, 1],
      topP: [0, 1],
    },
    "claude-3-haiku": {
      maxTokens: 200000,
      temperature: [0, 1],
      topP: [0, 1],
    },
    "claude-3-opus": {
      maxTokens: 200000,
      temperature: [0, 1],
      topP: [0, 1],
    },
    "titan-embed-text-v1": {
      dimensions: 1536,
      maxBatchSize: 25,
    },
    "titan-embed-text-v2": {
      dimensions: 1024,
      maxBatchSize: 25,
    },
  },
};

// LangChain patterns
const LANGCHAIN_PATTERNS = {
  chains: [
    /ConversationChain/i,
    /RetrievalQA/i,
    /ConversationalRetrievalChain/i,
    /LLMChain/i,
    /SequentialChain/i,
  ],
  memory: [
    /ConversationBufferMemory/i,
    /ConversationSummaryMemory/i,
    /VectorStoreRetrieverMemory/i,
  ],
  loaders: [/S3Loader/i, /PDFLoader/i, /JSONLoader/i, /TextLoader/i],
  vectorStores: [
    /ChromaDB/i,
    /MongoDBAtlasVectorSearch/i,
    /FAISS/i,
    /Pinecone/i,
  ],
};

// Security patterns
const SECURITY_ISSUES = {
  credentials: [
    /aws_access_key_id\s*=\s*["'][\w]+/i,
    /aws_secret_access_key\s*=\s*["'][\w]+/i,
    /AWS_ACCESS_KEY_ID\s*=\s*["'][\w]+/i,
    /AWS_SECRET_ACCESS_KEY\s*=\s*["'][\w]+/i,
  ],
  s3Patterns: [
    /s3:\/\/.*\/\*/, // Wildcard S3 access
    /PublicRead/i, // Public bucket access
    /PublicReadWrite/i,
  ],
};

class AWSBedrockValidator {
  constructor(projectRoot) {
    this.projectRoot = projectRoot;
    this.issues = [];
  }

  validate() {
    console.log("🔍 Validating AWS Bedrock & LangChain patterns...");

    this.validateBedrockConfiguration();
    this.validateLangChainPatterns();
    this.validateSecurityPatterns();
    this.validateS3Configuration();
    this.validateLambdaFunctions();
    this.validateECSTaskDefinitions();

    return this.generateReport();
  }

  validateBedrockConfiguration() {
    const jsFiles = this.findFiles(["*.js", "*.ts", "*.py"]);

    jsFiles.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check for Bedrock client initialization
        this.checkBedrockClient(content, file);

        // Check for proper model configuration
        this.checkModelConfiguration(content, file);

        // Check for embedding configuration
        this.checkEmbeddingConfiguration(content, file);
      } catch (error) {
        this.addIssue("error", `Cannot read file: ${file}`, error.message);
      }
    });
  }

  checkBedrockClient(content, filePath) {
    // Check for Bedrock client patterns
    let hasBedrockClient = false;
    BEDROCK_PATTERNS.client.patterns.forEach((pattern) => {
      if (pattern.test(content)) {
        hasBedrockClient = true;

        // Check for required configuration
        if (!content.includes("region")) {
          this.addIssue(
            "error",
            `Missing AWS region in Bedrock client: ${filePath}`,
            "Specify region in Bedrock client configuration",
          );
        }

        // Check for credentials
        if (
          !content.includes("credentials") &&
          !content.includes("fromIni") &&
          !content.includes("fromEnv")
        ) {
          this.addIssue(
            "warning",
            `No explicit credential provider in: ${filePath}`,
            "Use AWS credential provider chain or IAM roles",
          );
        }
      }
    });

    // Check for retry configuration
    if (hasBedrockClient && !content.includes("maxAttempts")) {
      this.addIssue(
        "warning",
        `No retry configuration for Bedrock client: ${filePath}`,
        "Configure maxAttempts and retryMode for resilience",
      );
    }
  }

  checkModelConfiguration(content, filePath) {
    // Check Claude model configuration
    const claudePattern = /modelId.*claude-3-(sonnet|haiku|opus)/i;
    if (claudePattern.test(content)) {
      // Check for proper parameters
      if (!content.includes("maxTokens") && !content.includes("max_tokens")) {
        this.addIssue(
          "warning",
          `Missing maxTokens configuration for Claude model: ${filePath}`,
          "Set maxTokens to control response length",
        );
      }

      // Check for temperature settings
      if (content.includes("temperature")) {
        const tempMatch = content.match(/temperature\s*:\s*([\d.]+)/);
        if (
          tempMatch &&
          (parseFloat(tempMatch[1]) > 1 || parseFloat(tempMatch[1]) < 0)
        ) {
          this.addIssue(
            "error",
            `Invalid temperature value in: ${filePath}`,
            "Temperature must be between 0 and 1",
          );
        }
      }
    }
  }

  checkEmbeddingConfiguration(content, filePath) {
    // Check Titan embeddings configuration
    const titanPattern = /titan-embed/i;
    if (titanPattern.test(content)) {
      // Check batch size
      const batchPattern = /batch.*size.*(\d+)/i;
      const batchMatch = content.match(batchPattern);
      if (batchMatch && parseInt(batchMatch[1]) > 25) {
        this.addIssue(
          "error",
          `Titan embedding batch size exceeds limit (25): ${filePath}`,
          "Reduce batch size to 25 or less",
        );
      }

      // Check for proper error handling
      if (!content.includes("try") && !content.includes("catch")) {
        this.addIssue(
          "warning",
          `No error handling for Titan embeddings: ${filePath}`,
          "Add try-catch for embedding API calls",
        );
      }
    }
  }

  validateLangChainPatterns() {
    const files = this.findFiles(["*.js", "*.ts", "*.py"]);

    files.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check for LangChain chains
        this.checkLangChainUsage(content, file);

        // Check memory management
        this.checkMemoryManagement(content, file);

        // Check loader patterns
        this.checkDataLoaders(content, file);
      } catch (error) {
        this.addIssue("error", `Cannot read file: ${file}`, error.message);
      }
    });
  }

  checkLangChainUsage(content, filePath) {
    let hasLangChain = false;

    LANGCHAIN_PATTERNS.chains.forEach((pattern) => {
      if (pattern.test(content)) {
        hasLangChain = true;

        // Check for proper chain configuration
        if (
          !content.includes("prompt") &&
          !content.includes("promptTemplate")
        ) {
          this.addIssue(
            "warning",
            `Missing prompt template in LangChain: ${filePath}`,
            "Define explicit prompt templates for chains",
          );
        }
      }
    });

    if (hasLangChain) {
      // Check for callback handlers
      if (
        !content.includes("callbacks") &&
        !content.includes("CallbackManager")
      ) {
        this.addIssue(
          "info",
          `No callback handlers in LangChain: ${filePath}`,
          "Consider adding callbacks for monitoring",
        );
      }
    }
  }

  checkMemoryManagement(content, filePath) {
    LANGCHAIN_PATTERNS.memory.forEach((pattern) => {
      if (pattern.test(content)) {
        // Check for memory limits
        if (
          !content.includes("maxTokenLimit") &&
          !content.includes("max_token_limit")
        ) {
          this.addIssue(
            "warning",
            `No memory limit configured: ${filePath}`,
            "Set maxTokenLimit to prevent memory overflow",
          );
        }

        // Check for memory persistence
        if (
          content.includes("ConversationBufferMemory") &&
          !content.includes("save_context") &&
          !content.includes("saveContext")
        ) {
          this.addIssue(
            "info",
            `Consider persisting conversation memory: ${filePath}`,
            "Implement memory persistence for production",
          );
        }
      }
    });
  }

  checkDataLoaders(content, filePath) {
    // Check S3 loader configuration
    if (/S3Loader/i.test(content)) {
      if (!content.includes("region")) {
        this.addIssue(
          "error",
          `S3Loader missing region configuration: ${filePath}`,
          "Specify AWS region for S3Loader",
        );
      }

      // Check for proper error handling
      if (!content.includes("onError") && !content.includes("catch")) {
        this.addIssue(
          "warning",
          `No error handling for S3Loader: ${filePath}`,
          "Add error handling for S3 operations",
        );
      }
    }
  }

  validateSecurityPatterns() {
    const files = this.findFiles([
      "*.js",
      "*.ts",
      "*.py",
      "*.env",
      "*.yml",
      "*.yaml",
    ]);

    files.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check for hardcoded credentials
        SECURITY_ISSUES.credentials.forEach((pattern) => {
          if (pattern.test(content)) {
            this.addIssue(
              "critical",
              `Hardcoded AWS credentials found: ${file}`,
              "Use IAM roles or environment variables",
            );
          }
        });

        // Check S3 security patterns
        SECURITY_ISSUES.s3Patterns.forEach((pattern) => {
          if (pattern.test(content)) {
            this.addIssue(
              "error",
              `Insecure S3 configuration: ${file}`,
              "Review S3 bucket policies and access controls",
            );
          }
        });
      } catch (error) {
        this.addIssue("error", `Cannot read file: ${file}`, error.message);
      }
    });
  }

  validateS3Configuration() {
    const configFiles = this.findFiles([
      "*.config.js",
      "*.config.ts",
      "serverless.yml",
      "template.yaml",
    ]);

    configFiles.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check for S3 bucket configuration
        if (content.includes("s3") || content.includes("S3")) {
          // Check for versioning
          if (
            !content.includes("Versioning") &&
            !content.includes("versioning")
          ) {
            this.addIssue(
              "warning",
              `S3 bucket versioning not configured: ${file}`,
              "Enable versioning for data protection",
            );
          }

          // Check for encryption
          if (
            !content.includes("ServerSideEncryption") &&
            !content.includes("encryption")
          ) {
            this.addIssue(
              "error",
              `S3 bucket encryption not configured: ${file}`,
              "Enable server-side encryption for S3 buckets",
            );
          }
        }
      } catch (error) {
        this.addIssue("error", `Cannot read file: ${file}`, error.message);
      }
    });
  }

  validateLambdaFunctions() {
    const lambdaFiles = this.findFiles([
      "*lambda*.js",
      "*lambda*.ts",
      "*handler*.js",
      "*handler*.ts",
    ]);

    lambdaFiles.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check for proper Lambda handler structure
        if (
          !content.includes("exports.handler") &&
          !content.includes("export const handler") &&
          !content.includes("def lambda_handler")
        ) {
          this.addIssue(
            "warning",
            `Lambda handler not properly exported: ${file}`,
            "Export handler function correctly",
          );
        }

        // Check for timeout handling
        if (!content.includes("context.getRemainingTimeInMillis")) {
          this.addIssue(
            "info",
            `No timeout monitoring in Lambda: ${file}`,
            "Monitor remaining execution time",
          );
        }

        // Check for cold start optimization
        if (!content.includes("warmup") && !content.includes("WARM")) {
          this.addIssue(
            "info",
            `Consider cold start optimization: ${file}`,
            "Implement Lambda warmup for better performance",
          );
        }
      } catch (error) {
        this.addIssue("error", `Cannot read file: ${file}`, error.message);
      }
    });
  }

  validateECSTaskDefinitions() {
    const taskDefFiles = this.findFiles([
      "*task-definition*.json",
      "*ecs*.json",
      "*fargate*.json",
    ]);

    taskDefFiles.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");
        const taskDef = JSON.parse(content);

        // Check memory and CPU configuration
        if (taskDef.memory && parseInt(taskDef.memory) < 512) {
          this.addIssue(
            "warning",
            `Low memory allocation for ECS task: ${file}`,
            "Consider increasing memory for RAG workloads",
          );
        }

        // Check for health checks
        if (!taskDef.healthCheck) {
          this.addIssue(
            "warning",
            `No health check configured: ${file}`,
            "Add health checks for container monitoring",
          );
        }

        // Check for logging configuration
        if (!content.includes("logConfiguration")) {
          this.addIssue(
            "error",
            `No logging configured for ECS task: ${file}`,
            "Configure CloudWatch logging",
          );
        }
      } catch (error) {
        // Not a JSON file or parsing error
      }
    });
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
      validator: "AWS Bedrock & LangChain Validator",
      timestamp: new Date().toISOString(),
      summary: {
        total: this.issues.length,
        critical: this.issues.filter((i) => i.severity === "critical").length,
        errors: this.issues.filter((i) => i.severity === "error").length,
        warnings: this.issues.filter((i) => i.severity === "warning").length,
        info: this.issues.filter((i) => i.severity === "info").length,
      },
      issues: this.issues,
    };

    // Print summary
    console.log("\n📊 AWS Bedrock & LangChain Validation Results:");
    console.log(`  Critical: ${report.summary.critical}`);
    console.log(`  Errors: ${report.summary.errors}`);
    console.log(`  Warnings: ${report.summary.warnings}`);
    console.log(`  Info: ${report.summary.info}`);

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
module.exports = AWSBedrockValidator;

// Allow direct execution
if (require.main === module) {
  const validator = new AWSBedrockValidator(process.cwd());
  const report = validator.validate();

  if (report.summary.critical > 0 || report.summary.errors > 0) {
    process.exit(1);
  }
}

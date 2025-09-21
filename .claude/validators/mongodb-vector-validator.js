// MongoDB Atlas Vector Search Validation
// Validates: Atlas Search indexes, vector configurations, aggregation pipelines

const fs = require("fs");
const path = require("path");

// MongoDB Vector Search patterns
const MONGODB_PATTERNS = {
  connection: {
    patterns: [
      /MongoClient/i,
      /mongoose\.connect/i,
      /mongodb\+srv:\/\//i,
      /atlas\.mongodb/i,
    ],
    required: ["retryWrites", "w", "readPreference"],
  },
  vectorSearch: {
    patterns: [/\$vectorSearch/i, /\$search/i, /atlas\.search/i, /knnBeta/i],
    indexTypes: ["vectorSearch", "search", "knn"],
  },
  aggregation: {
    patterns: [/aggregate\(/i, /\$lookup/i, /\$project/i, /\$match/i],
  },
};

// Atlas Search index configuration
const ATLAS_INDEX_CONFIG = {
  vectorDimensions: {
    "text-embedding-ada-002": 1536,
    "titan-embed-text-v1": 1536,
    "titan-embed-text-v2": 1024,
    "all-MiniLM-L6-v2": 384,
  },
  similarity: ["euclidean", "cosine", "dotProduct"],
  indexTypes: ["hnsw", "ivfflat"],
};

// Security patterns
const SECURITY_PATTERNS = {
  connectionString: [
    /mongodb:\/\/[^@]*:[^@]*@/i, // Credentials in connection string
    /password\s*=\s*["'][^"']+/i,
    /MONGO_PASSWORD/i,
  ],
  injection: [/\$where/i, /\$expr.*\$function/i, /mapReduce/i, /eval\(/i],
};

class MongoDBVectorValidator {
  constructor(projectRoot) {
    this.projectRoot = projectRoot;
    this.issues = [];
  }

  validate() {
    console.log("🔍 Validating MongoDB Atlas Vector Search patterns...");

    this.validateConnection();
    this.validateVectorSearchIndexes();
    this.validateAggregationPipelines();
    this.validateSecurity();
    this.validatePerformance();

    return this.generateReport();
  }

  validateConnection() {
    const configFiles = this.findFiles([
      "*.config.js",
      "*.config.ts",
      ".env",
      "*.yml",
    ]);

    configFiles.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check for MongoDB connection
        MONGODB_PATTERNS.connection.patterns.forEach((pattern) => {
          if (pattern.test(content)) {
            this.checkConnectionConfig(content, file);
          }
        });
      } catch (error) {
        this.addIssue("error", `Cannot read file: ${file}`, error.message);
      }
    });
  }

  checkConnectionConfig(content, filePath) {
    // Check for Atlas connection
    if (content.includes("mongodb+srv://") || content.includes("atlas")) {
      // Check for retry writes
      if (!content.includes("retryWrites=true")) {
        this.addIssue(
          "warning",
          `MongoDB connection missing retryWrites: ${filePath}`,
          "Add retryWrites=true to connection string",
        );
      }

      // Check for write concern
      if (
        !content.includes("w=majority") &&
        !content.includes("writeConcern")
      ) {
        this.addIssue(
          "warning",
          `MongoDB connection missing write concern: ${filePath}`,
          "Set w=majority for data durability",
        );
      }

      // Check for connection pooling
      if (!content.includes("maxPoolSize") && !content.includes("poolSize")) {
        this.addIssue(
          "info",
          `No connection pool size configured: ${filePath}`,
          "Configure maxPoolSize for better performance",
        );
      }
    }

    // Check for proper error handling
    if (!content.includes("MongoError") && !content.includes("catch")) {
      this.addIssue(
        "warning",
        `No MongoDB error handling: ${filePath}`,
        "Add error handling for MongoDB operations",
      );
    }
  }

  validateVectorSearchIndexes() {
    const indexFiles = this.findFiles([
      "*index*.js",
      "*index*.json",
      "*schema*.js",
    ]);

    indexFiles.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check for vector search configuration
        if (content.includes("vectorSearch") || content.includes("knn")) {
          this.checkVectorIndexConfig(content, file);
        }
      } catch (error) {
        // File reading error
      }
    });
  }

  checkVectorIndexConfig(content, filePath) {
    // Check for dimension specification
    if (!content.includes("dimension") && !content.includes("numDimensions")) {
      this.addIssue(
        "error",
        `Vector index missing dimension specification: ${filePath}`,
        "Specify vector dimensions in index definition",
      );
    }

    // Check dimension values
    const dimMatch = content.match(/dimension[s]?\s*:\s*(\d+)/i);
    if (dimMatch) {
      const dimension = parseInt(dimMatch[1]);
      const validDimensions = Object.values(
        ATLAS_INDEX_CONFIG.vectorDimensions,
      );

      if (!validDimensions.includes(dimension)) {
        this.addIssue(
          "warning",
          `Unusual vector dimension ${dimension}: ${filePath}`,
          `Common dimensions: ${validDimensions.join(", ")}`,
        );
      }
    }

    // Check for similarity metric
    if (!content.includes("similarity")) {
      this.addIssue(
        "warning",
        `No similarity metric specified: ${filePath}`,
        "Specify similarity metric (cosine, euclidean, dotProduct)",
      );
    }

    // Check for index type
    if (content.includes("hnsw")) {
      // Check HNSW parameters
      if (!content.includes("m") || !content.includes("efConstruction")) {
        this.addIssue(
          "info",
          `HNSW index missing optimization parameters: ${filePath}`,
          "Configure m and efConstruction for HNSW index",
        );
      }
    }
  }

  validateAggregationPipelines() {
    const queryFiles = this.findFiles(["*.js", "*.ts"]);

    queryFiles.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check for vector search queries
        if (content.includes("$vectorSearch") || content.includes("$search")) {
          this.checkVectorSearchQuery(content, file);
        }

        // Check aggregation pipelines
        if (content.includes("aggregate(")) {
          this.checkAggregationPipeline(content, file);
        }
      } catch (error) {
        this.addIssue("error", `Cannot read file: ${file}`, error.message);
      }
    });
  }

  checkVectorSearchQuery(content, filePath) {
    // Check for k/limit parameter
    if (!content.includes("limit") && !content.includes("numCandidates")) {
      this.addIssue(
        "warning",
        `Vector search missing result limit: ${filePath}`,
        "Set limit or numCandidates to control results",
      );
    }

    // Check for filter combination
    if (content.includes("$vectorSearch") && content.includes("filter")) {
      // Check for index on filter fields
      if (!content.includes("compound")) {
        this.addIssue(
          "info",
          `Consider compound index for filtered vector search: ${filePath}`,
          "Use compound indexes for better performance",
        );
      }
    }

    // Check for score projection
    if (!content.includes("score") && !content.includes("$meta")) {
      this.addIssue(
        "info",
        `Vector search not projecting similarity score: ${filePath}`,
        "Project score using $meta for ranking",
      );
    }
  }

  checkAggregationPipeline(content, filePath) {
    // Check for unbounded aggregations
    if (content.includes("aggregate(") && !content.includes("$limit")) {
      this.addIssue(
        "warning",
        `Aggregation pipeline without limit: ${filePath}`,
        "Add $limit stage to prevent memory issues",
      );
    }

    // Check for $lookup performance
    if (content.includes("$lookup")) {
      if (!content.includes("pipeline") && !content.includes("let")) {
        this.addIssue(
          "info",
          `Basic $lookup usage: ${filePath}`,
          "Consider pipeline $lookup for better performance",
        );
      }
    }

    // Check for allowDiskUse
    if (content.includes("$sort") || content.includes("$group")) {
      if (!content.includes("allowDiskUse")) {
        this.addIssue(
          "info",
          `Large aggregation without allowDiskUse: ${filePath}`,
          "Set allowDiskUse: true for large datasets",
        );
      }
    }
  }

  validateSecurity() {
    const files = this.findFiles(["*.js", "*.ts", ".env", "*.yml"]);

    files.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check for hardcoded credentials
        SECURITY_PATTERNS.connectionString.forEach((pattern) => {
          if (pattern.test(content)) {
            this.addIssue(
              "critical",
              `Potential hardcoded MongoDB credentials: ${file}`,
              "Use environment variables for credentials",
            );
          }
        });

        // Check for injection vulnerabilities
        SECURITY_PATTERNS.injection.forEach((pattern) => {
          if (pattern.test(content)) {
            this.addIssue(
              "error",
              `Potential MongoDB injection vulnerability: ${file}`,
              "Avoid $where, eval, and user input in queries",
            );
          }
        });

        // Check for field-level encryption
        if (content.includes("sensitive") || content.includes("personal")) {
          if (
            !content.includes("ClientEncryption") &&
            !content.includes("CSFLE")
          ) {
            this.addIssue(
              "info",
              `Consider field-level encryption for sensitive data: ${file}`,
              "Use MongoDB Client-Side Field Level Encryption",
            );
          }
        }
      } catch (error) {
        this.addIssue("error", `Cannot read file: ${file}`, error.message);
      }
    });
  }

  validatePerformance() {
    const queryFiles = this.findFiles(["*.js", "*.ts"]);

    queryFiles.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check for index hints
        if (content.includes(".find(") || content.includes(".findOne(")) {
          // Check for explain plans
          if (!content.includes(".explain(")) {
            this.addIssue(
              "info",
              `No query explain plans found: ${file}`,
              "Use explain() to optimize query performance",
            );
          }
        }

        // Check for bulk operations
        if (content.includes("insertOne") || content.includes("updateOne")) {
          if (
            !content.includes("bulkWrite") &&
            !content.includes("insertMany")
          ) {
            this.addIssue(
              "info",
              `Single document operations in loops: ${file}`,
              "Use bulkWrite or insertMany for batch operations",
            );
          }
        }

        // Check for change streams
        if (content.includes("watch(")) {
          if (
            !content.includes("resumeAfter") &&
            !content.includes("startAfter")
          ) {
            this.addIssue(
              "warning",
              `Change stream without resume token: ${file}`,
              "Handle resume tokens for change stream reliability",
            );
          }
        }
      } catch (error) {
        this.addIssue("error", `Cannot read file: ${file}`, error.message);
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
      validator: "MongoDB Atlas Vector Search Validator",
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
    console.log("\n📊 MongoDB Vector Search Validation Results:");
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
module.exports = MongoDBVectorValidator;

// Allow direct execution
if (require.main === module) {
  const validator = new MongoDBVectorValidator(process.cwd());
  const report = validator.validate();

  if (report.summary.critical > 0 || report.summary.errors > 0) {
    process.exit(1);
  }
}

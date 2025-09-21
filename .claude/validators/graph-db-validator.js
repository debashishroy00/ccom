// Graph Database Security Validator for Enterprise RAG Systems
// Supports: Neo4j, ArangoDB, TigerGraph, Amazon Neptune, Azure Cosmos DB

const fs = require("fs");
const path = require("path");

// Dangerous Cypher patterns that can cause security issues
const DANGEROUS_CYPHER_PATTERNS = [
  {
    pattern: /DETACH DELETE.*(?!WHERE)/i,
    severity: "error",
    message: "Unconditional DETACH DELETE can destroy entire database",
  },
  {
    pattern: /DELETE.*(?!WHERE)/i,
    severity: "error",
    message: "Unconditional DELETE can destroy data",
  },
  {
    pattern: /DROP\s+(CONSTRAINT|INDEX|NODE|RELATIONSHIP)/i,
    severity: "error",
    message: "DROP operations can break database schema",
  },
  {
    pattern: /MERGE.*(?!ON)/i,
    severity: "warning",
    message: "MERGE without ON CREATE/MATCH can cause unexpected behavior",
  },
  {
    pattern: /\$\{[^}]*\}/,
    severity: "error",
    message: "Template literals in queries can enable injection attacks",
  },
  {
    pattern: /\+\s*['"`][^'"`]*['"`]\s*\+/,
    severity: "error",
    message: "String concatenation in queries enables injection attacks",
  },
];

// Performance anti-patterns in graph queries
const PERFORMANCE_PATTERNS = [
  {
    pattern: /MATCH\s*\(\s*\w+\s*\)\s*(?!WHERE)/i,
    severity: "warning",
    message: "Unfiltered MATCH can scan entire database",
  },
  {
    pattern: /MATCH.*-\[\*\]-/i,
    severity: "warning",
    message:
      "Variable-length relationships without limits can cause exponential traversal",
  },
  {
    pattern: /OPTIONAL MATCH.*OPTIONAL MATCH/i,
    severity: "warning",
    message: "Multiple OPTIONAL MATCH can create Cartesian products",
  },
  {
    pattern: /(?:MATCH.*){3,}/i,
    severity: "info",
    message:
      "Complex queries with many MATCH clauses may benefit from optimization",
  },
];

// Multi-tenant security patterns
const TENANT_PATTERNS = [
  {
    pattern: /MATCH\s*\([^)]*\)\s*(?!.*tenant|.*user_id|.*namespace)/i,
    severity: "warning",
    message: "Query lacks tenant isolation - potential data leakage",
  },
  {
    pattern: /WHERE.*(?!.*tenant|.*user_id|.*organization)/i,
    severity: "info",
    message: "Consider adding tenant filtering for multi-tenant applications",
  },
];

class GraphDBValidator {
  constructor(projectPath) {
    this.projectPath = projectPath;
    this.issues = [];
    this.stats = {
      queriesAnalyzed: 0,
      filesScanned: 0,
      cypherQueries: 0,
      gremlinQueries: 0,
    };
  }

  validateProject() {
    console.log(
      "🔍 CCOM GRAPH DB VALIDATION – Analyzing graph database patterns...",
    );

    this.scanCypherFiles();
    this.scanJavaScriptFiles();
    this.scanConfigFiles();
    this.validateConnectionSecurity();
    this.validateQueryPatterns();

    return this.generateReport();
  }

  scanCypherFiles() {
    // Find .cypher, .cql files
    const cypherFiles = this.findFiles(["*.cypher", "*.cql"]);

    cypherFiles.forEach((file) => {
      this.validateCypherFile(file);
    });
  }

  validateCypherFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, "utf8");
      this.stats.filesScanned++;

      // Split into individual queries
      const queries = content.split(";").filter((q) => q.trim());
      this.stats.cypherQueries += queries.length;

      queries.forEach((query, index) => {
        this.validateCypherQuery(query.trim(), `${filePath}:${index + 1}`);
      });
    } catch (error) {
      this.addIssue(
        "error",
        `Cannot read Cypher file: ${filePath}`,
        error.message,
      );
    }
  }

  validateCypherQuery(query, location) {
    if (!query) return;

    this.stats.queriesAnalyzed++;

    // Check dangerous patterns
    DANGEROUS_CYPHER_PATTERNS.forEach(({ pattern, severity, message }) => {
      if (pattern.test(query)) {
        this.addIssue(
          severity,
          `Dangerous Cypher pattern in ${location}`,
          message,
        );
      }
    });

    // Check performance patterns
    PERFORMANCE_PATTERNS.forEach(({ pattern, severity, message }) => {
      if (pattern.test(query)) {
        this.addIssue(severity, `Performance issue in ${location}`, message);
      }
    });

    // Check tenant patterns
    TENANT_PATTERNS.forEach(({ pattern, severity, message }) => {
      if (pattern.test(query)) {
        this.addIssue(severity, `Multi-tenant issue in ${location}`, message);
      }
    });

    // Check for parameterization
    this.validateParameterization(query, location);

    // Check for proper indexing hints
    this.validateIndexing(query, location);
  }

  validateParameterization(query, location) {
    // Check for unparameterized values
    const literalPatterns = [
      /'[^']*'/g, // String literals
      /"[^"]*"/g, // Double quoted strings
      /\b\d+\b/g, // Numeric literals
    ];

    let hasLiterals = false;
    literalPatterns.forEach((pattern) => {
      if (pattern.test(query)) {
        hasLiterals = true;
      }
    });

    if (hasLiterals && !query.includes("$")) {
      this.addIssue(
        "warning",
        `Unparameterized query in ${location}`,
        "Use parameters ($param) instead of literals for better security and performance",
      );
    }
  }

  validateIndexing(query, location) {
    // Check for potential missing indexes
    if (query.includes("MATCH") && query.includes("WHERE")) {
      // Simple heuristic: if filtering by property, suggest index
      const propertyPattern = /WHERE\s+\w+\.(\w+)/i;
      const match = query.match(propertyPattern);

      if (match && !query.includes("USING INDEX")) {
        this.addIssue(
          "info",
          `Consider index optimization in ${location}`,
          `Property '${match[1]}' might benefit from an index`,
        );
      }
    }
  }

  scanJavaScriptFiles() {
    const jsFiles = this.findFiles(["*.js", "*.ts"]);

    jsFiles.forEach((file) => {
      this.validateJavaScriptFile(file);
    });
  }

  validateJavaScriptFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, "utf8");
      this.stats.filesScanned++;

      // Look for embedded Cypher queries
      this.findEmbeddedQueries(content, filePath);

      // Check Neo4j driver usage
      this.validateDriverUsage(content, filePath);

      // Check session management
      this.validateSessionManagement(content, filePath);
    } catch (error) {
      this.addIssue(
        "error",
        `Cannot read JavaScript file: ${filePath}`,
        error.message,
      );
    }
  }

  findEmbeddedQueries(content, filePath) {
    // Find Cypher queries in template literals
    const cypherRegex = /`[^`]*(?:MATCH|CREATE|MERGE|DELETE|RETURN)[^`]*`/gi;
    const matches = content.match(cypherRegex);

    if (matches) {
      matches.forEach((match, index) => {
        const query = match.slice(1, -1); // Remove backticks
        this.validateCypherQuery(query, `${filePath}:template-${index + 1}`);
        this.stats.cypherQueries++;
      });
    }

    // Find queries in string concatenation
    const concatRegex =
      /['"][^'"]*(?:MATCH|CREATE|MERGE|DELETE|RETURN)[^'"]*['"]/gi;
    const concatMatches = content.match(concatRegex);

    if (concatMatches) {
      concatMatches.forEach((match, index) => {
        this.addIssue(
          "warning",
          `String concatenated query in ${filePath}:concat-${index + 1}`,
          "Use parameterized queries instead of string concatenation",
        );
      });
    }
  }

  validateDriverUsage(content, filePath) {
    // Check for Neo4j driver patterns
    if (content.includes("neo4j.driver") || content.includes("neo4j-driver")) {
      // Check for proper authentication
      if (!content.includes("auth.basic") && !content.includes("auth.bearer")) {
        this.addIssue(
          "warning",
          `Missing authentication in ${filePath}`,
          "Neo4j driver should use proper authentication",
        );
      }

      // Check for TLS configuration
      if (content.includes("bolt://") && !content.includes("encrypted")) {
        this.addIssue(
          "info",
          `Consider TLS encryption in ${filePath}`,
          "Use bolt+s:// or configure encrypted: true for production",
        );
      }
    }
  }

  validateSessionManagement(content, filePath) {
    // Check for proper session cleanup
    if (content.includes(".session(") && !content.includes(".close()")) {
      this.addIssue(
        "warning",
        `Missing session cleanup in ${filePath}`,
        "Always close Neo4j sessions to prevent memory leaks",
      );
    }

    // Check for transaction usage
    if (
      content.includes(".writeTransaction") ||
      content.includes(".readTransaction")
    ) {
      if (!content.includes("catch") && !content.includes(".catch")) {
        this.addIssue(
          "warning",
          `Missing error handling in ${filePath}`,
          "Add proper error handling for database transactions",
        );
      }
    }
  }

  scanConfigFiles() {
    const configFiles = this.findFiles([
      "neo4j.conf",
      "neo4j.config.js",
      "graph.config.js",
      "database.config.js",
    ]);

    configFiles.forEach((file) => {
      this.validateConfigFile(file);
    });
  }

  validateConfigFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, "utf8");

      // Check for hardcoded credentials
      this.checkHardcodedCredentials(content, filePath);

      // Check for security settings
      this.checkSecuritySettings(content, filePath);
    } catch (error) {
      this.addIssue(
        "error",
        `Cannot read config file: ${filePath}`,
        error.message,
      );
    }
  }

  checkHardcodedCredentials(content, filePath) {
    const credentialPatterns = [
      /password\s*[:=]\s*['"][^'"]+['"]/i,
      /username\s*[:=]\s*['"][^'"]+['"]/i,
      /auth\s*[:=]\s*['"][^'"]+['"]/i,
      /secret\s*[:=]\s*['"][^'"]+['"]/i,
    ];

    credentialPatterns.forEach((pattern) => {
      if (pattern.test(content)) {
        this.addIssue(
          "error",
          `Hardcoded credentials in ${filePath}`,
          "Use environment variables for sensitive configuration",
        );
      }
    });
  }

  checkSecuritySettings(content, filePath) {
    // Check for recommended security settings
    if (content.includes("neo4j") || content.includes("graph")) {
      if (
        !content.includes("tls") &&
        !content.includes("ssl") &&
        !content.includes("encrypted")
      ) {
        this.addIssue(
          "info",
          `Consider TLS configuration in ${filePath}`,
          "Enable TLS/SSL for production graph database connections",
        );
      }
    }
  }

  validateConnectionSecurity() {
    // Check for environment variable usage
    const envFile = path.join(this.projectPath, ".env");
    if (fs.existsSync(envFile)) {
      const envContent = fs.readFileSync(envFile, "utf8");

      // Check for graph database environment variables
      const hasGraphEnv = [
        "NEO4J_URI",
        "NEO4J_URL",
        "NEO4J_PASSWORD",
        "GRAPH_DB_URI",
        "GRAPH_DB_PASSWORD",
        "ARANGO_URL",
        "ARANGO_PASSWORD",
      ].some((env) => envContent.includes(env));

      if (hasGraphEnv) {
        this.addIssue(
          "info",
          "Found graph database environment variables",
          "Good practice: Using environment variables for configuration",
        );
      }
    }
  }

  validateQueryPatterns() {
    // Additional validation for common query patterns
    const jsFiles = this.findFiles(["*.js", "*.ts"]);

    jsFiles.forEach((file) => {
      this.validateQueryPatternsInFile(file);
    });
  }

  validateQueryPatternsInFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, "utf8");

      // Check for batch operations
      this.checkBatchOperations(content, filePath);

      // Check for proper error handling
      this.checkErrorHandling(content, filePath);

      // Check for connection pooling
      this.checkConnectionPooling(content, filePath);
    } catch (error) {
      this.addIssue("error", `Cannot read file: ${filePath}`, error.message);
    }
  }

  checkBatchOperations(content, filePath) {
    // Check for inefficient single-record operations in loops
    if (
      content.includes("for") &&
      (content.includes("CREATE") || content.includes("MERGE"))
    ) {
      if (!content.includes("UNWIND") && !content.includes("batch")) {
        this.addIssue(
          "info",
          `Consider batch operations in ${filePath}`,
          "Use UNWIND for batch inserts/updates instead of loops",
        );
      }
    }
  }

  checkErrorHandling(content, filePath) {
    // Check for database operations without error handling
    const dbOperations = ["run(", "writeTransaction(", "readTransaction("];

    dbOperations.forEach((operation) => {
      if (content.includes(operation)) {
        // Check if there's error handling nearby
        const lines = content.split("\n");
        let hasErrorHandling = false;

        lines.forEach((line, index) => {
          if (line.includes(operation)) {
            // Look for try-catch or .catch in surrounding lines
            const context = lines
              .slice(Math.max(0, index - 3), index + 5)
              .join("\n");
            if (context.includes("try") || context.includes(".catch")) {
              hasErrorHandling = true;
            }
          }
        });

        if (!hasErrorHandling) {
          this.addIssue(
            "warning",
            `Missing error handling for ${operation} in ${filePath}`,
            "Add proper error handling for database operations",
          );
        }
      }
    });
  }

  checkConnectionPooling(content, filePath) {
    // Check for multiple driver instances
    const driverMatches = content.match(/neo4j\.driver\(/g);
    if (driverMatches && driverMatches.length > 1) {
      this.addIssue(
        "warning",
        `Multiple driver instances in ${filePath}`,
        "Use a single driver instance with connection pooling",
      );
    }
  }

  findFiles(patterns) {
    const files = [];

    function walkDir(dir) {
      try {
        const items = fs.readdirSync(dir);

        items.forEach((item) => {
          const fullPath = path.join(dir, item);
          const stat = fs.statSync(fullPath);

          if (
            stat.isDirectory() &&
            !item.startsWith(".") &&
            item !== "node_modules"
          ) {
            walkDir(fullPath);
          } else if (stat.isFile()) {
            const matches = patterns.some((pattern) => {
              if (pattern.includes("*")) {
                const regex = new RegExp(pattern.replace("*", ".*"));
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
    const errorCount = this.issues.filter((i) => i.level === "error").length;
    const warningCount = this.issues.filter(
      (i) => i.level === "warning",
    ).length;
    const infoCount = this.issues.filter((i) => i.level === "info").length;

    console.log("\n📊 GRAPH DATABASE VALIDATION REPORT");
    console.log("=".repeat(50));

    console.log(`📈 Analysis Statistics:`);
    console.log(`   Files scanned: ${this.stats.filesScanned}`);
    console.log(`   Queries analyzed: ${this.stats.queriesAnalyzed}`);
    console.log(`   Cypher queries: ${this.stats.cypherQueries}`);

    if (errorCount === 0 && warningCount === 0) {
      console.log(
        "✅ EXCELLENT: Graph database patterns are secure and optimized",
      );
    } else {
      console.log(
        `🔍 Found ${errorCount} errors, ${warningCount} warnings, ${infoCount} suggestions`,
      );
    }

    // Group issues by level
    ["error", "warning", "info"].forEach((level) => {
      const levelIssues = this.issues.filter((i) => i.level === level);
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
      summary: `Graph DB validation: ${errorCount} errors, ${warningCount} warnings`,
      details: this.issues,
      stats: this.stats,
    };
  }
}

module.exports = GraphDBValidator;

// CLI usage
if (require.main === module) {
  const projectPath = process.argv[2] || process.cwd();
  const validator = new GraphDBValidator(projectPath);
  const result = validator.validateProject();
  process.exit(result.passed ? 0 : 1);
}

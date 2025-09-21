// S3 Security Validator for RAG Applications
// Validates: Presigned URLs, multipart uploads, CORS, access policies, encryption

const fs = require("fs");
const path = require("path");

// S3 security patterns
const S3_SECURITY_PATTERNS = {
  presignedUrls: {
    generation: [
      /getSignedUrl/g,
      /generatePresignedUrl/g,
      /createPresignedPost/g,
      /presigned.*url/gi,
    ],
    security: [/expires.*in/gi, /expiration/gi, /ttl/gi, /max.*age/gi],
    vulnerable: [
      /expires.*:\s*[1-9]\d{6,}/, // Very long expiration (>1M seconds)
      /expires.*null/gi, // No expiration
      /expires.*undefined/gi, // Undefined expiration
    ],
  },
  multipart: {
    patterns: [
      /createMultipartUpload/g,
      /uploadPart/g,
      /completeMultipartUpload/g,
      /abortMultipartUpload/g,
      /listParts/g,
    ],
    security: [
      /abort.*timeout/gi,
      /cleanup.*incomplete/gi,
      /lifecycle.*incomplete/gi,
    ],
  },
  cors: {
    patterns: [
      /cors.*configuration/gi,
      /AllowedOrigins/g,
      /AllowedMethods/g,
      /AllowedHeaders/g,
      /ExposeHeaders/g,
    ],
    vulnerable: [
      /AllowedOrigins.*\*/, // Wildcard origins
      /AllowedMethods.*\*/, // All methods allowed
      /credentials.*true.*\*/, // Credentials with wildcard
    ],
  },
  encryption: {
    patterns: [
      /ServerSideEncryption/g,
      /SSE-S3/g,
      /SSE-KMS/g,
      /SSE-C/g,
      /encryption.*key/gi,
    ],
    required: [/AES256/g, /aws:kms/g, /customer.*key/gi],
  },
  access: {
    policies: [/bucket.*policy/gi, /Principal/g, /Resource/g, /Condition/g],
    vulnerable: [
      /Principal.*\*/, // Public access
      /Resource.*\*/, // All resources
      /Effect.*Allow.*Principal.*\*/, // Public allow
    ],
  },
};

// RAG-specific S3 patterns
const RAG_PATTERNS = {
  documents: [
    /document.*upload/gi,
    /pdf.*upload/gi,
    /file.*processing/gi,
    /text.*extraction/gi,
  ],
  embeddings: [
    /embedding.*storage/gi,
    /vector.*storage/gi,
    /faiss.*index/gi,
    /chromadb.*backup/gi,
  ],
  streaming: [/stream.*upload/gi, /chunk.*upload/gi, /progressive.*upload/gi],
};

// File size and type validations
const FILE_VALIDATION = {
  maxSize: {
    documents: 100 * 1024 * 1024, // 100MB for documents
    images: 10 * 1024 * 1024, // 10MB for images
    embeddings: 1024 * 1024 * 1024, // 1GB for embedding files
  },
  allowedTypes: {
    documents: [".pdf", ".txt", ".docx", ".md"],
    images: [".jpg", ".jpeg", ".png", ".gif"],
    data: [".json", ".csv", ".parquet"],
  },
};

class S3SecurityValidator {
  constructor(projectRoot) {
    this.projectRoot = projectRoot;
    this.issues = [];
  }

  validate() {
    console.log("🔍 Validating S3 security patterns for RAG applications...");

    this.validatePresignedUrls();
    this.validateMultipartUploads();
    this.validateCORSConfiguration();
    this.validateEncryption();
    this.validateAccessPolicies();
    this.validateRAGSpecificPatterns();
    this.validateFileHandling();

    return this.generateReport();
  }

  validatePresignedUrls() {
    const files = this.findFiles(["*.js", "*.ts", "*.py"]);

    files.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check for presigned URL generation
        this.checkPresignedUrlGeneration(content, file);

        // Check for security vulnerabilities
        this.checkPresignedUrlSecurity(content, file);

        // Check for proper validation
        this.checkPresignedUrlValidation(content, file);
      } catch (error) {
        this.addIssue("error", `Cannot read file: ${file}`, error.message);
      }
    });
  }

  checkPresignedUrlGeneration(content, filePath) {
    const hasPresignedUrls = S3_SECURITY_PATTERNS.presignedUrls.generation.some(
      (pattern) => pattern.test(content),
    );

    if (hasPresignedUrls) {
      // Check for expiration settings
      if (
        !S3_SECURITY_PATTERNS.presignedUrls.security.some((pattern) =>
          pattern.test(content),
        )
      ) {
        this.addIssue(
          "critical",
          `Presigned URLs without expiration: ${filePath}`,
          "Always set expiration for presigned URLs to limit access window",
        );
      }

      // Check for vulnerable expiration patterns
      S3_SECURITY_PATTERNS.presignedUrls.vulnerable.forEach((pattern) => {
        if (pattern.test(content)) {
          this.addIssue(
            "critical",
            `Insecure presigned URL expiration: ${filePath}`,
            "Set reasonable expiration times (minutes to hours, not days)",
          );
        }
      });

      // Check for content type validation
      if (
        !content.includes("ContentType") &&
        !content.includes("content-type")
      ) {
        this.addIssue(
          "error",
          `Presigned URLs without content type validation: ${filePath}`,
          "Specify allowed content types to prevent malicious uploads",
        );
      }

      // Check for file size limits
      if (
        !content.includes("ContentLength") &&
        !content.includes("content-length")
      ) {
        this.addIssue(
          "warning",
          `Presigned URLs without size limits: ${filePath}`,
          "Set content length limits to prevent large file attacks",
        );
      }
    }
  }

  checkPresignedUrlSecurity(content, filePath) {
    // Check for proper conditions in presigned URLs
    if (
      content.includes("createPresignedPost") ||
      content.includes("getSignedUrl")
    ) {
      if (!content.includes("Conditions") && !content.includes("conditions")) {
        this.addIssue(
          "error",
          `Presigned URLs without security conditions: ${filePath}`,
          "Add conditions to restrict file types, sizes, and other parameters",
        );
      }

      // Check for bucket restrictions
      if (!content.includes("bucket") || content.includes("bucket.*variable")) {
        this.addIssue(
          "warning",
          `Dynamic bucket selection in presigned URLs: ${filePath}`,
          "Restrict presigned URLs to specific buckets",
        );
      }

      // Check for key prefix restrictions
      if (
        !content.includes("key.*prefix") &&
        !content.includes("starts-with")
      ) {
        this.addIssue(
          "info",
          `No key prefix restrictions: ${filePath}`,
          "Restrict upload paths using key prefixes",
        );
      }
    }
  }

  checkPresignedUrlValidation(content, filePath) {
    // Check for client-side validation
    if (content.includes("presigned") || content.includes("upload")) {
      if (!content.includes("validate") && !content.includes("check")) {
        this.addIssue(
          "warning",
          `No client-side validation for uploads: ${filePath}`,
          "Validate file types and sizes before upload",
        );
      }

      // Check for server-side verification
      if (!content.includes("webhook") && !content.includes("notification")) {
        this.addIssue(
          "info",
          `No server-side upload verification: ${filePath}`,
          "Consider S3 event notifications for upload verification",
        );
      }
    }
  }

  validateMultipartUploads() {
    const files = this.findFiles(["*.js", "*.ts", "*.py"]);

    files.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        this.checkMultipartImplementation(content, file);
        this.checkMultipartSecurity(content, file);
        this.checkMultipartCleanup(content, file);
      } catch (error) {
        this.addIssue("error", `Cannot read file: ${file}`, error.message);
      }
    });
  }

  checkMultipartImplementation(content, filePath) {
    const hasMultipart = S3_SECURITY_PATTERNS.multipart.patterns.some(
      (pattern) => pattern.test(content),
    );

    if (hasMultipart) {
      // Check for complete implementation
      const requiredMethods = [
        "createMultipartUpload",
        "uploadPart",
        "completeMultipartUpload",
      ];
      const missingMethods = requiredMethods.filter(
        (method) => !content.includes(method),
      );

      if (missingMethods.length > 0) {
        this.addIssue(
          "error",
          `Incomplete multipart upload implementation: ${filePath}`,
          `Missing methods: ${missingMethods.join(", ")}`,
        );
      }

      // Check for abort handling
      if (!content.includes("abortMultipartUpload")) {
        this.addIssue(
          "warning",
          `No abort handling for multipart uploads: ${filePath}`,
          "Implement abortMultipartUpload for failed uploads",
        );
      }

      // Check for progress tracking
      if (!content.includes("progress") && !content.includes("callback")) {
        this.addIssue(
          "info",
          `No progress tracking for multipart uploads: ${filePath}`,
          "Add progress tracking for better user experience",
        );
      }
    }
  }

  checkMultipartSecurity(content, filePath) {
    if (content.includes("multipart")) {
      // Check for proper part verification
      if (!content.includes("ETag") && !content.includes("etag")) {
        this.addIssue(
          "error",
          `Multipart uploads without ETag verification: ${filePath}`,
          "Verify ETags to ensure part integrity",
        );
      }

      // Check for part size validation
      if (!content.includes("partSize") && !content.includes("part.*size")) {
        this.addIssue(
          "warning",
          `No part size validation: ${filePath}`,
          "Validate part sizes (5MB minimum, except last part)",
        );
      }

      // Check for maximum parts limit
      if (!content.includes("maxParts") && !content.includes("10000")) {
        this.addIssue(
          "info",
          `No maximum parts limit: ${filePath}`,
          "AWS allows maximum 10,000 parts per upload",
        );
      }
    }
  }

  checkMultipartCleanup(content, filePath) {
    if (content.includes("multipart")) {
      // Check for cleanup of incomplete uploads
      if (
        !S3_SECURITY_PATTERNS.multipart.security.some((pattern) =>
          pattern.test(content),
        )
      ) {
        this.addIssue(
          "warning",
          `No cleanup for incomplete multipart uploads: ${filePath}`,
          "Implement lifecycle policies to clean up incomplete uploads",
        );
      }

      // Check for timeout handling
      if (!content.includes("timeout") && !content.includes("expir")) {
        this.addIssue(
          "info",
          `No timeout for multipart operations: ${filePath}`,
          "Set timeouts to prevent hanging uploads",
        );
      }
    }
  }

  validateCORSConfiguration() {
    const configFiles = this.findFiles(["*.json", "*.yml", "*.yaml", "*.tf"]);

    configFiles.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        if (
          S3_SECURITY_PATTERNS.cors.patterns.some((pattern) =>
            pattern.test(content),
          )
        ) {
          this.checkCORSSecurity(content, file);
        }
      } catch (error) {
        // File reading error
      }
    });
  }

  checkCORSSecurity(content, filePath) {
    // Check for wildcard origins
    if (content.includes("AllowedOrigins") && content.includes("*")) {
      this.addIssue(
        "critical",
        `CORS allows all origins (*): ${filePath}`,
        "Restrict AllowedOrigins to specific domains",
      );
    }

    // Check for overly permissive methods
    if (content.includes("AllowedMethods") && content.includes("*")) {
      this.addIssue(
        "error",
        `CORS allows all methods (*): ${filePath}`,
        "Specify only required HTTP methods (GET, POST, PUT)",
      );
    }

    // Check for credentials with wildcard
    S3_SECURITY_PATTERNS.cors.vulnerable.forEach((pattern) => {
      if (pattern.test(content)) {
        this.addIssue(
          "critical",
          `Dangerous CORS configuration: ${filePath}`,
          "Never use wildcard origins with credentials: true",
        );
      }
    });

    // Check for proper headers
    if (
      content.includes("AllowedHeaders") &&
      !content.includes("Content-Type")
    ) {
      this.addIssue(
        "warning",
        `CORS missing Content-Type header: ${filePath}`,
        "Include Content-Type in AllowedHeaders for file uploads",
      );
    }
  }

  validateEncryption() {
    const files = this.findFiles([
      "*.json",
      "*.yml",
      "*.yaml",
      "*.tf",
      "*.js",
      "*.ts",
      "*.py",
    ]);

    let hasEncryption = false;

    files.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        if (content.includes("s3") || content.includes("S3")) {
          const hasEncryptionConfig =
            S3_SECURITY_PATTERNS.encryption.patterns.some((pattern) =>
              pattern.test(content),
            );

          if (hasEncryptionConfig) {
            hasEncryption = true;
            this.checkEncryptionConfiguration(content, file);
          }
        }
      } catch (error) {
        // File reading error
      }
    });

    if (!hasEncryption) {
      this.addIssue(
        "critical",
        "No S3 encryption configuration found",
        "Enable server-side encryption for all S3 buckets",
      );
    }
  }

  checkEncryptionConfiguration(content, filePath) {
    // Check for encryption type
    if (
      !S3_SECURITY_PATTERNS.encryption.required.some((pattern) =>
        pattern.test(content),
      )
    ) {
      this.addIssue(
        "error",
        `S3 encryption configured but type unclear: ${filePath}`,
        "Specify encryption type: SSE-S3, SSE-KMS, or SSE-C",
      );
    }

    // Check for KMS key configuration
    if (content.includes("SSE-KMS") && !content.includes("KMSMasterKeyID")) {
      this.addIssue(
        "warning",
        `KMS encryption without key specification: ${filePath}`,
        "Specify KMS key ID for better key management",
      );
    }

    // Check for bucket default encryption
    if (
      !content.includes("BucketEncryption") &&
      !content.includes("default.*encryption")
    ) {
      this.addIssue(
        "warning",
        `No bucket default encryption: ${filePath}`,
        "Set default encryption at bucket level",
      );
    }
  }

  validateAccessPolicies() {
    const policyFiles = this.findFiles([
      "*policy*.json",
      "*bucket*.json",
      "*.tf",
    ]);

    policyFiles.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        if (content.includes("bucket") || content.includes("Policy")) {
          this.checkAccessPolicySecurity(content, file);
        }
      } catch (error) {
        // File reading error
      }
    });
  }

  checkAccessPolicySecurity(content, filePath) {
    // Check for public access
    S3_SECURITY_PATTERNS.access.vulnerable.forEach((pattern) => {
      if (pattern.test(content)) {
        this.addIssue(
          "critical",
          `Potentially public S3 access: ${filePath}`,
          "Review bucket policy for unintended public access",
        );
      }
    });

    // Check for principle of least privilege
    if (content.includes("s3:*") || content.includes('Action": "*"')) {
      this.addIssue(
        "error",
        `Overly broad S3 permissions: ${filePath}`,
        "Grant only specific permissions needed",
      );
    }

    // Check for resource restrictions
    if (
      content.includes("Resource") &&
      content.includes("*") &&
      !content.includes("arn:aws:s3:::")
    ) {
      this.addIssue(
        "warning",
        `Broad resource permissions: ${filePath}`,
        "Specify exact bucket and object ARNs",
      );
    }

    // Check for conditions
    if (!content.includes("Condition") && content.includes("Allow")) {
      this.addIssue(
        "info",
        `No conditions in policy: ${filePath}`,
        "Consider adding conditions for IP, time, or other restrictions",
      );
    }
  }

  validateRAGSpecificPatterns() {
    const files = this.findFiles(["*.js", "*.ts", "*.py"]);

    files.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check RAG document handling
        this.checkRAGDocumentSecurity(content, file);

        // Check embedding storage security
        this.checkEmbeddingStorageSecurity(content, file);
      } catch (error) {
        this.addIssue("error", `Cannot read file: ${file}`, error.message);
      }
    });
  }

  checkRAGDocumentSecurity(content, filePath) {
    const hasDocumentHandling = RAG_PATTERNS.documents.some((pattern) =>
      pattern.test(content),
    );

    if (hasDocumentHandling) {
      // Check for file type validation
      if (!content.includes("mimetype") && !content.includes("content-type")) {
        this.addIssue(
          "error",
          `Document upload without type validation: ${filePath}`,
          "Validate file types to prevent malicious uploads",
        );
      }

      // Check for virus scanning
      if (!content.includes("scan") && !content.includes("antivirus")) {
        this.addIssue(
          "warning",
          `No virus scanning for uploaded documents: ${filePath}`,
          "Implement virus scanning for user-uploaded content",
        );
      }

      // Check for content sanitization
      if (!content.includes("sanitiz") && !content.includes("clean")) {
        this.addIssue(
          "info",
          `No content sanitization: ${filePath}`,
          "Sanitize extracted text from documents",
        );
      }
    }
  }

  checkEmbeddingStorageSecurity(content, filePath) {
    const hasEmbeddingStorage = RAG_PATTERNS.embeddings.some((pattern) =>
      pattern.test(content),
    );

    if (hasEmbeddingStorage) {
      // Check for encryption of embeddings
      if (!content.includes("encrypt") && !content.includes("cipher")) {
        this.addIssue(
          "warning",
          `Embedding storage without encryption: ${filePath}`,
          "Encrypt embedding vectors before storage",
        );
      }

      // Check for access control
      if (!content.includes("private") && !content.includes("restricted")) {
        this.addIssue(
          "error",
          `No access control for embeddings: ${filePath}`,
          "Restrict access to embedding storage",
        );
      }

      // Check for backup security
      if (content.includes("backup") && !content.includes("encrypt")) {
        this.addIssue(
          "warning",
          `Embedding backups without encryption: ${filePath}`,
          "Encrypt embedding backups",
        );
      }
    }
  }

  validateFileHandling() {
    const files = this.findFiles(["*.js", "*.ts", "*.py"]);

    files.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check file size validation
        this.checkFileSizeValidation(content, file);

        // Check file type validation
        this.checkFileTypeValidation(content, file);
      } catch (error) {
        this.addIssue("error", `Cannot read file: ${file}`, error.message);
      }
    });
  }

  checkFileSizeValidation(content, filePath) {
    if (content.includes("upload") || content.includes("file")) {
      // Check for size limits
      if (!content.includes("size") && !content.includes("length")) {
        this.addIssue(
          "warning",
          `No file size validation: ${filePath}`,
          "Implement file size limits to prevent large uploads",
        );
      }

      // Check for reasonable limits
      const sizeMatch = content.match(/size.*?(\d+)/i);
      if (sizeMatch) {
        const size = parseInt(sizeMatch[1]);

        if (size > 1000000000) {
          // 1GB
          this.addIssue(
            "warning",
            `Very large file size limit (${size}): ${filePath}`,
            "Consider if such large files are necessary",
          );
        }
      }
    }
  }

  checkFileTypeValidation(content, filePath) {
    if (content.includes("upload") || content.includes("file")) {
      // Check for file type restrictions
      if (!content.includes("extension") && !content.includes("mimetype")) {
        this.addIssue(
          "error",
          `No file type validation: ${filePath}`,
          "Validate file types and extensions",
        );
      }

      // Check for executable file blocking
      if (!content.includes("exe") && !content.includes("script")) {
        this.addIssue(
          "info",
          `Consider blocking executable files: ${filePath}`,
          "Block .exe, .bat, .sh and other executable extensions",
        );
      }
    }
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
      validator: "S3 Security Validator",
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
    console.log("\n📊 S3 Security Validation Results:");
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
module.exports = S3SecurityValidator;

// Allow direct execution
if (require.main === module) {
  const validator = new S3SecurityValidator(process.cwd());
  const report = validator.validate();

  if (report.summary.critical > 0 || report.summary.errors > 0) {
    process.exit(1);
  }
}

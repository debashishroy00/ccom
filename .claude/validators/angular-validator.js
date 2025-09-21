// Angular Validator for RAG Applications
// Validates: RxJS memory leaks, change detection, performance patterns, Observable management

const fs = require("fs");
const path = require("path");

// Angular patterns and anti-patterns
const ANGULAR_PATTERNS = {
  rxjs: {
    subscriptions: [
      /\.subscribe\s*\(/g,
      /new\s+Subject\s*\(/g,
      /new\s+BehaviorSubject\s*\(/g,
      /new\s+ReplaySubject\s*\(/g,
    ],
    unsubscribe: [
      /\.unsubscribe\s*\(/g,
      /takeUntil\s*\(/g,
      /takeWhile\s*\(/g,
      /first\s*\(/g,
      /take\s*\(\s*1\s*\)/g,
    ],
    asyncPipe: [/\|\s*async/g, /async\s*\|/g],
  },
  changeDetection: {
    strategy: [
      /ChangeDetectionStrategy\.OnPush/g,
      /changeDetection:\s*ChangeDetectionStrategy/g,
    ],
    optimization: [/trackBy/g, /\*ngFor.*trackBy/g, /trackByFn/g],
    lifecycle: [/OnDestroy/g, /ngOnDestroy/g, /OnInit/g, /ngOnInit/g],
  },
  performance: {
    lazyLoading: [/loadChildren/g, /import\(.*\.module/g, /lazy.*load/gi],
    virtualScrolling: [
      /cdk-virtual-scroll/g,
      /virtual.*scroll/gi,
      /\*cdkVirtualFor/g,
    ],
    onPush: [/OnPush/g, /ChangeDetectionStrategy\.OnPush/g],
  },
  rag: {
    httpCalls: [/http\.get/g, /http\.post/g, /httpClient/g],
    streaming: [
      /EventSource/g,
      /WebSocket/g,
      /Server.*Sent.*Events/gi,
      /streaming/gi,
    ],
    stateManagement: [
      /@ngrx/g,
      /store\.dispatch/g,
      /store\.select/g,
      /akita/gi,
      /state.*management/gi,
    ],
  },
};

// Memory leak patterns
const MEMORY_LEAK_PATTERNS = {
  subscriptions: [
    /\.subscribe\s*\(\s*[^)]*\)\s*;?\s*$/gm, // Subscribe without unsubscribe
    /interval\s*\(/g,
    /timer\s*\(/g,
    /fromEvent\s*\(/g,
  ],
  eventListeners: [
    /addEventListener/g,
    /document\.addEventListener/g,
    /window\.addEventListener/g,
  ],
  intervals: [/setInterval/g, /setTimeout/g, /requestAnimationFrame/g],
};

// Performance anti-patterns
const PERFORMANCE_ANTIPATTERNS = {
  changeDetection: [
    /function\s*\(/g, // Functions in templates
    /\(\)\s*=>/g, // Arrow functions in templates
    /\*ngFor.*length/g, // Accessing length in ngFor
  ],
  http: [
    /http.*subscribe.*subscribe/g, // Nested HTTP calls
    /forkJoin.*\.subscribe/g, // ForkJoin without proper error handling
  ],
};

class AngularValidator {
  constructor(projectRoot) {
    this.projectRoot = projectRoot;
    this.issues = [];
  }

  validate() {
    console.log("🔍 Validating Angular patterns for RAG applications...");

    this.validateAngularProject();
    this.validateRxJSPatterns();
    this.validateChangeDetection();
    this.validatePerformancePatterns();
    this.validateRAGSpecificPatterns();
    this.validateMemoryLeaks();

    return this.generateReport();
  }

  validateAngularProject() {
    // Check if this is an Angular project
    const angularJson = path.join(this.projectRoot, "angular.json");
    const packageJson = path.join(this.projectRoot, "package.json");

    if (!fs.existsSync(angularJson) && !fs.existsSync(packageJson)) {
      this.addIssue(
        "info",
        "Not an Angular project",
        "Angular validator skipped",
      );
      return;
    }

    if (fs.existsSync(packageJson)) {
      try {
        const pkg = JSON.parse(fs.readFileSync(packageJson, "utf8"));

        // Check Angular version
        const angularCore = pkg.dependencies?.["@angular/core"];
        if (!angularCore) {
          this.addIssue(
            "info",
            "Angular not detected in dependencies",
            "Skipping Angular validation",
          );
          return;
        }

        // Check for common RAG dependencies
        this.checkRAGDependencies(pkg);

        // Check for RxJS version
        const rxjs = pkg.dependencies?.["rxjs"];
        if (!rxjs) {
          this.addIssue(
            "warning",
            "RxJS not found in dependencies",
            "RxJS required for Angular reactive patterns",
          );
        }
      } catch (error) {
        this.addIssue("error", "Cannot parse package.json", error.message);
      }
    }
  }

  checkRAGDependencies(pkg) {
    const ragDeps = {
      openai: "OpenAI SDK for embeddings",
      langchain: "LangChain for RAG workflows",
      "@aws-sdk/client-bedrock": "AWS Bedrock client",
      "@aws-sdk/client-s3": "S3 client for document storage",
      "socket.io-client": "WebSocket for streaming responses",
      rxjs: "Reactive programming",
    };

    Object.entries(ragDeps).forEach(([dep, desc]) => {
      if (pkg.dependencies?.[dep] || pkg.devDependencies?.[dep]) {
        this.addIssue("info", `RAG dependency found: ${dep}`, desc);
      }
    });
  }

  validateRxJSPatterns() {
    const tsFiles = this.findFiles(["*.ts", "*.component.ts", "*.service.ts"]);

    tsFiles.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check for subscription patterns
        this.checkSubscriptionPatterns(content, file);

        // Check for memory leak potential
        this.checkMemoryLeakPatterns(content, file);

        // Check for proper unsubscribe patterns
        this.checkUnsubscribePatterns(content, file);
      } catch (error) {
        this.addIssue("error", `Cannot read file: ${file}`, error.message);
      }
    });
  }

  checkSubscriptionPatterns(content, filePath) {
    const subscribeMatches = content.match(
      ANGULAR_PATTERNS.rxjs.subscriptions[0],
    );
    const unsubscribeMatches = content.match(
      /\.unsubscribe|takeUntil|takeWhile|first\(\)|take\(1\)/g,
    );

    if (subscribeMatches) {
      const subscribeCount = subscribeMatches.length;
      const unsubscribeCount = unsubscribeMatches
        ? unsubscribeMatches.length
        : 0;

      if (subscribeCount > unsubscribeCount) {
        this.addIssue(
          "error",
          `Potential memory leak: ${subscribeCount} subscriptions vs ${unsubscribeCount} unsubscribe patterns: ${filePath}`,
          "Use takeUntil(destroy$), async pipe, or manual unsubscribe in ngOnDestroy",
        );
      }

      // Check for OnDestroy implementation
      if (subscribeCount > 0 && !content.includes("OnDestroy")) {
        this.addIssue(
          "warning",
          `Component with subscriptions missing OnDestroy: ${filePath}`,
          "Implement OnDestroy to handle subscription cleanup",
        );
      }
    }

    // Check for async pipe usage (good practice)
    const asyncPipeMatches = content.match(ANGULAR_PATTERNS.rxjs.asyncPipe[0]);
    if (subscribeMatches && !asyncPipeMatches) {
      this.addIssue(
        "info",
        `Consider using async pipe instead of manual subscription: ${filePath}`,
        "Async pipe automatically handles subscription lifecycle",
      );
    }
  }

  checkMemoryLeakPatterns(content, filePath) {
    // Check for interval/timer without cleanup
    MEMORY_LEAK_PATTERNS.subscriptions.forEach((pattern) => {
      if (pattern.test(content)) {
        if (
          !content.includes("clearInterval") &&
          !content.includes("takeUntil")
        ) {
          this.addIssue(
            "error",
            `Potential memory leak from timer/interval: ${filePath}`,
            "Clear intervals in ngOnDestroy or use takeUntil operator",
          );
        }
      }
    });

    // Check for event listeners
    MEMORY_LEAK_PATTERNS.eventListeners.forEach((pattern) => {
      if (pattern.test(content)) {
        if (!content.includes("removeEventListener")) {
          this.addIssue(
            "warning",
            `Event listener without cleanup: ${filePath}`,
            "Remove event listeners in ngOnDestroy",
          );
        }
      }
    });
  }

  checkUnsubscribePatterns(content, filePath) {
    // Check for proper unsubscribe patterns
    if (content.includes("subscribe(")) {
      // Check for takeUntil pattern (best practice)
      if (content.includes("takeUntil")) {
        if (
          !content.includes("destroy$") &&
          !content.includes("unsubscribe$")
        ) {
          this.addIssue(
            "info",
            `takeUntil used but destroy$ subject not found: ${filePath}`,
            "Ensure destroy$ subject is properly implemented",
          );
        }
      }

      // Check for subscription assignment
      if (
        !content.includes("subscription") &&
        !content.includes("takeUntil") &&
        !content.includes("| async")
      ) {
        this.addIssue(
          "warning",
          `Manual subscription without assignment: ${filePath}`,
          "Assign subscription to variable for proper cleanup",
        );
      }
    }
  }

  validateChangeDetection() {
    const componentFiles = this.findFiles(["*.component.ts"]);

    componentFiles.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check for OnPush strategy
        if (!content.includes("OnPush")) {
          this.addIssue(
            "info",
            `Component not using OnPush strategy: ${file}`,
            "Consider OnPush for better performance in RAG applications",
          );
        }

        // Check for trackBy in templates
        const templateFile = file.replace(".component.ts", ".component.html");
        if (fs.existsSync(templateFile)) {
          this.checkTemplatePatterns(templateFile);
        }
      } catch (error) {
        this.addIssue(
          "error",
          `Cannot read component file: ${file}`,
          error.message,
        );
      }
    });
  }

  checkTemplatePatterns(templateFile) {
    try {
      const content = fs.readFileSync(templateFile, "utf8");

      // Check for ngFor without trackBy
      const ngForMatches = content.match(/\*ngFor/g);
      const trackByMatches = content.match(/trackBy/g);

      if (ngForMatches && !trackByMatches) {
        this.addIssue(
          "warning",
          `*ngFor without trackBy function: ${templateFile}`,
          "Add trackBy for better performance with dynamic lists",
        );
      }

      // Check for functions in templates (performance issue)
      if (
        content.includes("()") &&
        (content.includes(".length") || content.includes("function"))
      ) {
        this.addIssue(
          "error",
          `Function calls in template: ${templateFile}`,
          "Move function calls to component properties or use OnPush strategy",
        );
      }

      // Check for nested subscriptions in template
      if (content.includes("| async") && content.includes("| async")) {
        const asyncCount = (content.match(/\| async/g) || []).length;
        if (asyncCount > 3) {
          this.addIssue(
            "warning",
            `Multiple async pipes in template (${asyncCount}): ${templateFile}`,
            "Consider combining observables with combineLatest or using resolver",
          );
        }
      }
    } catch (error) {
      this.addIssue(
        "error",
        `Cannot read template file: ${templateFile}`,
        error.message,
      );
    }
  }

  validatePerformancePatterns() {
    const files = this.findFiles(["*.ts", "*.service.ts"]);

    files.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check for lazy loading
        if (file.includes("routing") || file.includes("router")) {
          if (!content.includes("loadChildren")) {
            this.addIssue(
              "info",
              `No lazy loading detected in routing: ${file}`,
              "Consider lazy loading for large RAG applications",
            );
          }
        }

        // Check for virtual scrolling in large lists
        if (
          content.includes("ngFor") &&
          !content.includes("cdk-virtual-scroll")
        ) {
          this.addIssue(
            "info",
            `Large lists without virtual scrolling: ${file}`,
            "Use CDK virtual scrolling for large datasets",
          );
        }
      } catch (error) {
        this.addIssue("error", `Cannot read file: ${file}`, error.message);
      }
    });
  }

  validateRAGSpecificPatterns() {
    const serviceFiles = this.findFiles(["*.service.ts"]);

    serviceFiles.forEach((file) => {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check for RAG service patterns
        this.checkRAGServicePatterns(content, file);

        // Check for streaming patterns
        this.checkStreamingPatterns(content, file);

        // Check for error handling
        this.checkErrorHandling(content, file);
      } catch (error) {
        this.addIssue(
          "error",
          `Cannot read service file: ${file}`,
          error.message,
        );
      }
    });
  }

  checkRAGServicePatterns(content, filePath) {
    // Check for HTTP calls
    if (content.includes("http.")) {
      // Check for proper error handling
      if (!content.includes("catchError")) {
        this.addIssue(
          "warning",
          `HTTP calls without error handling: ${filePath}`,
          "Add catchError operator for robust RAG services",
        );
      }

      // Check for retry logic
      if (!content.includes("retry") && !content.includes("retryWhen")) {
        this.addIssue(
          "info",
          `HTTP calls without retry logic: ${filePath}`,
          "Consider retry for failed API calls in RAG workflows",
        );
      }

      // Check for timeout
      if (!content.includes("timeout")) {
        this.addIssue(
          "warning",
          `HTTP calls without timeout: ${filePath}`,
          "Add timeout for RAG API calls to prevent hanging",
        );
      }
    }

    // Check for caching
    if (content.includes("embedding") || content.includes("search")) {
      if (!content.includes("cache") && !content.includes("Cache")) {
        this.addIssue(
          "info",
          `RAG service without caching: ${filePath}`,
          "Consider caching embeddings and search results",
        );
      }
    }
  }

  checkStreamingPatterns(content, filePath) {
    // Check for streaming implementations
    if (content.includes("EventSource") || content.includes("WebSocket")) {
      if (!content.includes("close") && !content.includes("disconnect")) {
        this.addIssue(
          "error",
          `Streaming connection without cleanup: ${filePath}`,
          "Close streaming connections in ngOnDestroy",
        );
      }

      // Check for error handling in streams
      if (!content.includes("onerror") && !content.includes("error")) {
        this.addIssue(
          "warning",
          `Streaming without error handling: ${filePath}`,
          "Handle streaming errors gracefully",
        );
      }
    }

    // Check for Server-Sent Events patterns
    if (content.includes("Server") && content.includes("Event")) {
      if (!content.includes("readyState")) {
        this.addIssue(
          "info",
          `SSE without connection state check: ${filePath}`,
          "Check connection state for robust streaming",
        );
      }
    }
  }

  checkErrorHandling(content, filePath) {
    // Check for global error handling
    if (content.includes("Observable") && !content.includes("catchError")) {
      this.addIssue(
        "warning",
        `Observable without error handling: ${filePath}`,
        "Add catchError for robust error handling",
      );
    }

    // Check for user-friendly error messages
    if (
      content.includes("error") &&
      !content.includes("user") &&
      !content.includes("message")
    ) {
      this.addIssue(
        "info",
        `Error handling without user-friendly messages: ${filePath}`,
        "Provide user-friendly error messages for RAG failures",
      );
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
            entry.name !== "node_modules" &&
            entry.name !== "dist"
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
      validator: "Angular RAG Validator",
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
    console.log("\n📊 Angular RAG Validation Results:");
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
module.exports = AngularValidator;

// Allow direct execution
if (require.main === module) {
  const validator = new AngularValidator(process.cwd());
  const report = validator.validate();

  if (report.summary.critical > 0 || report.summary.errors > 0) {
    process.exit(1);
  }
}

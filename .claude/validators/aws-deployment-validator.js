// AWS Deployment Validation for ECS Fargate, Lambda, S3, and API Gateway
// Validates deployment configurations, security settings, and best practices

const fs = require('fs');
const path = require('path');

// ECS Fargate patterns
const ECS_PATTERNS = {
  taskDefinition: {
    required: ['family', 'memory', 'cpu', 'networkMode'],
    memory: {
      min: 512,
      max: 30720,
      recommended: 2048
    },
    cpu: {
      min: 256,
      max: 4096,
      recommended: 1024
    }
  },
  service: {
    required: ['desiredCount', 'launchType', 'networkConfiguration'],
    healthCheck: ['healthCheckGracePeriodSeconds', 'targetGroupArn']
  },
  container: {
    required: ['image', 'portMappings', 'logConfiguration'],
    security: ['readonlyRootFilesystem', 'privileged', 'user']
  }
};

// Lambda patterns
const LAMBDA_PATTERNS = {
  configuration: {
    required: ['runtime', 'handler', 'timeout', 'memorySize'],
    runtime: ['nodejs18.x', 'nodejs20.x', 'python3.11', 'python3.12'],
    limits: {
      timeout: { min: 1, max: 900, recommended: 60 },
      memory: { min: 128, max: 10240, recommended: 1024 }
    }
  },
  security: {
    required: ['role', 'executionRole'],
    environment: ['KMS_KEY_ID', 'ENABLE_XRAY']
  },
  vpc: {
    patterns: [/vpcConfig/, /securityGroupIds/, /subnetIds/]
  }
};

// API Gateway patterns
const API_GATEWAY_PATTERNS = {
  configuration: {
    required: ['restApiId', 'stageName', 'deploymentId'],
    security: ['apiKeyRequired', 'authorizationType', 'authorizerId']
  },
  throttling: {
    burstLimit: 5000,
    rateLimit: 10000
  },
  cors: {
    headers: ['Access-Control-Allow-Origin', 'Access-Control-Allow-Methods']
  }
};

// S3 patterns
const S3_PATTERNS = {
  bucket: {
    required: ['BucketName', 'VersioningConfiguration'],
    encryption: ['ServerSideEncryptionConfiguration', 'BucketEncryption'],
    security: ['PublicAccessBlockConfiguration', 'BucketPolicy']
  },
  lifecycle: {
    patterns: [/LifecycleConfiguration/, /transition/, /expiration/]
  }
};

// CloudFormation/Terraform patterns
const IAC_PATTERNS = {
  cloudformation: ['template.yaml', 'template.yml', 'template.json', 'stack.yaml'],
  terraform: ['*.tf', 'terraform.tfvars', 'variables.tf'],
  cdk: ['cdk.json', 'cdk.context.json']
};

class AWSDeploymentValidator {
  constructor(projectRoot) {
    this.projectRoot = projectRoot;
    this.issues = [];
  }

  validate() {
    console.log('🔍 Validating AWS deployment patterns (ECS, Lambda, S3, API Gateway)...');

    this.validateECSConfiguration();
    this.validateLambdaFunctions();
    this.validateAPIGateway();
    this.validateS3Buckets();
    this.validateIaCTemplates();
    this.validateDockerfiles();
    this.validateEnvironmentVariables();

    return this.generateReport();
  }

  validateECSConfiguration() {
    const taskDefFiles = this.findFiles([
      '*task-definition*.json',
      '*task-def*.json',
      '*ecs*.json',
      '*fargate*.json'
    ]);

    taskDefFiles.forEach(file => {
      try {
        const content = fs.readFileSync(file, 'utf8');
        const taskDef = JSON.parse(content);

        this.checkECSTaskDefinition(taskDef, file);

      } catch (error) {
        // Not JSON or parsing error
      }
    });

    // Check for ECS service definitions
    const serviceFiles = this.findFiles(['*service*.json', '*ecs-service*.yml']);
    serviceFiles.forEach(file => {
      this.checkECSService(file);
    });
  }

  checkECSTaskDefinition(taskDef, filePath) {
    // Check memory and CPU
    if (taskDef.memory) {
      const memory = parseInt(taskDef.memory);
      if (memory < ECS_PATTERNS.taskDefinition.memory.min) {
        this.addIssue('error',
          `ECS task memory below minimum (${memory}MB): ${filePath}`,
          `Minimum memory is ${ECS_PATTERNS.taskDefinition.memory.min}MB`
        );
      }
      if (memory < ECS_PATTERNS.taskDefinition.memory.recommended) {
        this.addIssue('warning',
          `Low memory for production workload (${memory}MB): ${filePath}`,
          `Recommend at least ${ECS_PATTERNS.taskDefinition.memory.recommended}MB for RAG workloads`
        );
      }
    }

    // Check container definitions
    if (taskDef.containerDefinitions) {
      taskDef.containerDefinitions.forEach((container, idx) => {
        // Check logging
        if (!container.logConfiguration) {
          this.addIssue('error',
            `No logging configured for container ${idx}: ${filePath}`,
            'Configure CloudWatch logging for containers'
          );
        }

        // Check health check
        if (!container.healthCheck) {
          this.addIssue('warning',
            `No health check for container ${idx}: ${filePath}`,
            'Add health check for container monitoring'
          );
        }

        // Check secrets management
        if (container.environment) {
          container.environment.forEach(env => {
            if (env.name.includes('KEY') || env.name.includes('SECRET')) {
              this.addIssue('critical',
                `Potential secret in environment variable: ${filePath}`,
                'Use AWS Secrets Manager or Parameter Store'
              );
            }
          });
        }

        // Check for security settings
        if (container.privileged === true) {
          this.addIssue('error',
            `Container running in privileged mode: ${filePath}`,
            'Disable privileged mode for security'
          );
        }
      });
    }

    // Check network mode
    if (taskDef.networkMode !== 'awsvpc') {
      this.addIssue('warning',
        `ECS task not using awsvpc network mode: ${filePath}`,
        'Use awsvpc for Fargate compatibility'
      );
    }
  }

  checkECSService(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');

      // Check for auto-scaling
      if (!content.includes('AutoScaling') && !content.includes('TargetTrackingScaling')) {
        this.addIssue('info',
          `No auto-scaling configured for ECS service: ${filePath}`,
          'Configure auto-scaling for production workloads'
        );
      }

      // Check for load balancer
      if (!content.includes('loadBalancer') && !content.includes('targetGroup')) {
        this.addIssue('warning',
          `No load balancer configured: ${filePath}`,
          'Add ALB/NLB for high availability'
        );
      }

    } catch (error) {
      // File reading error
    }
  }

  validateLambdaFunctions() {
    const lambdaFiles = this.findFiles([
      '*lambda*.js', '*lambda*.ts', '*lambda*.py',
      '*handler*.js', '*handler*.ts', '*handler*.py',
      'serverless.yml', 'serverless.yaml'
    ]);

    lambdaFiles.forEach(file => {
      try {
        const content = fs.readFileSync(file, 'utf8');

        // Check Lambda handler
        if (file.endsWith('.js') || file.endsWith('.ts') || file.endsWith('.py')) {
          this.checkLambdaHandler(content, file);
        }

        // Check serverless configuration
        if (file.includes('serverless')) {
          this.checkServerlessConfig(content, file);
        }

      } catch (error) {
        this.addIssue('error', `Cannot read file: ${file}`, error.message);
      }
    });
  }

  checkLambdaHandler(content, filePath) {
    // Check for handler export
    const hasHandler = content.includes('exports.handler') ||
                      content.includes('export const handler') ||
                      content.includes('def lambda_handler');

    if (!hasHandler) {
      this.addIssue('warning',
        `Lambda handler not found or improperly exported: ${filePath}`,
        'Ensure handler function is properly exported'
      );
    }

    // Check for async/await usage
    if (content.includes('async') && !content.includes('await')) {
      this.addIssue('info',
        `Async function without await: ${filePath}`,
        'Ensure proper async/await usage'
      );
    }

    // Check for error handling
    if (!content.includes('try') || !content.includes('catch')) {
      this.addIssue('warning',
        `No error handling in Lambda function: ${filePath}`,
        'Add try-catch for error handling'
      );
    }

    // Check for timeout monitoring
    if (!content.includes('getRemainingTimeInMillis')) {
      this.addIssue('info',
        `No timeout monitoring: ${filePath}`,
        'Monitor remaining execution time for long operations'
      );
    }

    // Check for cold start optimization
    const hasWarmup = content.includes('warmup') ||
                     content.includes('WARM_START') ||
                     content.includes('keep-warm');

    if (!hasWarmup) {
      this.addIssue('info',
        `No cold start optimization: ${filePath}`,
        'Consider implementing warmup strategy'
      );
    }
  }

  checkServerlessConfig(content, filePath) {
    // Check memory configuration
    if (!content.includes('memorySize')) {
      this.addIssue('warning',
        `No memory configuration in serverless.yml: ${filePath}`,
        'Set memorySize for Lambda functions'
      );
    }

    // Check timeout configuration
    if (!content.includes('timeout')) {
      this.addIssue('warning',
        `No timeout configuration: ${filePath}`,
        'Set appropriate timeout values'
      );
    }

    // Check for VPC configuration
    if (content.includes('vpc:')) {
      if (!content.includes('securityGroupIds') || !content.includes('subnetIds')) {
        this.addIssue('error',
          `Incomplete VPC configuration: ${filePath}`,
          'Specify both securityGroupIds and subnetIds'
        );
      }
    }

    // Check for environment variables
    if (content.includes('environment:') &&
        (content.includes('API_KEY') || content.includes('SECRET'))) {
      this.addIssue('critical',
        `Potential secrets in serverless.yml: ${filePath}`,
        'Use AWS Secrets Manager or SSM Parameter Store'
      );
    }
  }

  validateAPIGateway() {
    const apiFiles = this.findFiles([
      '*api-gateway*.json', '*api-gateway*.yml',
      'openapi*.json', 'openapi*.yaml',
      'swagger*.json', 'swagger*.yaml'
    ]);

    apiFiles.forEach(file => {
      try {
        const content = fs.readFileSync(file, 'utf8');
        this.checkAPIGatewayConfig(content, file);

      } catch (error) {
        // File reading error
      }
    });
  }

  checkAPIGatewayConfig(content, filePath) {
    // Check for authentication
    if (!content.includes('authorizer') && !content.includes('authorizationType')) {
      this.addIssue('error',
        `No authentication configured for API Gateway: ${filePath}`,
        'Add API authentication (IAM, Cognito, or Lambda authorizer)'
      );
    }

    // Check for throttling
    if (!content.includes('throttle') && !content.includes('rateLimit')) {
      this.addIssue('warning',
        `No throttling configured: ${filePath}`,
        'Configure rate limiting to prevent abuse'
      );
    }

    // Check for CORS
    if (!content.includes('cors') && !content.includes('Access-Control')) {
      this.addIssue('info',
        `No CORS configuration: ${filePath}`,
        'Configure CORS for browser-based access'
      );
    }

    // Check for request validation
    if (!content.includes('requestValidator') && !content.includes('validateRequest')) {
      this.addIssue('warning',
        `No request validation: ${filePath}`,
        'Add request validation for API inputs'
      );
    }
  }

  validateS3Buckets() {
    const s3Files = this.findFiles([
      '*s3*.json', '*s3*.yml', '*bucket*.json', '*bucket*.yml',
      'template.yaml', 'template.yml'
    ]);

    s3Files.forEach(file => {
      try {
        const content = fs.readFileSync(file, 'utf8');

        if (content.includes('AWS::S3::Bucket') || content.includes('s3:')) {
          this.checkS3Configuration(content, file);
        }

      } catch (error) {
        // File reading error
      }
    });
  }

  checkS3Configuration(content, filePath) {
    // Check for versioning
    if (!content.includes('VersioningConfiguration') && !content.includes('versioning')) {
      this.addIssue('warning',
        `S3 bucket versioning not configured: ${filePath}`,
        'Enable versioning for data protection'
      );
    }

    // Check for encryption
    if (!content.includes('BucketEncryption') &&
        !content.includes('ServerSideEncryption')) {
      this.addIssue('error',
        `S3 bucket encryption not configured: ${filePath}`,
        'Enable server-side encryption (SSE-S3 or SSE-KMS)'
      );
    }

    // Check for public access block
    if (!content.includes('PublicAccessBlockConfiguration')) {
      this.addIssue('error',
        `No public access block configuration: ${filePath}`,
        'Configure PublicAccessBlockConfiguration to prevent data leaks'
      );
    }

    // Check for lifecycle policies
    if (!content.includes('LifecycleConfiguration')) {
      this.addIssue('info',
        `No lifecycle configuration: ${filePath}`,
        'Configure lifecycle policies for cost optimization'
      );
    }

    // Check for bucket policies
    if (content.includes('BucketPolicy')) {
      if (content.includes('Principal": "*"') || content.includes('Principal: "*"')) {
        this.addIssue('critical',
          `S3 bucket policy allows public access: ${filePath}`,
          'Restrict bucket policy principals'
        );
      }
    }
  }

  validateIaCTemplates() {
    const iacFiles = this.findFiles([
      ...IAC_PATTERNS.cloudformation,
      ...IAC_PATTERNS.terraform,
      ...IAC_PATTERNS.cdk
    ]);

    iacFiles.forEach(file => {
      try {
        const content = fs.readFileSync(file, 'utf8');

        // Check for hardcoded values
        if (content.includes('arn:aws') && content.includes(':123456789012:')) {
          this.addIssue('error',
            `Hardcoded AWS account ID: ${file}`,
            'Use parameters or variables for account IDs'
          );
        }

        // Check for parameter usage
        if (file.includes('template') && !content.includes('Parameters')) {
          this.addIssue('info',
            `No parameters defined in template: ${file}`,
            'Use parameters for reusability'
          );
        }

        // Check for outputs
        if (file.includes('template') && !content.includes('Outputs')) {
          this.addIssue('info',
            `No outputs defined in template: ${file}`,
            'Define outputs for cross-stack references'
          );
        }

      } catch (error) {
        // File reading error
      }
    });
  }

  validateDockerfiles() {
    const dockerfiles = this.findFiles(['Dockerfile', 'Dockerfile.*']);

    dockerfiles.forEach(file => {
      try {
        const content = fs.readFileSync(file, 'utf8');

        // Check for non-root user
        if (!content.includes('USER')) {
          this.addIssue('error',
            `Docker container running as root: ${file}`,
            'Add USER directive to run as non-root'
          );
        }

        // Check for health check
        if (!content.includes('HEALTHCHECK')) {
          this.addIssue('warning',
            `No HEALTHCHECK in Dockerfile: ${file}`,
            'Add HEALTHCHECK for container monitoring'
          );
        }

        // Check for multi-stage build
        const fromCount = (content.match(/FROM/g) || []).length;
        if (fromCount === 1) {
          this.addIssue('info',
            `Single-stage Docker build: ${file}`,
            'Consider multi-stage builds for smaller images'
          );
        }

        // Check for secrets
        if (content.includes('ARG') &&
            (content.includes('PASSWORD') || content.includes('SECRET'))) {
          this.addIssue('critical',
            `Potential secrets in Dockerfile: ${file}`,
            'Never include secrets in Dockerfiles'
          );
        }

      } catch (error) {
        this.addIssue('error', `Cannot read file: ${file}`, error.message);
      }
    });
  }

  validateEnvironmentVariables() {
    const envFiles = this.findFiles(['.env', '.env.*', '*.env']);

    envFiles.forEach(file => {
      try {
        const content = fs.readFileSync(file, 'utf8');

        // Check for AWS credentials
        if (content.includes('AWS_ACCESS_KEY_ID') ||
            content.includes('AWS_SECRET_ACCESS_KEY')) {
          this.addIssue('critical',
            `AWS credentials in environment file: ${file}`,
            'Use IAM roles instead of hardcoded credentials'
          );
        }

        // Check for production values
        if (file.includes('.env') && !file.includes('.example')) {
          this.addIssue('warning',
            `Environment file should not be committed: ${file}`,
            'Add to .gitignore and use .env.example instead'
          );
        }

      } catch (error) {
        // File reading error
      }
    });
  }

  findFiles(patterns) {
    const files = [];

    const searchDir = (dir) => {
      try {
        const entries = fs.readdirSync(dir, { withFileTypes: true });

        entries.forEach(entry => {
          const fullPath = path.join(dir, entry.name);

          if (entry.isDirectory() && !entry.name.startsWith('.') &&
              entry.name !== 'node_modules') {
            searchDir(fullPath);
          } else if (entry.isFile()) {
            patterns.forEach(pattern => {
              if (pattern.startsWith('*')) {
                if (entry.name.endsWith(pattern.slice(1))) {
                  files.push(fullPath);
                }
              } else if (pattern.endsWith('*')) {
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

  addIssue(severity, message, suggestion = '') {
    this.issues.push({ severity, message, suggestion });
  }

  generateReport() {
    const report = {
      validator: 'AWS Deployment Validator (ECS/Lambda/S3/API Gateway)',
      timestamp: new Date().toISOString(),
      summary: {
        total: this.issues.length,
        critical: this.issues.filter(i => i.severity === 'critical').length,
        errors: this.issues.filter(i => i.severity === 'error').length,
        warnings: this.issues.filter(i => i.severity === 'warning').length,
        info: this.issues.filter(i => i.severity === 'info').length
      },
      issues: this.issues
    };

    // Print summary
    console.log('\n📊 AWS Deployment Validation Results:');
    console.log(`  Critical: ${report.summary.critical}`);
    console.log(`  Errors: ${report.summary.errors}`);
    console.log(`  Warnings: ${report.summary.warnings}`);
    console.log(`  Info: ${report.summary.info}`);

    // Print critical and error issues
    this.issues.forEach(issue => {
      if (issue.severity === 'critical' || issue.severity === 'error') {
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
module.exports = AWSDeploymentValidator;

// Allow direct execution
if (require.main === module) {
  const validator = new AWSDeploymentValidator(process.cwd());
  const report = validator.validate();

  if (report.summary.critical > 0 || report.summary.errors > 0) {
    process.exit(1);
  }
}
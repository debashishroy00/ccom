// ESLint Configuration for Enterprise RAG/Vector/Graph Projects
// Optimized for ChromaDB, Weaviate, FAISS, Neo4j, Hybrid RAG, Agentic RAG

module.exports = {
  extends: ["eslint:recommended"],
  env: {
    node: true,
    es2022: true,
  },
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: "module",
  },
  rules: {
    // === VECTOR STORE PATTERNS ===

    // Memory management for embeddings (critical for large vector operations)
    "max-params": ["error", 5], // Vector functions get complex fast
    "max-statements": ["error", 25], // Force chunking of embedding operations
    "max-depth": ["error", 4], // Prevent nested vector operations
    "max-lines-per-function": ["error", 100], // Break down complex retrieval logic

    // Async patterns for vector operations (ChromaDB, Weaviate, FAISS)
    "no-await-in-loop": "error", // Force batch processing for embeddings
    "require-await": "error", // Prevent fake async in vector operations
    "no-return-await": "error", // Optimize async vector calls
    "prefer-promise-all": "error", // Batch vector operations

    // === GRAPH DATABASE PATTERNS (Neo4j, etc.) ===

    // Cypher injection prevention
    "prefer-template": "error", // Prevent Cypher injection via concatenation
    "no-template-curly-in-string": "error", // Catch accidental template usage
    quotes: ["error", "single", { allowTemplateLiterals: false }], // Consistent quoting

    // === SECURITY FOR MULTI-TENANT RAG ===

    // Code injection prevention
    "no-eval": "error",
    "no-implied-eval": "error",
    "no-new-func": "error",
    "no-script-url": "error",

    // Dynamic access patterns
    "dot-notation": "error", // Prevent dynamic property access
    "no-new-object": "error", // Use object literals

    // === PERFORMANCE PATTERNS ===

    // Array/object management for large datasets
    "no-array-constructor": "error",
    "prefer-spread": "error", // Use spread instead of apply
    "no-useless-concat": "error", // Optimize string operations

    // === RAG-SPECIFIC PATTERNS ===

    // Function naming for clarity in RAG pipelines
    "func-names": ["error", "always"], // Named functions for stack traces
    "consistent-return": "error", // Always return from retrieval functions
    "no-magic-numbers": [
      "error",
      { ignore: [0, 1, -1, 100, 1000, 1536, 1024, 384] },
    ], // Allow common vector dimensions

    // === ERROR HANDLING (Critical for RAG reliability) ===

    "no-throw-literal": "error", // Use Error objects
    "prefer-promise-reject-errors": "error", // Proper promise rejection
    "no-unmodified-loop-condition": "error", // Prevent infinite loops in agents

    // === VARIABLE MANAGEMENT ===

    "no-var": "error", // Use const/let
    "prefer-const": "error", // Immutable by default
    "no-unused-vars": [
      "error",
      { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
    ],
    "no-undef": "error", // Catch typos in vector operations

    // === STYLE CONSISTENCY ===

    semi: ["error", "always"],
    "comma-dangle": ["error", "never"],
    indent: ["error", 2],
    "linebreak-style": ["error", "unix"],
    "no-trailing-spaces": "error",
  },

  // Custom overrides for specific RAG patterns
  overrides: [
    {
      // Vector store files
      files: [
        "**/embeddings/**/*.js",
        "**/vector-store/**/*.js",
        "**/chroma/**/*.js",
        "**/weaviate/**/*.js",
      ],
      rules: {
        "max-statements": ["error", 30], // Vector operations need more statements
        "no-magic-numbers": [
          "error",
          { ignore: [0, 1, -1, 50, 100, 512, 768, 1024, 1536, 3072] },
        ], // Common embedding dimensions
      },
    },
    {
      // Graph database files
      files: ["**/neo4j/**/*.js", "**/graph/**/*.js", "**/cypher/**/*.js"],
      rules: {
        "max-lines-per-function": ["error", 150], // Graph queries can be complex
        "prefer-template": "error", // Critical for Cypher injection prevention
      },
    },
    {
      // Agentic RAG files
      files: ["**/agents/**/*.js", "**/tools/**/*.js", "**/react/**/*.js"],
      rules: {
        "max-depth": ["error", 5], // Agents can have deeper logic
        complexity: ["error", 15], // Allow complex decision trees
        "no-unmodified-loop-condition": "error", // Critical for agent loops
      },
    },
    {
      // Hybrid RAG files (combining multiple retrieval methods)
      files: ["**/hybrid/**/*.js", "**/fusion/**/*.js", "**/rerank/**/*.js"],
      rules: {
        "max-params": ["error", 7], // Fusion functions need more parameters
        "max-statements": ["error", 35], // Complex scoring logic
      },
    },
  ],
};

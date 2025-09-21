/**
 * Shared validation utilities to reduce DRY violations across validators
 * Extracted from multiple validator files to prevent code duplication
 */

/**
 * Check if a string contains potentially sensitive information
 * @param {string} str String to check
 * @returns {boolean} True if string might contain secrets
 */
function containsPotentialSecrets(str) {
    const secretPatterns = [
        /password\s*[=:]\s*['"][^'"]+['"]/i,
        /api[_-]?key\s*[=:]\s*['"][^'"]+['"]/i,
        /secret\s*[=:]\s*['"][^'"]+['"]/i,
        /token\s*[=:]\s*['"][^'"]+['"]/i
    ];

    return secretPatterns.some(pattern => pattern.test(str));
}

/**
 * Check if configuration contains hardcoded values that should be environment variables
 * @param {string} content File content to analyze
 * @returns {Array} Array of issues found
 */
function validateConfigurationSecurity(content) {
    const issues = [];
    const lines = content.split('\n');

    lines.forEach((line, index) => {
        if (containsPotentialSecrets(line)) {
            issues.push({
                line: index + 1,
                message: 'Potential hardcoded secret detected',
                suggestion: 'Use environment variables for sensitive configuration'
            });
        }
    });

    return issues;
}

/**
 * Standard security validation logic shared across validators
 * @param {Object} context Validation context
 * @returns {Array} Security issues found
 */
function performStandardSecurityValidation(context) {
    const issues = [];
    const { content, filename } = context;

    // Check for hardcoded secrets
    const secretIssues = validateConfigurationSecurity(content);
    issues.push(...secretIssues);

    // Check for dangerous functions
    const dangerousPatterns = [
        { pattern: /eval\s*\(/g, message: 'Avoid using eval() - security risk' },
        { pattern: /innerHTML\s*=/g, message: 'Potential XSS risk with innerHTML' },
        { pattern: /document\.write\s*\(/g, message: 'Avoid document.write() - can cause security issues' }
    ];

    dangerousPatterns.forEach(({ pattern, message }) => {
        const matches = content.match(pattern);
        if (matches) {
            issues.push({
                pattern: pattern.source,
                message,
                count: matches.length,
                filename
            });
        }
    });

    return issues;
}

/**
 * Common validation result formatting
 * @param {Array} issues Array of validation issues
 * @param {string} validationType Type of validation performed
 * @returns {Object} Formatted validation result
 */
function formatValidationResult(issues, validationType) {
    return {
        type: validationType,
        timestamp: new Date().toISOString(),
        issueCount: issues.length,
        status: issues.length === 0 ? 'PASS' : 'FAIL',
        issues: issues
    };
}

/**
 * Generate comprehensive validation summary
 * @param {Array} results Array of validation results
 * @returns {Object} Summary with scores and recommendations
 */
function generateValidationSummary(results) {
    const totalIssues = results.reduce((sum, result) => sum + result.issueCount, 0);
    const passedValidations = results.filter(r => r.status === 'PASS').length;
    const score = Math.round((passedValidations / results.length) * 100);

    return {
        overallScore: score,
        totalValidations: results.length,
        passedValidations,
        totalIssues,
        grade: score >= 90 ? 'A' : score >= 80 ? 'B' : score >= 70 ? 'C' : score >= 60 ? 'D' : 'F',
        results
    };
}

module.exports = {
    containsPotentialSecrets,
    validateConfigurationSecurity,
    performStandardSecurityValidation,
    formatValidationResult,
    generateValidationSummary
};
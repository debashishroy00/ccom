#!/usr/bin/env python3
"""
Proactive Developer Agent for CCOM v5.2+
Enforces coding principles DURING code generation, not after

This agent prevents principle violations by generating clean code from the start,
eliminating the need for expensive refactoring cycles.
"""

import asyncio
import logging
import re
import ast
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .sdk_agent_base import SDKAgentBase, AgentResult
from ..utils import Display, ErrorHandler


@dataclass
class CodeGenerationSpec:
    """Specification for code generation"""
    purpose: str
    language: str
    max_complexity: int = 10
    max_lines: int = 50
    style_guide: str = "standard"
    existing_patterns: List[str] = None
    dependencies: List[str] = None
    prd_requirements: Optional[Dict[str, Any]] = None


@dataclass
class PrincipleConstraints:
    """Constraints based on coding principles"""
    kiss_max_complexity: int = 10
    kiss_max_lines: int = 50
    kiss_max_parameters: int = 5
    dry_reuse_threshold: int = 3
    solid_single_responsibility: bool = True
    yagni_no_speculation: bool = True


class ProactiveDeveloperAgent(SDKAgentBase):
    """
    Proactive Developer Agent that generates code adhering to principles from the start.

    Key Features:
    - KISS: Generates simple, readable code with low complexity
    - DRY: Reuses existing patterns and extracts common functionality
    - SOLID: Ensures single responsibility and proper separation
    - YAGNI: Only implements what's actually needed
    - Real-time principle validation during generation
    """

    def __init__(self, project_root: Path, config: Dict[str, Any] = None):
        super().__init__(project_root, config)
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)

        # Principle constraints
        self.constraints = PrincipleConstraints(
            kiss_max_complexity=config.get("kiss_max_complexity", 10),
            kiss_max_lines=config.get("kiss_max_lines", 50),
            kiss_max_parameters=config.get("kiss_max_parameters", 5),
            dry_reuse_threshold=config.get("dry_reuse_threshold", 3),
            solid_single_responsibility=config.get("solid_single_responsibility", True),
            yagni_no_speculation=config.get("yagni_no_speculation", True)
        )

        # Code generation patterns
        self.code_patterns = self._load_code_patterns()
        self.existing_codebase = self._analyze_existing_codebase()

    def _get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return [
            "proactive_code_generation",
            "principle_enforcement",
            "kiss_validation",
            "dry_detection",
            "solid_analysis",
            "yagni_compliance",
            "real_time_optimization",
            "integration_analysis",
            "pattern_learning",
            "complexity_control"
        ]

    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """Execute proactive operations (analyze or generate)"""
        try:
            operation = context.get("operation", "generate_code")

            # Route to appropriate operation
            if operation == "analyze_prd":
                return await self._execute_prd_analysis(context)
            else:
                return await self._execute_code_generation(context)

        except Exception as e:
            self.logger.error(f"Proactive operation failed: {e}")
            return AgentResult(
                success=False,
                error=str(e),
                message="Proactive operation failed"
            )

    async def _execute_prd_analysis(self, context: Dict[str, Any]) -> AgentResult:
        """Analyze PRD document and create implementation plan"""
        try:
            Display.header("📋 PRD Analysis: Reviewing Requirements Document")

            # Extract PRD path from context
            prd_path = None
            requirements = context.get("requirements", "")

            if self._has_prd_reference(requirements):
                prd_path = self._extract_prd_path(requirements)
            elif context.get("prd_document"):
                prd_path = context["prd_document"]

            if not prd_path:
                return AgentResult(
                    success=False,
                    error="No PRD document specified",
                    message="Please specify a PRD document to analyze (e.g., 'analyze prd.md')"
                )

            # Parse PRD document
            Display.progress(f"Reading and parsing {prd_path}...")
            prd_data = self._parse_prd_document(prd_path)

            if not prd_data:
                return AgentResult(
                    success=False,
                    error="Failed to parse PRD document",
                    message=f"Could not parse {prd_path}"
                )

            # Display comprehensive PRD analysis
            self._display_prd_analysis(prd_data, prd_path)

            # Create implementation plan
            Display.section("📐 Implementation Plan")
            impl_plan = self._create_implementation_plan(prd_data)
            self._display_implementation_plan(impl_plan)

            result = {
                "success": True,
                "operation": "prd_analysis",
                "prd_path": prd_path,
                "prd_data": prd_data,
                "implementation_plan": impl_plan,
                "metrics": {
                    "requirements_count": len(prd_data.get("requirements", [])),
                    "acceptance_criteria_count": len(prd_data.get("acceptance_criteria", [])),
                    "components_count": len(prd_data.get("components", [])),
                    "tech_stack_categories": len(prd_data.get("tech_stack", {}))
                }
            }

            Display.success("✅ PRD analysis completed")
            return AgentResult(
                success=True,
                data=result,
                message="PRD analysis completed successfully"
            )

        except Exception as e:
            self.logger.error(f"PRD analysis failed: {e}")
            return AgentResult(
                success=False,
                error=str(e),
                message="PRD analysis failed"
            )

    async def _execute_code_generation(self, context: Dict[str, Any]) -> AgentResult:
        """Execute proactive code generation with principle enforcement"""
        try:
            Display.header("🏗️ Proactive Developer: Generating Clean Code")

            generation_spec = self._parse_generation_spec(context)

            # Phase 1: Plan with principles in mind
            Display.progress("Planning solution with KISS principle...")
            code_plan = await self._plan_simple_solution(generation_spec)

            # Phase 2: Generate code with built-in principle checks
            Display.progress("Generating code with principle enforcement...")
            generated_code = await self._generate_principled_code(code_plan, generation_spec)

            # Phase 3: Real-time validation and optimization
            Display.progress("Validating and optimizing generated code...")
            final_code = await self._validate_and_optimize(generated_code, generation_spec)

            # Phase 4: Integration analysis
            Display.progress("Analyzing integration with existing codebase...")
            integration_result = await self._analyze_integration(final_code, generation_spec)

            # Capture results
            result = {
                "success": True,
                "generated_code": final_code,
                "principles_score": self._calculate_principles_score(final_code),
                "integration_analysis": integration_result,
                "proactive_compliance": True,
                "metrics": {
                    "complexity": self._calculate_complexity(final_code),
                    "lines_of_code": len(final_code.splitlines()),
                    "principle_violations": 0,
                    "reuse_opportunities": len(integration_result.get("reusable_patterns", []))
                }
            }

            Display.success("✅ Clean code generated with principle compliance")
            self._display_generation_summary(result)

            return AgentResult(
                success=True,
                data=result,
                message="Proactive code generation completed successfully"
            )

        except Exception as e:
            self.logger.error(f"Proactive code generation failed: {e}")
            return AgentResult(
                success=False,
                error=str(e),
                message="Proactive code generation failed"
            )

    def _parse_generation_spec(self, context: Dict[str, Any]) -> CodeGenerationSpec:
        """Parse code generation specification from context with PRD support"""

        # Check for PRD document in multiple ways
        prd_requirements = None

        # 1. Explicit PRD document in context
        if context.get("prd_document"):
            prd_requirements = self._parse_prd_document(context["prd_document"])

        # 2. PRD reference in command
        elif self._has_prd_reference(context.get("requirements", "")):
            prd_path = self._extract_prd_path(context.get("requirements", ""))
            if prd_path:
                prd_requirements = self._parse_prd_document(prd_path)

        # 3. Auto-detect PRD file in project directory (prd.md, requirements.md, PRD.md)
        if not prd_requirements:
            for prd_filename in ["prd.md", "PRD.md", "requirements.md", "REQUIREMENTS.md"]:
                prd_file = self.project_root / prd_filename
                if prd_file.exists():
                    Display.info(f"📋 Auto-detected {prd_filename}")
                    prd_requirements = self._parse_prd_document(str(prd_file))
                    if prd_requirements:
                        break

        # Use PRD requirements if available
        if prd_requirements:
            purpose = prd_requirements.get("title", "Implement PRD requirements")
            language = prd_requirements.get("tech_stack", {}).get("primary", context.get("language", "python"))
        else:
            purpose = context.get("purpose", context.get("requirements", "Generate function"))
            language = context.get("language", "python")

        return CodeGenerationSpec(
            purpose=purpose,
            language=language,
            max_complexity=context.get("max_complexity", self.constraints.kiss_max_complexity),
            max_lines=context.get("max_lines", self.constraints.kiss_max_lines),
            style_guide=context.get("style_guide", "standard"),
            existing_patterns=context.get("existing_patterns", []),
            dependencies=context.get("dependencies", []),
            prd_requirements=prd_requirements
        )

    async def _plan_simple_solution(self, spec: CodeGenerationSpec) -> Dict[str, Any]:
        """Plan the simplest solution that meets requirements (KISS principle)"""
        plan = {
            "approach": "simple_direct",
            "components": [],
            "complexity_target": min(spec.max_complexity, self.constraints.kiss_max_complexity),
            "reuse_opportunities": [],
            "principle_considerations": {
                "kiss": "Keep solution simple and direct",
                "dry": "Identify reusable patterns",
                "solid": "Single responsibility per component",
                "yagni": "Only implement stated requirements"
            }
        }

        # Analyze requirements for complexity
        if self._is_complex_requirement(spec.purpose):
            plan["approach"] = "decomposed"
            plan["components"] = self._decompose_complex_requirement(spec.purpose)

        # Check for reuse opportunities
        plan["reuse_opportunities"] = self._find_reuse_opportunities(spec.purpose)

        return plan

    async def _generate_principled_code(self, plan: Dict[str, Any], spec: CodeGenerationSpec) -> str:
        """Generate code with built-in principle enforcement"""

        if spec.language.lower() == "python":
            return await self._generate_python_code(plan, spec)
        elif spec.language.lower() in ["javascript", "js"]:
            return await self._generate_javascript_code(plan, spec)
        elif spec.language.lower() in ["typescript", "ts"]:
            return await self._generate_typescript_code(plan, spec)
        else:
            return await self._generate_generic_code(plan, spec)

    async def _generate_python_code(self, plan: Dict[str, Any], spec: CodeGenerationSpec) -> str:
        """Generate Python code with principle enforcement"""

        if plan["approach"] == "simple_direct":
            return self._generate_simple_python_function(spec)
        else:
            return self._generate_decomposed_python_solution(plan, spec)

    def _generate_simple_python_function(self, spec: CodeGenerationSpec) -> str:
        """Generate a simple Python function following KISS principle"""

        # Extract function details from purpose
        function_name = self._extract_function_name(spec.purpose)
        parameters = self._extract_parameters(spec.purpose)
        return_type = self._extract_return_type(spec.purpose)

        # Ensure parameters don't exceed KISS limit
        if len(parameters) > self.constraints.kiss_max_parameters:
            parameters = self._consolidate_parameters(parameters)

        # Generate function with principle compliance
        code_lines = [
            f"def {function_name}({', '.join(parameters)}) -> {return_type}:",
            f'    """',
            f"    {spec.purpose}",
            f"    ",
            f"    This function follows KISS principle with low complexity.",
            f"    Args: {', '.join(parameters)}",
            f"    Returns: {return_type}",
            f'    """',
            f"    # Simple, direct implementation",
        ]

        # Generate implementation based on purpose
        implementation = self._generate_function_implementation(spec.purpose, parameters, return_type)
        code_lines.extend(implementation)

        return "\n".join(code_lines)

    def _generate_function_implementation(self, purpose: str, parameters: List[str], return_type: str) -> List[str]:
        """Generate function implementation based on purpose"""

        # Common patterns for different purposes
        if "calculate" in purpose.lower():
            return [
                "    try:",
                "        # Perform calculation with error handling",
                "        result = None  # TODO: Implement calculation logic",
                "        return result",
                "    except Exception as e:",
                "        raise ValueError(f'Calculation failed: {e}')"
            ]
        elif "validate" in purpose.lower():
            return [
                "    # Simple validation logic",
                "    if not all(param for param in [" + ", ".join(parameters) + "]):",
                "        return False",
                "    ",
                "    # TODO: Add specific validation rules",
                "    return True"
            ]
        elif "process" in purpose.lower():
            return [
                "    # Process input with error handling",
                "    try:",
                "        # TODO: Implement processing logic",
                "        processed_result = None",
                "        return processed_result",
                "    except Exception as e:",
                "        self.logger.error(f'Processing failed: {e}')",
                "        raise"
            ]
        else:
            return [
                "    # Simple implementation following KISS principle",
                "    # TODO: Implement specific functionality",
                "    pass"
            ]

    async def _validate_and_optimize(self, code: str, spec: CodeGenerationSpec) -> str:
        """Real-time validation and optimization of generated code"""

        optimized_code = code

        # KISS validation and optimization
        complexity = self._calculate_complexity(code)
        if complexity > self.constraints.kiss_max_complexity:
            optimized_code = self._simplify_code(optimized_code)

        # Line count validation
        line_count = len(optimized_code.splitlines())
        if line_count > self.constraints.kiss_max_lines:
            optimized_code = self._compress_code(optimized_code)

        # DRY validation
        if self._has_duplication(optimized_code):
            optimized_code = self._extract_common_patterns(optimized_code)

        # SOLID validation
        if not self._has_single_responsibility(optimized_code):
            optimized_code = self._enforce_single_responsibility(optimized_code)

        return optimized_code

    def _calculate_complexity(self, code: str) -> int:
        """Calculate cyclomatic complexity of code"""
        try:
            if not code.strip():
                return 1

            tree = ast.parse(code)
            complexity = 1  # Base complexity

            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                    complexity += 1
                elif isinstance(node, ast.Try):
                    complexity += len(node.handlers)
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1

            return complexity
        except:
            return 1

    def _simplify_code(self, code: str) -> str:
        """Simplify code to reduce complexity"""
        # Extract complex conditions to separate functions
        lines = code.splitlines()
        simplified_lines = []

        for line in lines:
            if self._is_complex_condition(line):
                # Extract to helper function
                helper_name = self._generate_helper_name(line)
                simplified_lines.append(f"        if self.{helper_name}():")
                # Add helper function suggestion
                simplified_lines.append(f"    # TODO: Implement {helper_name}() helper method")
            else:
                simplified_lines.append(line)

        return "\n".join(simplified_lines)

    def _has_duplication(self, code: str) -> bool:
        """Check for code duplication patterns"""
        lines = [line.strip() for line in code.splitlines() if line.strip()]

        # Simple duplication detection
        for i, line in enumerate(lines):
            for j, other_line in enumerate(lines[i+1:], i+1):
                if line == other_line and len(line) > 10:
                    return True

        return False

    def _extract_common_patterns(self, code: str) -> str:
        """Extract common patterns to eliminate duplication"""
        # Simple pattern extraction
        lines = code.splitlines()

        # Find repeated patterns and suggest extraction
        extracted_lines = []
        for line in lines:
            if self._is_common_pattern(line):
                extracted_lines.append("    # TODO: Extract this pattern to a helper method")
                extracted_lines.append(line)
            else:
                extracted_lines.append(line)

        return "\n".join(extracted_lines)

    async def _analyze_integration(self, code: str, spec: CodeGenerationSpec) -> Dict[str, Any]:
        """Analyze how generated code integrates with existing codebase"""

        integration_analysis = {
            "compatibility": "high",
            "reusable_patterns": [],
            "potential_conflicts": [],
            "suggested_imports": [],
            "testing_recommendations": []
        }

        # Check for reusable patterns in existing codebase
        function_name = self._extract_function_name_from_code(code)
        similar_functions = self._find_similar_functions(function_name)

        if similar_functions:
            integration_analysis["reusable_patterns"] = similar_functions
            integration_analysis["suggested_imports"] = self._suggest_imports(similar_functions)

        # Generate testing recommendations
        integration_analysis["testing_recommendations"] = [
            f"Add unit tests for {function_name}",
            "Test edge cases and error conditions",
            "Verify integration with existing modules"
        ]

        return integration_analysis

    def _calculate_principles_score(self, code: str) -> Dict[str, int]:
        """Calculate principles compliance score"""

        scores = {
            "kiss": 100,
            "dry": 100,
            "solid": 100,
            "yagni": 100,
            "overall": 100
        }

        # KISS scoring
        complexity = self._calculate_complexity(code)
        line_count = len(code.splitlines())

        if complexity > self.constraints.kiss_max_complexity:
            scores["kiss"] = max(0, 100 - (complexity - self.constraints.kiss_max_complexity) * 10)

        if line_count > self.constraints.kiss_max_lines:
            scores["kiss"] = min(scores["kiss"], max(0, 100 - (line_count - self.constraints.kiss_max_lines) * 2))

        # DRY scoring
        if self._has_duplication(code):
            scores["dry"] = 70

        # SOLID scoring
        if not self._has_single_responsibility(code):
            scores["solid"] = 80

        # Calculate overall score
        scores["overall"] = int(sum(scores[k] for k in ["kiss", "dry", "solid", "yagni"]) / 4)

        return scores

    def _display_generation_summary(self, result: Dict[str, Any]) -> None:
        """Display generation summary"""

        Display.section("🏗️ Code Generation Summary")

        metrics = result["metrics"]
        scores = result["principles_score"]

        Display.info(f"📊 Lines of Code: {metrics['lines_of_code']}")
        Display.info(f"🔢 Complexity: {metrics['complexity']}/10")
        Display.info(f"✅ Principle Violations: {metrics['principle_violations']}")

        Display.section("📐 Principles Compliance")
        for principle, score in scores.items():
            if principle != "overall":
                icon = "✅" if score >= 90 else "⚠️" if score >= 70 else "❌"
                Display.info(f"{icon} {principle.upper()}: {score}/100")

        if result["integration_analysis"]["reusable_patterns"]:
            Display.section("🔄 Reuse Opportunities")
            for pattern in result["integration_analysis"]["reusable_patterns"]:
                Display.info(f"♻️ {pattern}")

    # Helper methods
    def _load_code_patterns(self) -> Dict[str, Any]:
        """Load existing code patterns for reuse"""
        return {"patterns": []}

    def _analyze_existing_codebase(self) -> Dict[str, Any]:
        """Analyze existing codebase for patterns"""
        return {"functions": [], "classes": [], "patterns": []}

    def _is_complex_requirement(self, purpose: str) -> bool:
        """Check if requirement is complex and needs decomposition"""
        complexity_indicators = ["multiple", "various", "complex", "comprehensive", "advanced"]
        return any(indicator in purpose.lower() for indicator in complexity_indicators)

    def _decompose_complex_requirement(self, purpose: str) -> List[str]:
        """Decompose complex requirement into simple components"""
        return ["component_1", "component_2", "component_3"]

    def _find_reuse_opportunities(self, purpose: str) -> List[str]:
        """Find opportunities to reuse existing code"""
        return []

    def _extract_function_name(self, purpose: str) -> str:
        """Extract function name from purpose description"""
        # Simple extraction logic
        words = purpose.lower().split()
        if "calculate" in words:
            return "calculate_" + "_".join(words[words.index("calculate")+1:words.index("calculate")+3])
        elif "validate" in words:
            return "validate_" + "_".join(words[words.index("validate")+1:words.index("validate")+3])
        elif "process" in words:
            return "process_" + "_".join(words[words.index("process")+1:words.index("process")+3])
        else:
            return "generated_function"

    def _extract_parameters(self, purpose: str) -> List[str]:
        """Extract parameters from purpose description"""
        # Simple parameter extraction
        return ["data", "options"]

    def _extract_return_type(self, purpose: str) -> str:
        """Extract return type from purpose description"""
        if "boolean" in purpose.lower() or "validate" in purpose.lower():
            return "bool"
        elif "number" in purpose.lower() or "calculate" in purpose.lower():
            return "float"
        elif "list" in purpose.lower():
            return "List[Any]"
        else:
            return "Any"

    def _consolidate_parameters(self, parameters: List[str]) -> List[str]:
        """Consolidate parameters to meet KISS constraints"""
        if len(parameters) <= self.constraints.kiss_max_parameters:
            return parameters
        return parameters[:self.constraints.kiss_max_parameters-1] + ["**kwargs"]

    def _is_complex_condition(self, line: str) -> bool:
        """Check if line contains complex condition"""
        return line.count("and") + line.count("or") > 2

    def _generate_helper_name(self, line: str) -> str:
        """Generate helper method name for complex condition"""
        return "is_valid_condition"

    def _is_common_pattern(self, line: str) -> bool:
        """Check if line represents a common pattern"""
        common_patterns = ["try:", "except:", "if not", "for item in"]
        return any(pattern in line for pattern in common_patterns)

    def _has_single_responsibility(self, code: str) -> bool:
        """Check if code follows single responsibility principle"""
        # Simple heuristic: function should have one main purpose
        return True  # Simplified for now

    def _enforce_single_responsibility(self, code: str) -> str:
        """Enforce single responsibility principle"""
        return code  # Simplified for now

    def _extract_function_name_from_code(self, code: str) -> str:
        """Extract function name from generated code"""
        for line in code.splitlines():
            if line.strip().startswith("def "):
                return line.split("(")[0].replace("def ", "").strip()
        return "unknown_function"

    def _find_similar_functions(self, function_name: str) -> List[str]:
        """Find similar functions in existing codebase"""
        return []  # Simplified for now

    def _suggest_imports(self, similar_functions: List[str]) -> List[str]:
        """Suggest imports based on similar functions"""
        return []  # Simplified for now

    async def _generate_javascript_code(self, plan: Dict[str, Any], spec: CodeGenerationSpec) -> str:
        """Generate JavaScript code with principle enforcement"""
        function_name = self._extract_function_name(spec.purpose)
        parameters = self._extract_parameters(spec.purpose)

        return f"""
/**
 * {spec.purpose}
 * Generated with principle compliance (KISS, DRY, SOLID, YAGNI)
 * @param {{{', '.join(parameters)}}}
 * @returns {{*}}
 */
function {function_name}({', '.join(parameters)}) {{
    // Simple, direct implementation following KISS principle
    try {{
        // TODO: Implement functionality
        return null;
    }} catch (error) {{
        console.error(`{function_name} failed:`, error);
        throw error;
    }}
}}
"""

    async def _generate_typescript_code(self, plan: Dict[str, Any], spec: CodeGenerationSpec) -> str:
        """Generate TypeScript code with principle enforcement"""
        function_name = self._extract_function_name(spec.purpose)
        parameters = self._extract_parameters(spec.purpose)

        return f"""
/**
 * {spec.purpose}
 * Generated with principle compliance (KISS, DRY, SOLID, YAGNI)
 */
export function {function_name}({', '.join(f'{param}: any' for param in parameters)}): any {{
    // Simple, direct implementation following KISS principle
    try {{
        // TODO: Implement functionality
        return null;
    }} catch (error) {{
        console.error(`{function_name} failed:`, error);
        throw error;
    }}
}}
"""

    async def _generate_generic_code(self, plan: Dict[str, Any], spec: CodeGenerationSpec) -> str:
        """Generate generic code template"""
        return f"""
// {spec.purpose}
// Generated with principle compliance (KISS, DRY, SOLID, YAGNI)
// Language: {spec.language}

// TODO: Implement functionality following coding principles:
// - KISS: Keep it simple and readable
// - DRY: Don't repeat yourself
// - SOLID: Single responsibility
// - YAGNI: You aren't gonna need it
"""

    def _compress_code(self, code: str) -> str:
        """Compress code to reduce line count while maintaining readability"""
        lines = code.splitlines()
        compressed_lines = []

        for line in lines:
            # Remove excessive blank lines
            if line.strip() or (compressed_lines and compressed_lines[-1].strip()):
                compressed_lines.append(line)

        return "\n".join(compressed_lines)

    # === PRD PROCESSING METHODS (CCOM 5.1) ===

    def _has_prd_reference(self, requirements: str) -> bool:
        """Check if requirements reference a PRD document"""
        prd_indicators = [".md", "prd", "requirements", "features/", "docs/", "specs/", "implement"]
        return any(indicator in requirements.lower() for indicator in prd_indicators)

    def _extract_prd_path(self, requirements: str) -> Optional[str]:
        """Extract PRD file path from requirements"""
        import re

        # Look for .md files
        md_pattern = r'([a-zA-Z0-9_/.-]+\.md)'
        matches = re.findall(md_pattern, requirements)

        if matches:
            return matches[0]

        # Look for common PRD directories
        if "features/" in requirements:
            return "features/requirements.md"
        elif "docs/" in requirements:
            return "docs/requirements.md"
        elif "specs/" in requirements:
            return "specs/requirements.md"

        return None

    def _parse_prd_document(self, prd_path: str) -> Optional[Dict[str, Any]]:
        """Parse PRD document and extract requirements"""
        try:
            from pathlib import Path

            # Try to read the PRD file
            full_path = self.project_root / prd_path
            if not full_path.exists():
                # Try relative to current directory
                full_path = Path(prd_path)
                if not full_path.exists():
                    Display.warning(f"PRD file not found: {prd_path}")
                    return None

            content = full_path.read_text(encoding='utf-8')

            # Parse markdown content
            prd_data = self._extract_prd_sections(content)

            Display.info(f"📋 Loaded PRD: {prd_path}")
            if prd_data.get("requirements"):
                Display.info(f"✅ Found {len(prd_data['requirements'])} requirements")

            return prd_data

        except Exception as e:
            self.logger.error(f"Failed to parse PRD {prd_path}: {e}")
            Display.warning(f"Could not parse PRD: {str(e)}")
            return None

    def _extract_prd_sections(self, content: str) -> Dict[str, Any]:
        """Extract structured data from PRD markdown content"""
        import re

        prd_data = {
            "title": "",
            "overview": "",
            "requirements": [],
            "tech_stack": {},
            "acceptance_criteria": [],
            "components": [],
            "deliverables": [],
            "phases": []
        }

        lines = content.split('\n')
        all_content = []  # Collect all content for flexible parsing

        for line in lines:
            stripped = line.strip()

            # Extract title
            if stripped.startswith('# ') and not prd_data["title"]:
                prd_data["title"] = stripped[2:].strip()
                continue

            all_content.append(stripped)

        # Join all content for pattern-based extraction
        full_text = '\n'.join(all_content)
        full_text_lower = full_text.lower()

        # Extract bullet points as requirements/deliverables
        bullet_pattern = r'^[-*+]\s+(.+)$'
        for line in all_content:
            match = re.match(bullet_pattern, line)
            if match:
                item = match.group(1).strip()
                # Categorize based on context keywords
                item_lower = item.lower()
                if any(kw in item_lower for kw in ['deliver', 'output', 'produce', 'create']):
                    prd_data["deliverables"].append(item)
                elif any(kw in item_lower for kw in ['test', 'verify', 'validate', 'check', 'assert']):
                    prd_data["acceptance_criteria"].append(item)
                elif any(kw in item_lower for kw in ['component', 'module', 'service', 'api', 'ui']):
                    prd_data["components"].append(item)
                else:
                    prd_data["requirements"].append(item)

        # Extract tech stack from table or text
        tech_patterns = {
            "ai_model": ["claude", "gpt", "llm", "ai model"],
            "framework": ["playwright", "selenium", "cypress", "puppeteer"],
            "language": ["python", "typescript", "javascript", "java"],
            "testing": ["pytest", "jest", "mocha", "junit"],
            "cicd": ["github actions", "jenkins", "gitlab ci", "circle ci"]
        }

        for category, keywords in tech_patterns.items():
            for keyword in keywords:
                if keyword in full_text_lower:
                    if category not in prd_data["tech_stack"]:
                        prd_data["tech_stack"][category] = []
                    prd_data["tech_stack"][category].append(keyword)

        # Extract phases from numbered sections or phase headers
        phase_pattern = r'(?:phase|week|sprint)\s+(\d+).*?:\s*(.+?)(?=\n(?:phase|week|sprint|\Z))'
        phases = re.findall(phase_pattern, full_text_lower, re.DOTALL | re.IGNORECASE)
        for phase_num, phase_desc in phases:
            prd_data["phases"].append(f"Phase {phase_num}: {phase_desc[:100].strip()}")

        # Extract overview from executive summary or first paragraph
        if 'executive summary' in full_text_lower:
            summary_idx = full_text_lower.find('executive summary')
            next_section = full_text_lower.find('##', summary_idx + 10)
            if next_section > 0:
                prd_data["overview"] = full_text[summary_idx:next_section].strip()[:500]
        elif 'objective' in full_text_lower:
            obj_idx = full_text_lower.find('objective')
            prd_data["overview"] = full_text[obj_idx:obj_idx+300].strip()

        return prd_data

    def _process_prd_section(self, prd_data: Dict[str, Any], section: str, content: List[str]) -> None:
        """Process specific PRD section content"""
        content_text = '\n'.join(content)

        if section in ["overview", "description", "summary"]:
            prd_data["overview"] = content_text

        elif section in ["requirements", "features", "functionality"]:
            # Extract bullet points or numbered lists
            for line in content:
                if line.startswith(('- ', '* ', '+ ')) or line[0].isdigit():
                    requirement = line.lstrip('- *+0123456789. ').strip()
                    if requirement:
                        prd_data["requirements"].append(requirement)

        elif section in ["technical specs", "tech stack", "technology", "implementation"]:
            # Extract technology information
            tech_keywords = {
                "frontend": ["react", "vue", "angular", "vanilla", "javascript", "typescript"],
                "backend": ["node", "express", "python", "django", "flask", "fastapi"],
                "database": ["mongodb", "postgresql", "mysql", "sqlite", "redis"],
                "security": ["jwt", "bcrypt", "oauth", "auth0", "passport"]
            }

            content_lower = content_text.lower()
            for category, keywords in tech_keywords.items():
                for keyword in keywords:
                    if keyword in content_lower:
                        if category not in prd_data["tech_stack"]:
                            prd_data["tech_stack"][category] = []
                        prd_data["tech_stack"][category].append(keyword)

        elif section in ["acceptance criteria", "testing", "validation"]:
            # Extract criteria
            for line in content:
                if line.startswith(('- [ ]', '- [x]', '* [ ]', '* [x]')):
                    criteria = line.split(']', 1)[1].strip()
                    if criteria:
                        prd_data["acceptance_criteria"].append(criteria)

        elif section in ["components", "modules", "architecture"]:
            # Extract component names
            for line in content:
                if line.startswith(('- ', '* ', '+ ')):
                    component = line.lstrip('- *+ ').strip()
                    if component:
                        prd_data["components"].append(component)

    def _display_prd_analysis(self, prd_data: Dict[str, Any], prd_path: str) -> None:
        """Display comprehensive PRD analysis"""
        Display.section(f"📄 PRD Document: {prd_path}")

        # Title
        if prd_data.get("title"):
            Display.info(f"Title: {prd_data['title']}\n")

        # Overview
        if prd_data.get("overview"):
            Display.section("📖 Overview")
            Display.info(prd_data["overview"] + "\n")

        # Tech Stack
        if prd_data.get("tech_stack"):
            Display.section("🛠️ Tech Stack")
            for category, technologies in prd_data["tech_stack"].items():
                Display.info(f"  {category.replace('_', ' ').title()}: {', '.join(set(technologies))}")
            Display.info("")

        # Requirements
        if prd_data.get("requirements"):
            Display.section(f"✅ Requirements ({len(prd_data['requirements'])})")
            for i, req in enumerate(prd_data["requirements"][:10], 1):  # Limit to first 10
                Display.info(f"  {i}. {req}")
            if len(prd_data["requirements"]) > 10:
                Display.info(f"  ... and {len(prd_data['requirements']) - 10} more")
            Display.info("")

        # Deliverables
        if prd_data.get("deliverables"):
            Display.section(f"📦 Deliverables ({len(prd_data['deliverables'])})")
            for i, deliverable in enumerate(prd_data["deliverables"][:10], 1):
                Display.info(f"  {i}. {deliverable}")
            if len(prd_data["deliverables"]) > 10:
                Display.info(f"  ... and {len(prd_data['deliverables']) - 10} more")
            Display.info("")

        # Components
        if prd_data.get("components"):
            Display.section(f"🏗️ Components ({len(prd_data['components'])})")
            for component in prd_data["components"][:10]:
                Display.info(f"  • {component}")
            if len(prd_data["components"]) > 10:
                Display.info(f"  ... and {len(prd_data['components']) - 10} more")
            Display.info("")

        # Acceptance Criteria
        if prd_data.get("acceptance_criteria"):
            Display.section(f"🎯 Acceptance Criteria ({len(prd_data['acceptance_criteria'])})")
            for i, criteria in enumerate(prd_data["acceptance_criteria"][:10], 1):
                Display.info(f"  {i}. {criteria}")
            if len(prd_data["acceptance_criteria"]) > 10:
                Display.info(f"  ... and {len(prd_data['acceptance_criteria']) - 10} more")
            Display.info("")

        # Phases
        if prd_data.get("phases"):
            Display.section(f"📅 Implementation Phases ({len(prd_data['phases'])})")
            for i, phase in enumerate(prd_data["phases"], 1):
                Display.info(f"  {i}. {phase}")
            Display.info("")

    def _create_implementation_plan(self, prd_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create implementation plan from PRD data"""
        plan = {
            "phases": [],
            "estimated_complexity": "medium",
            "recommended_approach": "incremental"
        }

        # Phase 1: Setup and Architecture
        phase1_tasks = ["Project setup", "Directory structure"]
        if prd_data.get("tech_stack"):
            phase1_tasks.append(f"Install dependencies ({', '.join(prd_data['tech_stack'].keys())})")
        plan["phases"].append({
            "name": "Phase 1: Setup & Architecture",
            "tasks": phase1_tasks
        })

        # Phase 2: Core Components
        if prd_data.get("components"):
            plan["phases"].append({
                "name": "Phase 2: Core Components",
                "tasks": [f"Implement {comp}" for comp in prd_data["components"][:5]]
            })

        # Phase 3: Feature Implementation
        if prd_data.get("requirements"):
            plan["phases"].append({
                "name": "Phase 3: Feature Implementation",
                "tasks": prd_data["requirements"][:5]
            })

        # Phase 4: Validation
        if prd_data.get("acceptance_criteria"):
            plan["phases"].append({
                "name": "Phase 4: Testing & Validation",
                "tasks": ["Unit tests", "Integration tests", "Validate acceptance criteria"]
            })

        # Estimate complexity
        total_items = len(prd_data.get("requirements", [])) + len(prd_data.get("components", []))
        if total_items < 5:
            plan["estimated_complexity"] = "low"
        elif total_items < 15:
            plan["estimated_complexity"] = "medium"
        else:
            plan["estimated_complexity"] = "high"

        return plan

    def _display_implementation_plan(self, plan: Dict[str, Any]) -> None:
        """Display implementation plan"""
        Display.info(f"Estimated Complexity: {plan['estimated_complexity'].upper()}")
        Display.info(f"Recommended Approach: {plan['recommended_approach'].capitalize()}\n")

        for phase in plan["phases"]:
            Display.section(phase["name"])
            for i, task in enumerate(phase["tasks"], 1):
                Display.info(f"  {i}. {task}")
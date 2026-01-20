import logging
import os
from typing import Optional, Dict, Any, List, Tuple, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json
import re


class TDDStage(Enum):
    """Enum representing stages in the TDD cycle"""
    RED = "red"
    GREEN = "green"
    REFACTOR = "refactor"


@dataclass
class TestResult:
    """Test result data container with enhanced fields"""
    passed: bool
    message: str
    coverage: float
    execution_time: float = 0.0
    test_count: int = 0
    failing_tests: List[str] = field(default_factory=list)


@dataclass
class CycleData:
    """Data container for a complete TDD cycle"""
    cycle_id: int
    feature_name: str
    test_content: str = ""
    implementation_content: str = ""
    refactored_content: str = ""
    test_metrics: Dict[str, Any] = field(default_factory=dict)
    impl_metrics: Dict[str, Any] = field(default_factory=dict)
    test_results: List[TestResult] = field(default_factory=list)
    current_stage: TDDStage = TDDStage.RED
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None


class TDDManager:
    """
    Manages the TDD cycle for AI-driven development

    This class facilitates Test-Driven Development by tracking cycles,
    evaluating code quality, and providing insights for autonomous agents.
    """

    def __init__(self, project_path: str, logger: Optional[logging.Logger] = None):
        """
        Initialize the TDD Manager

        Args:
            project_path: Path to the project directory
            logger: Optional logger instance
        """
        self.project_path = os.path.abspath(project_path)
        self.logger = logger or self._setup_default_logger()
        self.cycles: Dict[int, CycleData] = {}
        self.current_cycle_id = 0
        self._load_history()

    def _setup_default_logger(self) -> logging.Logger:
        """Create and configure a default logger"""
        logger = logging.getLogger("tdd_manager")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _load_history(self) -> None:
        """Load TDD cycle history from file if it exists"""
        history_path = os.path.join(self.project_path, "tdd_history.json")
        if os.path.exists(history_path):
            try:
                with open(history_path, 'r') as f:
                    data = json.load(f)
                    self.current_cycle_id = data.get("last_cycle_id", 0)
                    # Additional history loading logic would go here
                self.logger.info(f"Loaded TDD history with {self.current_cycle_id} cycles")
            except Exception as e:
                self.logger.error(f"Failed to load TDD history: {e}")

    def _save_history(self) -> None:
        """Save current TDD cycle history to file"""
        history_path = os.path.join(self.project_path, "tdd_history.json")
        try:
            with open(history_path, 'w') as f:
                json.dump({
                    "last_cycle_id": self.current_cycle_id,
                    "last_updated": str(datetime.now()),
                    "cycles": {
                        str(cycle_id): {
                            "feature_name": cycle.feature_name,
                            "start_time": str(cycle.start_time),
                            "end_time": str(cycle.end_time) if cycle.end_time else None,
                            "current_stage": cycle.current_stage.value,
                            "test_results": [
                                {
                                    "passed": result.passed,
                                    "message": result.message,
                                    "coverage": result.coverage,
                                    "execution_time": result.execution_time,
                                    "test_count": result.test_count,
                                    "failing_tests": result.failing_tests
                                } for result in cycle.test_results
                            ]
                        } for cycle_id, cycle in self.cycles.items()
                    }
                }, f, indent=2)
            self.logger.debug(f"Saved TDD history to {history_path}")
        except Exception as e:
            self.logger.error(f"Failed to save TDD history: {e}")

    def get_test_content(self, cycle_id: int) -> Optional[str]:
        """
        Retrieve the test content for a specific TDD cycle.

        Args:
            cycle_id: The ID of the cycle

        Returns:
            The test content string if found, else None
        """
        if cycle_id not in self.cycles:
            self.logger.error(f"Cycle {cycle_id} not found in get_test_content")
            return None

        return self.cycles[cycle_id].test_content

    def start_cycle(self, feature_name: str) -> int:
        """
        Start a new TDD cycle for a feature

        Args:
            feature_name: Name of the feature being developed

        Returns:
            The ID of the new cycle
        """
        self.current_cycle_id += 1
        self.cycles[self.current_cycle_id] = CycleData(
            cycle_id=self.current_cycle_id,
            feature_name=feature_name
        )
        self.logger.info(f"Starting TDD cycle {self.current_cycle_id} for {feature_name}")
        self._save_history()
        return self.current_cycle_id

    def set_stage(self, cycle_id: int, stage: TDDStage) -> bool:
        """
        Set the current stage for a TDD cycle

        Args:
            cycle_id: The ID of the cycle to update
            stage: The new TDD stage

        Returns:
            True if successful, False otherwise
        """
        if cycle_id not in self.cycles:
            self.logger.error(f"Cycle {cycle_id} not found")
            return False

        self.cycles[cycle_id].current_stage = stage
        self.logger.info(f"Cycle {cycle_id} moved to {stage.value} stage")
        self._save_history()
        return True

    def add_test_content(self, cycle_id: int, test_content: str) -> Dict[str, Any]:
        """
        Add test content to a cycle and evaluate its quality

        Args:
            cycle_id: The ID of the cycle
            test_content: The test code content

        Returns:
            Dictionary of test quality metrics
        """
        if cycle_id not in self.cycles:
            self.logger.error(f"Cycle {cycle_id} not found")
            return {}

        cycle = self.cycles[cycle_id]
        cycle.test_content = test_content
        cycle.test_metrics = self.evaluate_test_quality(test_content)
        self._save_history()
        return cycle.test_metrics

    def add_implementation(self, cycle_id: int, implementation: str) -> Dict[str, Any]:
        """
        Add implementation code to a cycle and evaluate its quality

        Args:
            cycle_id: The ID of the cycle
            implementation: The implementation code

        Returns:
            Dictionary of implementation quality metrics
        """
        if cycle_id not in self.cycles:
            self.logger.error(f"Cycle {cycle_id} not found")
            return {}

        cycle = self.cycles[cycle_id]
        cycle.implementation_content = implementation
        cycle.impl_metrics = self.evaluate_implementation_quality(implementation)
        self._save_history()
        return cycle.impl_metrics

    def add_refactored_implementation(self, cycle_id: int, refactored_code: str) -> Dict[str, Any]:
        """
        Add refactored implementation code to a cycle

        Args:
            cycle_id: The ID of the cycle
            refactored_code: The refactored implementation code

        Returns:
            Dictionary of implementation quality metrics for the refactored code
        """
        if cycle_id not in self.cycles:
            self.logger.error(f"Cycle {cycle_id} not found")
            return {}

        cycle = self.cycles[cycle_id]
        cycle.refactored_content = refactored_code
        metrics = self.evaluate_implementation_quality(refactored_code)

        # Compare with original implementation
        original_metrics = cycle.impl_metrics
        delta_metrics = {
            f"delta_{k}": metrics[k] - original_metrics[k] if isinstance(metrics[k], (int, float)) else 0
            for k in metrics if k in original_metrics
        }

        # Add delta metrics to the result
        result = {**metrics, **delta_metrics}
        self._save_history()
        return result

    def evaluate_test_quality(self, test_content: str) -> Dict[str, Any]:
        """
        Evaluate the quality of generated tests

        Args:
            test_content: The test code to evaluate

        Returns:
            Dictionary of test quality metrics
        """
        # Count test functions more accurately using regex
        test_funcs = re.findall(r'def\s+test_\w+\s*\(', test_content)

        metrics = {
            'test_count': len(test_funcs),
            'has_assertions': self._check_assertions(test_content),
            'assertion_count': self._count_assertions(test_content),
            'has_edge_cases': self._check_edge_cases(test_content),
            'has_error_handling': self._check_error_handling(test_content),
            'has_setup_teardown': 'setUp' in test_content or 'tearDown' in test_content or 'setup_method' in test_content,
            'has_mocks': 'mock' in test_content.lower() or 'patch' in test_content or 'MagicMock' in test_content,
            'test_isolation': self._check_test_isolation(test_content),
            'test_readability': self._measure_test_readability(test_content)
        }
        return metrics

    def _check_assertions(self, content: str) -> bool:
        """Check if content contains test assertions"""
        assertion_patterns = [
            r'assert\s+',
            r'assertEqual\(',
            r'assertEquals\(',
            r'assertRaises\(',
            r'assertIs\(',
            r'assertIn\(',
            r'assertIsNone\(',
            r'assertTrue\(',
            r'assertFalse\(',
            r'expect\(.+\)\.to',
            r'should\.',
            r'should\(.+\)'
        ]
        return any(re.search(pattern, content) for pattern in assertion_patterns)

    def _count_assertions(self, content: str) -> int:
        """Count the number of assertions in the test content"""
        assertion_patterns = [
            r'assert\s+',
            r'assert[A-Z][a-zA-Z]+\(',
            r'expect\(.+\)\.',
            r'should\.'
        ]
        count = 0
        for pattern in assertion_patterns:
            count += len(re.findall(pattern, content))
        return count

    def _check_edge_cases(self, content: str) -> bool:
        """Check for presence of edge case testing"""
        edge_case_indicators = [
            'edge case',
            'boundary',
            'empty',
            'null',
            'none',
            'invalid',
            'maximum',
            'minimum',
            'zero',
            'overflow',
            'negative',
            'corner case'
        ]
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in edge_case_indicators)

    def _check_error_handling(self, content: str) -> bool:
        """Check for presence of error handling tests"""
        error_patterns = [
            r'try\s*:',
            r'except\s+',
            r'assert.+Raises\(',
            r'with\s+pytest\.raises\(',
            r'with\s+self\.assertRaises\(',
            r'should(_not)?\s+raise\s+'
        ]
        return any(re.search(pattern, content) for pattern in error_patterns)

    def _check_test_isolation(self, content: str) -> bool:
        """Check if tests appear to be isolated"""
        isolation_indicators = [
            'setUp',
            'tearDown',
            'setup_method',
            'teardown_method',
            '@pytest.fixture',
            'mock',
            'patch',
            '@patch',
            '@mock'
        ]
        return any(indicator in content for indicator in isolation_indicators)

    def _measure_test_readability(self, content: str) -> float:
        """
        Measure test readability on a scale of 0-10
        Higher score indicates better readability
        """
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        if not non_empty_lines:
            return 0.0

        # Calculate average line length (shorter is generally more readable)
        avg_line_length = sum(len(line) for line in non_empty_lines) / len(non_empty_lines)
        line_length_score = max(0, min(5, 10 - (avg_line_length - 30) / 10))

        # Check for descriptive test names
        test_names = re.findall(r'def\s+(test_\w+)', content)
        descriptive_names = sum(1 for name in test_names if len(name) > 10 and '_' in name)
        name_score = 5 * (descriptive_names / len(test_names) if test_names else 0)

        return line_length_score + name_score

    def evaluate_implementation_quality(self, impl_content: str) -> Dict[str, Any]:
        """
        Evaluate the quality of implementation

        Args:
            impl_content: The implementation code to evaluate

        Returns:
            Dictionary of implementation quality metrics
        """
        metrics = {
            'cyclomatic_complexity': self._calculate_complexity(impl_content),
            'has_documentation': self._check_documentation(impl_content),
            'has_type_hints': self._check_type_hints(impl_content),
            'has_error_handling': self._check_error_handling(impl_content),
            'code_to_comment_ratio': self._calculate_code_comment_ratio(impl_content),
            'function_count': len(re.findall(r'def\s+\w+\s*\(', impl_content)),
            'class_count': len(re.findall(r'class\s+\w+', impl_content)),
            'average_function_length': self._calculate_avg_function_length(impl_content),
            'duplication_score': self._detect_code_duplication(impl_content),
            'readability_score': self._measure_code_readability(impl_content)
        }
        return metrics

    def _calculate_complexity(self, content: str) -> int:
        """
        Calculate cyclomatic complexity (more comprehensive)

        Args:
            content: Code content to analyze

        Returns:
            Estimated cyclomatic complexity score
        """
        complexity_indicators = [
            (r'\bif\s+', 1),
            (r'\belse\s*:', 1),
            (r'\belif\s+', 1),
            (r'\bfor\s+', 1),
            (r'\bwhile\s+', 1),
            (r'\btry\s*:', 1),
            (r'\bexcept\s+', 1),
            (r'\bwith\s+', 0.5),  # Lower weight for 'with' statements
            (r'\band\s+', 0.5),  # Boolean operators add complexity
            (r'\bor\s+', 0.5),
            (r'\bnot\s+', 0.2),
            (r'\breturn\s+', 0.2),  # Multiple returns can increase complexity
            (r'\braise\s+', 0.5),
            (r'\bbreak\b', 0.5),
            (r'\bcontinue\b', 0.5),
            (r'\bcomprehension', 0.5),  # List/dict comprehensions
            (r'lambda\s+', 0.5)
        ]

        complexity = 1  # Base complexity
        for pattern, weight in complexity_indicators:
            complexity += len(re.findall(pattern, content)) * weight

        return round(complexity)

    def _check_documentation(self, content: str) -> bool:
        """
        Check for presence of documentation

        Args:
            content: Code content to analyze

        Returns:
            True if sufficient documentation is found
        """
        # Check for docstrings
        has_docstrings = '"""' in content or "'''" in content

        # Check for module-level docstring
        module_docstring = re.search(r'^([\'"]{3}|[\'"]{3}).*?([\'"]{3}|[\'"]{3})', content, re.DOTALL)

        # Check for function/class docstrings
        func_class_docstrings = re.findall(r'def\s+\w+\s*\([^)]*\):\s*([\'"]{3}|[\'"]{3})', content)
        class_docstrings = re.findall(r'class\s+\w+.*?:\s*([\'"]{3}|[\'"]{3})', content)

        # Calculate docstring coverage
        func_count = len(re.findall(r'def\s+\w+\s*\(', content))
        class_count = len(re.findall(r'class\s+\w+', content))
        docstring_count = len(func_class_docstrings) + len(class_docstrings)

        if func_count + class_count == 0:
            return bool(module_docstring)

        docstring_coverage = docstring_count / (func_count + class_count)

        # Consider documentation good if there are docstrings and coverage is at least 50%
        return has_docstrings and (docstring_coverage >= 0.5 or bool(module_docstring))

    def _check_type_hints(self, content: str) -> bool:
        """
        Check for presence of type hints

        Args:
            content: Code content to analyze

        Returns:
            True if sufficient type hints are found
        """
        # Look for function parameter type hints and return type hints
        param_hints = re.findall(r'def\s+\w+\s*\(([^)]*:.*?[^,])\)', content)
        return_hints = re.findall(r'def\s+\w+\s*\([^)]*\)\s*->\s*\w+', content)

        # Count functions
        func_count = len(re.findall(r'def\s+\w+\s*\(', content))

        if func_count == 0:
            # No functions to type hint
            return True

        # Calculate type hint coverage
        type_hint_coverage = (len(param_hints) + len(return_hints)) / (
                    func_count * 2)  # Each function can have param and return hints

        # Consider type hints good if coverage is at least 50%
        return type_hint_coverage >= 0.5

    def _calculate_code_comment_ratio(self, content: str) -> float:
        """
        Calculate the ratio of code to comments

        Args:
            content: Code content to analyze

        Returns:
            Ratio of comments to code lines (higher is more commented)
        """
        lines = content.split('\n')
        code_lines = 0
        comment_lines = 0
        docstring_mode = False
        docstring_delimiter = None

        for line in lines:
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                continue

            # Handle docstrings
            if docstring_mode:
                comment_lines += 1
                if stripped.endswith(docstring_delimiter):
                    docstring_mode = False
                    docstring_delimiter = None
            elif stripped.startswith('"""') or stripped.startswith("'''"):
                comment_lines += 1
                delimiter = stripped[:3]
                if not (stripped.endswith(delimiter) and len(stripped) > 3):
                    docstring_mode = True
                    docstring_delimiter = delimiter
            # Handle regular comments
            elif stripped.startswith('#'):
                comment_lines += 1
            # Code lines
            else:
                code_lines += 1

        if code_lines == 0:
            return 0.0

        return comment_lines / code_lines

    def _calculate_avg_function_length(self, content: str) -> float:
        """
        Calculate average function length in lines

        Args:
            content: Code content to analyze

        Returns:
            Average function length or 0 if no functions found
        """
        # First split the content into lines
        lines = content.split('\n')

        # Find function definitions
        function_starts = []
        for i, line in enumerate(lines):
            if re.match(r'\s*def\s+\w+\s*\(', line):
                function_starts.append(i)

        if not function_starts:
            return 0.0

        # Calculate function lengths
        function_lengths = []
        for i in range(len(function_starts)):
            start = function_starts[i]
            end = function_starts[i + 1] if i + 1 < len(function_starts) else len(lines)

            # Find where function ends (by indentation)
            func_indent = len(lines[start]) - len(lines[start].lstrip())
            for j in range(start + 1, end):
                if lines[j].strip() and len(lines[j]) - len(lines[j].lstrip()) <= func_indent:
                    end = j
                    break

            function_lengths.append(end - start)

        if not function_lengths:
            return 0.0

        return sum(function_lengths) / len(function_lengths)

    def _detect_code_duplication(self, content: str) -> float:
        """
        Detect potential code duplication (naive approach)

        Args:
            content: Code content to analyze

        Returns:
            Duplication score (0-1, higher means more duplication)
        """
        # Split into lines
        lines = [line.strip() for line in content.split('\n') if line.strip()]

        if len(lines) <= 5:
            return 0.0

        # Look for repeated line patterns (3+ lines)
        patterns = set()
        duplication_count = 0

        for i in range(len(lines) - 2):
            pattern = (lines[i], lines[i + 1], lines[i + 2])
            if pattern in patterns:
                duplication_count += 1
            patterns.add(pattern)

        if not patterns:
            return 0.0

        return min(1.0, duplication_count / len(patterns))

    def _measure_code_readability(self, content: str) -> float:
        """
        Measure code readability on a scale of 0-10
        Higher score indicates better readability

        Args:
            content: Code content to analyze

        Returns:
            Readability score (0-10)
        """
        lines = [line for line in content.split('\n') if line.strip()]

        if not lines:
            return 0.0

        # Calculate average line length (shorter is generally more readable)
        avg_line_length = sum(len(line) for line in lines) / len(lines)
        line_length_score = max(0, min(4, 8 - (avg_line_length - 60) / 10))

        # Check for descriptive variable/function names
        tokens = re.findall(r'\b[a-zA-Z_]\w*\b', content)
        single_char_vars = sum(1 for token in tokens if len(token) == 1 and token not in ('i', 'j', 'k', 'x', 'y', 'z'))
        name_score = max(0, min(3, 3 - (single_char_vars / max(1, len(tokens)) * 20)))

        # Check indentation consistency
        indents = [len(line) - len(line.lstrip()) for line in lines if line.strip()]
        if indents:
            unique_indents = set(indents)
            # Check if indents are consistent multiples
            consistent = all(indent % min(unique_indents or [4]) == 0 for indent in unique_indents if indent > 0)
            indent_score = 3 if consistent else 1
        else:
            indent_score = 0

        return line_length_score + name_score + indent_score

    def record_test_result(self, cycle_id: int, test_result: TestResult) -> None:
        """
        Record the results of a test run

        Args:
            cycle_id: The ID of the cycle
            test_result: The test result data
        """
        if cycle_id not in self.cycles:
            self.logger.error(f"Cycle {cycle_id} not found")
            return

        self.cycles[cycle_id].test_results.append(test_result)
        self.logger.info(f"Recorded test result for cycle {cycle_id}: {test_result.passed}")
        self._save_history()

    def complete_cycle(self, cycle_id: int) -> None:
        """
        Mark a TDD cycle as complete

        Args:
            cycle_id: The ID of the cycle to complete
        """
        if cycle_id not in self.cycles:
            self.logger.error(f"Cycle {cycle_id} not found")
            return

        self.cycles[cycle_id].end_time = datetime.now()
        self.logger.info(f"Completed TDD cycle {cycle_id}")
        self._save_history()

    def should_refactor(self, cycle_id: int) -> Tuple[bool, str]:
        """
        Determine if code needs refactoring based on metrics

        Args:
            cycle_id: The ID of the cycle to evaluate

        Returns:
            Tuple of (needs_refactoring, reason)
        """
        if cycle_id not in self.cycles:
            self.logger.error(f"Cycle {cycle_id} not found")
            return False, "Cycle not found"

        cycle = self.cycles[cycle_id]
        impl = cycle.implementation_content
        metrics = cycle.impl_metrics if cycle.impl_metrics else self.evaluate_implementation_quality(impl)

        reasons = []

        # Check code quality metrics
        if metrics.get('cyclomatic_complexity', 0) > 10:
            reasons.append(f"High cyclomatic complexity ({metrics.get('cyclomatic_complexity')})")
        if not metrics.get('has_documentation', False):
            reasons.append("Missing or insufficient documentation")
        if not metrics.get('has_type_hints', False):
            reasons.append("Missing or insufficient type hints")
        if not metrics.get('has_error_handling', False):
            reasons.append("Missing error handling")
        if metrics.get('average_function_length', 0) > 20:
            reasons.append(f"Functions too long (avg {metrics.get('average_function_length', 0):.1f} lines)")
        if metrics.get('duplication_score', 0) > 0.3:
            reasons.append("Potential code duplication detected")
        if metrics.get('readability_score', 0) < 5:
            reasons.append(f"Low code readability (score: {metrics.get('readability_score', 0):.1f}/10)")

        needs_refactoring = bool(reasons)
        reason = "\n".join(reasons) if reasons else "Code meets quality standards"

        return needs_refactoring, reason

    def generate_cycle_report(self, cycle_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate a report of the TDD cycle(s)

        Args:
            cycle_id: Optional specific cycle ID to report on

        Returns:
            Dictionary with cycle metrics and history
        """
        if cycle_id is not None:
            if cycle_id not in self.cycles:
                self.logger.error(f"Cycle {cycle_id} not found")
                return {}

            cycle = self.cycles[cycle_id]
            return self._generate_single_cycle_report(cycle)

        # Generate overall report
        completed_cycles = [c for c in self.cycles.values() if c.end_time is not None]
        active_cycles = [c for c in self.cycles.values() if c.end_time is None]

        test_results = [result for cycle in self.cycles.values() for result in cycle.test_results]

        return {
            'total_cycles': len(self.cycles),
            'completed_cycles': len(completed_cycles),
            'active_cycles': len(active_cycles),
            'passed_cycles': sum(1 for c in completed_cycles if any(r.passed for r in c.test_results)),
            'failed_cycles': sum(1 for c in completed_cycles if all(not r.passed for r in c.test_results)),
            'average_coverage': sum(r.coverage for r in test_results) / len(test_results) if test_results else 0,
            'average_complexity': sum(
                c.impl_metrics.get('cyclomatic_complexity', 0) for c in self.cycles.values()) / len(
                self.cycles) if self.cycles else 0,
            'cycles': [self._generate_single_cycle_report(c) for c in self.cycles.values()]
        }

    def _generate_single_cycle_report(self, cycle: CycleData) -> Dict[str, Any]:
        """
        Generate a report for a single TDD cycle

        Args:
            cycle: The cycle data object

        Returns:
            Dictionary with cycle metrics
        """
        duration = None
        if cycle.end_time:
            duration = (cycle.end_time - cycle.start_time).total_seconds()

        latest_result = cycle.test_results[-1] if cycle.test_results else None

        return {
            'cycle_id': cycle.cycle_id,
            'feature': cycle.feature_name,
            'stage': cycle.current_stage.value,
            'start_time': str(cycle.start_time),
            'end_time': str(cycle.end_time) if cycle.end_time else None,
            'duration_seconds': duration,
            'test_metrics': cycle.test_metrics,
            'implementation_metrics': cycle.impl_metrics,
            'latest_result': {
                'passed': latest_result.passed,
                'message': latest_result.message,
                'coverage': latest_result.coverage,
                'execution_time': latest_result.execution_time,
                'test_count': latest_result.test_count,
                'failing_tests': latest_result.failing_tests
            } if latest_result else None,
            'test_history': [
                {
                    'passed': r.passed,
                    'message': r.message,
                    'coverage': r.coverage,
                    'timestamp': str(r.execution_time)
                } for r in cycle.test_results
            ]
        }

    def get_agent_suggestions(self, cycle_id: int) -> List[Dict[str, Any]]:
        """
        Provide AI agent suggestions based on cycle metrics

        Args:
            cycle_id: The ID of the TDD cycle

        Returns:
            List of suggestions as dicts with 'category' and 'recommendation'
        """
        if cycle_id not in self.cycles:
            self.logger.error(f"Cycle {cycle_id} not found")
            return []

        suggestions = []
        cycle = self.cycles[cycle_id]
        metrics = cycle.impl_metrics or self.evaluate_implementation_quality(cycle.implementation_content)

        if metrics.get('cyclomatic_complexity', 0) > 10:
            suggestions.append({
                "category": "refactoring",
                "recommendation": "Reduce cyclomatic complexity by simplifying conditionals or breaking down functions."
            })
        if not metrics.get('has_documentation', False):
            suggestions.append({
                "category": "documentation",
                "recommendation": "Add or improve docstrings to enhance maintainability."
            })
        if not metrics.get('has_type_hints', False):
            suggestions.append({
                "category": "type_safety",
                "recommendation": "Incorporate type hints for better clarity and IDE support."
            })
        if metrics.get('code_to_comment_ratio', 0) < 0.1:
            suggestions.append({
                "category": "commenting",
                "recommendation": "Add meaningful comments explaining complex logic or business rules."
            })
        if metrics.get('readability_score', 0) < 6:
            suggestions.append({
                "category": "readability",
                "recommendation": "Improve variable names and reduce line length for better readability."
            })
        if metrics.get('duplication_score', 0) > 0.3:
            suggestions.append({
                "category": "refactoring",
                "recommendation": "Detect and remove repeated logic blocks to improve maintainability."
            })

        return suggestions

    def progress_cycle_stage(self, cycle_id: int) -> Optional[TDDStage]:
        """
        Progress the given TDD cycle to the next stage.

        Returns:
            The new stage if successful, None otherwise.
        """
        if cycle_id not in self.cycles:
            self.logger.error(f"Cannot progress: Cycle {cycle_id} does not exist.")
            return None

        current_stage = self.cycles[cycle_id].current_stage
        next_stage = {
            TDDStage.RED: TDDStage.GREEN,
            TDDStage.GREEN: TDDStage.REFACTOR,
            TDDStage.REFACTOR: None  # End of cycle
        }.get(current_stage, None)

        if next_stage:
            self.cycles[cycle_id].current_stage = next_stage
            self.logger.info(f"Cycle {cycle_id} progressed to stage: {next_stage.value}")
        else:
            self.cycles[cycle_id].end_time = datetime.now()
            self.logger.info(f"Cycle {cycle_id} marked complete (from {current_stage.value})")

        self._save_history()
        return next_stage


import json
import os
import logging
import random
import re
import time
import subprocess
import threading
import queue
import tkinter as tk
import uuid
from tkinter import ttk, messagebox, filedialog, scrolledtext
from typing import Dict, Optional, Any, List, Callable, Union
from datetime import datetime

import unicodedata

from src.agents.project_rag_coordinator import ProjectRAGCoordinator
from src.models.tdd_manager import TDDManager, TDDStage


def create_default_metadata(name, error_message):
    """Helper function to create default metadata with error information"""
    return {
        'project_name': name,
        'project_description': error_message,
        'project_structure': [],
        'key_features': [],
        'project_tasks': ['Resolve AI response parsing error'],
        'implemented_features': [],
        'planned_features': [],
        'feature_priorities': {
            'high': [],
            'medium': [],
            'low': []
        },
        'validation_notes': [error_message]
    }


class AIResponseParser:
    @staticmethod
    def sanitize_prompt(prompt: str) -> str:
        """Normalize and strip unsafe characters from user prompt."""
        if not isinstance(prompt, str):
            return ""
        clean = ''.join(
            c for c in unicodedata.normalize('NFKD', prompt)
            if unicodedata.category(c)[0] != 'C'  # Remove control chars
        )
        return clean.strip()

    @staticmethod
    def validate_prompt(prompt: str) -> bool:
        """Ensure the prompt is descriptive enough for generation."""
        if not prompt or len(prompt) < 10:
            return False

        lowered = prompt.lower()
        has_keyword = any(word in lowered for word in (
            'create', 'build', 'design', 'develop', 'generate', 'html', 'website',
            'app', 'api', 'tool', 'script', 'python', 'js', 'game', 'component'
        ))

        return has_keyword

    @staticmethod
    def parse_ai_response(response: Optional[str]) -> Union[Dict, List, None]:
        """
        Attempts to extract and parse the first valid JSON object or array from an AI response.

        :param response: Raw string response from the AI
        :return: Parsed JSON object or array, or None if parsing fails
        """
        if not response:
            logging.warning("Empty response received for parsing.")
            return None

        try:
            # If it’s already valid JSON, great.
            parsed = json.loads(response)
            return parsed
        except Exception:
            pass  # Proceed to attempt extraction

        # Regex to extract JSON-like content (object or array)
        json_match = re.search(r'(\{.*\}|\[.*\])', response, re.DOTALL)
        if json_match:
            candidate = json_match.group(1)
            try:
                parsed = json.loads(candidate)
                return parsed
            except json.JSONDecodeError as e:
                logging.error(f"Regex-extracted JSON failed to parse: {e}")

        # Try looking for a 'raw' field inside a known error envelope
        if '"raw":' in response:
            raw_match = re.search(r'"raw"\s*:\s*"(.+?)"', response, re.DOTALL)
            if raw_match:
                raw_content = raw_match.group(1).encode('utf-8').decode('unicode_escape')
                try:
                    json_start = raw_content.find('{')
                    json_end = raw_content.rfind('}') + 1
                    if json_start != -1 and json_end > json_start:
                        parsed = json.loads(raw_content[json_start:json_end])
                        return parsed
                except json.JSONDecodeError as e:
                    logging.warning(f"Failed to parse JSON inside raw field: {e}")

        logging.warning("Failed to extract valid JSON from AI response.")
        return None


class ProjectManager:
    @staticmethod
    def create_project_structure(project_path: str, metadata: Dict[str, Any], logger: Callable[[str], None]):
        """
        Create the project structure, generate files, and log progress.
        Enhanced with more robust error handling and flexibility.
        """
        try:
            logger("Creating project structure...")

            # Ensure project path exists
            os.makedirs(project_path, exist_ok=True)

            # Create directories with error handling
            directories = ['src', 'tests', 'docs', 'config', 'scripts']
            directories.extend(metadata.get('project_structure', []))

            for directory in directories:
                try:
                    dir_path = os.path.join(project_path, directory)
                    os.makedirs(dir_path, exist_ok=True)
                    logger(f"Created directory: {dir_path}")
                except OSError as dir_error:
                    logger(f"Warning: Could not create directory {directory}: {dir_error}")

            # Create files with more robust handling
            initial_files = metadata.get('initial_files', {})

            # Handle both dict and list of dicts
            if isinstance(initial_files, dict):
                for filename, content in initial_files.items():
                    file_path = os.path.join(project_path, filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content or '')
                    logger(f"Created file: {file_path}")

            elif isinstance(initial_files, list):
                for file_entry in initial_files:
                    if isinstance(file_entry, dict):
                        filename = file_entry.get('file_name') or file_entry.get('filename')
                        content = file_entry.get('content', '')
                        if filename:
                            file_path = os.path.join(project_path, filename)
                            os.makedirs(os.path.dirname(file_path), exist_ok=True)
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                            logger(f"Created file: {file_path}")
                    else:
                        logger(f"Warning: Skipping unexpected initial_files item: {file_entry}")
            else:
                logger("Warning: initial_files format unrecognized.")

            # Write README with fallback
            readme_path = os.path.join(project_path, 'README.md')
            try:
                with open(readme_path, 'w', encoding='utf-8') as readme:
                    readme.write(metadata.get('readme', '# Project Generated by Red-Green-Refactor IDE'))
                logger(f"Created README: {readme_path}")
            except IOError as readme_error:
                logger(f"Could not create README: {readme_error}")

        except Exception as e:
            logger(f"Critical error in project structure creation: {e}")
            raise

    @staticmethod
    def write_todo_list(project_path: str, tasks: Union[List[str], List[Dict[str, str]]],
                        logger: Callable[[str], None]):
        """
        Write a TODO.md file to track tasks with enhanced flexibility.

        Supports both list of strings and list of dictionaries with 'description' key.
        """
        todo_path = os.path.join(project_path, 'TODO.md')
        try:
            with open(todo_path, 'w', encoding='utf-8') as todo_file:
                todo_file.write("# TODO List\n\n")

                # Handle different task input formats
                for task in tasks:
                    # If task is a dictionary, try to get 'description'
                    if isinstance(task, dict):
                        description = task.get('description', str(task))
                    # If task is a string, use it directly
                    elif isinstance(task, str):
                        description = task
                    # For other types, convert to string
                    else:
                        description = str(task)

                    # Write task with checkbox
                    todo_file.write(f"- [ ] {description}\n")

            logger("Wrote TODO.md with tasks.")
        except IOError as e:
            logger(f"Error writing TODO list: {e}")

    @staticmethod
    def write_list_md(project_path: str, features: Dict[str, List[str]], logger: Callable[[str], None]):
        """
        Write a LIST.md file to track features and priorities with improved error handling.
        """
        list_path = os.path.join(project_path, 'LIST.md')
        try:
            with open(list_path, 'w', encoding='utf-8') as list_file:
                list_file.write("# Feature Tracking\n\n")

                # Ensure default structure if features are empty
                if not features:
                    features = {
                        'high': ['Initial project setup'],
                        'medium': [],
                        'low': []
                    }

                for priority, feature_list in features.items():
                    # Normalize priority display
                    display_priority = priority.capitalize()
                    list_file.write(f"## {display_priority} Priority\n")

                    # Handle empty feature lists
                    if not feature_list:
                        list_file.write("- No features defined\n")
                    else:
                        for feature in feature_list:
                            list_file.write(f"- {feature}\n")

                    list_file.write("\n")

            logger("Wrote LIST.md with feature tracking.")
        except IOError as e:
            logger(f"Error writing feature list: {e}")

    @staticmethod
    def run_tests(project_path: str, logger: Callable[[str], None]) -> bool:
        """
        Run tests in the project with enhanced logging and error handling.
        """
        logger("Running tests...")
        try:
            # Use pytest with comprehensive reporting
            result = subprocess.run(
                [
                    'pytest',
                    '--disable-warnings',
                    '--maxfail=1',
                    '-v',  # Verbose output
                    '--tb=short'  # Shorter traceback
                ],
                cwd=project_path,
                text=True,
                capture_output=True
            )

            # Log full output
            logger(result.stdout)

            # Log errors separately
            if result.stderr:
                logger(f"Test Stderr: {result.stderr}")

            # Determine test success
            test_success = result.returncode == 0

            # Provide detailed logging
            if test_success:
                logger("All tests passed successfully!")
            else:
                logger("Some tests failed. Review the output above.")

            return test_success

        except Exception as e:
            logger(f"Critical error running tests: {e}")
            return False


class RequirementAgent:
    def __init__(self, agent):
        self.agent = agent

    def analyze(self, requirements: str) -> Dict:
        logging.info(f"Analyzing requirements: {requirements}")
        related_chunks = self.agent.get_relevant_rag_context(
            f"What are best practices for: {requirements}",
            top_k=3,
            as_context=True
        )

        context = {
            "requirements": requirements,
            "project_name": self.agent._generate_project_name(),
            "retrieved_context": related_chunks
        }
        ai_response = self.agent.process_prompt_with_ai("requirement_analysis", context)
        project_scope = AIResponseParser.parse_ai_response(ai_response)
        if not project_scope:
            project_scope = {
                "project_name": context["project_name"],
                "key_features": ["Core Functionality"],
                "constraints": []
            }
        return project_scope


class ArchitectureAgent:
    def __init__(self, agent):
        self.agent = agent

    def design(self, project_scope: Dict) -> Dict:
        logging.info("Designing project architecture")
        related_chunks = self.agent.get_relevant_rag_context(
            f"What architectures are recommended for projects like: {project_scope.get('project_name')}"
        )

        context = {
            "project_scope": project_scope,
            "default_structure": [
                "src/",
                "tests/",
                "docs/",
                "README.md"
            ],
            "retrieved_context": related_chunks
        }
        ai_response = self.agent.process_prompt_with_ai("architecture_design", context)
        architecture = AIResponseParser.parse_ai_response(ai_response)
        if not architecture:
            architecture = {
                "project_name": project_scope.get("project_name", "Unnamed Project"),
                "directory_structure": context["default_structure"],
                "initial_modules": [],
                "testing_framework": "pytest"
            }
        return architecture


class TestGenerationAgent:
    def __init__(self, agent):
        self.agent = agent
        self.tdd = agent.tdd

    def generate_tests(self, architecture: Dict) -> List[Dict]:
        logging.info("Generating RED-phase test cases")
        # Skip tests if project looks purely visual
        if any(k in str(architecture).lower() for k in ["html", "css", "web", "landing", "portfolio"]):
            logging.info("Skipping test generation — visual/static project.")
            return []

        context = {"architecture": architecture}
        related_chunks = self.agent.get_relevant_rag_context(
            f"What kinds of tests are common for systems like: {architecture.get('project_name')}")
        context["retrieved_context"] = related_chunks
        ai_response = self.agent.process_prompt_with_ai("test_generation", context)
        parsed = AIResponseParser.parse_ai_response(ai_response)

        if not isinstance(parsed, list):
            logging.warning("Invalid test format, using fallback.")
            parsed = [{
                "name": "test_project_initialization",
                "description": "Verify project initializes correctly",
                "module": "test_core.py"
            }]

        valid_tests = []
        for test in parsed:
            if not isinstance(test, dict) or "name" not in test:
                continue

            name = test["name"]
            description = test.get("description", "No description provided")
            module = test.get("module", "test_misc.py")

            # test_code = self._generate_red_test(name, description)

            # Track the full TDD cycle from RED
            cycle_id = self.tdd.start_cycle(name)

            test_code = self.tdd.get_test_content(cycle_id)
            context = {
                "test_name": test["name"],
                "test_code": test_code,
                "requirements": self.project_scope or {},
            }

            self.tdd.add_test_content(cycle_id, test_code)
            self.tdd.set_stage(cycle_id, TDDStage.RED)

            valid_tests.append({
                "name": name,
                "description": description,
                "module": module,
                "content": test_code,
                "cycle_id": cycle_id
            })

        return valid_tests

    def _generate_red_test(self, name: str, description: str) -> str:
        class_name = name.replace("test_", "Test").title().replace("_", "")
        return f'''# {name}
# {description}

import unittest

class {class_name}(unittest.TestCase):
    def test_unimplemented(self):
        self.fail("🔴 RED: This test is intentionally failing until the feature is implemented.")

if __name__ == '__main__':
    unittest.main()
'''


class FeatureImplementationAgent:
    def __init__(self, agent):
        self.agent = agent

    def implement_features(self, tests: List[Dict]) -> Dict:
        logging.info("Implementing features")
        context = {
            "tests": tests
        }
        related_chunks = self.agent.get_relevant_rag_context(
            "How are similar features typically implemented?")
        context["retrieved_context"] = related_chunks
        ai_response = self.agent.process_prompt_with_ai("feature_implementation", context)
        implementation_results = AIResponseParser.parse_ai_response(ai_response)
        if not implementation_results:
            implementation_results = {
                "implemented_modules": [],
                "test_coverage": {}
            }
        return implementation_results


class RefactoringAgent:
    def __init__(self, agent):
        self.agent = agent

    def refactor_code(self, implementation_results: Dict):
        logging.info("Performing code refactoring")
        context = {
            "implementation_results": implementation_results
        }

        # Feed the AI some actual files, not just vibes
        context = enrich_context_with_relevant_files(context, self.agent.project_path)

        related_chunks = self.agent.get_relevant_rag_context(
            "What are best practices for refactoring Python code?")
        context["retrieved_context"] = related_chunks
        self.agent.process_prompt_with_ai("code_refactoring", context)


class ValidationAgent:
    def __init__(self, agent):
        self.agent = agent

    def validate_project(self) -> Dict:
        logging.info("Validating project")
        validation_results = {
            "test_success_rate": self.agent._run_tests(),
            "code_quality_score": self.agent._analyze_code_quality()
        }
        return validation_results


class StateManagementSystem:
    def __init__(self, project_path):
        self.project_path = project_path  # Store project path
        self.state = {
            "tasks": [],
            "completed_tasks": [],
            "code_files": {},  # Dictionary to track file content
            "test_results": {},
            "errors": [],
            "dependencies": [],
            "last_updated": datetime.now().isoformat()
        }

        # Create observers list for real-time notification
        self.observers = []

        # Ensure project directory exists
        os.makedirs(project_path, exist_ok=True)

        # Create a visible TODO.md right away to show activity
        self._create_initial_todo()

    def register_observer(self, callback_fn):
        """Register a function to be called when state changes"""
        self.observers.append(callback_fn)

    def _notify_observers(self, event_type, data=None):
        """Notify all observers of state change"""
        for observer in self.observers:
            try:
                observer(event_type, data)
            except Exception as e:
                logging.error(f"Observer notification failed: {e}")

    def _create_initial_todo(self):
        """Create initial TODO.md to show system is active"""
        todo_content = "# Project Development TODO\n\n## Initialization\n- [x] System started\n- [ ] Analyzing requirements\n\n_Last updated: {}".format(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        todo_path = os.path.join(self.project_path, "TODO.md")
        with open(todo_path, 'w', encoding='utf-8') as f:
            f.write(todo_content)
        logging.info(f"Created initial TODO.md at {todo_path}")

    def log_task(self, task):
        """Add a task and update TODO.md"""
        self.state["tasks"].append(task)
        self.state["last_updated"] = datetime.now().isoformat()
        self._update_todo_file()
        self._notify_observers("task_added", task)

    def complete_task(self, task):
        """Mark task as completed and update TODO.md"""
        if task in self.state["tasks"]:
            self.state["tasks"].remove(task)
        self.state["completed_tasks"].append(task)
        self.state["last_updated"] = datetime.now().isoformat()
        self._update_todo_file()
        self._notify_observers("task_completed", task)

    def add_code_file(self, filename, content):
        """Add a code file to the state and write it to disk."""
        self.state["code_files"][filename] = content
        self.state["last_updated"] = datetime.now().isoformat()

        # Write the file to disk
        try:
            # Create necessary directories
            file_path = os.path.join(self.project_path, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Write the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logging.info(f"Successfully wrote file to disk: {filename}")
            self._notify_observers("file_created", filename)
        except Exception as e:
            error_msg = f"Failed to write file {filename} to disk: {e}"
            logging.error(error_msg)
            self.log_error(error_msg)

    def add_test_result(self, test_name, result):
        self.state["test_results"][test_name] = result
        self.state["last_updated"] = datetime.now().isoformat()
        self._notify_observers("test_result", (test_name, result))

    def log_error(self, error):
        self.state["errors"].append(str(error))
        self.state["last_updated"] = datetime.now().isoformat()
        self._notify_observers("error", error)

    def add_dependency(self, dependency):
        if dependency not in self.state["dependencies"]:
            self.state["dependencies"].append(dependency)
            self.state["last_updated"] = datetime.now().isoformat()
            self._notify_observers("dependency_added", dependency)

    def _update_todo_file(self):
        """Update the TODO.md file with current tasks"""
        todo_path = os.path.join(self.project_path, "TODO.md")

        # Build content
        content = "# Project Development TODO\n\n"

        # Add active tasks
        if self.state["tasks"]:
            content += "## Active Tasks\n"
            for task in self.state["tasks"]:
                content += f"- [ ] {task}\n"
            content += "\n"

        # Add completed tasks
        if self.state["completed_tasks"]:
            content += "## Completed\n"
            for task in self.state["completed_tasks"]:
                content += f"- [x] {task}\n"
            content += "\n"

        # Add errors if any
        if self.state["errors"]:
            content += "## Issues\n"
            for error in self.state["errors"][-5:]:  # Show only last 5 errors
                content += f"- ⚠️ {error}\n"
            content += "\n"

        # Add timestamp
        content += f"\n_Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"

        try:
            with open(todo_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logging.error(f"Failed to update TODO.md: {e}")

    def export_state(self, path):
        import json
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=4)
        self._notify_observers("state_exported", path)

    def load_state(self, path):
        import json
        with open(path, 'r', encoding='utf-8') as f:
            self.state = json.load(f)
        self._notify_observers("state_loaded", path)


class DependencyManagementUnit:
    def __init__(self, project_path):
        self.project_path = project_path

    def install_dependencies(self, dependencies):
        for dep in dependencies:
            try:
                subprocess.run(["pip", "install", dep], check=True)
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to install dependency: {dep}: {e}")

    def save_requirements(self, dependencies):
        req_path = os.path.join(self.project_path, "requirements.txt")
        with open(req_path, "w", encoding='utf-8') as f:
            for dep in dependencies:
                f.write(f"{dep}\n")


class AutomatedTestingFramework:
    def __init__(self, project_path):
        self.project_path = project_path

    def run_tests(self):
        try:
            result = subprocess.run([
                "pytest", "--maxfail=5", "--disable-warnings", "--tb=short"
            ], cwd=self.project_path, capture_output=True, text=True)

            logging.info(result.stdout)
            if result.stderr:
                logging.warning(result.stderr)
            return result.returncode == 0

        except Exception as e:
            logging.error(f"Automated testing failed: {e}")
            return False


def detect_relevant_files(prompt: str, project_path: str) -> List[str]:
    """
    Naive keyword-to-filename mapping to detect likely relevant files based on prompt.
    """
    relevant_map = {
        "html": ["index.html"],
        "css": ["style.css", "styles.css", "main.css"],
        "javascript": ["scripts.js", "main.js", "app.js"],
        "design": ["index.html", "style.css", "scripts.js"],
        "webpage": ["index.html", "style.css", "scripts.js"],
        "portfolio": ["index.html", "style.css", "scripts.js"],
        "landing": ["index.html"],
        "backend": ["app.py", "main.py", "api.py"],
        "api": ["app.py", "api.py"],
        "test": ["test_", "_test.py"]
    }

    prompt = prompt.lower()
    matched_files = set()

    for keyword, files in relevant_map.items():
        if keyword in prompt:
            for fname in files:
                full_path = os.path.join(project_path, fname)
                if os.path.exists(full_path):
                    matched_files.add(full_path)

    return list(matched_files)


def enrich_context_with_relevant_files(context: Dict[str, Any], project_path: str) -> Dict[str, Any]:
    prompt_text = context.get("prompt") or context.get("project_scope", {}).get("description", "")
    relevant_files = detect_relevant_files(prompt_text, project_path)
    enriched_files = []

    for file_path in relevant_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                enriched_files.append({
                    "filename": os.path.relpath(file_path, project_path),
                    "content": f.read()
                })
        except Exception as e:
            logging.warning(f"Failed to read relevant file: {file_path}: {e}")

    if enriched_files:
        context["relevant_files"] = enriched_files
        context["instruction"] = (
            f"Update the following files to match the goal: '{prompt_text}'. "
            "Only change what's necessary. Do not delete unrelated code."
        )
    return context


class AutonomousProjectAgent:
    def __init__(self, project_path: str, ide_instance=None):
        self.project_path = project_path
        self.ide_instance = ide_instance
        self.state = StateManagementSystem(self.project_path)
        self.rag = ProjectRAGCoordinator(self.project_path, use_ollama=True, state=self.state)
        self.tdd = TDDManager(self.project_path)
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.current_phase = "idle"
        self.development_stages = [
            "requirement_analysis",
            "architecture_design",
            "test_driven_development",
            "implementation",
            "refactoring",
            "validation"
        ]

        # Set up visible project directory
        os.makedirs(project_path, exist_ok=True)

        self.setup_logging()

        # Improved components
        self.state = StateManagementSystem(self.project_path)  # Pass project_path
        self.dependency_manager = DependencyManagementUnit(self.project_path)
        self.testing_framework = AutomatedTestingFramework(self.project_path)

        # Create specialized agents
        self.requirement_agent = RequirementAgent(self)
        self.architecture_agent = ArchitectureAgent(self)
        self.test_generation_agent = TestGenerationAgent(self)
        self.feature_implementation_agent = FeatureImplementationAgent(self)
        self.refactoring_agent = RefactoringAgent(self)
        self.validation_agent = ValidationAgent(self)

        # Development artifacts
        self.project_scope = None
        self.architecture = None
        self.tests = []

        # Feedback integration
        self.feedback_buffer = None

        # Create development journal
        self._create_development_journal()

    def get_relevant_rag_context(self, query: str, top_k=3, as_context=False) -> List[str]:
        return self.rag.query(query, top_k=top_k, as_context=as_context)

    def add_feedback(self, feedback: Dict[str, Any]):
        """
        Add feedback to be considered in the next iteration.
        """
        self.feedback_buffer = feedback

    def _create_development_journal(self):
        """Create a development journal file to show thinking process"""
        journal_path = os.path.join(self.project_path, "DEVLOG.md")
        with open(journal_path, 'w', encoding='utf-8') as f:
            f.write("# Development Journal\n\n")
            f.write(f"Project initialized at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Project Phases\n\n")
            f.write("1. 🔍 Requirement Analysis - Understanding what we need to build\n")
            f.write("2. 📐 Architecture Design - Planning the structure\n")
            f.write("3. 🧪 Test-Driven Development - Writing tests first\n")
            f.write("4. ⚙️ Implementation - Building the actual code\n")
            f.write("5. 🔧 Refactoring - Improving the code quality\n")
            f.write("6. ✅ Validation - Ensuring everything works\n\n")
            f.write("## Activity Log\n\n")
        logging.info(f"Created development journal at {journal_path}")

    def _update_development_journal(self, entry, phase=None):
        """Add an entry to the development journal"""
        if phase:
            formatted_entry = f"### {phase}\n{entry}\n\n"
        else:
            formatted_entry = f"- {entry}\n"

        journal_path = os.path.join(self.project_path, "DEVLOG.md")
        try:
            with open(journal_path, 'a', encoding='utf-8') as f:
                f.write(f"{formatted_entry}")
                f.write(f"_Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n\n")
        except Exception as e:
            logging.error(f"Failed to update development journal: {e}")

    def setup_logging(self):
        """Configure logging for the autonomous project agent."""
        log_file = os.path.join(self.project_path, 'autonomous_agent.log')
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [AutonomousProjectAgent] %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

    def process_prompt_with_ai(self, stage: str, context: Dict, is_meta_prompt=False) -> Optional[str]:
        """
        Process AI prompt for a specific development stage, with meta-prompting.
        """
        try:
            logging.info(f"THINKING: Processing {stage} with context keys: {list(context.keys())}")
            # Inject relevant files if this stage modifies or writes code
            if stage in ["feature_implementation", "code_refactoring"]:
                prompt_text = context.get("prompt") or context.get("project_scope", {}).get("description", "")
                relevant_files = detect_relevant_files(prompt_text, self.project_path)
                context["relevant_files"] = []

                for file_path in relevant_files:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            context["relevant_files"].append({
                                "filename": os.path.relpath(file_path, self.project_path),
                                "content": f.read()
                            })
                    except Exception as e:
                        logging.warning(f"Failed to read {file_path}: {e}")

                if context["relevant_files"]:
                    context["instruction"] = (
                        f"Update the following files to match the goal: '{prompt_text}'. "
                        "Only change what's necessary. Do not delete unrelated code."
                    )
            self._update_development_journal(f"Starting to process: {stage}", f"AI Processing - {stage}")

            combined_input = json.dumps({"stage": stage, "context": context, "meta_prompt": is_meta_prompt})
            ai_script_path = "src/models/ai_assistant.py"
            command = ["python", ai_script_path, combined_input]

            self.state.log_task(f"Processing {stage}")

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )

            stdout_chunks, stderr_chunks = [], []

            # Collect stdout/stderr without assuming structure
            while True:
                stdout_line = process.stdout.readline()
                if stdout_line:
                    stdout_chunks.append(stdout_line)
                    if stdout_line.strip().startswith('{'):
                        logging.info(f"AI progress: {stdout_line[:80].strip()}...")

                stderr_line = process.stderr.readline()
                if stderr_line:
                    stderr_chunks.append(stderr_line)
                    logging.warning(f"AI warning: {stderr_line.strip()}")

                if not stdout_line and not stderr_line and process.poll() is not None:
                    break

            remaining_out, remaining_err = process.communicate()
            stdout_chunks.append(remaining_out or "")
            stderr_chunks.append(remaining_err or "")

            full_stdout = ''.join(stdout_chunks).strip()
            full_stderr = ''.join(stderr_chunks).strip()

            if process.returncode != 0 or full_stderr:
                logging.error(f"AI Assistant Error: {full_stderr}")
                self.state.log_error(f"AI processing failed: {full_stderr}")
                return None

            # Attempt to extract valid JSON from AI output
            try:
                json_start = full_stdout.index('{')
                json_end = full_stdout.rindex('}') + 1
                json_blob = full_stdout[json_start:json_end]
                json.loads(json_blob)  # Verify validity
            except (ValueError, json.JSONDecodeError) as e:
                logging.error(f"Failed to parse JSON from AI response: {e}")
                self.state.log_error("AI response not in valid JSON format.")
                return None

            # Mark task complete and log summary
            self.state.complete_task(f"Processing {stage}")
            preview = json_blob[:100] + "..." if len(json_blob) > 100 else json_blob
            self._update_development_journal(f"AI Response Summary:\n```\n{preview}\n```")

            return json_blob.strip()

        except Exception as e:
            error_msg = f"Critical error in process_prompt_with_ai: {e}"
            logging.error(error_msg)
            self.state.log_error(error_msg)
            return None

    def start_autonomous_development(self, initial_requirements: str):
        """
        Initiate the autonomous project development process.
        :param initial_requirements: Initial project requirements or description
        """
        # Create a README.md immediately to show activity
        readme_path = os.path.join(self.project_path, "README.md")
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(f"# Autonomous Project\n\n")
            f.write(f"Project started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Requirements: {initial_requirements}\n\n")
            f.write("## Development Status\n\n")
            f.write("🔄 Initializing autonomous development...\n")

        # Log the start
        logging.info(f"Starting autonomous development with requirements: {initial_requirements}")
        self._update_development_journal(f"Starting development with requirements: {initial_requirements}",
                                         "Project Initialization")

        # Launch the development workflow in a thread
        threading.Thread(
            target=self._development_workflow,
            args=(initial_requirements,),
            daemon=True
        ).start()

        # Create an immediate feedback to show we're working
        self.state.log_task("Initializing development workflow")


    def _update_readme_status(self, status_message):
        """Update the README.md with current status"""
        readme_path = os.path.join(self.project_path, "README.md")
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.readlines()

            # Find the status section and update it
            status_index = -1
            for i, line in enumerate(content):
                if "## Development Status" in line:
                    status_index = i
                    break

            if status_index >= 0:
                # Replace or add the status line
                if status_index + 1 < len(content) and content[status_index + 1].startswith(
                        ("🔄", "🔍", "📐", "🧪", "⚙️", "🔧", "✅", "❌", "🎉")):
                    content[status_index + 1] = f"{status_message}\n"
                else:
                    content.insert(status_index + 1, f"{status_message}\n")

            with open(readme_path, 'w', encoding='utf-8') as f:
                f.writelines(content)
        except Exception as e:
            logging.error(f"Failed to update README status: {e}")

    def _create_structure_from_architecture(self, architecture):
        """Create directory structure based on architecture definition"""
        try:
            for path in architecture.get("directory_structure", []):
                full_path = os.path.join(self.project_path, path)
                if path.endswith('/'):
                    os.makedirs(full_path, exist_ok=True)
                    self.state.log_task(f"Created directory: {path}")
                else:
                    # It's a file, create an empty file or placeholder
                    dirname = os.path.dirname(full_path)
                    if dirname:
                        os.makedirs(dirname, exist_ok=True)

                    # Only create if it doesn't exist
                    if not os.path.exists(full_path):
                        with open(full_path, 'w', encoding='utf-8') as f:
                            if path.endswith('.md'):
                                f.write(f"# {os.path.basename(path).replace('.md', '')}\n\nPlaceholder content.\n")
                            elif path.endswith('.py'):
                                f.write(f"# {os.path.basename(path)}\n# Placeholder file\n\n")
                            elif path.endswith('.html'):
                                f.write(
                                    f"<!DOCTYPE html>\n<html>\n<head>\n    <title>Placeholder</title>\n</head>\n<body>\n    <h1>Placeholder</h1>\n</body>\n</html>")

                        self.state.log_task(f"Created file: {path}")
        except Exception as e:
            error_msg = f"Failed to create structure: {e}"
            logging.error(error_msg)
            self.state.log_error(error_msg)

    def _inject_creative_thought(self, context):
        """Add a creative thought to the development journal to simulate developer thinking"""
        creative_thoughts = {
            "architecture": [
                "I'm considering a more modular approach to make testing easier.",
                "The requirements suggest a need for high scalability. I should plan for that.",
                "Should I use a database here? Let me think about the data persistence needs.",
                "This might benefit from a service-oriented architecture pattern.",
                "I wonder if I should separate the UI and business logic more clearly."
            ],
            "testing": [
                "I should focus on testing edge cases first.",
                "Integration tests will be crucial for this feature.",
                "I need to mock external dependencies for these tests.",
                "Test-driven approach would work well for these complex business rules.",
                "Should set up a test fixture for consistent data across tests."
            ],
            "implementation": [
                "I'll use dependency injection here to improve testability.",
                "This looks like a good candidate for the strategy pattern.",
                "Caching might improve performance for this feature.",
                "I'm going to implement this using async operations for better responsiveness.",
                "This would be cleaner with a factory method."
            ],
            "refactoring": [
                "This method is doing too much. I'll break it down.",
                "These similar functions could be consolidated.",
                "Variable names here could be more descriptive.",
                "I should extract this logic into a separate utility class.",
                "This algorithm could be optimized with memoization."
            ]
        }

        thought = random.choice(creative_thoughts.get(context, ["Hmm, thinking about the best approach..."]))
        self._update_development_journal(f"💭 {thought}", "Creative Thinking")
        logging.info(f"Creative thought: {thought}")

    def _add_spontaneous_improvement(self):
        """Add a spontaneous improvement to show creative behavior"""
        improvements = [
            {"file": "README.md",
             "content": "## How to Contribute\n\nContributions are welcome! Please feel free to submit a Pull Request.\n"},
            {"file": "CHANGELOG.md",
             "content": "# Changelog\n\n## [0.1.0] - Initial Release\n- Basic functionality implemented\n"},
            {"file": ".gitignore",
             "content": "# Python\n__pycache__/\n*.py[cod]\n*$py.class\n*.so\n.Python\nbuild/\ndist/\n"},
            {"file": "src/utils.py",
             "content": "# Utility functions\n\ndef safe_get(data, key, default=None):\n    \"\"\"Safely get a value from a dictionary.\"\"\"\n    return data.get(key, default)\n"},
            {"file": "LICENSE",
             "content": "MIT License\n\nPermission is hereby granted, free of charge, to any person obtaining a copy of this software...\n"}
        ]

        improvement = random.choice(improvements)
        filename = improvement["file"]
        content = improvement["content"]

        # Check if file exists and append to it, or create new
        file_path = os.path.join(self.project_path, filename)
        if os.path.exists(file_path):
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write("\n" + content)
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        self.state.log_task(f"Spontaneous improvement: Added/updated {filename}")
        self._update_development_journal(f"Spontaneously added: {filename}", "Spontaneous Improvement")

    def _create_final_documentation(self):
        """Create final documentation for the project"""
        # Update README with completion info
        readme_path = os.path.join(self.project_path, "README.md")
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Add installation and usage sections
            content += "\n\n## Installation\n\n"
            content += "```bash\n"
            content += "pip install -r requirements.txt\n"
            content += "```\n\n"

            content += "## Usage\n\n"
            content += "```python\n"
            content += "# Example usage will go here\n"
            content += "```\n\n"

            # Add stats about development
            content += f"## Development Statistics\n\n"
            content += f"- Files created: {len(self.state.state['code_files'])}\n"
            content += f"- Tasks completed: {len(self.state.state['completed_tasks'])}\n"
            content += f"- Development time: {len(self.state.state['completed_tasks']) * 2} minutes (simulated)\n"

            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logging.error(f"Failed to create final documentation: {e}")

    def _development_workflow(self, initial_requirements: str):
        try:
            # Phase 1: Requirement Analysis
            self.current_phase = "requirement_analysis"
            self._update_readme_status("🔍 Analyzing requirements...")
            self._update_development_journal("Starting requirement analysis", "Requirement Analysis")

            self.project_scope = self.requirement_agent.analyze(initial_requirements)
            self.rag.embed_current_vault()
            feedback = self.project_scope
            self.state.log_task("Analyzed Requirements")
            self._update_development_journal(
                f"Project scope defined:\n```json\n{json.dumps(self.project_scope, indent=2)}\n```")
            self._update_readme_status("✅ Requirements analyzed")

            time.sleep(1)

            iteration_count = 0
            max_iterations = 3

            while iteration_count < max_iterations:
                iteration_count += 1
                self._update_development_journal(f"Starting iteration {iteration_count}/{max_iterations}",
                                                 f"Iteration {iteration_count}")

                # Phase 2: Architecture Design
                self.current_phase = "architecture_design"
                self._update_readme_status("📐 Designing architecture...")

                if random.random() < 0.7:
                    self._inject_creative_thought("architecture")

                context = {
                    "project_scope": feedback,
                    "default_structure": ["src/", "tests/", "docs/", "README.md"]
                }
                if self.feedback_buffer:
                    context["previous_feedback"] = self.feedback_buffer

                self.architecture = self.architecture_agent.design(context)
                self._create_structure_from_architecture(self.architecture)
                self.rag.embed_current_vault()
                self.state.log_task("Designed Architecture")
                self._update_development_journal(
                    f"Architecture design:\n```json\n{json.dumps(self.architecture, indent=2)}\n```")
                self._update_readme_status("✅ Architecture designed")

                # Phase 3: Test-Driven Development (RED)
                self.current_phase = "test_driven_development"
                self._update_readme_status("🧪 Generating tests...")

                if random.random() < 0.5:
                    self._inject_creative_thought("testing")

                test_context = {"architecture": self.architecture}
                if self.feedback_buffer:
                    test_context["previous_feedback"] = self.feedback_buffer

                self.tests = self.test_generation_agent.generate_tests(test_context)

                for test in self.tests:
                    test_name = test.get('name')
                    test_module = test.get('module', 'test_unknown.py')
                    test_content = test.get('content', '')

                    cycle_id = self.tdd.start_cycle(test_name)
                    test['cycle_id'] = cycle_id
                    self.tdd.set_stage(cycle_id, TDDStage.RED)
                    self.tdd.add_test_content(cycle_id, test_content)

                    test_path = os.path.join(self.project_path, 'tests', test_module)
                    os.makedirs(os.path.dirname(test_path), exist_ok=True)
                    with open(test_path, 'w', encoding='utf-8') as f:
                        f.write(test_content)

                    self.rag.log_ai_response("tdd_red", test_content)
                    self.state.log_task(f"Created RED test: {test_name}")

                # Confirm RED state (tests fail)
                red_failed = not self.testing_framework.run_tests()
                if red_failed:
                    self._update_development_journal("Red phase confirmed: tests fail as expected.")
                else:
                    self._update_development_journal("Warning: RED tests unexpectedly passed!", "⚠️ TDD Violation")

                self._update_readme_status("✅ Tests generated")

                # Phase 4: Implementation (GREEN)
                self.current_phase = "implementation"
                self._update_readme_status("⚙️ Implementing features...")

                if random.random() < 0.8:
                    self._inject_creative_thought("implementation")

                impl_context = {"tests": self.tests}
                if self.feedback_buffer:
                    impl_context["previous_feedback"] = self.feedback_buffer

                implementation_results = self.feature_implementation_agent.implement_features(self.tests)

                for mod in implementation_results.get("implemented_modules", []):
                    filename = mod.get("filename", "unknown.py")
                    content = mod.get("content", "# Empty file")

                    self.state.add_code_file(filename, content)
                    self.state.log_task(f"Implemented: {filename}")

                # Update GREEN stage for each test
                for test in self.tests:
                    cycle_id = test.get('cycle_id')
                    filename = test.get("module", "unknown.py")
                    impl_code = next((m.get("content") for m in implementation_results.get("implemented_modules", [])
                                      if m.get("filename") == filename), None)
                    if cycle_id and impl_code:
                        self.tdd.set_stage(cycle_id, TDDStage.GREEN)
                        self.tdd.add_implementation(cycle_id, impl_code)

                self.rag.embed_current_vault()
                self._update_readme_status("✅ Features implemented")

                # Phase 5: Refactoring (conditional)
                self.current_phase = "refactoring"
                self._update_readme_status("🔧 Evaluating need for refactoring...")

                if random.random() < 0.3:
                    self._inject_creative_thought("refactoring")

                for test in self.tests:
                    cycle_id = test.get("cycle_id")
                    if not cycle_id:
                        continue

                    needs_refactor, reason = self.tdd.should_refactor(cycle_id)
                    if needs_refactor:
                        self._update_development_journal(f"Refactoring triggered for {test['name']}:\n{reason}")
                        self.tdd.set_stage(cycle_id, TDDStage.REFACTOR)
                        self.refactoring_agent.refactor_code({"cycle_id": cycle_id})
                    else:
                        self._update_development_journal(f"No refactoring needed for {test['name']}")

                    self.tdd.complete_cycle(cycle_id)

                self._update_readme_status("✅ Code refactored")

                # Phase 6: Validation
                self.current_phase = "validation"
                self._update_readme_status("✅ Validating code...")

                success = self.testing_framework.run_tests()
                self.state.add_test_result(f"iteration_{iteration_count}_validation", success)

                if not success and iteration_count < max_iterations:
                    self._update_development_journal("Tests failed, need to fix implementation!", "Validation Failed")
                    self._update_readme_status("❌ Tests failed, fixing issues...")
                    feedback = {"success": success, "needs_refinement": True}
                    self.feedback_buffer = feedback
                else:
                    feedback = {"success": success}
                    self.feedback_buffer = None

                self._update_development_journal(f"Completed iteration {iteration_count} with success: {success}")

                if random.random() < 0.4:
                    self._add_spontaneous_improvement()

                time.sleep(1)

            self.current_phase = "completed"
            self._update_readme_status("🎉 Project development completed!")
            self._update_development_journal("Autonomous project development completed.", "Project Completion")
            self._create_final_documentation()
            self.rag.embed_current_vault()
            self.state.export_state(os.path.join(self.project_path, "project_state.json"))
            logging.info("Autonomous project development completed.")

        except Exception as e:
            error_msg = f"Autonomous development failed: {e}"
            logging.error(error_msg)
            self.state.log_error(error_msg)
            self.current_phase = "error"
            self._update_readme_status(f"❌ Development error: {str(e)[:50]}...")
            self.state.export_state(os.path.join(self.project_path, "project_state_error.json"))

        # Final vault sync
        self.rag.embed_current_vault()

        # 🔓 FIX: Re-enable prompt input at the end of dev
        if hasattr(self, 'ide_instance') and self.ide_instance:
            self.ide_instance.safe_ui_call(self.ide_instance.toggle_generation_ui, True)

    def _analyze_requirements(self, requirements: str) -> Dict:
        """
        Analyze and break down project requirements.

        :param requirements: Initial project description
        :return: Structured project scope
        """
        logging.info(f"Analyzing requirements: {requirements}")

        context = {
            "requirements": requirements,
            "project_name": self._generate_project_name()
        }

        ai_response = self.process_prompt_with_ai("requirement_analysis", context)
        if ai_response:
            self.rag.log_ai_response("requirement_analysis", ai_response)

        # Parse AI response or use default
        try:
            project_scope = json.loads(ai_response) if ai_response else {
                "project_name": context["project_name"],
                "key_features": ["Core Functionality"],
                "constraints": []
            }
        except json.JSONDecodeError:
            project_scope = {
                "project_name": context["project_name"],
                "key_features": ["Core Functionality"],
                "constraints": []
            }

        return project_scope

    def _design_project_architecture(self, project_scope: Dict) -> Dict:
        """
        Design initial project architecture and structure.

        :param project_scope: Analyzed project requirements
        :return: Project architecture blueprint
        """
        logging.info("Designing project architecture")

        # Determine if this is a web project
        is_web_project = any(keyword in str(project_scope).lower() for keyword in ["web", "html", "website", "page"])

        default_structure = [
            "src/",
            "tests/",
            "docs/",
            "README.md"
        ]

        if is_web_project:
            default_structure = [
                "index.html",
                "css/",
                "js/",
                "images/",
                "README.md"
            ]

        context = {
            "project_scope": project_scope,
            "default_structure": default_structure,
            "is_web_project": is_web_project
        }

        ai_response = self.process_prompt_with_ai("architecture_design", context)
        if ai_response:
            self.rag.log_ai_response("architecture_design", ai_response)

        # Parse AI response or use default
        try:
            architecture = json.loads(ai_response) if ai_response else {
                "project_name": project_scope.get("project_name", "Unnamed Project"),
                "directory_structure": context["default_structure"],
                "initial_modules": [],
                "testing_framework": "pytest" if not is_web_project else "manual"
            }
        except json.JSONDecodeError:
            architecture = {
                "project_name": project_scope.get("project_name", "Unnamed Project"),
                "directory_structure": context["default_structure"],
                "initial_modules": [],
                "testing_framework": "pytest" if not is_web_project else "manual"
            }

        return architecture

    def _generate_initial_tests(self, architecture: Dict) -> List[Dict]:
        """
        Generate initial test cases for the project.

        :param architecture: Project architecture blueprint
        :return: List of initial test cases
        """
        logging.info("Generating initial test cases")

        context = {
            "architecture": architecture
        }

        ai_response = self.process_prompt_with_ai("test_generation", context)
        if ai_response:
            self.rag.log_ai_response("test_generation", ai_response)

        # Parse AI response or use default
        try:
            initial_tests = json.loads(ai_response) if ai_response else [
                {
                    "name": "test_project_initialization",
                    "description": "Verify project initializes correctly",
                    "module": "test_core.py"
                }
            ]
        except json.JSONDecodeError:
            initial_tests = [
                {
                    "name": "test_project_initialization",
                    "description": "Verify project initializes correctly",
                    "module": "test_core.py"
                }
            ]

        return initial_tests

    def _implement_features(self, tests: List[Dict]) -> Dict:
        """
        Implement features based on generated test cases.

        :param tests: List of test cases
        :return: Implementation results
        """
        logging.info("Implementing features")

        context = {
            "tests": tests,
            "output_format": "Return a JSON object with an 'implemented_modules' array where each module has 'filename' and 'content' properties"
        }

        # Enrich context with relevant files before asking AI
        context = enrich_context_with_relevant_files(context, self.project_path)

        ai_response = self.process_prompt_with_ai("feature_implementation", context)
        if ai_response:
            self.rag.log_ai_response("feature_implementation", ai_response)

        # Parse AI response or fallback
        try:
            implementation_results = json.loads(ai_response) if ai_response else {
                "implemented_modules": [],
                "test_coverage": {}
            }

            for module in implementation_results.get("implemented_modules", []):
                logging.info(f"AI generated file: {module.get('filename')}")

        except json.JSONDecodeError:
            logging.error(f"JSON decode error for feature implementation response: {ai_response[:200]}...")
            implementation_results = self._extract_code_from_text(ai_response)

        return implementation_results

    def _perform_code_refactoring(self, implementation_results: Dict):
        """
        Refactor implemented code to improve quality and maintainability.

        :param implementation_results: Results from feature implementation
        """
        logging.info("Performing code refactoring")

        context = {
            "implementation_results": implementation_results
        }

        self.process_prompt_with_ai("code_refactoring", context)

    def _validate_project(self) -> Dict:
        """
        Validate the overall project quality and completeness.

        :return: Validation results
        """
        logging.info("Validating project")

        validation_results = {
            "test_success_rate": self._run_tests(),
            "code_quality_score": self._analyze_code_quality()
        }

        return validation_results

    def _run_tests(self) -> float:
        """
        Run project tests and calculate success rate.
        :return: Percentage of tests passed
        """
        try:
            result = subprocess.run(
                ['pytest', '--disable-warnings', '--quiet'],
                capture_output=True,
                text=True,
                cwd=self.project_path
            )
            # Basic test success rate calculation
            total_tests = result.stdout.count('collected')
            passed_tests = result.stdout.count('passed')

            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            return success_rate
        except Exception as e:
            logging.error(f"Test execution failed: {e}")
            return 0.0

    def _analyze_code_quality(self) -> float:
        """
        Perform basic code quality analysis.
        :return: Code quality score (0-100)
        """
        try:
            result = subprocess.run(
                ['pylint', self.project_path],
                capture_output=True,
                text=True
            )
            # Parse pylint output and convert to quality score
            # This is a simplistic implementation and can be enhanced
            quality_score = 100 - result.stdout.count('issue')
            return max(0, min(quality_score, 100))
        except Exception as e:
            logging.error(f"Code quality analysis failed: {e}")
            return 50.0  # Default neutral score

    def _generate_project_name(self) -> str:
        """
        Generate a unique project name.
        :return: Generated project name
        """
        project_prefixes = [
            "quantum", "dynamic", "smart", "advanced", "intelligent",
            "adaptive", "innovative", "next-gen", "ultra", "pro"
        ]
        project_suffixes = [
            "system", "framework", "solution", "engine", "platform"
        ]
        prefix = random.choice(project_prefixes)
        suffix = random.choice(project_suffixes)
        unique_id = str(uuid.uuid4())[:8]
        return f"{prefix}_{suffix}_{unique_id}"

    def get_current_status(self) -> Dict:
        """
        Retrieve the current status of the autonomous project development.
        :return: Current development status
        """
        return {
            "phase": self.current_phase,
            "timestamp": datetime.now().isoformat(),
            "completed_tasks": len(self.state.state["completed_tasks"]),
            "total_files": len(self.state.state["code_files"]),
            "errors": len(self.state.state["errors"])
        }


class ProjectContext:
    def __init__(self, project_name, description, path):
        self.project_name = project_name
        self.description = description
        self.path = path
        self.milestones = []
        self.tasks = []
        self.completed_tasks = []
        self.documentation = []
        self.current_phase = "Planning"

    def update_milestones(self, milestone):
        if milestone not in self.milestones:
            self.milestones.append(milestone)

    def complete_task(self, task):
        if task in self.tasks:
            self.tasks.remove(task)
            self.completed_tasks.append(task)

    def add_documentation(self, doc):
        self.documentation.append(doc)


def generate_readme(context: ProjectContext):
    """
    Generate a README.md file with project information and instructions.
    """
    readme_path = os.path.join(context.path, 'README.md')
    with open(readme_path, 'w', encoding='utf-8') as readme:
        readme.write(f"# {context.project_name}\n\n")
        readme.write(f"## Description\n{context.description}\n\n")
        readme.write("## Milestones\n")
        for milestone in context.milestones:
            readme.write(f"- {milestone}\n")
        readme.write("\n## Completed Tasks\n")
        for task in context.completed_tasks:
            readme.write(f"- {task}\n")
        readme.write("\n## How to Use\n")
        readme.write("1. Follow the setup instructions in `docs/SETUP.md`.\n")
        readme.write("2. Run the main script in the `src` folder.\n")
        readme.write("3. Run tests using `pytest`.\n")


def transition_to_next_phase(context: ProjectContext):
    """
    Transition the project to the next phase based on context and progress.
    """
    if context.current_phase == "Planning":
        context.current_phase = "Development"
    elif context.current_phase == "Development":
        if len(context.tasks) == 0:
            context.current_phase = "Testing"
        else:
            logging.info("Development phase ongoing, tasks remain.")
    elif context.current_phase == "Testing":
        if all(task in context.completed_tasks for task in context.tasks):
            context.current_phase = "Documentation"
        else:
            logging.info("Testing phase ongoing, not all tasks completed.")
    elif context.current_phase == "Documentation":
        context.current_phase = "Ready for Review"
    else:
        logging.info("Project is ready for review.")


class RedGreenRefactorIDE:
    def __init__(self, root=None):
        self.root = root or tk.Tk()
        self.root.title("Red-Green-Refactor IDE")
        self.root.geometry("1400x900")

        self.ai_task_queue = queue.Queue()
        self.ai_response_queue = queue.Queue()
        self.setup_logging()
        self.setup_menu()
        self.create_main_layout()
        self.poll_queue()  # Start polling the queue
        self.projects_base_dir = os.path.join('data', 'projects')
        self.current_project_files = {}
        os.makedirs(self.projects_base_dir, exist_ok=True)

        self.current_project = None
        self.project_tree = None

        self.setup_logging()
        self.setup_ui()

    def safe_ui_call(self, func: Callable, *args, **kwargs):
        self.root.after(0, lambda: func(*args, **kwargs))

    def handle_state_event(self, event_type, data):
        if event_type == "file_created":
            self.populate_tree_view()

    def setup_ui(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_command(label="Open Project", command=self.open_project)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True)

        left_panel = ttk.Frame(main_container)
        self.project_tree = ttk.Treeview(left_panel, columns=('path',), show='tree')
        self.project_tree.pack(fill=tk.BOTH, expand=True)
        main_container.add(left_panel)

        right_panel = ttk.Frame(main_container)
        self.output_console = scrolledtext.ScrolledText(right_panel, wrap=tk.WORD, state='disabled', height=20)
        self.output_console.pack(fill=tk.BOTH, expand=True)
        main_container.add(right_panel)

    def poll_queue(self):
        try:
            while not self.ai_response_queue.empty():
                status, data = self.ai_response_queue.get_nowait()
                if status == "success":
                    self.root.after(0, lambda d=data: self.finalize_project_generation(d))
                elif status == "error":
                    self.root.after(0, lambda msg=data: self.handle_generation_failure(error_message=msg))
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.poll_queue)

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Existing menu setup with additional error handling
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.safe_new_project)
        file_menu.add_command(label="Open Project", command=self.safe_open_project)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

    def safe_new_project(self):
        try:
            self.new_project()
        except Exception as e:
            messagebox.showerror("Project Creation Error", str(e))
            logging.error(f"Project creation failed: {e}")

    def safe_open_project(self):
        try:
            self.open_project()
        except Exception as e:
            messagebox.showerror("Project Open Error", str(e))
            logging.error(f"Project open failed: {e}")

    def create_main_layout(self):
        # Existing main layout with enhanced error handling
        try:
            main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
            main_container.pack(fill=tk.BOTH, expand=True)

            # Layout components with extensive error handling
            left_panel = self.create_left_panel(main_container)
            right_panel = self.create_right_panel(main_container)

            main_container.add(left_panel)
            main_container.add(right_panel)

            self.create_command_bar(self.root)
        except Exception as e:
            messagebox.showerror("Layout Initialization Error", str(e))
            logging.critical(f"Layout creation failed: {e}")

    def create_left_panel(self, parent):
        left_panel = ttk.Frame(parent)
        self.project_tree = self.create_project_tree(left_panel)
        self.output_console = self.create_output_console(left_panel)
        return left_panel

    def create_right_panel(self, parent):
        right_panel = ttk.PanedWindow(parent, orient=tk.VERTICAL)
        self.ai_plan_listbox = self.create_ai_plan(right_panel)
        self.file_editor = self.create_file_editor(right_panel)
        return right_panel

    def create_project_tree(self, parent):
        tree = ttk.Treeview(parent, columns=('path',), show='tree')
        tree.pack(fill=tk.BOTH, expand=True)
        tree.bind('<<TreeviewSelect>>', self.on_file_select)
        return tree

    def create_output_console(self, parent):
        console = scrolledtext.ScrolledText(
            parent, height=15, wrap=tk.WORD, state='disabled'
        )
        console.pack(fill=tk.X, side=tk.BOTTOM)
        return console

    def create_ai_plan(self, parent):
        plan_frame = ttk.LabelFrame(parent, text="AI Project Plan")
        listbox = tk.Listbox(plan_frame, height=10)
        listbox.pack(fill=tk.BOTH, expand=True)
        parent.add(plan_frame)
        return listbox

    def create_file_editor(self, parent):
        editor_frame = ttk.LabelFrame(parent, text="File Contents")
        editor = scrolledtext.ScrolledText(
            editor_frame, wrap=tk.WORD, undo=True
        )
        editor.pack(fill=tk.BOTH, expand=True)
        editor.bind('<<Modified>>', self.on_file_modified)
        parent.add(editor_frame)
        return editor

    def create_command_bar(self, parent):
        command_bar = ttk.Frame(parent)
        command_bar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(command_bar, text="Project Prompt:").pack(side=tk.LEFT, padx=(0, 5))
        self.prompt_entry = ttk.Entry(command_bar, width=50)
        self.prompt_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        button_frame = ttk.Frame(command_bar)
        button_frame.pack(side=tk.LEFT, padx=5)

        self.generate_btn = ttk.Button(
            button_frame, text="Generate Project", command=self.generate_project_with_ai
        )
        self.generate_btn.pack(side=tk.LEFT, padx=2)

        self.pause_btn = ttk.Button(
            button_frame, text="Pause", command=self.pause_project, state=tk.DISABLED
        )
        self.pause_btn.pack(side=tk.LEFT, padx=2)

        self.stop_btn = ttk.Button(
            button_frame, text="Stop", command=self.stop_project, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=2)

    def process_prompt_with_ai(self, combined_input: str) -> Optional[str]:
        ai_script_path = "src/models/ai_assistant.py"
        python_executable = 'python'

        try:
            command = [python_executable, ai_script_path, combined_input]
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            ai_response, error = process.communicate()
            if process.returncode != 0 or error:
                raise Exception(f"AI Assistant Error: {error.strip()}")
            return ai_response.strip()
        except Exception as e:
            self.safe_ui_call(self.log_output, f"Failed to communicate with AI: {e}")
            return None

    def new_project(self):
        project_id = str(uuid.uuid4())
        project_path = os.path.join(self.projects_base_dir, project_id)
        os.makedirs(project_path, exist_ok=True)
        self.current_project = project_path
        self.safe_ui_call(self.log_output, f"New project created: {project_path}")

    def open_project(self):
        project_path = filedialog.askdirectory(initialdir=self.projects_base_dir)
        if project_path:
            self.current_project = project_path
            self.safe_ui_call(self.log_output, f"Opened project: {project_path}")

            self.populate_tree_view()

    def populate_tree_view(self):
        if not self.current_project:
            return

        self.project_tree.delete(*self.project_tree.get_children())
        for root, dirs, files in os.walk(self.current_project):
            parent = self.project_tree.insert('', 'end', text=os.path.basename(root), values=(root,))
            for file in files:
                self.project_tree.insert(parent, 'end', text=file, values=(os.path.join(root, file),))

    def run_project_generation(self, metadata: Dict[str, Any]):
        """
        Run project generation and ensure tasks are processed.
        """
        if not self.current_project:
            self.safe_ui_call(self.log_output, "No project selected. Create or open a project first.")

            return

        self.safe_ui_call(self.log_output, "Starting project generation...")

        # Initialize project context
        context = ProjectContext(
            project_name=metadata.get("project_name", "Unnamed Project"),
            description=metadata.get("project_description", "No description provided."),
            path=self.current_project
        )

        # Update milestones and tasks
        context.milestones.extend(metadata.get("milestones", []))
        context.tasks.extend(metadata.get("tasks", []))

        # Generate project structure
        ProjectManager.create_project_structure(self.current_project, metadata, self.log_output)

        # Write TODO.md
        ProjectManager.write_todo_list(self.current_project, context.tasks, self.log_output)

        # Generate documentation
        generate_readme(context)

        # Run tests
        if ProjectManager.run_tests(self.current_project, self.log_output):
            context.complete_task("Run all tests")
            self.safe_ui_call(self.log_output, "All tests passed successfully!")

        # Update project phase
        transition_to_next_phase(context)

        if context.current_phase == "Ready for Review":
            self.safe_ui_call(self.log_output, "Project development is complete and ready for review.")

        else:
            # Continue autonomous workflow
            self.continue_autonomous_workflow(metadata)

    def continue_autonomous_workflow(self, metadata: Dict[str, Any]):
        """
        Continue the workflow based on AI feedback and project state.
        """
        if not metadata.get("next_steps"):
            self.safe_ui_call(self.log_output, "Project development is complete.")

            return

        self.safe_ui_call(self.log_output, "Requesting additional steps from AI...")

        ai_agent = AutonomousProjectAgent(self.current_project)
        ai_agent.state.register_observer(self.handle_state_event)

        ai_feedback = ai_agent.process_prompt_with_ai("next_steps", {"current_state": metadata})

        if ai_feedback:
            parsed_metadata = AIResponseParser.parse_ai_response(ai_feedback)
            self.run_project_generation(parsed_metadata)
        else:
            self.safe_ui_call(self.log_output, "No further steps provided by AI.")

    def generate_project_with_ai(self):
        """
        Start autonomous project generation with AI.
        """
        raw_prompt = self.prompt_entry.get()
        prompt = AIResponseParser.sanitize_prompt(raw_prompt)

        if not AIResponseParser.validate_prompt(prompt):
            messagebox.showwarning("Invalid Prompt", "Please provide a clear, meaningful project description.")
            return

        self.safe_ui_call(self.log_output, "Starting AI-based autonomous project generation...")

        self.toggle_generation_ui(False)

        # Create project directory
        project_id = str(uuid.uuid4())
        project_path = os.path.join(self.projects_base_dir, project_id)
        os.makedirs(project_path, exist_ok=True)
        self.current_project = project_path

        # Initialize Autonomous Project Agent
        self.ai_agent = AutonomousProjectAgent(self.current_project, ide_instance=self)
        self.ai_agent.state.register_observer(self.handle_state_event)

        # Run an initial setup prompt to get initial files
        init_context = {
            "prompt": prompt,
            "format": "Return JSON with 'initial_files', 'project_tasks', and 'project_structure'"
        }
        initial_response = self.ai_agent.process_prompt_with_ai("initial_project_setup", init_context)

        # If initial files are returned, parse and write them
        initial_metadata = AIResponseParser.parse_ai_response(initial_response)
        if initial_metadata and "initial_files" in initial_metadata:
            initial_files = initial_metadata.get("initial_files", {})

            if isinstance(initial_files, dict):
                for filename, content in initial_files.items():
                    self.ai_agent.state.add_code_file(filename, content)
            elif isinstance(initial_files, list):
                for file_entry in initial_files:
                    if isinstance(file_entry, dict):
                        filename = file_entry.get("filename")
                        content = file_entry.get("content", "# Placeholder content\n")
                    else:
                        filename = str(file_entry)
                        content = "# Placeholder content\n"
                    if filename:
                        self.ai_agent.state.add_code_file(filename, content)

            # Optional: also write project structure if included
            if "project_structure" in initial_metadata:
                ProjectManager.create_project_structure(self.ai_agent.project_path, initial_metadata, print)

            self.populate_tree_view()

        self.ai_agent.start_autonomous_development(prompt)

        self.safe_ui_call(self.log_output, "Autonomous agent has been launched.")

        self.populate_tree_view()
        self.update_ai_plan('\n'.join([
            "Analyzing requirements",
            "Designing architecture",
            "Generating tests",
            "Implementing features",
            "Refactoring code",
            "Validating project"
        ]))

    def threaded_ai_generation(self, prompt):
        """
        Run AI generation logic in a separate thread and enqueue results.
        """
        try:
            ai_response = self.process_prompt_with_ai(prompt)
            if ai_response:
                parsed_metadata = AIResponseParser.parse_ai_response(ai_response)
                self.ai_response_queue.put(("success", parsed_metadata))
            else:
                self.ai_response_queue.put(("error", "AI response is empty."))
        except Exception as e:
            logging.error(f"AI generation thread error: {e}")
            self.ai_response_queue.put(("error", str(e)))

    def finalize_project_generation(self, parsed_metadata):
        """
        Finalize the project generation with enhanced documentation and structure.

        :param parsed_metadata: Metadata returned by AI project generation
        """
        try:
            # Generate a sanitized project ID
            project_id = str(uuid.uuid4()).replace("-", "")
            project_path = os.path.normpath(os.path.join(self.projects_base_dir, project_id))

            # Create the project structure
            ProjectManager.create_project_structure(project_path, parsed_metadata)

            # Generate comprehensive project documentation
            self._generate_project_docs(project_path, parsed_metadata)

            # Set the current project and refresh the UI
            self.current_project = project_path
            self.populate_project_tree()

            # Format project structure and tasks for AI Plan
            project_structure = parsed_metadata.get('project_structure', [])
            project_tasks = parsed_metadata.get('project_tasks', [])

            # Update AI Plan with tasks
            formatted_tasks = '\n'.join(project_tasks)
            self.update_ai_plan(formatted_tasks)

            self.safe_ui_call(self.log_output, f"Project {project_id} generated successfully at {project_path}!")


        except Exception as e:
            logging.error(f"Project finalization error: {e}")
            messagebox.showerror("Generation Error", str(e))
        finally:
            self.toggle_generation_ui(True)

    def _generate_project_docs(self, project_path, parsed_metadata):
        """
        Generate comprehensive project documentation.

        :param project_path: Path to the project directory
        :param parsed_metadata: Metadata returned by AI project generation
        """
        # Ensure docs directory exists
        docs_dir = os.path.join(project_path, 'docs')
        os.makedirs(docs_dir, exist_ok=True)

        # Generate README.md
        readme_path = os.path.join(project_path, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(f"# {parsed_metadata.get('project_name', 'Unnamed Project')}\n\n")
            f.write("## Project Overview\n")
            f.write(parsed_metadata.get('project_description', 'No description available') + "\n\n")
            f.write("## Key Features\n")
            for feature in parsed_metadata.get('key_features', []):
                f.write(f"- {feature}\n")
            f.write("\n## Setup and Installation\n")
            f.write("(Add setup instructions here)\n")

        # Generate TODO.md with project tasks
        todo_path = os.path.join(project_path, 'TODO.md')
        with open(todo_path, 'w', encoding='utf-8') as f:
            f.write("# Project Tasks and Milestones\n\n")
            f.write("## Pending Tasks\n")
            for task in parsed_metadata.get('project_tasks', []):
                f.write(f"- [ ] {task}\n")

        # Generate LIST.md for feature tracking and prioritization
        list_path = os.path.join(project_path, 'LIST.md')
        with open(list_path, 'w', encoding='utf-8') as f:
            f.write("# Project Feature Tracking\n\n")

            # Implemented Features
            f.write("## Implemented Features\n")
            for feature in parsed_metadata.get('implemented_features', []):
                f.write(f"- [x] {feature}\n")

            # Planned Features
            f.write("\n## Planned Features\n")
            for feature in parsed_metadata.get('planned_features', []):
                f.write(f"- [ ] {feature}\n")

            # Priority Levels
            f.write("\n## Feature Priorities\n")
            priorities = parsed_metadata.get('feature_priorities', {})
            for priority, features in priorities.items():
                f.write(f"\n### {priority.capitalize()} Priority\n")
                for feature in features:
                    f.write(f"- {feature}\n")

            # Validation Notes
            f.write("\n## Validation Notes\n")
            validations = parsed_metadata.get('validation_notes', [])
            for note in validations:
                f.write(f"- {note}\n")

    def handle_generation_failure(self, error_message="AI generation failed. Please try again."):
        """
        Handle AI generation failure and update UI.
        """
        messagebox.showerror("AI Generation Failed", error_message)
        self.toggle_generation_ui(True)

    def toggle_generation_ui(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.prompt_entry.config(state=state)
        self.generate_btn.config(state=state)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)

    def populate_project_tree(self):
        try:
            self.project_tree.delete(*self.project_tree.get_children())
            self.current_project_files.clear()

            for root, dirs, files in os.walk(self.current_project):
                parent = self.project_tree.insert(
                    '',
                    'end',
                    text=os.path.basename(root),
                    values=(root,)
                )
                for file in files:
                    file_path = os.path.join(root, file)
                    file_id = self.project_tree.insert(
                        parent,
                        'end',
                        text=file,
                        values=(file_path,)
                    )
                    self.current_project_files[file_id] = file_path
        except Exception as e:
            logging.error(f"Error in populate_project_tree: {e}")

    def on_file_select(self, event):
        selected_item = self.project_tree.selection()
        if selected_item:
            file_path = self.project_tree.item(selected_item[0])['values'][0]
            if os.path.isfile(file_path):
                self.current_file_path = file_path
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.file_editor.delete('1.0', tk.END)
                    self.file_editor.insert('1.0', content)
                    self.file_editor.edit_modified(False)

    def on_file_modified(self, event=None):
        pass

    def update_ai_plan(self, plan_text: str):
        self.ai_plan_listbox.delete(0, tk.END)
        steps = plan_text.split('\n')
        for step in steps:
            if step.strip():
                self.ai_plan_listbox.insert(tk.END, step)

    def run_tests(self):
        try:
            result = subprocess.run(
                ['pytest'],
                capture_output=True,
                text=True,
                cwd=self.current_project
            )
            self.safe_ui_call(self.log_output, result.stdout)

            if result.returncode == 0:
                self.safe_ui_call(self.log_output, "Tests passed successfully!")

            else:
                self.safe_ui_call(self.log_output, "Tests failed:\n" + result.stderr)

        except Exception as e:
            self.safe_ui_call(self.log_output, f"Test execution error: {e}")

    def log_output(self, message: str):
        self.output_console.config(state='normal')
        self.output_console.insert(tk.END, message + "\n")
        self.output_console.see(tk.END)
        self.output_console.config(state='disabled')
        logging.info(message)

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[logging.FileHandler('project.log'), logging.StreamHandler()]
        )

    def show_about(self):
        messagebox.showinfo(
            "About Red-Green-Refactor IDE",
            "A comprehensive development environment for Test-Driven Development."
        )

    def pause_project(self):
        self.safe_ui_call(self.log_output, "Project generation paused.")

    def stop_project(self):
        self.safe_ui_call(self.log_output, "Project generation stopped.")

        self.prompt_entry.config(state=tk.NORMAL)
        self.generate_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)


if __name__ == '__main__':
    root = tk.Tk()
    app = RedGreenRefactorIDE(root)
    root.mainloop()


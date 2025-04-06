from typing import List, Dict, Any, Optional
from src.utils.file_helpers import enrich_context_with_relevant_files, detect_relevant_files
from src.agents.project_rag_coordinator import ProjectRAGCoordinator
from src.core.state_management import StateManagementSystem
from src.core.dependency_manager import DependencyManagementUnit
from src.core.automated_testing import AutomatedTestingFramework
from src.core.subtask_manager import SubtaskManager
from src.models.tdd_manager import TDDManager, TDDStage
from src.agents.architecture_agent import ArchitectureAgent
from src.agents.feature_implementation_agent import FeatureImplementationAgent
from src.agents.refactoring_agent import RefactoringAgent
from src.agents.requirement_agent import RequirementAgent
from src.agents.test_generation_agent import TestGenerationAgent
from src.agents.validation_agent import ValidationAgent
from datetime import datetime
import traceback
import uuid
import time
import random
import threading
import json
import subprocess
import logging
import queue
import os


class AutonomousProjectAgent:
    def __init__(self, project_path: str, ide_instance=None):
        self.project_path = project_path
        self.ide_instance = ide_instance
        self.state = StateManagementSystem(self.project_path)
        self.subtask_manager = SubtaskManager(
            state=self.state,
            log_fn=self._update_development_journal
        )
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

        # Prompt recursion tracking
        self.recursion_depth = 0
        self.recursion_history = []
        self.max_recursion_depth = 3
        self.prompt_cache = {}

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

    def create_subtask(self, *args, **kwargs):
        return self.subtask_manager.create_subtask(*args, **kwargs)

    def start_subtask(self, *args, **kwargs):
        return self.subtask_manager.start_subtask(*args, **kwargs)

    def complete_subtask(self, *args, **kwargs):
        return self.subtask_manager.complete_subtask(*args, **kwargs)

    def fail_subtask(self, *args, **kwargs):
        return self.subtask_manager.fail_subtask(*args, **kwargs)

    def get_subtask_status(self, *args, **kwargs):
        return self.subtask_manager.get_subtask_status(*args, **kwargs)

    def get_subtask_result(self, *args, **kwargs):
        return self.subtask_manager.get_subtask_result(*args, **kwargs)

    def process_prompt_with_recursion(self, stage: str, context: Dict, depth: int = 0) -> Optional[str]:
        """
        Process AI prompt with support for recursive decomposition of complex problems.

        :param stage: The development stage for this prompt
        :param context: The context for the prompt
        :param depth: Current recursion depth
        :return: AI response or None on failure
        """
        if depth >= self.max_recursion_depth:
            logging.warning(f"Maximum recursion depth reached for {stage}")
            return None

        # Create a cache key based on the stage and essential context
        cache_key = f"{stage}:{hash(json.dumps(context, sort_keys=True, default=str))}"

        # Check cache first
        if cache_key in self.prompt_cache:
            logging.info(f"Using cached response for {stage} at depth {depth}")
            return self.prompt_cache[cache_key]

        # Track recursion
        self.recursion_depth = depth
        self.recursion_history.append((stage, datetime.now().isoformat()))

        # Add recursion context
        context["recursion_depth"] = depth
        context["recursion_history"] = self.recursion_history.copy()

        # Process original prompt with AI
        logging.info(f"Processing prompt with recursion depth {depth} for stage {stage}")

        if depth > 0:
            # For recursive calls, mark this as a meta-prompt
            response = self.process_prompt_with_ai(stage, context, is_meta_prompt=True)
        else:
            response = self.process_prompt_with_ai(stage, context)

        if not response:
            return None

        try:
            # Parse response
            response_data = json.loads(response)

            # Check if response suggests decomposition
            if "requires_decomposition" in response_data and response_data[
                "requires_decomposition"] and depth < self.max_recursion_depth - 1:
                logging.info(f"Decomposing complex task at depth {depth} for {stage}")

                # Decompose into subtasks
                subtasks = response_data.get("subtasks", [])
                subtask_results = {}

                # Process each subtask recursively
                for i, subtask in enumerate(subtasks):
                    subtask_name = subtask.get("name", f"subtask_{i}")
                    subtask_context = subtask.get("context", {})

                    # Combine original context with subtask-specific context
                    combined_context = context.copy()
                    combined_context.update(subtask_context)

                    # Process recursively
                    subtask_result = self.process_prompt_with_recursion(
                        f"{stage}_{subtask_name}",
                        combined_context,
                        depth + 1
                    )

                    if subtask_result:
                        try:
                            subtask_results[subtask_name] = json.loads(subtask_result)
                        except json.JSONDecodeError:
                            subtask_results[subtask_name] = subtask_result

                # Re-integrate results
                integration_context = context.copy()
                integration_context["subtask_results"] = subtask_results

                # Final integration prompt
                final_response = self.process_prompt_with_ai(
                    f"{stage}_integration",
                    integration_context,
                    is_meta_prompt=True
                )

                if final_response:
                    # Cache the integrated result
                    self.prompt_cache[cache_key] = final_response
                    return final_response

            # No decomposition needed or possible, return original response
            self.prompt_cache[cache_key] = response
            return response

        except json.JSONDecodeError:
            logging.error(f"Failed to parse JSON in recursive prompt at depth {depth}")
            return response
        finally:
            # Reset recursion tracking when returning from a recursive call
            if len(self.recursion_history) > 0:
                self.recursion_history.pop()

            if depth == 0:
                self.recursion_depth = 0

    def process_prompt_with_ai(self, stage: str, context: Dict, is_meta_prompt=False) -> Optional[str]:
        """
        Process AI prompt for a specific development stage, with meta-prompting.
        """
        subtask_id = None
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

            subtask_id = None
            if stage not in self.development_stages:
                # This is likely a subtask, create tracking for it
                subtask_id = f"{stage}_{uuid.uuid4().hex[:8]}"
                self.create_subtask(subtask_id, f"Processing AI prompt for {stage}", context=context)
                self.start_subtask(subtask_id)
            else:
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
                error_msg = f"AI Assistant Error: {full_stderr}"
                logging.error(error_msg)

                if subtask_id:
                    self.fail_subtask(subtask_id, error_msg)
                else:
                    self.state.log_error(f"AI processing failed: {full_stderr}")

                return None

            # Attempt to extract valid JSON from AI output
            try:
                json_start = full_stdout.index('{')
                json_end = full_stdout.rindex('}') + 1
                json_blob = full_stdout[json_start:json_end]
                json.loads(json_blob)  # Verify validity
            except (ValueError, json.JSONDecodeError) as e:
                error_msg = f"Failed to parse JSON from AI response: {e}"
                logging.error(error_msg)

                if subtask_id:
                    self.fail_subtask(subtask_id, error_msg)
                else:
                    self.state.log_error("AI response not in valid JSON format.")

                return None

            # Mark task complete and log summary
            if subtask_id:
                self.complete_subtask(subtask_id, json_blob)
            else:
                self.state.complete_task(f"Processing {stage}")

            preview = json_blob[:100] + "..." if len(json_blob) > 100 else json_blob
            self._update_development_journal(f"AI Response Summary:\n```\n{preview}\n```")

            return json_blob.strip()

        except Exception as e:
            error_msg = f"Critical error in process_prompt_with_ai: {e}"
            logging.error(error_msg)

            if subtask_id:
                self.fail_subtask(subtask_id, error_msg)
            else:
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
            f.write("\n## Subtasks\n\n")
            f.write("| Task ID | Description | Status | Created | Updated |\n")
            f.write("|---------|-------------|--------|---------|--------|\n")

        # Log the start
        logging.info(f"Starting autonomous development with requirements: {initial_requirements}")
        self._update_development_journal(f"Starting development with requirements: {initial_requirements}",
                                         "Project Initialization")

        # Create initial subtask
        init_task_id = self.create_subtask(
            "init_development",
            "Initialize development workflow",
            context={"requirements": initial_requirements}
        )
        self.start_subtask(init_task_id)

        # Launch the development workflow in a thread
        threading.Thread(
            target=self._development_workflow,
            args=(initial_requirements, init_task_id),
            daemon=True
        ).start()

        # Create an immediate feedback to show we're working
        self.state.log_task("Initializing development workflow")

    def _update_readme_subtasks(self):
        """Update the README.md with current subtask status"""
        readme_path = os.path.join(self.project_path, "README.md")
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.readlines()

            # Find the subtasks section and update it
            subtasks_index = -1
            for i, line in enumerate(content):
                if "## Subtasks" in line:
                    subtasks_index = i
                    break

            if subtasks_index >= 0:
                # Clear existing subtask table (keep the header)
                new_content = content[:subtasks_index + 3]  # Keep up to the table header

                # Add the table headers
                if len(new_content) < subtasks_index + 3:
                    new_content.append("## Subtasks\n\n")
                    new_content.append("| Task ID | Description | Status | Created | Updated |\n")
                    new_content.append("|---------|-------------|--------|---------|--------|\n")

                # Add subtask rows
                for task_id, task in self.subtask_manager.subtasks.items():
                    status = task["status"]
                    status_emoji = {
                        "pending": "⏳",
                        "in_progress": "🔄",
                        "completed": "✅",
                        "failed": "❌"
                    }.get(status, "❓")

                    created = datetime.fromisoformat(task["created_at"]).strftime("%H:%M:%S")
                    updated = datetime.fromisoformat(task["updated_at"]).strftime("%H:%M:%S")

                    new_content.append(
                        f"| {task_id[:10]}... | {task['description'][:30]}... | {status_emoji} {status} | {created} | {updated} |\n"
                    )

                # Add the rest of the content
                found_next_section = False
                for i in range(subtasks_index + 3, len(content)):
                    if content[i].startswith("## "):
                        found_next_section = True

                    if found_next_section:
                        new_content.append(content[i])

                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_content)

            else:
                # Add subtasks section if it doesn't exist
                with open(readme_path, 'a', encoding='utf-8') as f:
                    f.write("\n## Subtasks\n\n")
                    f.write("| Task ID | Description | Status | Created | Updated |\n")
                    f.write("|---------|-------------|--------|---------|--------|\n")

                    for task_id, task in self.subtask_manager.subtasks.items():
                        status = task["status"]
                        status_emoji = {
                            "pending": "⏳",
                            "in_progress": "🔄",
                            "completed": "✅",
                            "failed": "❌"
                        }.get(status, "❓")

                        created = datetime.fromisoformat(task["created_at"]).strftime("%H:%M:%S")
                        updated = datetime.fromisoformat(task["updated_at"]).strftime("%H:%M:%S")

                        f.write(
                            f"| {task_id[:10]}... | {task['description'][:30]}... | {status_emoji} {status} | {created} | {updated} |\n"
                        )
        except Exception as e:
            logging.error(f"Failed to update README subtasks: {e}")

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

            # Also update subtasks
            self._update_readme_subtasks()

        except Exception as e:
            logging.error(f"Failed to update README status: {e}")

    def _create_structure_from_architecture(self, architecture):
        """Create directory structure based on architecture definition"""
        task_id = None
        try:
            task_id = self.create_subtask(
                "create_structure",
                "Create initial project structure",
                context={"architecture": architecture}
            )
            self.start_subtask(task_id)

            created_dirs = []
            created_files = []

            for path in architecture.get("directory_structure", []):
                full_path = os.path.join(self.project_path, path)
                if path.endswith('/'):
                    os.makedirs(full_path, exist_ok=True)
                    created_dirs.append(path)
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

                        created_files.append(path)
                        self.state.log_task(f"Created file: {path}")

            self.complete_subtask(task_id, {
                "created_directories": created_dirs,
                "created_files": created_files
            })
            self.save_checkpoint()

        except Exception as e:
            error_msg = f"Failed to create structure: {e}"
            logging.error(error_msg)
            self.state.log_error(error_msg)

            if task_id:
                self.fail_subtask(task_id, error_msg)

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

    def _development_workflow(self, initial_requirements: str, init_task_id: str):
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

                    self.save_checkpoint()

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
                    self.save_checkpoint()
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
                        self.save_checkpoint()
                    else:
                        self._update_development_journal(f"No refactoring needed for {test['name']}")

                    self.tdd.complete_cycle(cycle_id)

                self._update_readme_status("✅ Code refactored")

                # Phase 6: Validation
                self.current_phase = "validation"
                self._update_readme_status("✅ Validating code...")

                success = self.testing_framework.run_tests()
                self.state.add_test_result(f"iteration_{iteration_count}_validation", success)
                self.save_checkpoint()

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
                    self.save_checkpoint()

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
            if hasattr(self.ide_instance, "ai_response_queue"):
                self.ide_instance.ai_response_queue.put(("completed", "Autonomous development finished"))

    def save_checkpoint(self):
        """Persist current agent state for crash recovery with file-level error tracking."""
        checkpoint_path = os.path.join(self.project_path, "project_state.json")

        try:
            self.state.export_state(checkpoint_path)
            logging.info(f"Checkpoint saved at: {checkpoint_path}")
        except Exception as e:
            logging.error(f"❌ Failed to save checkpoint to {checkpoint_path}")
            logging.error(f"Exception: {e}")
            logging.debug(traceback.format_exc())

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

import logging
import threading
from typing import Dict, Any, Optional

from src.agents.AutonomousProjectAgent import AutonomousProjectAgent
from src.utils.parser_utils import AIResponseParser
from src.core.ai_runner import run_ai_prompt


class AIAgentOrchestrator:
    """
    Orchestrates AI agent activities, handling communication and coordination.
    """

    def __init__(self, controller):
        self.controller = controller
        self.ai_agent = None
        self.generation_stop_event = threading.Event()
        self.current_thread = None

    @staticmethod
    def _build_metadata_prompt(user_prompt: str) -> str:
        """
        Convert a free-form project request into the strict metadata contract
        consumed by AIResponseParser and AutonomousProjectAgent.

        The initial LLM call is a specification/bootstrap stage. It must not
        answer the user's request conversationally because the next stage
        requires machine-readable project metadata.
        """
        return f"""
You are the project bootstrap stage of RuneScript's autonomous project generator.
Transform the USER OBJECTIVE below into project metadata for the autonomous agent.

RESPONSE CONTRACT:
- Return ONLY one valid JSON object.
- Do not use Markdown fences.
- Do not add explanations before or after the JSON.
- Use double quotes for every JSON key and string.
- initial_files MUST be an empty object {{}} in this bootstrap response.
- Do NOT inline source files, markdown documents, status files, or other generated artifacts here.
- RuneScript's later autonomous stages are responsible for creating and modifying files.
- project_tasks and planned_features must contain concrete executable work items.
- Do not claim you lack repository or terminal access. This stage only prepares metadata;
  RuneScript's autonomous agent performs the subsequent project work.

Required shape:
{{
  "project_name": "string",
  "project_description": "string",
  "project_structure": ["relative/path"],
  "key_features": ["string"],
  "project_tasks": ["string"],
  "implemented_features": [],
  "planned_features": ["string"],
  "feature_priorities": {{
    "high": ["string"],
    "medium": ["string"],
    "low": ["string"]
  }},
  "validation_notes": ["string"],
  "initial_files": {{}},
  "next_steps": ["string"]
}}

USER OBJECTIVE:
{user_prompt}
""".strip()

    def process_prompt_with_ai(self, combined_input: str) -> Optional[str]:
        """Process prompt with AI and return response."""
        try:
            ai_script_path = "src/models/ai_assistant.py"
            metadata_prompt = self._build_metadata_prompt(combined_input)
            result = run_ai_prompt(ai_script_path, metadata_prompt)
            print("PROCESS_PROMPT_WITH_AI:\t", result)
            return result
        except Exception as e:
            logging.error(f"Failed to communicate with AI: {e}")
            self.controller.ui_manager.log_output(f"Failed to communicate with AI: {e}")
            return None

    def threaded_ai_generation(self, prompt: str):
        """Run AI generation logic in a separate thread and enqueue results."""
        self.current_thread = threading.current_thread()
        self.generation_stop_event.clear()

        try:
            # Log start of AI processing
            self.controller.ui_manager.log_output("Sending prompt to AI for processing...")

            # Process initial prompt with AI
            ai_response = self.process_prompt_with_ai(prompt)
            if not ai_response:
                self.controller.ai_response_queue.put(("error", "AI response is empty."))
                return

            # Check if generation was stopped
            if self.generation_stop_event.is_set():
                self.controller.ai_response_queue.put(("error", "Generation process was stopped."))
                return

            # Parse AI response
            self.controller.ui_manager.log_output("Parsing AI response...")
            parsed_metadata = AIResponseParser.parse_ai_response(ai_response)
            if not isinstance(parsed_metadata, dict):
                self.controller.ai_response_queue.put(("error", "Failed to parse AI metadata."))
                return

            required_fields = ("project_name", "project_description", "project_tasks")
            missing_fields = [field for field in required_fields if field not in parsed_metadata]
            if missing_fields:
                logging.error("AI metadata missing required fields: %s", ", ".join(missing_fields))
                self.controller.ai_response_queue.put((
                    "error",
                    f"AI metadata missing required fields: {', '.join(missing_fields)}"
                ))
                return

            # Initialize AI agent
            self._initialize_ai_agent(parsed_metadata)

            # Start autonomous development if agent initialized successfully
            if self.ai_agent:
                self.ai_agent.start_autonomous_development(prompt)

            # Let controller know we're good
            self.controller.ai_response_queue.put(("success", parsed_metadata))

        except Exception as e:
            logging.error(f"AI generation thread error: {e}")
            self.controller.ai_response_queue.put(("error", str(e)))
        finally:
            self.current_thread = None

    def _initialize_ai_agent(self, parsed_metadata: Dict[str, Any]) -> None:
        """Initialize the AI agent with project metadata."""
        try:
            self.controller.ui_manager.log_output("Initializing AI agent...")
            self.ai_agent = AutonomousProjectAgent(self.controller.current_project, ide_instance=self.controller)
            self.ai_agent.state.register_observer(self.handle_state_event)

            # Load initial files into AI agent state
            initial_files = parsed_metadata.get("initial_files", {})

            # Support both dictionary and list formats
            if isinstance(initial_files, dict):
                for filename, content in initial_files.items():
                    self.ai_agent.state.add_code_file(filename, content)
                    self.controller.ui_manager.log_output(f"Added code file to agent: {filename}")
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
                        self.controller.ui_manager.log_output(f"Added code file to agent: {filename}")

            # Also load code_files if available (some AI responses use this format)
            code_files = parsed_metadata.get("code_files", [])
            if isinstance(code_files, list):
                for file_entry in code_files:
                    if isinstance(file_entry, dict):
                        filename = file_entry.get("filename") or file_entry.get("path")
                        content = file_entry.get("content", "# Placeholder content\n")
                        if filename:
                            self.ai_agent.state.add_code_file(filename, content)
                            self.controller.ui_manager.log_output(f"Added code file to agent: {filename}")

            self.controller.ui_manager.log_output("AI agent initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize AI agent: {e}")
            self.ai_agent = None
            raise

    def handle_state_event(self, event_type, data):
        """Handle autonomous state events without touching Tk from worker threads."""
        if not self.controller.current_project:
            logging.debug("No project loaded.")
            return

        if event_type not in ("file_created", "file_updated"):
            return

        if isinstance(data, dict):
            filename = data.get("filename") or data.get("path") or "unknown"
        else:
            filename = str(data) if data is not None else "unknown"

        action = "File created" if event_type == "file_created" else "File updated"
        self.controller.ui_manager.log_output(f"{action}: {filename}")

        # State observers run in autonomous worker threads. Queue the actual
        # widget refresh for IDEController.poll_queue(), which runs in Tk.
        if hasattr(self.controller, "ai_response_queue"):
            self.controller.ai_response_queue.put((event_type, filename))

    def continue_autonomous_workflow(self, metadata: Dict[str, Any]):
        """Continue the workflow based on AI feedback and project state."""
        if not metadata.get("next_steps"):
            self.controller.ui_manager.log_output("Project development is complete.")
            return

        self.controller.ui_manager.log_output("Requesting additional steps from AI...")

        if not self.ai_agent:
            self.ai_agent = AutonomousProjectAgent(self.controller.current_project, ide_instance=self.controller)
            self.ai_agent.state.register_observer(self.handle_state_event)

        ai_feedback = self.ai_agent.process_prompt_with_ai("next_steps", {"current_state": metadata})

        if ai_feedback:
            parsed_metadata = AIResponseParser.parse_ai_response(ai_feedback)
            if parsed_metadata:
                self.controller.project_manager.run_project_generation(parsed_metadata)
            else:
                self.controller.ui_manager.log_output("Failed to parse AI feedback.")
        else:
            self.controller.ui_manager.log_output("No further steps provided by AI.")

    def stop_generation(self):
        """Stop the current generation process."""
        if self.current_thread and self.current_thread.is_alive():
            self.generation_stop_event.set()
            self.controller.ui_manager.log_output("Stopping AI generation process...")
            return True
        return False

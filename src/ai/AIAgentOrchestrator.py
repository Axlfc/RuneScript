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

    def process_prompt_with_ai(self, combined_input: str) -> Optional[str]:
        """Process prompt with AI and return response"""
        try:
            ai_script_path = "src/models/ai_assistant.py"
            result = run_ai_prompt(ai_script_path, combined_input)
            return result
        except Exception as e:
            logging.error(f"Failed to communicate with AI: {e}")
            self.controller.ui_manager.log_output(f"Failed to communicate with AI: {e}")
            return None

    def threaded_ai_generation(self, prompt: str):
        """Run AI generation logic in a separate thread and enqueue results"""
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
            if not parsed_metadata:
                self.controller.ai_response_queue.put(("error", "Failed to parse AI metadata."))
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
        """Initialize the AI agent with project metadata"""
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
        """Handle state events from the autonomous agent"""
        if not self.controller.current_project:
            logging.info("No project loaded.")
            return

        if event_type == "file_created":
            self.controller.ui_manager.log_output(f"File created: {data.get('filename', 'unknown')}")
            self.controller.ui_manager.file_manager.populate_tree_view()
        elif event_type == "file_updated":
            self.controller.ui_manager.log_output(f"File updated: {data.get('filename', 'unknown')}")
            # Refresh the file in editor if it's currently open
            if hasattr(self.controller.ui_manager.file_manager, "refresh_current_file"):
                self.controller.ui_manager.file_manager.refresh_current_file()

    def continue_autonomous_workflow(self, metadata: Dict[str, Any]):
        """Continue the workflow based on AI feedback and project state"""
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
        """Stop the current generation process"""
        if self.current_thread and self.current_thread.is_alive():
            self.generation_stop_event.set()
            self.controller.ui_manager.log_output("Stopping AI generation process...")
            return True
        return False
import os
from pathlib import Path

from lib.git_cli.utils.event_bus import EventBus
from lib.git_cli.commands.dispatcher import CommandDispatcher
from lib.git_cli.services.git_service import GitService
from lib.git_cli.ui.ui_controller import UIController
from lib.git_cli.infra.git_command_runner import GitCommandRunner
from lib.git_cli.infra.git_status_formatter import GitStatusFormatter
from lib.git_cli.components.ansi_renderer import AnsiRenderer


class Application:
    """
    Main application class that initializes and coordinates all components.
    Follows the Dependency Injection pattern to provide components with their dependencies.
    """

    def __init__(self, repo_dir=None):
        # Core properties
        self.repo_dir = Path(repo_dir or os.getcwd())

        # Initialize the event bus for communication between components
        self.event_bus = EventBus()

        # Initialize core services
        self.dispatcher = CommandDispatcher(repo_dir=str(self.repo_dir))

        # These will be initialized later when UI is available
        self.ansi_renderer = None
        self.command_runner = None
        self.status_formatter = None
        self.git_service = None
        self.ui_controller = None

    def initialize_with_ui(self, main_window, output_text):
        print(f"Initializing Application UI with output_text: {output_text}")

        # Step 1: Setup ANSI renderer
        self.ansi_renderer = AnsiRenderer(output_text)
        self.ansi_renderer.define_ansi_tags(output_text)

        # Step 2: Setup services
        self.command_runner = GitCommandRunner(self.dispatcher, self.ansi_renderer, self.repo_dir)
        self.status_formatter = GitStatusFormatter(self.ansi_renderer, self.repo_dir)
        self.git_service = GitService(
            repo_dir=self.repo_dir,
            command_runner=self.command_runner,
            status_formatter=self.status_formatter,
            event_bus=self.event_bus
        )

        # Step 3: Create UIController (AHORA ya puedes pasarle todo)
        self.ui_controller = UIController(
            git_service=self.git_service,
            main_window=main_window,
            output_text=output_text,
            event_bus=self.event_bus
        )

        self.ui_controller.ansi_renderer = self.ansi_renderer

    def _setup_event_listeners(self):
        """Set up event listeners for application-wide events"""
        self.event_bus.subscribe("git.status.changed", self.git_service.refresh_status)
        self.event_bus.subscribe("ui.refresh.staging", self.git_service.refresh_staging_view)
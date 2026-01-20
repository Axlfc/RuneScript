# lib/git_cli/infra/git_command_runner.py
from lib.git_cli.executor import GitExecutor


class GitCommandRunner:
    def __init__(self, dispatcher, ansi_renderer, repo_dir):
        self.dispatcher = dispatcher
        self.ansi_renderer = ansi_renderer
        self.repo_dir = repo_dir
        self.git_executor = GitExecutor()

    def run(self, command_line: str, widget):
        from lib.git_cli.fallback_executor import execute_raw_git_command

        try:
            result = self.dispatcher.dispatch_line(command_line)
            if not result["success"]:
                # fall back for raw output (like ANSI diff)
                raw_result = execute_raw_git_command(command_line, repo_dir=self.repo_dir)
                text = raw_result["stdout"] or raw_result["stderr"]
                self.ansi_renderer.insert_ansi_text(widget, f"{command_line}\n{text}\n", tag="error" if not raw_result["success"] else None)
            else:
                self.ansi_renderer.insert_ansi_text(widget, f"{result['stdout']}\n")
        except Exception as e:
            self.ansi_renderer.insert_ansi_text(widget, f"Fatal error: {e}\n", tag="error")

        widget.see("end")


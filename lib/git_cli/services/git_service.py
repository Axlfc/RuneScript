import threading
from pathlib import Path

from lib.git_cli.core.repository import Repository


class GitService:
    """
    Service class that handles all Git operations and abstracts Git functionality
    from the UI. It provides a clean interface for UI components to interact with Git.
    """

    def __init__(self, repo_dir, command_runner, status_formatter, event_bus):
        self.repo_dir = Path(repo_dir)
        self.repo = Repository(repo_dir)
        self.command_runner = command_runner
        self.status_formatter = status_formatter
        self.event_bus = event_bus
        self.command_history = []
        self.history_pointer = [0]

    def execute_command(self, command, output_text):
        """Execute a Git command and update the output text widget"""
        if not command.strip():
            return

        # Add command to history
        self.command_history.append(command)
        self.history_pointer[0] = len(self.command_history)

        # Special handling for status command
        if command == "status --porcelain -u":
            self.status_formatter.format_status(output_text)
        else:
            # Run the command in a separate thread
            threading.Thread(
                target=self.command_runner.run,
                args=(command, output_text),
                daemon=True
            ).start()

        # Notify that a command was executed
        self.event_bus.publish("git.command.executed", {"command": command})

    def run_git(self, *args):
        """Run a git command directly and return the output"""
        return self.command_runner.git_executor.run_git(*args, repo_dir=self.repo_dir)

    def refresh_status(self):
        """Refresh the repository status information"""
        repo = Repository(self.repo_dir)
        branch = repo.get_current_branch()

        status_info = {}
        if branch:
            status_info["branch"] = branch
            status_info["message"] = f"Current branch: {branch}"
        else:
            # Get the current commit hash if detached
            short_hash, _, _ = self.run_git("rev-parse", "--short", "HEAD")
            if short_hash.strip():
                status_info["commit"] = short_hash.strip()
                status_info["message"] = f"Current commit: {short_hash.strip()}"
            else:
                status_info["message"] = "Error: Invalid identifier"

        # Publish the status information
        self.event_bus.publish("git.status.updated", status_info)

    def refresh_staging_view(self):
        """Get the current staged and unstaged files and publish the information"""
        output, _, _ = self.run_git("status", "--porcelain")
        unstaged = []
        staged = []

        for line in output.splitlines():
            if not line:
                continue

            status_code = line[:2]
            file_path = line[3:]

            staged_code = status_code[0]
            unstaged_code = status_code[1]

            if staged_code != ' ' and unstaged_code == ' ':
                # Staged only
                staged.append(file_path)
            elif staged_code == ' ' and unstaged_code != ' ':
                # Unstaged only
                unstaged.append(file_path)
            else:
                # Both staged and unstaged — treat as unstaged for simplicity
                unstaged.append(file_path)

        # Publish the staging information
        self.event_bus.publish("git.staging.updated", {
            "staged_files": staged,
            "unstaged_files": unstaged
        })

    def stage_files(self, file_paths):
        """Stage the specified files"""
        if not file_paths:
            return

        file_paths_str = " ".join(f'"{f}"' for f in file_paths)
        _, success, _ = self.run_git("add", *file_paths)

        if success:
            self.event_bus.publish("git.status.changed")

    def unstage_files(self, file_paths):
        """Unstage the specified files"""
        if not file_paths:
            return

        file_paths_str = " ".join(f'"{f}"' for f in file_paths)
        _, success, _ = self.run_git("reset", "--", *file_paths)

        if success:
            self.event_bus.publish("git.status.changed")

    def stage_all_files(self):
        """Stage all changed files"""
        _, success, _ = self.run_git("add", ".")

        if success:
            self.event_bus.publish("git.status.changed")

    def unstage_all_files(self):
        """Unstage all files"""
        _, success, _ = self.run_git("reset")

        if success:
            self.event_bus.publish("git.status.changed")

    def discard_changes(self, file_paths):
        """Discard changes in the specified files"""
        if not file_paths:
            return

        file_paths_str = " ".join(f'"{f}"' for f in file_paths)
        _, success, _ = self.run_git("checkout", "--", *file_paths)

        if success:
            self.event_bus.publish("git.status.changed")

    def commit(self, message, amend=False):
        """Commit staged changes"""
        if not message:
            return False

        args = ["commit", "-m", message]
        if amend:
            args.append("--amend")

        _, success, _ = self.run_git(*args)

        if success:
            self.event_bus.publish("git.status.changed")
            self.event_bus.publish("git.commit.created")
            return True
        return False

    def push(self):
        """Push commits to remote"""
        _, success, _ = self.run_git("push")

        if success:
            self.event_bus.publish("git.push.completed")

    def get_branches(self):
        """Get list of branches"""
        output, _, _ = self.run_git("branch", "--all")
        branches = []

        for line in output.splitlines():
            if line.strip():
                # Remove the '*' prefix for current branch
                branch = line.strip()
                if branch.startswith("*"):
                    branch = branch[1:].strip()
                branches.append(branch)

        return branches

    def create_branch(self, name):
        """Create a new branch"""
        if not name:
            return False

        _, success, _ = self.run_git("branch", name)

        if success:
            self.event_bus.publish("git.branch.created", {"name": name})
            return True
        return False

    def checkout_branch(self, name):
        """Checkout a branch"""
        if not name:
            return False

        _, success, _ = self.run_git("checkout", name)

        if success:
            self.event_bus.publish("git.status.changed")
            self.event_bus.publish("git.branch.changed", {"name": name})
            return True
        return False

    def get_commit_details(self, commit_hash):
        """Get details about a specific commit"""
        output, success, _ = self.run_git("show", "--name-status", commit_hash)

        if success:
            # Parse the commit details
            lines = output.splitlines()
            commit_info = {
                "hash": commit_hash,
                "author": next((l for l in lines if l.startswith("Author:")), ""),
                "date": next((l for l in lines if l.startswith("Date:")), ""),
                "message": [],
                "files": []
            }

            # Extract the commit message
            message_started = False
            for line in lines:
                if message_started:
                    if line.startswith("diff --git"):
                        break
                    commit_info["message"].append(line.strip())
                elif line.strip() == "":
                    message_started = True

            # Extract changed files
            for line in lines:
                if line.startswith(("A\t", "M\t", "D\t")):
                    status, filename = line.split("\t", 1)
                    commit_info["files"].append({"status": status, "filename": filename})

            return commit_info
        return None

    def get_file_diff(self, file_path, mode="working"):
        """Get the diff for a specific file"""
        if mode.lower() == "working":
            output, success, _ = self.run_git("diff", "--", file_path)
        elif mode.lower() == "staged":
            output, success, _ = self.run_git("diff", "--staged", "--", file_path)
        else:
            output, success, _ = self.run_git("diff", "HEAD", "--", file_path)

        if success:
            return output
        return ""
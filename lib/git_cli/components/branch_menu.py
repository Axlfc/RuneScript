import subprocess
from tkinter import Menu, simpledialog, END


class BranchMenuManager:
    """
    Component that manages the Branch dropdown menu.
    """
    print("CLASS TRIGGERED")
    def __init__(self, menubar, git_window):
        self.menubar = menubar
        self.git_window = git_window
        self.setup_branch_menu()
        self.populate_branch_menu()

    def setup_branch_menu(self):
        """Setup the Branch dropdown menu."""
        self.branch_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Branch", menu=self.branch_menu)

        # Add "Create new branch" option at the top
        self.branch_menu.add_command(
            label="ðŸŒ± Create new branch",
            command=self.create_new_branch
        )
        self.branch_menu.add_separator()

    def populate_branch_menu(self):
        self.branch_menu.delete(0, END)
        try:
            branches_output = subprocess.check_output(
                ["git", "branch", "--all"], text=True
            )
            branches = list(
                filter(None, [branch.strip() for branch in branches_output.split("\n")])
            )
            active_branch = next(
                (branch[2:] for branch in branches if branch.startswith("*")), None
            )
            for branch in branches:
                is_active = branch.startswith("*")
                branch_name = branch[2:] if is_active else branch
                display_name = f"âœ“ {branch_name}" if is_active else branch_name
                self.branch_menu.add_command(
                    label=display_name,
                    command=lambda b=branch_name: self.checkout_branch(b)
                )
        except subprocess.CalledProcessError as e:
            self.git_window.ansi_renderer.insert_ansi_text(
                self.git_window.output_text, f"Error fetching branches: {e.output}\n", "error"
            )

    def checkout_branch(self, branch):
        self.git_window.execute_command(f"checkout {branch}")
        self.populate_branch_menu()
        self.git_window.update_commit_list(self.git_window.commit_list)
        self.git_window.update_status()

    def checkout_remote_branch(self, remote_name):
        """Checkout a remote branch (tracking)."""
        try:
            local_name = remote_name.split("/")[-1]
            self.git_window.execute_command(f"checkout -b {local_name} {remote_name}")
        except Exception as e:
            self.git_window.ansi_renderer.insert_ansi_text(f"Remote checkout error: {e}\n", "error")
        self.git_window.update_status()
        self.git_window.commit_list_view.update_commit_list()
        self.populate_branch_menu()

    def create_new_branch(self):
        """Prompt user to create a new branch from current HEAD."""
        branch_name = simpledialog.askstring("Create Branch", "Enter new branch name:")
        if branch_name:
            self.git_window.execute_command(f"branch {branch_name}")
            self.populate_branch_menu()

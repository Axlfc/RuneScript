class GitOps:
    def __init__(self, repo_dir, git_executor):
        self.repo_dir = repo_dir
        self.git_executor = git_executor

    def run_command(self, command, *args):
        full_command = f"{command} {' '.join(args)}"
        stdout, stderr, return_code = self.git_executor.run_git(full_command, repo_dir=self.repo_dir)
        if return_code != 0:
            raise Exception(f"Git command failed: {stderr}")
        return stdout.strip()

    def get_branches(self):
        return self.run_command("branch").splitlines()

    def checkout_branch(self, branch_name):
        return self.run_command("checkout", branch_name)

    def create_new_branch(self, branch_name):
        return self.run_command("checkout", "-b", branch_name)

    def get_commit_history(self, branch_name=None, max_count=50):
        branch = branch_name or "HEAD"
        return self.run_command("log", "--pretty=format:%H|%an|%ar|%s", "--max-count", str(max_count), branch)

    def stage_file(self, filename):
        return self.run_command("add", "-f", filename)

    def unstage_file(self, filename):
        return self.run_command("reset", "HEAD", filename)

    def commit_changes(self, message):
        return self.run_command("commit", "-m", message)

    def push_changes(self):
        return self.run_command("push")

    def pull_changes(self):
        return self.run_command("pull")

    def fetch_changes(self):
        return self.run_command("fetch")

    def get_status(self):
        return self.run_command("status", "--porcelain", "-u")
class GitConfig:
    """Handles Git configuration"""

    def __init__(self, repo_dir):
        self.repo_dir = repo_dir

    def get_config(self, key):
        """Get a Git config value"""
        import subprocess
        try:
            return subprocess.check_output(
                ["git", "-C", str(self.repo_dir), "config", "--get", key],
                text=True
            ).strip()
        except subprocess.CalledProcessError:
            return None

    def set_config(self, key, value):
        """Set a Git config value"""
        import subprocess
        try:
            subprocess.check_call(
                ["git", "-C", str(self.repo_dir), "config", key, value]
            )
            return True
        except subprocess.CalledProcessError:
            return False
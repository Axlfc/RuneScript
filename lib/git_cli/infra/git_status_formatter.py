class GitStatusFormatter:
    def __init__(self, ansi_renderer, repo_dir):
        self.ansi_renderer = ansi_renderer
        self.repo_dir = repo_dir

    def format_status(self, widget):
        from lib.git_cli.executor import GitExecutor
        import re

        stdout, _, _ = GitExecutor.run_git("status", "--porcelain", "-u", repo_dir=self.repo_dir)

        if not stdout.strip():
            widget.insert("end", "Your branch is up to date.\n\n")
            return

        for line in stdout.strip().splitlines():
            status, filename = line[:2], line[3:]
            widget.insert("end", status, self._status_tag(status))
            widget.insert("end", f" <{filename}>\n")

            if status.strip() in ("M",):
                diff_out, _, _ = GitExecutor.run_git("diff", "--color", filename, repo_dir=self.repo_dir)
                ansi_escape = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
                for diff_line in diff_out.splitlines()[1:]:
                    line_clean = ansi_escape.sub("", diff_line)
                    self.ansi_renderer.apply_ansi_styles(widget, line_clean)
                widget.insert("end", f" </{filename}>\n\n")

    def _status_tag(self, status):
        return {
            " M": "modified",
            "M ": "modified",
            "MM": "modified_multiple",
            "??": "untracked",
            "A ": "added",
            " D": "deleted",
            "D ": "deleted",
            "R ": "renamed",
            "C ": "copied",
            "U ": "unmerged",
            "!!": "ignored"
        }.get(status, "default")

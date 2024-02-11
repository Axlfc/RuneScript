import argparse
import subprocess
import os
import sys

git_icon = "🐙"

git_icons = {
    "commit": "📝",
    "push": "🚀",
    "pull": "🔄",
    "merge": "🔀",
    "clone": "🔄➕",
    "fetch": "🔍➕",
    "add": "➕",
    "checkout": "🛒",
    "branch": "🌳",
    "hard": "💥",
    "pristine": "🧼",
    "status": "🛠️",
    "log": "📜"
}


def run_git_command(command, *args, repo_dir=None):
    """
    Executes a git command and handles errors.

    Args:
    command (str): The git command to run.
    *args: Arguments for the git command.
    repo_dir (str, optional): Directory of the git repository.

    Returns:
    str: Standard output from the git command.
    """
    try:
        result = subprocess.run(["git"] + [command] + list(args),
                                check=True,
                                capture_output=True,
                                text=True,
                                cwd=repo_dir)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing Git {command}: {e.stderr}", file=sys.stderr)
        sys.exit(1)


# Function to emulate git commit alias
def git_commit(message, repo_dir=None):
    run_git_command("add", "-A", repo_dir=repo_dir)
    run_git_command("commit", "-am", message, repo_dir=repo_dir)
    print(git_icons["commit"], "Commit successful")


def git_push(repo_dir=None):
    run_git_command("push", repo_dir=repo_dir)
    print(git_icons["push"], "Push successful")


def git_pull(repo_dir=None):
    run_git_command("pull", repo_dir=repo_dir)
    print(git_icons["pull"], "Pull successful")


def git_merge(branch, repo_dir=None):
    run_git_command("merge", branch, repo_dir=repo_dir)
    print(git_icons["merge"], f"Merge of {branch} successful")


def git_clone(url, repo_dir=None):
    run_git_command("clone", url, repo_dir=repo_dir)
    print(git_icons["clone"], f"Clone of {url} successful")


def git_fetch(repo_dir=None):
    run_git_command("fetch", repo_dir=repo_dir)
    print(git_icons["fetch"], "Fetch successful")


def git_add(repo_dir=None):
    run_git_command("add", ".", repo_dir=repo_dir)
    print(git_icons["add"], "Add successful")


def git_checkout(branch, repo_dir=None):
    run_git_command("checkout", branch, repo_dir=repo_dir)
    print(git_icons["checkout"], f"Checkout to {branch} successful")


def git_branch(repo_dir=None):
    branches = run_git_command("branch", repo_dir=repo_dir)
    print(git_icons["branch"], "Branches:\n", branches)


def git_hard(repo_dir=None):
    run_git_command("reset", "--hard", repo_dir=repo_dir)
    print(git_icons["hard"], "Hard reset successful")


def git_pristine(delete_ignored_files=False, repo_dir=None):
    run_git_command("reset", "--hard", repo_dir=repo_dir)
    if delete_ignored_files:
        run_git_command("clean", "-fdx", repo_dir=repo_dir)
    else:
        run_git_command("clean", "-fd", repo_dir=repo_dir)
    print(git_icons["pristine"], "Pristine reset successful")


def git_status(repo_dir=None):
    status = run_git_command("status", repo_dir=repo_dir)
    print(git_icons["status"], "Status:\n", status)


def git_log(repo_dir=None):
    log = run_git_command("log", repo_dir=repo_dir)
    print(git_icons["log"], "Log:\n", log)


def is_git_repository(directory_path):
    try:
        subprocess.check_call(['git', '-C', directory_path, 'status'], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    parser = argparse.ArgumentParser(description="Emulate Git aliases in Python")
    subparsers = parser.add_subparsers(dest="command", help="Git commands")

    # Setup argument parsers for different git commands
    commit_parser = subparsers.add_parser("commit", help="Emulate git commit alias")
    commit_parser.add_argument("message", help="Commit message")
    commit_parser.add_argument("--repo-dir", help="Directory of the git repository", default=os.getcwd())

    push_parser = subparsers.add_parser("push", help="Emulate git push alias")
    push_parser.add_argument("--repo-dir", help="Directory of the git repository", default=os.getcwd())

    pull_parser = subparsers.add_parser("pull", help="Emulate git pull alias")
    pull_parser.add_argument("--repo-dir", help="Directory of the git repository", default=os.getcwd())

    merge_parser = subparsers.add_parser("merge", help="Emulate git merge alias")
    merge_parser.add_argument("branch", help="Branch to merge")
    merge_parser.add_argument("--repo-dir", help="Directory of the git repository", default=os.getcwd())

    clone_parser = subparsers.add_parser("clone", help="Emulate git clone alias")
    clone_parser.add_argument("url", help="Repository URL")
    clone_parser.add_argument("--repo-dir", help="Directory of the git repository", default=os.getcwd())

    fetch_parser = subparsers.add_parser("fetch", help="Emulate git fetch alias")
    fetch_parser.add_argument("--repo-dir", help="Directory of the git repository", default=os.getcwd())

    add_parser = subparsers.add_parser("add", help="Emulate git add alias")
    add_parser.add_argument("--repo-dir", help="Directory of the git repository", default=os.getcwd())

    checkout_parser = subparsers.add_parser("checkout", help="Emulate git checkout alias")
    checkout_parser.add_argument("branch", help="Branch to checkout")
    checkout_parser.add_argument("--repo-dir", help="Directory of the git repository", default=os.getcwd())

    branch_parser = subparsers.add_parser("branch", help="Emulate git branch alias")
    branch_parser.add_argument("--repo-dir", help="Directory of the git repository", default=os.getcwd())

    hard_parser = subparsers.add_parser("hard", help="Emulate git hard reset alias")
    hard_parser.add_argument("--repo-dir", help="Directory of the git repository", default=os.getcwd())

    pristine_parser = subparsers.add_parser("pristine", help="Emulate git pristine alias")
    pristine_parser.add_argument("--delete-ignored", action="store_true", help="Delete ignored files")
    pristine_parser.add_argument("--repo-dir", help="Directory of the git repository", default=os.getcwd())

    status_parser = subparsers.add_parser("status", help="Emulate git status alias")
    status_parser.add_argument("--repo-dir", help="Directory of the git repository", default=os.getcwd())

    log_parser = subparsers.add_parser("log", help="Emulate git log alias")
    log_parser.add_argument("--repo-dir", help="Directory of the git repository", default=os.getcwd())

    args = parser.parse_args()

    if args.command == "commit":
        git_commit(args.message, repo_dir=args.repo_dir)
    elif args.command == "push":
        git_push(repo_dir=args.repo_dir)
    elif args.command == "pull":
        git_pull(repo_dir=args.repo_dir)
    elif args.command == "merge":
        git_merge(args.branch, repo_dir=args.repo_dir)
    elif args.command == "clone":
        git_clone(args.url, repo_dir=args.repo_dir)
    elif args.command == "fetch":
        git_fetch(repo_dir=args.repo_dir)
    elif args.command == "add":
        git_add(repo_dir=args.repo_dir)
    elif args.command == "checkout":
        git_checkout(args.branch, repo_dir=args.repo_dir)
    elif args.command == "branch":
        git_branch(repo_dir=args.repo_dir)
    elif args.command == "hard":
        git_hard(repo_dir=args.repo_dir)
    elif args.command == "pristine":
        git_pristine(args.delete_ignored, repo_dir=args.repo_dir)
    elif args.command == "status":
        git_status(repo_dir=args.repo_dir)
    elif args.command == "log":
        git_log(repo_dir=args.repo_dir)


# Command-line interface
if __name__ == "__main__":
    main()

import argparse
import subprocess
import os
import re
import sys
import logging
import configparser

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)
config = configparser.ConfigParser()
config.read("git_config.ini")
default_repo_dir = config.get("git", "default_repo_dir", fallback=os.getcwd())
default_username = config.get("git", "default_username", fallback=None)
default_email = config.get("git", "default_email", fallback=None)
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
    "log": "📜",
    "diff": "🔍",
    "blame": "🧟\u200d♂️",
    "rebase": "🔃",
    "stash": "📦",
    "unstash": "📤",
    "remote": "🌐",
    "config": "⚙️",
    "tag": "🏷️",
    "init": "🚀",
}


def run_git_command(command, *args, repo_dir=None, encoding="utf-8"):
    """
    Executes a git command and handles errors.

    Args:
    command (str): The git command to run.
    *args: Arguments for the git command.
    repo_dir (str, optional): Directory of the git repository.
    encoding (str, optional): Encoding to use for interpreting the command output.

    Returns:
    str: Standard output from the git command.
    """
    try:
        result = subprocess.run(
            ["git"] + [command] + list(args),
            check=True,
            capture_output=True,
            text=True,
            cwd=repo_dir,
            encoding=encoding,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing Git {command}: {e.stderr}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)


def is_git_repository(directory_path):
    """
    is_git_repository

    Args:
        directory_path (Any): Description of directory_path.

    Returns:
        None: Description of return value.
    """
    try:
        subprocess.check_call(["git", "-C", directory_path, "status"], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def is_valid_branch_name(branch):
    """
    is_valid_branch_name

    Args:
        branch (Any): Description of branch.

    Returns:
        None: Description of return value.
    """
    return re.match("^[\\w.-]+$", branch) is not None


def is_valid_file_path(file_path):
    """
    is_valid_file_path

    Args:
        file_path (Any): Description of file_path.

    Returns:
        None: Description of return value.
    """
    return os.path.isfile(file_path)


def is_valid_repo_url(url):
    """
    is_valid_repo_url

    Args:
        url (Any): Description of url.

    Returns:
        None: Description of return value.
    """
    return True


def git_tag(tag_name, repo_dir=None):
    """
    Adds a Git tag to the current repository.

    Args:
        tag_name (str): The name of the tag to create.
        repo_dir (str, optional): The directory of the Git repository.
    """
    try:
        run_git_command("tag", tag_name, repo_dir=repo_dir)
        logger.info(f"{git_icons['tag']} Tag '{tag_name}' created successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error creating Git tag '{tag_name}': {e.stderr}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)


def git_commit(message, repo_dir=None):
    """
    git_commit

    Args:
        message (Any): Description of message.
        repo_dir (Any): Description of repo_dir.

    Returns:
        None: Description of return value.
    """
    status_output = run_git_command("status", repo_dir=repo_dir)
    if "Changes not staged for commit" in status_output:
        logger.error(
            "There are unstaged changes. Please stage your changes before committing."
        )
        sys.exit(1)
    if not message.strip():
        logger.error("No commit message provided.")
        sys.exit(1)
    run_git_command("add", "-A", repo_dir=repo_dir)
    try:
        run_git_command("commit", "-am", message, repo_dir=repo_dir)
        logger.info(f"{git_icons['commit']} Commit successful")
    except subprocess.CalledProcessError as e:
        if "nothing to commit" in e.stderr:
            logger.error("No changes to commit.")
        else:
            logger.error(f"Error executing Git commit: {e.stderr}")
        sys.exit(1)


def git_push(repo_dir=None):
    """
    git_push

    Args:
        repo_dir (Any): Description of repo_dir.

    Returns:
        None: Description of return value.
    """
    run_git_command("push", repo_dir=repo_dir)
    logger.info(f"{git_icons['push']} Push successful")


def git_pull(repo_dir=None):
    """
    git_pull

    Args:
        repo_dir (Any): Description of repo_dir.

    Returns:
        None: Description of return value.
    """
    run_git_command("pull", repo_dir=repo_dir)
    logger.info(f"{git_icons['pull']} Pull successful")


def git_merge(branch, repo_dir=None):
    """
    git_merge

    Args:
        branch (Any): Description of branch.
        repo_dir (Any): Description of repo_dir.

    Returns:
        None: Description of return value.
    """
    if not is_valid_branch_name(branch):
        logger.error("Invalid branch name provided.")
        sys.exit(1)
    run_git_command("merge", branch, repo_dir=repo_dir)
    logger.info(f"{git_icons['merge']} Merge of {branch} successful")


def git_clone(url, repo_dir=None):
    """
    git_clone

    Args:
        url (Any): Description of url.
        repo_dir (Any): Description of repo_dir.

    Returns:
        None: Description of return value.
    """
    if not is_valid_repo_url(url):
        logger.error("Invalid repository URL provided.")
        sys.exit(1)
    run_git_command("clone", url, repo_dir=repo_dir)
    logger.info(f"{git_icons['clone']} Clone of {url} successful")


def git_fetch(repo_dir=None):
    """
    git_fetch

    Args:
        repo_dir (Any): Description of repo_dir.

    Returns:
        None: Description of return value.
    """
    run_git_command("fetch", repo_dir=repo_dir)
    logger.info(f"{git_icons['fetch']} Fetch successful")


def git_add(repo_dir=None):
    """
    git_add

    Args:
        repo_dir (Any): Description of repo_dir.

    Returns:
        None: Description of return value.
    """
    run_git_command("add", ".", repo_dir=repo_dir)
    logger.info(f"{git_icons['add']} Add successful")


def git_checkout(branch, repo_dir=None):
    """
    git_checkout

    Args:
        branch (Any): Description of branch.
        repo_dir (Any): Description of repo_dir.

    Returns:
        None: Description of return value.
    """
    run_git_command("checkout", branch, repo_dir=repo_dir)
    logger.info(f"{git_icons['checkout']} Checkout to {branch} successful")


def git_branch(repo_dir=None):
    """
    git_branch

    Args:
        repo_dir (Any): Description of repo_dir.

    Returns:
        None: Description of return value.
    """
    branches = run_git_command("branch", repo_dir=repo_dir)
    logger.info(f"{git_icons['branch']} Branches:\n{branches}")


def git_hard(repo_dir=None):
    """
    git_hard

    Args:
        repo_dir (Any): Description of repo_dir.

    Returns:
        None: Description of return value.
    """
    run_git_command("reset", "--hard", repo_dir=repo_dir)
    logger.info(f"{git_icons['hard']} Hard reset successful")


def git_pristine(delete_ignored_files=False, repo_dir=None):
    """
    git_pristine

    Args:
        delete_ignored_files (Any): Description of delete_ignored_files.
        repo_dir (Any): Description of repo_dir.

    Returns:
        None: Description of return value.
    """
    run_git_command("reset", "--hard", repo_dir=repo_dir)
    if delete_ignored_files:
        run_git_command("clean", "-fdx", repo_dir=repo_dir)
    else:
        run_git_command("clean", "-fd", repo_dir=repo_dir)
    logger.info(f"{git_icons['pristine']} Pristine reset successful")


def git_status(repo_dir=None):
    """
    git_status

    Args:
        repo_dir (Any): Description of repo_dir.

    Returns:
        None: Description of return value.
    """
    status = run_git_command("status", repo_dir=repo_dir)
    diff = run_git_command("diff", "--color", repo_dir=repo_dir)
    logger.info(f"{git_icons['status']} Status:\n{status}")


def git_log(repo_dir=None):
    """
    git_log

    Args:
        repo_dir (Any): Description of repo_dir.

    Returns:
        None: Description of return value.
    """
    log_format = "%Cred%h %Cblue%an%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr)%Creset"
    log = run_git_command(
        "log",
        "--graph",
        "--pretty=format:" + log_format,
        "--abbrev-commit",
        "--date=relative",
        repo_dir=repo_dir,
    )
    logger.info(f"{git_icons['log']} Log:\n{log}")


def git_diff(repo_dir=None):
    """
    git_diff

    Args:
        repo_dir (Any): Description of repo_dir.

    Returns:
        None: Description of return value.
    """
    run_git_command("config", "--local", "color.ui", "auto", repo_dir=repo_dir)
    diff = run_git_command("diff", "--color", repo_dir=repo_dir)
    logger.info(f"{git_icons['diff']} Diff:\n{diff}")


def git_blame(file, repo_dir=None):
    """
    git_blame

    Args:
        file (Any): Description of file.
        repo_dir (Any): Description of repo_dir.

    Returns:
        None: Description of return value.
    """
    blame = run_git_command("blame", file, repo_dir=repo_dir)
    logger.info(f"{git_icons['blame']} Blame:\n{blame}")


def git_rebase(branch, repo_dir=None):
    """
    git_rebase

    Args:
        branch (Any): Description of branch.
        repo_dir (Any): Description of repo_dir.

    Returns:
        None: Description of return value.
    """
    run_git_command("rebase", branch, repo_dir=repo_dir)
    logger.info(f"{git_icons['rebase']} Rebase onto {branch} successful")


def git_stash(repo_dir=None):
    """
    git_stash

    Args:
        repo_dir (Any): Description of repo_dir.

    Returns:
        None: Description of return value.
    """
    run_git_command("stash", repo_dir=repo_dir)
    logger.info(f"{git_icons['stash']} Stash successful")


def git_unstash(repo_dir=None):
    """
    git_unstash

    Args:
        repo_dir (Any): Description of repo_dir.

    Returns:
        None: Description of return value.
    """
    run_git_command("stash", "pop", repo_dir=repo_dir)
    logger.info(f"{git_icons['unstash']} Unstash successful")


def git_remote(repo_dir=None):
    """
    git_remote

    Args:
        repo_dir (Any): Description of repo_dir.

    Returns:
        None: Description of return value.
    """
    remotes = run_git_command("remote", "-v", repo_dir=repo_dir)
    logger.info(f"{git_icons['remote']} Remotes:\n{remotes}")


def git_config(username=None, email=None, repo_dir=None):
    """
    git_config

    Args:
        username (Any): Description of username.
        email (Any): Description of email.
        repo_dir (Any): Description of repo_dir.

    Returns:
        None: Description of return value.
    """
    if username:
        run_git_command("config", "user.name", username, repo_dir=repo_dir)
        logger.info(f"{git_icons['config']} Config user.name set to {username}")
    if email:
        run_git_command("config", "user.email", email, repo_dir=repo_dir)
        logger.info(f"{git_icons['config']} Config user.email set to {email}")


def git_init(repo_dir=None):
    """
    git_init

    Args:
        repo_dir (Any): Description of repo_dir.

    Returns:
        None: Description of return value.
    """
    run_git_command("init", repo_dir=repo_dir)
    logger.info(f"{git_icons['init']} Git repository initialized")


def main():
    """
    main

    Args:
        None

    Returns:
        None: Description of return value.
    """
    parser = argparse.ArgumentParser(description="Emulate Git aliases in Python")
    parser.add_argument(
        "--repo-dir", help="Directory of the git repository", default=default_repo_dir
    )
    subparsers = parser.add_subparsers(dest="command", help="Git commands")
    commit_parser = subparsers.add_parser("commit", help="Emulate git commit alias")
    commit_parser.add_argument("message", help="Commit message")
    commit_parser.add_argument(
        "--repo-dir", help="Directory of the git repository", default=default_repo_dir
    )
    push_parser = subparsers.add_parser("push", help="Emulate git push alias")
    push_parser.add_argument(
        "--repo-dir", help="Directory of the git repository", default=default_repo_dir
    )
    pull_parser = subparsers.add_parser("pull", help="Emulate git pull alias")
    pull_parser.add_argument(
        "--repo-dir", help="Directory of the git repository", default=default_repo_dir
    )
    merge_parser = subparsers.add_parser("merge", help="Emulate git merge alias")
    merge_parser.add_argument("branch", help="Branch to merge")
    merge_parser.add_argument(
        "--repo-dir", help="Directory of the git repository", default=default_repo_dir
    )
    clone_parser = subparsers.add_parser("clone", help="Emulate git clone alias")
    clone_parser.add_argument("url", help="Repository URL")
    clone_parser.add_argument(
        "--repo-dir", help="Directory of the git repository", default=default_repo_dir
    )
    fetch_parser = subparsers.add_parser("fetch", help="Emulate git fetch alias")
    fetch_parser.add_argument(
        "--repo-dir", help="Directory of the git repository", default=default_repo_dir
    )
    add_parser = subparsers.add_parser("add", help="Emulate git add alias")
    add_parser.add_argument(
        "--repo-dir", help="Directory of the git repository", default=default_repo_dir
    )
    checkout_parser = subparsers.add_parser(
        "checkout", help="Emulate git checkout alias"
    )
    checkout_parser.add_argument("branch", help="Branch to checkout")
    checkout_parser.add_argument(
        "--repo-dir", help="Directory of the git repository", default=default_repo_dir
    )
    branch_parser = subparsers.add_parser("branch", help="Emulate git branch alias")
    branch_parser.add_argument(
        "--repo-dir", help="Directory of the git repository", default=default_repo_dir
    )
    hard_parser = subparsers.add_parser("hard", help="Emulate git hard reset alias")
    hard_parser.add_argument(
        "--repo-dir", help="Directory of the git repository", default=default_repo_dir
    )
    pristine_parser = subparsers.add_parser(
        "pristine", help="Emulate git pristine alias"
    )
    pristine_parser.add_argument(
        "--delete-ignored", action="store_true", help="Delete ignored files"
    )
    pristine_parser.add_argument(
        "--repo-dir", help="Directory of the git repository", default=default_repo_dir
    )
    status_parser = subparsers.add_parser("status", help="Emulate git status alias")
    status_parser.add_argument(
        "--repo-dir", help="Directory of the git repository", default=default_repo_dir
    )
    log_parser = subparsers.add_parser("log", help="Emulate git log alias")
    log_parser.add_argument(
        "--repo-dir", help="Directory of the git repository", default=default_repo_dir
    )
    diff_parser = subparsers.add_parser("diff", help="Emulate git diff alias")
    diff_parser.add_argument(
        "--repo-dir", help="Directory of the git repository", default=default_repo_dir
    )
    blame_parser = subparsers.add_parser("blame", help="Emulate git blame alias")
    blame_parser.add_argument("file", help="File to blame")
    blame_parser.add_argument(
        "--repo-dir", help="Directory of the git repository", default=default_repo_dir
    )
    rebase_parser = subparsers.add_parser("rebase", help="Emulate git rebase alias")
    rebase_parser.add_argument("branch", help="Branch to rebase onto")
    rebase_parser.add_argument(
        "--repo-dir", help="Directory of the git repository", default=default_repo_dir
    )
    stash_parser = subparsers.add_parser("stash", help="Emulate git stash alias")
    stash_parser.add_argument(
        "--repo-dir", help="Directory of the git repository", default=default_repo_dir
    )
    unstash_parser = subparsers.add_parser("unstash", help="Emulate git unstash alias")
    unstash_parser.add_argument(
        "--repo-dir", help="Directory of the git repository", default=default_repo_dir
    )
    remote_parser = subparsers.add_parser("remote", help="Emulate git remote alias")
    remote_parser.add_argument(
        "--repo-dir", help="Directory of the git repository", default=default_repo_dir
    )
    config_parser = subparsers.add_parser("config", help="Set git configuration")
    config_parser.add_argument("--username", help="Git username")
    config_parser.add_argument("--email", help="Git email")
    config_parser.add_argument(
        "--repo-dir", help="Directory of the git repository", default=default_repo_dir
    )
    init_parser = subparsers.add_parser("init", help="Emulate git init alias")
    init_parser.add_argument(
        "--repo-dir",
        help="Directory to initialize as a git repository",
        default=default_repo_dir,
    )
    tag_parser = subparsers.add_parser("tag", help="Emulate git tag alias")
    tag_parser.add_argument("tag_name", help="Name of the tag to create")
    tag_parser.add_argument(
        "--repo-dir", help="Directory of the git repository", default=default_repo_dir
    )
    args = parser.parse_args()
    if args.command is not None:
        if not args.repo_dir:
            args.repo_dir = default_repo_dir
        if args.command not in ["clone", "init"] and (
            not is_git_repository(args.repo_dir)
        ):
            logger.error(
                f"{args.repo_dir} is not a Git repository. Please check the directory path and try again."
            )
            sys.exit(1)
        if args.command is None:
            parser.print_help()
            sys.exit(1)
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
        elif args.command == "diff":
            git_diff(repo_dir=args.repo_dir)
        elif args.command == "blame":
            git_blame(args.file, repo_dir=args.repo_dir)
        elif args.command == "rebase":
            git_rebase(args.branch, repo_dir=args.repo_dir)
        elif args.command == "stash":
            git_stash(repo_dir=args.repo_dir)
        elif args.command == "unstash":
            git_unstash(repo_dir=args.repo_dir)
        elif args.command == "remote":
            git_remote(repo_dir=args.repo_dir)
        elif args.command == "config":
            git_config(username=args.username, email=args.email, repo_dir=args.repo_dir)
        elif args.command == "init":
            git_init(repo_dir=args.repo_dir)
        elif args.command == "tag":
            git_tag(args.tag_name, repo_dir=args.repo_dir)
    else:
        args.repo_dir = default_repo_dir
        while True:
            user_input = input("> ").strip()
            if user_input == "exit":
                break
            elif user_input == "help":
                print("Available commands:")
                print("commit [message] - Commit changes")
                print("push - Push changes to remote repository")
                print("pull - Pull changes from remote repository")
                print("merge [branch] - Merge a branch into current branch")
                print("clone [url] - Clone a repository")
                print("fetch - Fetch changes from remote repository")
                print("add - Add changes to staging area")
                print("checkout [branch] - Switch to another branch")
                print("branch - List all branches")
                print("hard - Reset to last commit")
                print("pristine - Reset to pristine state")
                print("status - Show status of repository")
                print("log - Show commit history")
                print("diff - Show differences since last commit")
                print("blame [file] - Show who last modified each line of a file")
                print("rebase [branch] - Reapply commits on top of another base tip")
                print("stash - Stash changes")
                print("unstash - Apply stashed changes")
                print("remote - Show remote repositories")
                print(
                    "config --username [username] --email [email] - Set Git configuration"
                )
                print("init - Initialize a new Git repository")
            else:
                tokens = user_input.split()
                command = tokens[0]
                command_handlers = {
                    "commit": lambda: git_commit(
                        " ".join(tokens[1:]), repo_dir=args.repo_dir
                    ),
                    "push": lambda: git_push(repo_dir=args.repo_dir),
                    "pull": lambda: git_pull(repo_dir=args.repo_dir),
                    "merge": lambda: git_merge(tokens[1], repo_dir=args.repo_dir),
                    "clone": lambda: git_clone(tokens[1], repo_dir=args.repo_dir),
                    "fetch": lambda: git_fetch(repo_dir=args.repo_dir),
                    "add": lambda: git_add(repo_dir=args.repo_dir),
                    "checkout": lambda: git_checkout(tokens[1], repo_dir=args.repo_dir),
                    "branch": lambda: git_branch(repo_dir=args.repo_dir),
                    "hard": lambda: git_hard(repo_dir=args.repo_dir),
                    "pristine": lambda: git_pristine(False, repo_dir=args.repo_dir),
                    "status": lambda: git_status(repo_dir=args.repo_dir),
                    "log": lambda: git_log(repo_dir=args.repo_dir),
                    "diff": lambda: git_diff(repo_dir=args.repo_dir),
                    "blame": lambda: git_blame(tokens[1], repo_dir=args.repo_dir),
                    "rebase": lambda: git_rebase(tokens[1], repo_dir=args.repo_dir),
                    "stash": lambda: git_stash(repo_dir=args.repo_dir),
                    "unstash": lambda: git_unstash(repo_dir=args.repo_dir),
                    "remote": lambda: git_remote(repo_dir=args.repo_dir),
                    "config": lambda: (
                        git_config(
                            username=tokens[1], email=tokens[2], repo_dir=args.repo_dir
                        )
                        if len(tokens) >= 3
                        else print(
                            "Usage: config --username [username] --email [email]"
                        )
                    ),
                    "init": lambda: git_init(repo_dir=args.repo_dir),
                }
                if command in command_handlers:
                    command_handlers[command]()
                else:
                    print(
                        f"Unknown command: {command}. Type 'help' for available commands."
                    )


if __name__ == "__main__":
    main()

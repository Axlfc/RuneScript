import subprocess


git_icon = "🐙"
git_commit_icon = "📝"  # Pen emoji for commit
git_log_icon = "📜"
git_push_icon = "🚀"    # Rocket emoji for push
git_pull_icon = "🔄"    # Loop emoji for pull
git_merge_icon = "🔀"   # Shuffle emoji for merge
git_clone_icon = "🔄➕"  # Loop + plus emoji for clone
git_fetch_icon = "🔍➕"  # Magnifying glass + plus emoji for fetch
git_add_icon = "➕"      # Plus emoji for add
git_checkout_icon = "🛒" # Shopping cart emoji for checkout
git_branch_icon = "🌳"   # Tree emoji for branch
git_hard_icon = "💥"     # Explosion emoji for hard reset
git_pristine_icon = "🧼" # Soap emoji for pristine
git_status = "🛠️"


# Function to emulate git commit alias
def git_commit(message):
    subprocess.run(['git', 'add', '-A'])
    subprocess.run(['git', 'commit', '-am', message])


# Function to emulate git push alias
def git_push():
    subprocess.run(['git', 'fetch'])
    branch = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True).stdout.strip()
    upstream = subprocess.run(['git', 'rev-parse', '--symbolic-full-name', f'{branch}@{{upstream}}'], capture_output=True, text=True)
    if upstream.returncode == 0:
        subprocess.run(['git', 'push'])
    else:
        subprocess.run(['git', 'push', '--set-upstream', 'origin', branch])


# Function to emulate git pull alias
def git_pull():
    branch = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True).stdout.strip()
    subprocess.run(['git', 'pull', 'origin', branch])


# Function to emulate git merge alias
def git_merge():
    branch = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True).stdout.strip()
    subprocess.run(['git', 'merge', 'origin', '--no-ff', branch])


# Function to emulate git clone alias
def git_clone(url):
    if url.startswith('http'):
        subprocess.run(['git', 'clone', url])
    else:
        subprocess.run(['git', 'clone', f'https://{url}'])


# Function to emulate git fetch alias
def git_fetch():
    subprocess.run(['git', 'fetch', '-f', '--prune'])


# Function to emulate git add alias
def git_add():
    subprocess.run(['git', 'add'])


# Function to emulate git checkout alias
def git_checkout(branch):
    subprocess.run(['git', 'checkout', branch])


# Function to emulate git branch alias
def git_branch():
    subprocess.run(['git', 'branch'])


# Function to emulate git hard alias
def git_hard():
    subprocess.run(['git', 'reset', '--hard'])


# Function to emulate git pristine alias
def git_pristine(delete_ignored_files=False):
    branch = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True).stdout.strip()
    subprocess.run(['git', 'fetch', 'origin', branch])
    subprocess.run(['git', 'checkout', '--force', '-B', branch, f'origin/{branch}'])
    subprocess.run(['git', 'reset', '--hard'])
    if delete_ignored_files:
        subprocess.run(['git', 'clean', '-fdx'])
    else:
        subprocess.run(['git', 'clean', '-fd'])
    subprocess.run(['git', 'submodule', 'update', '--init', '--recursive', '--force'])
    subprocess.run(['git', 'submodule', 'foreach', 'git', 'fetch'])
    subprocess.run(['git', 'submodule', 'foreach', 'git', 'checkout', '--force', '-B', branch, f'origin/{branch}'])
    subprocess.run(['git', 'submodule', 'foreach', 'git', 'reset', '--hard'])
    if delete_ignored_files:
        subprocess.run(['git', 'submodule', 'foreach', 'git', 'clean', '-fdx'])
    else:
        subprocess.run(['git', 'submodule', 'foreach', 'git', 'clean', '-fd'])


def git_status():
    subprocess.run(['git', 'status'])


def git_log():
    subprocess.run(['git', 'log'])


# Command-line interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Emulate Git aliases in Python")
    subparsers = parser.add_subparsers(dest="command", help="Git commands")

    commit_parser = subparsers.add_parser("commit", help="Emulate git commit alias")
    commit_parser.add_argument("message", help="Commit message")

    clone_parser = subparsers.add_parser("clone", help="Emulate git clone alias")
    clone_parser.add_argument("url", help="Repository URL")

    checkout_parser = subparsers.add_parser("checkout", help="Emulate git checkout alias")
    checkout_parser.add_argument("branch", help="Branch name")

    pristine_parser = subparsers.add_parser("pristine", help="Emulate git pristine alias")
    pristine_parser.add_argument("--ignored", action="store_true", help="Delete ignored files")

    args = parser.parse_args()

    if args.command == "commit":
        git_commit(args.message)
    elif args.command == "push":
        git_push()
    elif args.command == "pull":
        git_pull()
    elif args.command == "merge":
        git_merge()
    elif args.command == "clone":
        git_clone(args.url)
    elif args.command == "fetch":
        git_fetch()
    elif args.command == "add":
        git_add()
    elif args.command == "checkout":
        git_checkout(args.branch)
    elif args.command == "branch":
        git_branch()
    elif args.command == "hard":
        git_hard()
    elif args.command == "pristine":
        git_pristine(args.ignored)
    elif args.command == "status":
        git_status()
    elif args.command == "log":
        git_log()


'''def is_git_repository(directory_path):
    try:
        # Run the git command to check if the directory is a Git repository
        subprocess.run(['git', '-C', directory_path, 'status'], check=True)
        return True
    except subprocess.CalledProcessError:
        return False
'''
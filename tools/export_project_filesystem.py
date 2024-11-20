import os
import sys
import argparse


def export_project_filesystem(root_path,
                              default_ignored_paths=None,
                              additional_ignored_paths=None,
                              ignored_extensions=None):
    """
    Export project filesystem tree with ability to ignore specific paths and file extensions.

    Args:
        root_path (str): Root directory path of the project
        default_ignored_paths (list, optional): Default list of directories/files to ignore
        additional_ignored_paths (list, optional): Extra paths to ignore beyond defaults
        ignored_extensions (list, optional): List of file extensions to ignore
    """
    # Default ignored paths
    if default_ignored_paths is None:
        default_ignored_paths = [
            '__pycache__',
            '.git',
            '.venv',
            'venv',
            'env',
            '.env',
            '.pytest_cache',
            'node_modules',
            '.idea',
            '.vscode',
        ]

    # Combine default and additional ignored paths
    if additional_ignored_paths:
        default_ignored_paths.extend(additional_ignored_paths)

    # Default ignored extensions
    if ignored_extensions is None:
        ignored_extensions = [
            '.pyc',
            '.log',
            '.lock',
            '.DS_Store',
            '.png',
            '.jpg',
            '.jpeg',
            '.gif',
            '.svg',
            '.ico',
        ]

    def should_ignore(path):
        """Check if path should be ignored."""
        path_parts = path.split(os.path.sep)
        return any(ignored in path_parts for ignored in default_ignored_paths) or \
            any(path.endswith(ext) for ext in ignored_extensions)

    def generate_tree(directory, prefix=''):
        """Recursively generate filesystem tree."""
        if not os.path.exists(directory):
            return ''

        tree = ''
        items = sorted(os.listdir(directory))

        for i, item in enumerate(items):
            full_path = os.path.join(directory, item)

            # Skip ignored paths
            if should_ignore(full_path):
                continue

            # Determine tree connector
            is_last = (i == len(items) - 1)
            connector = '└── ' if is_last else '├── '

            # Add item to tree
            tree += prefix + connector + item + '\n'

            # Recursively process subdirectories
            if os.path.isdir(full_path):
                extension = '    ' if is_last else '│   '
                tree += generate_tree(full_path, prefix + extension)

        return tree

    # Generate and print the tree
    tree_output = os.path.basename(root_path) + '/\n' + generate_tree(root_path)
    return tree_output


def main():
    parser = argparse.ArgumentParser(description="Export a project filesystem tree.")
    parser.add_argument('root_path', type=str, help='Root directory of the project.')
    parser.add_argument('--additional_ignored', type=str, nargs='*',
                        help='Additional paths to ignore.', default=[])
    parser.add_argument('--ignored_extensions', type=str, nargs='*',
                        help='File extensions to ignore.', default=[])

    # Optional output to file
    parser.add_argument('--output', type=str, help='File to save the output.')

    args = parser.parse_args()

    tree = export_project_filesystem(
        root_path=args.root_path,
        additional_ignored_paths=args.additional_ignored,
        ignored_extensions=args.ignored_extensions
    )

    if args.output:
        with open(args.output, 'w') as file:
            file.write(tree)
        print(f"Filesystem tree saved to {args.output}")
    else:
        print(tree)


if __name__ == '__main__':
    main()

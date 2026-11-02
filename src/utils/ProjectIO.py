import os
import subprocess


class ProjectIO:
    """
    Handles project file operations with specific support for TDD workflow
    """

    def __init__(self, log_function=print):
        self.log = log_function

    def create_structure(self, project_path, metadata=None, log_fn=None):
        """Create directories without turning file paths into directories."""
        log_fn = log_fn or self.log

        directories = {"", "src", "tests", "docs"}

        def add_structure_entry(entry):
            if not isinstance(entry, str):
                return

            normalized = entry.strip().replace("\\", "/")
            if not normalized:
                return

            # Explicit trailing slash means a directory. Otherwise, entries
            # with a filename extension contribute only their parent directory.
            if normalized.endswith("/"):
                directories.add(normalized.rstrip("/"))
                return

            basename = os.path.basename(normalized)
            _, extension = os.path.splitext(basename)
            if extension:
                parent = os.path.dirname(normalized)
                if parent:
                    directories.add(parent)
            else:
                directories.add(normalized)

        if metadata and "project_structure" in metadata:
            structure = metadata["project_structure"]
            if isinstance(structure, list):
                for entry in structure:
                    add_structure_entry(entry)
            elif isinstance(structure, dict):
                for entry in structure.keys():
                    add_structure_entry(entry)

        for directory in sorted(directories):
            dir_path = os.path.join(project_path, directory)
            os.makedirs(dir_path, exist_ok=True)
            log_fn(f"Created directory: {dir_path}")

        # Create empty __init__.py files for Python packages
        for directory in ["src", "tests"]:
            init_path = os.path.join(project_path, directory, "__init__.py")
            if not os.path.exists(init_path):
                with open(init_path, "w") as f:
                    pass  # Create empty file
                log_fn(f"Created: {init_path}")

        # Create pytest.ini if it doesn't exist
        pytest_path = os.path.join(project_path, "pytest.ini")
        if not os.path.exists(pytest_path):
            with open(pytest_path, "w") as f:
                f.write("[pytest]\npython_files = test_*.py\n")
            log_fn(f"Created: {pytest_path}")

    def create_module_with_test(self, project_path, module_name):
        """Create a new module with a corresponding test file"""
        # Create implementation file
        module_path = os.path.join(project_path, "src", f"{module_name}.py")
        with open(module_path, "w") as f:
            f.write(f"""# {module_name}.py
# Implementation for {module_name}

class {module_name.capitalize()}:
    \"\"\"
    Implementation class for {module_name}
    \"\"\"

    def __init__(self):
        pass

    # Add methods here
""")

        # Create test file
        test_path = os.path.join(project_path, "tests", f"test_{module_name}.py")
        with open(test_path, "w") as f:
            f.write(f"""# test_{module_name}.py
# Tests for {module_name}

import pytest
from src.{module_name} import {module_name.capitalize()}

def test_{module_name}_creation():
    \"\"\"Test that {module_name.capitalize()} can be instantiated\"\"\"
    instance = {module_name.capitalize()}()
    assert instance is not None
""")

        return module_path, test_path

    def run_tests(self, project_path=None, on_complete=None):
        """Run pytest on the project asynchronously if on_complete is provided"""
        if not project_path:
            self.log("No project path specified")
            if on_complete:
                on_complete(False, "", "No project path specified")
            return False, "", "No project path specified"

        command = ["pytest", "-v"]

        # If on_complete is provided, we use ThreadManager
        if on_complete:
            from src.utils.thread_manager import thread_manager
            task_id = f"tests_{os.path.basename(project_path)}"

            def handle_complete(ret, stdout, stderr):
                self.log(f"Test command finished with code: {ret}")
                if stdout: self.log("Test output:\n" + stdout)
                if stderr: self.log("Test errors:\n" + stderr)
                on_complete(ret == 0, stdout, stderr)

            thread_manager.run_subprocess(command, task_id, on_complete=handle_complete, cwd=project_path)
            return True # Indicates started
        else:
            try:
                # Fallback to blocking for non-UI/legacy use cases
                result = subprocess.run(
                    command,
                    cwd=project_path,
                    capture_output=True,
                    encoding='utf-8',
                    errors='replace'
                )
                return result.returncode == 0, result.stdout, result.stderr
            except Exception as e:
                return False, "", str(e)

    def get_implementation_for_test(self, test_file_path):
        """Get the implementation file path corresponding to a test file"""
        # Extract module name from test file path
        file_name = os.path.basename(test_file_path)

        if not file_name.startswith("test_"):
            return None

        module_name = file_name[5:]  # Remove "test_"
        if module_name.endswith(".py"):
            module_name = module_name[:-3]  # Remove ".py"

        # Get project path
        project_path = os.path.dirname(os.path.dirname(test_file_path))

        # Implementation file path
        impl_path = os.path.join(project_path, "src", f"{module_name}.py")

        if os.path.exists(impl_path):
            return impl_path
        return None

    def get_test_for_implementation(self, impl_file_path):
        """Get the test file path corresponding to an implementation file"""
        # Extract module name from implementation file path
        file_name = os.path.basename(impl_file_path)

        if file_name.endswith(".py"):
            module_name = file_name[:-3]  # Remove ".py"
        else:
            module_name = file_name

        # Get project path
        project_path = os.path.dirname(os.path.dirname(impl_file_path))

        # Test file path
        test_path = os.path.join(project_path, "tests", f"test_{module_name}.py")

        if os.path.exists(test_path):
            return test_path
        return None

    def is_test_file(self, file_path):
        """Check if a file is a test file"""
        file_name = os.path.basename(file_path)
        return file_name.startswith("test_") and file_name.endswith(".py")

    def is_implementation_file(self, file_path):
        """Check if a file is an implementation file"""
        if not file_path.endswith(".py"):
            return False

        file_name = os.path.basename(file_path)
        return not file_name.startswith("test_") and file_name != "__init__.py"

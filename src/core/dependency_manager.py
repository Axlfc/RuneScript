import subprocess
import logging
import os


class DependencyManagementUnit:
    def __init__(self, project_path):
        self.project_path = project_path

    def install_dependencies(self, dependencies):
        for dep in dependencies:
            try:
                subprocess.run(["pip", "install", dep], check=True)
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to install dependency: {dep}: {e}")

    def save_requirements(self, dependencies):
        req_path = os.path.join(self.project_path, "requirements.txt")
        with open(req_path, "w", encoding='utf-8') as f:
            for dep in dependencies:
                f.write(f"{dep}\n")


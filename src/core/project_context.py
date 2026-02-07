import json
import logging
import os
from datetime import datetime


class ProjectContext:
    def __init__(self, project_name, description, path):
        self.project_name = project_name
        self.description = description
        self.path = path
        self.milestones = []
        self.tasks = []
        self.completed_tasks = []
        self.documentation = []
        self.current_phase = "Planning"

    def update_milestones(self, milestone):
        if milestone not in self.milestones:
            self.milestones.append(milestone)

    def complete_task(self, task):
        if task in self.tasks:
            self.tasks.remove(task)
            self.completed_tasks.append(task)

    def add_documentation(self, doc):
        self.documentation.append(doc)

    def to_dict(self):
        return {
            "project_name": self.project_name,
            "description": self.description,
            "path": self.path,
            "milestones": self.milestones,
            "tasks": self.tasks,
            "completed_tasks": self.completed_tasks,
            "documentation": self.documentation,
            "current_phase": self.current_phase,
            "last_updated": datetime.now().isoformat()
        }

    def save_context(self):
        context_path = os.path.join(self.path, "project_context.json")
        with open(context_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=4)

    @classmethod
    def load_context(cls, path):
        context_path = os.path.join(path, "project_context.json")
        with open(context_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        ctx = cls(data["project_name"], data["description"], path)
        ctx.milestones = data.get("milestones", [])
        ctx.tasks = data.get("tasks", [])
        ctx.completed_tasks = data.get("completed_tasks", [])
        ctx.documentation = data.get("documentation", [])
        ctx.current_phase = data.get("current_phase", "Planning")
        return ctx



def generate_readme(context: ProjectContext):
    """
    Generate a README.md file with project information and instructions.
    """
    readme_path = os.path.join(context.path, 'README.md')
    with open(readme_path, 'w', encoding='utf-8') as readme:
        readme.write(f"# {context.project_name}\n\n")
        readme.write(f"## Description\n{context.description}\n\n")
        readme.write("## Milestones\n")
        for milestone in context.milestones:
            readme.write(f"- {milestone}\n")
        readme.write("\n## Completed Tasks\n")
        for task in context.completed_tasks:
            readme.write(f"- {task}\n")
        readme.write("\n## How to Use\n")
        readme.write("1. Follow the setup instructions in `docs/SETUP.md`.\n")
        readme.write("2. Run the main script in the `src` folder.\n")
        readme.write("3. Run tests using `pytest`.\n")


def transition_to_next_phase(context: ProjectContext):
    """
    Transition the project to the next phase based on context and progress.
    """
    if context.current_phase == "Planning":
        context.current_phase = "Development"
    elif context.current_phase == "Development":
        if len(context.tasks) == 0:
            context.current_phase = "Testing"
        else:
            logging.info("Development phase ongoing, tasks remain.")
    elif context.current_phase == "Testing":
        if all(task in context.completed_tasks for task in context.tasks):
            context.current_phase = "Documentation"
        else:
            logging.info("Testing phase ongoing, not all tasks completed.")
    elif context.current_phase == "Documentation":
        context.current_phase = "Ready for Review"
    else:
        logging.info("Project is ready for review.")



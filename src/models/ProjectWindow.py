import os
import logging
import re
import subprocess
import threading
import queue
import tkinter as tk
import uuid
from tkinter import ttk, messagebox, filedialog, scrolledtext
from typing import Dict, Optional, Any


class AIResponseParser:
    @staticmethod
    def validate_prompt(prompt: str) -> bool:
        """
        Validate the AI project generation prompt.
        Ensures prompt meets minimum complexity and clarity requirements.
        """
        min_length = 20  # Minimum meaningful prompt length
        max_length = 500  # Prevent overly complex prompts

        if not prompt or len(prompt) < min_length:
            return False

        # Sophisticated validation
        required_keywords = ['create', 'develop', 'build', 'implement']
        return (len(prompt) <= max_length and
                any(keyword in prompt.lower() for keyword in required_keywords))

    @staticmethod
    def parse_ai_response(response: str) -> Dict[str, Any]:
        """
        Parse AI response into structured metadata
        """
        try:
            # Structured parsing with fallback
            parsed_data = {
                'project_structure': [],
                'initial_files': {},
                'test_cases': [],
                'dependencies': []
            }

            # Basic structure extraction
            structure_match = re.findall(r'Project Structure:(.*?)(?=Test Cases:|$)', response, re.DOTALL)
            print("HOLAAAAAAAA")
            if structure_match:
                parsed_data['project_structure'] = [
                    dir.strip() for dir in structure_match[0].split('\n') if dir.strip()
                ]

            # File content extraction
            file_matches = re.findall(r'File: (.*?)\n```(.*?)```', response, re.DOTALL)
            for filename, content in file_matches:
                parsed_data['initial_files'][filename.strip()] = content.strip()

            return parsed_data
        except Exception as e:
            logging.error(f"AI response parsing error: {e}")
            return {}


class ProjectManager:
    @staticmethod
    def create_project_structure(project_path: str, metadata: Dict[str, Any]) -> None:
        """
        Create a comprehensive and modular project structure
        """
        directories = [
                          'src', 'tests', 'docs', 'config', 'scripts'
                      ] + metadata.get('project_structure', [])

        for directory in directories:
            dir_path = os.path.join(project_path, directory)
            os.makedirs(dir_path, exist_ok=True)

        # Create initial files
        for filename, content in metadata.get('initial_files', {}).items():
            file_path = os.path.join(project_path, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        # Generate README
        readme_path = os.path.join(project_path, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as readme:
            readme.write(f"""# Project Development Guide

## Project Overview
Generated with Red-Green-Refactor IDE

## Setup Instructions
1. Ensure Python 3.8+ is installed
2. Create virtual environment: `python -m venv venv`
3. Activate virtual environment
4. Install dependencies: `pip install -r requirements.txt`
5. Run tests: `pytest`

## Development Workflow
- Write tests first
- Implement minimal code to pass tests
- Continuously refactor
""")


class RedGreenRefactorIDE:
    def __init__(self, root=None):
        self.root = root or tk.Tk()
        self.root.title("Red-Green-Refactor IDE")
        self.root.geometry("1400x900")

        self.ai_task_queue = queue.Queue()
        self.ai_response_queue = queue.Queue()
        self.setup_logging()
        self.setup_menu()
        self.create_main_layout()
        self.poll_queue()  # Start polling the queue
        self.projects_base_dir = os.path.join('data', 'projects')
        self.current_project_files = {}
        os.makedirs(self.projects_base_dir, exist_ok=True)

    def poll_queue(self):
        """
        Process AI responses from the queue on the main thread.
        """
        try:
            while not self.ai_response_queue.empty():
                status, data = self.ai_response_queue.get_nowait()
                if status == "success":
                    self.finalize_project_generation(data)
                elif status == "error":
                    self.handle_generation_failure(error_message=data)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.poll_queue)  # Poll the queue every 100ms

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Existing menu setup with additional error handling
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.safe_new_project)
        file_menu.add_command(label="Open Project", command=self.safe_open_project)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

    def safe_new_project(self):
        try:
            self.new_project()
        except Exception as e:
            messagebox.showerror("Project Creation Error", str(e))
            logging.error(f"Project creation failed: {e}")

    def safe_open_project(self):
        try:
            self.open_project()
        except Exception as e:
            messagebox.showerror("Project Open Error", str(e))
            logging.error(f"Project open failed: {e}")

    def create_main_layout(self):
        # Existing main layout with enhanced error handling
        try:
            main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
            main_container.pack(fill=tk.BOTH, expand=True)

            # Layout components with extensive error handling
            left_panel = self.create_left_panel(main_container)
            right_panel = self.create_right_panel(main_container)

            main_container.add(left_panel)
            main_container.add(right_panel)

            self.create_command_bar(self.root)
        except Exception as e:
            messagebox.showerror("Layout Initialization Error", str(e))
            logging.critical(f"Layout creation failed: {e}")

    def create_left_panel(self, parent):
        left_panel = ttk.Frame(parent)
        self.project_tree = self.create_project_tree(left_panel)
        self.output_console = self.create_output_console(left_panel)
        return left_panel

    def create_right_panel(self, parent):
        right_panel = ttk.PanedWindow(parent, orient=tk.VERTICAL)
        self.ai_plan_listbox = self.create_ai_plan(right_panel)
        self.file_editor = self.create_file_editor(right_panel)
        return right_panel

    def create_project_tree(self, parent):
        tree = ttk.Treeview(parent, columns=('path',), show='tree')
        tree.pack(fill=tk.BOTH, expand=True)
        tree.bind('<<TreeviewSelect>>', self.on_file_select)
        return tree

    def create_output_console(self, parent):
        console = scrolledtext.ScrolledText(
            parent, height=15, wrap=tk.WORD, state='disabled'
        )
        console.pack(fill=tk.X, side=tk.BOTTOM)
        return console

    def create_ai_plan(self, parent):
        plan_frame = ttk.LabelFrame(parent, text="AI Project Plan")
        listbox = tk.Listbox(plan_frame, height=10)
        listbox.pack(fill=tk.BOTH, expand=True)
        parent.add(plan_frame)
        return listbox

    def create_file_editor(self, parent):
        editor_frame = ttk.LabelFrame(parent, text="File Contents")
        editor = scrolledtext.ScrolledText(
            editor_frame, wrap=tk.WORD, undo=True
        )
        editor.pack(fill=tk.BOTH, expand=True)
        editor.bind('<<Modified>>', self.on_file_modified)
        parent.add(editor_frame)
        return editor

    def create_command_bar(self, parent):
        command_bar = ttk.Frame(parent)
        command_bar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(command_bar, text="Project Prompt:").pack(side=tk.LEFT, padx=(0, 5))
        self.prompt_entry = ttk.Entry(command_bar, width=50)
        self.prompt_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        button_frame = ttk.Frame(command_bar)
        button_frame.pack(side=tk.LEFT, padx=5)

        self.generate_btn = ttk.Button(
            button_frame, text="Generate Project", command=self.generate_project_with_ai
        )
        self.generate_btn.pack(side=tk.LEFT, padx=2)

        self.pause_btn = ttk.Button(
            button_frame, text="Pause", command=self.pause_project, state=tk.DISABLED
        )
        self.pause_btn.pack(side=tk.LEFT, padx=2)

        self.stop_btn = ttk.Button(
            button_frame, text="Stop", command=self.stop_project, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=2)

    def process_prompt_with_ai(self, combined_input: str) -> Optional[str]:
        ai_script_path = "src/models/ai_assistant.py"
        python_executable = 'python'

        try:
            command = [python_executable, ai_script_path, combined_input]
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            ai_response, error = process.communicate()
            if process.returncode != 0 or error:
                raise Exception(f"AI Assistant Error: {error.strip()}")
            return ai_response.strip()
        except Exception as e:
            self.log_output(f"Failed to communicate with AI: {e}")
            return None

    def new_project(self):
        project_id = str(uuid.uuid4())
        project_path = os.path.join(self.projects_base_dir, project_id)

        try:
            os.makedirs(project_path, exist_ok=True)
            os.makedirs(os.path.join(project_path, 'src'), exist_ok=True)
            os.makedirs(os.path.join(project_path, 'tests'), exist_ok=True)

            with open(os.path.join(project_path, 'README.md'), 'w') as f:
                f.write(f"# Project {project_id}\n\nCreated with Red-Green-Refactor IDE")

            self.current_project = project_path
            self.populate_project_tree()
            self.log_output(f"New project created: {project_id}")

        except Exception as e:
            self.log_output(f"Error creating project: {e}")
            messagebox.showerror("Project Creation Error", str(e))

    def open_project(self):
        os.makedirs(self.projects_base_dir, exist_ok=True)
        project_path = filedialog.askdirectory(
            title="Open Existing Project",
            initialdir=self.projects_base_dir
        )

        if project_path and os.path.exists(project_path):
            if os.path.exists(os.path.join(project_path, 'src')) and \
                    os.path.exists(os.path.join(project_path, 'tests')):
                self.current_project = project_path
                self.populate_project_tree()
                self.log_output(f"Opened project: {os.path.basename(project_path)}")
            else:
                messagebox.showerror(
                    "Invalid Project",
                    "Selected directory is not a valid project. Must contain 'src' and 'tests' directories."
                )

    def generate_project_with_ai(self):
        """
        Validate prompt and start AI generation in a new thread.
        """
        prompt = self.prompt_entry.get().strip()

        if not AIResponseParser.validate_prompt(prompt):
            messagebox.showwarning("Invalid Prompt", "Please provide a clear, meaningful project description.")
            return

        self.toggle_generation_ui(False)

        # Start AI generation in a background thread
        threading.Thread(
            target=self.threaded_ai_generation,
            args=(prompt,),
            daemon=True
        ).start()

    def threaded_ai_generation(self, prompt):
        """
        Run AI generation logic in a separate thread and enqueue results.
        """
        try:
            ai_response = self.process_prompt_with_ai(prompt)
            if ai_response:
                parsed_metadata = AIResponseParser.parse_ai_response(ai_response)
                self.ai_response_queue.put(("success", parsed_metadata))
            else:
                self.ai_response_queue.put(("error", "AI response is empty."))
        except Exception as e:
            logging.error(f"AI generation thread error: {e}")
            self.ai_response_queue.put(("error", str(e)))

    def finalize_project_generation(self, parsed_metadata):
        """
        Finalize the project generation and update UI.
        """
        try:
            # Generate a sanitized project ID
            project_id = str(uuid.uuid4()).replace("-", "")
            project_path = os.path.normpath(os.path.join(self.projects_base_dir, project_id))

            # Create the project structure
            ProjectManager.create_project_structure(project_path, parsed_metadata)

            # Set the current project and refresh the UI
            self.current_project = project_path
            self.populate_project_tree()

            # Format project structure for AI Plan
            project_structure = parsed_metadata.get('project_structure', [])
            formatted_structure = '\n'.join(project_structure)  # Convert list to string
            self.update_ai_plan(formatted_structure)

            self.log_output(f"Project {project_id} generated successfully at {project_path}!")

        except Exception as e:
            logging.error(f"Project finalization error: {e}")
            messagebox.showerror("Generation Error", str(e))
        finally:
            self.toggle_generation_ui(True)

    def handle_generation_failure(self, error_message="AI generation failed. Please try again."):
        """
        Handle AI generation failure and update UI.
        """
        messagebox.showerror("AI Generation Failed", error_message)
        self.toggle_generation_ui(True)

    def toggle_generation_ui(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.prompt_entry.config(state=state)
        self.generate_btn.config(state=state)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)

    def populate_project_tree(self):
        try:
            self.project_tree.delete(*self.project_tree.get_children())
            self.current_project_files.clear()

            for root, dirs, files in os.walk(self.current_project):
                parent = self.project_tree.insert(
                    '',
                    'end',
                    text=os.path.basename(root),
                    values=(root,)
                )
                for file in files:
                    file_path = os.path.join(root, file)
                    file_id = self.project_tree.insert(
                        parent,
                        'end',
                        text=file,
                        values=(file_path,)
                    )
                    self.current_project_files[file_id] = file_path
        except Exception as e:
            logging.error(f"Error in populate_project_tree: {e}")

    def on_file_select(self, event):
        selected_item = self.project_tree.selection()
        if selected_item:
            file_path = self.project_tree.item(selected_item[0])['values'][0]
            if os.path.isfile(file_path):
                self.current_file_path = file_path
                with open(file_path, 'r') as f:
                    content = f.read()
                    self.file_editor.delete('1.0', tk.END)
                    self.file_editor.insert('1.0', content)
                    self.file_editor.edit_modified(False)

    def on_file_modified(self, event=None):
        pass

    def update_ai_plan(self, plan_text: str):
        self.ai_plan_listbox.delete(0, tk.END)
        steps = plan_text.split('\n')
        for step in steps:
            if step.strip():
                self.ai_plan_listbox.insert(tk.END, step)

    def run_tests(self):
        try:
            result = subprocess.run(
                ['pytest'],
                capture_output=True,
                text=True,
                cwd=self.current_project
            )
            self.log_output(result.stdout)
            if result.returncode == 0:
                self.log_output("Tests passed successfully!")
            else:
                self.log_output("Tests failed:\n" + result.stderr)
        except Exception as e:
            self.log_output(f"Test execution error: {e}")

    def log_output(self, message: str):
        self.output_console.config(state='normal')
        self.output_console.insert(tk.END, message + "\n")
        self.output_console.see(tk.END)
        self.output_console.config(state='disabled')

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler('red_green_refactor.log'),
                logging.StreamHandler()
            ]
        )

    def show_about(self):
        messagebox.showinfo(
            "About Red-Green-Refactor IDE",
            "A comprehensive development environment for Test-Driven Development."
        )

    def pause_project(self):
        self.log_output("Project generation paused.")

    def stop_project(self):
        self.log_output("Project generation stopped.")
        self.prompt_entry.config(state=tk.NORMAL)
        self.generate_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)


if __name__ == '__main__':
    root = tk.Tk()
    app = RedGreenRefactorIDE(root)
    root.mainloop()

